from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging
import json
from datetime import datetime
from typing import Optional

from core.database import get_db
from core.security import get_current_learner, security
from schemas.schemas import TutorSessionResponse, TutorChat
from models.models import TutorSession, Subject
from services.rag_engine import rag_engine
from services.event_publisher import event_publisher
from services.identity_service_client import identity_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/learning",
    tags=["tutor-sessions"],
    dependencies=[Depends(security)]
)


@router.post("/sessions/start")
async def start_tutor_session(
    request: Request,
    course_id: int,
    subject_id: int,
    topic: str = "General",
    db: Session = Depends(get_db)
):
    """Start a new AI tutor session"""
    
    try:
        # Get current user from identity service
        current_user = await get_current_learner(request)
        # Fallback to email if id/userId is missing
        user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        # Ensure subject exists (Bypass ForeignKeyViolation by auto-creating if missing)
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            logger.info(f"Subject {subject_id} not found in DB. Auto-creating to satisfy foreign key.")
            new_subject = Subject(
                id=subject_id,
                name=f"Topic {subject_id}",
                description=f"Auto-generated subject for tutoring on {topic}"
            )
            db.add(new_subject)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"Could not auto-create subject {subject_id}: {str(e)}")
        
        # Create new session
        session = TutorSession(
            user_id=user_id,
            subject_id=subject_id,
            topic=topic,
            messages=json.dumps([]),  # Empty message history
            duration_minutes=0,
            created_at=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Publish session started event
        await event_publisher.publish_learner_session_started(
            learner_id=user_id,
            course_id=str(course_id),
            session_id=str(session.id),
            module_id=str(subject_id)
        )
        
        logger.info(f"Session {session.id} started for user {user_id}")
        
        # Generate AI greeting
        greeting_prompt = f"The user just started a session on {topic}. Please provide a friendly greeting and ask what they'd like to learn."
        ai_response = await rag_engine.generate_response(
            learner_id=user_id,
            course_id=str(course_id),
            learner_message="Hi, I'd like to start learning",
            conversation_history=[]
        )
        
        return {
            "session_id": session.id,
            "topic": topic,
            "ai_greeting": ai_response.get('response', 'Hello! I\'m here to help you learn.'),
            "session_started_at": session.created_at,
            "status": "active"
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions so the specific status code/detail is preserved
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error starting session: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start tutoring session: {str(e)}"
        )


@router.post("/sessions/{session_id}/message")
async def send_message_to_tutor(
    request: Request,
    session_id: int,
    chat: TutorChat,
    db: Session = Depends(get_db)
):
    """Send a message to the AI tutor and get response"""
    
    try:
        # Get current user
        current_user = await get_current_learner(request)
        # Fallback to email if id/userId is missing
        user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        email = current_user.get('email')
        
        logger.info(f"DEBUG: Looking for session {session_id} for user_id: '{user_id}' (Email: {email})")
        
        # Log all sessions for this user to debug
        all_user_sessions = db.query(TutorSession).filter(TutorSession.user_id == user_id).all()
        logger.info(f"DEBUG: Found {len(all_user_sessions)} total sessions in DB for this user_id")
        for s in all_user_sessions:
            logger.info(f"DEBUG: Existing Session in DB - ID: {s.id}, UserID: '{s.user_id}', Topic: {s.topic}")

        # Get session
        session = db.query(TutorSession).filter(
            TutorSession.id == session_id,
            TutorSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Parse conversation history
        messages = json.loads(session.messages) if session.messages else []
        
        # Add user message to history
        messages.append({
            "role": "user",
            "content": chat.message
        })
        
        # Generate AI response using RAG
        ai_response = await rag_engine.generate_response(
            learner_id=user_id,
            course_id=chat.subject_id,
            learner_message=chat.message,
            conversation_history=messages[:-1],  # Exclude the message just added
            course_title=chat.context or "Course"
        )
        
        # Check if escalation is needed
        if ai_response.get('escalation_needed'):
            await event_publisher.publish_escalation_triggered(
                learner_id=user_id,
                session_id=str(session_id),
                course_id=str(chat.subject_id),
                reason="Low confidence or repeated questions"
            )
        
        # Add AI response to history
        messages.append({
            "role": "assistant",
            "content": ai_response.get('response')
        })
        
        # Update session with new messages
        session.messages = json.dumps(messages)
        session.updated_at = datetime.utcnow()
        db.commit()
        
        # Publish AI response event for analytics
        await event_publisher.publish_ai_response_generated(
            learner_id=user_id,
            session_id=str(session_id),
            course_id=str(chat.subject_id),
            model_used=ai_response.get('model_used', 'gpt-4'),
            tokens_used=ai_response.get('metadata', {}).get('tokens', 0),
            confidence_score=ai_response.get('average_confidence', 0)
        )
        
        return {
            "session_id": session_id,
            "user_message": chat.message,
            "ai_response": ai_response.get('response'),
            "confidence_score": ai_response.get('average_confidence'),
            "escalation_needed": ai_response.get('escalation_needed', False),
            "suggestions": ai_response.get('metadata', {}).get('retrieved_sources', [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get("/sessions/{session_id}")
async def get_session(
    request: Request,
    session_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve session details and transcript"""
    
    try:
        current_user = await get_current_learner(request)
        # Fallback to email if id/userId is missing
        user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        session = db.query(TutorSession).filter(
            TutorSession.id == session_id,
            TutorSession.user_id == user_id
        ).first()
        
        if not session:
            logger.info(f"Session {session_id} not found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        messages = json.loads(session.messages) if session.messages else []
        
        return {
            "session_id": session.id,
            "topic": session.topic,
            "messages": messages,
            "created_at": session.created_at,
            "ended_at": session.ended_at,
            "status": "ended" if session.ended_at else "active"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )


@router.post("/sessions/{session_id}/end")
async def end_tutor_session(
    request: Request,
    session_id: int,
    feedback: str = None,
    difficulty: int = None,
    db: Session = Depends(get_db)
):
    """End a tutor session and get summary"""
    
    try:
        current_user = await get_current_learner(request)
        # Fallback to email if id/userId is missing
        user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        session = db.query(TutorSession).filter(
            TutorSession.id == session_id,
            TutorSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Parse messages
        messages = json.loads(session.messages) if session.messages else []
        
        # Calculate duration
        if session.created_at:
            duration = (datetime.utcnow() - session.created_at).total_seconds() / 60
            session.duration_minutes = int(duration)
        
        session.ended_at = datetime.utcnow()
        
        # Extract topics learned from conversation
        topics_learned = [msg['content'][:50] for msg in messages[::2]][:5]
        
        db.commit()
        
        # Publish session completed event
        await event_publisher.publish_learner_session_completed(
            learner_id=user_id,
            course_id=str(session.subject_id),
            session_id=str(session.id),
            duration_minutes=session.duration_minutes,
            topics_learned=topics_learned,
            escalated=False
        )
        
        logger.info(f"Session {session_id} ended for user {user_id}")
        
        return {
            "session_id": session_id,
            "duration_minutes": session.duration_minutes,
            "messages_count": len(messages),
            "session_summary": {
                "topics_covered": topics_learned,
                "total_exchanges": len([m for m in messages if m['role'] == 'user']),
                "quality_feedback": feedback or "Not provided"
            },
            "ended_at": session.ended_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end session"
        )


@router.get("/sessions")
async def list_sessions(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all sessions for the current user"""
    
    try:
        current_user = await get_current_learner(request)
        # Fallback to email if id/userId is missing
        user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        sessions_query = db.query(TutorSession).filter(
            TutorSession.user_id == user_id
        )
        
        total_count = sessions_query.count()
        sessions = sessions_query.offset(skip).limit(limit).all()
        
        return {
            "sessions": [
                {
                    "id": s.id,
                    "topic": s.topic,
                    "duration_minutes": s.duration_minutes,
                    "created_at": s.created_at,
                    "ended_at": s.ended_at,
                    "status": "ended" if s.ended_at else "active"
                }
                for s in sessions
            ],
            "total": total_count
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error listing sessions: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )
