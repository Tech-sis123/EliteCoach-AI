from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user, get_current_user_id
from app.models.users import User
from app.services.ai_tutor import ai_tutor_service
from app.schemas.ai_tutor import SessionMessageRead, SessionSummaryRead, KnowledgeCheckRead, KnowledgeCheckResponse
from pydantic import BaseModel
from typing import List
import uuid

router = APIRouter()

class SessionStart(BaseModel):
    lesson_id: uuid.UUID

class MessageIn(BaseModel):
    message: str

class CheckAnswerIn(BaseModel):
    answer: str

@router.post("/session/start")
async def start_session(
    data: SessionStart,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await ai_tutor_service.start_session(db, user_id, data.lesson_id)

@router.post("/session/{id}/message")
async def send_message(
    id: uuid.UUID,
    data: MessageIn,
    db: AsyncSession = Depends(get_db)
):
    return await ai_tutor_service.get_response(db, id, data.message)

@router.get("/session/{id}/messages", response_model=List[SessionMessageRead])
async def get_messages(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await ai_tutor_service.get_messages(db, id)

@router.get("/session/{id}/summary", response_model=SessionSummaryRead)
async def get_summary(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await ai_tutor_service.get_summary(db, id)

@router.get("/session/{id}/escalation-status")
async def get_escalation_status(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if the session has been escalated to a human tutor."""
    from app.models.ai_tutor import Escalation
    from sqlalchemy import select
    query = select(Escalation).where(Escalation.session_id == id)
    result = await db.execute(query)
    esc = result.scalar_one_or_none()
    return {
        "is_escalated": esc is not None,
        "status": esc.status if esc else None,
        "resolved": esc.resolved if esc else False
    }

@router.get("/learning/lesson/{id}/checks", response_model=List[KnowledgeCheckRead])
async def get_lesson_checks(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await ai_tutor_service.get_knowledge_checks(db, id)

@router.post("/learning/lesson/{id}/checks/{check_id}", response_model=KnowledgeCheckResponse)
async def submit_check_response(
    id: uuid.UUID,
    check_id: uuid.UUID,
    data: CheckAnswerIn,
    db: AsyncSession = Depends(get_db)
):
    # In a real app we'd get the session_id from active sessions for this user+lesson
    # For now, this is a simplified version
    from app.models.ai_tutor import LessonSession, SessionStatus
    from sqlalchemy import select, and_
    result = await db.execute(select(LessonSession).where(and_(LessonSession.lesson_id == id, LessonSession.status == SessionStatus.ACTIVE)).limit(1))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=400, detail="No active session for this lesson")
    
    return await ai_tutor_service.submit_knowledge_check(db, session.id, check_id, data.answer)
