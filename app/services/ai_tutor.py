from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, desc
from app.models.ai_tutor import LessonSession, SessionMessage, SessionStatus, Escalation
from app.models.content import RagChunk, Lesson
from app.models.learning import LearnerProfile
from app.services.analytics import analytics_service
from app.services.escalation import escalation_service
from app.integrations.anthropic_client import anthropic_client
from app.core.logging import logger
import uuid
import json

class AiTutorService:
    async def start_session(self, db: AsyncSession, user_id: uuid.UUID, lesson_id: uuid.UUID):
        session = LessonSession(
            learner_id=user_id,
            lesson_id=lesson_id,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_response(self, db: AsyncSession, session_id: uuid.UUID, user_message: str):
        # 1. Load session and context
        query = select(LessonSession).where(LessonSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one()
        
        # 2. Get history
        history_query = select(SessionMessage).where(SessionMessage.session_id == session_id).order_by(desc(SessionMessage.created_at)).limit(10)
        history_result = await db.execute(history_query)
        history = history_result.scalars().all()[::-1]
        
        # 3. RAG - Vector Search (Simplified for and placeholder for pgvector)
        # In a real implementation, we would use pgvector here.
        rag_query = select(RagChunk).where(RagChunk.lesson_id == session.lesson_id).limit(3)
        rag_result = await db.execute(rag_query)
        chunks = rag_result.scalars().all()
        context_text = "\n".join([c.chunk_text for c in chunks])
        
        # 4. Build Prompts
        lesson_query = select(Lesson).where(Lesson.id == session.lesson_id)
        lesson_result = await db.execute(lesson_query)
        lesson = lesson_result.scalar_one()

        system_prompt = f"""
        You are a tutor for the lesson titled "{lesson.title}".
        You must only answer using the provided lesson context below.
        If the question cannot be answered from the context, say:
        "I cannot answer that from this lesson. Would you like me to escalate to a human tutor?"
        Do not make up information.
        
        Lesson Context:
        {context_text}
        """
        
        formatted_history = []
        for msg in history:
            formatted_history.append({"role": msg.role, "content": msg.content})
        
        formatted_history.append({"role": "user", "content": user_message})
        
        # 5. Call AI
        reply = await anthropic_client.get_completion(system_prompt, formatted_history)
        
        # 6. Save messages
        user_msg_db = SessionMessage(session_id=session_id, role="user", content=user_message)
        assistant_msg_db = SessionMessage(session_id=session_id, role="assistant", content=reply)
        db.add(user_msg_db)
        db.add(assistant_msg_db)
        
        # Track event
        await analytics_service.track(
            event_type="lesson.ai_message_sent",
            actor_id=session.learner_id,
            entity_type="lesson_session",
            entity_id=session_id
        )

        # 7. Escalation Triggers
        escalated = False
        escalation_id = None
        
        # Simple keywords for frustration
        frustrated_keywords = ['i dont understand', "don't get it", 'this makes no sense', 'confused', 'lost']
        if any(keyword in user_message.lower() for keyword in frustrated_keywords):
            esc = await escalation_service.create_escalation(db, session_id, "frustrated_language")
            escalated = True
            escalation_id = esc.id
             
        await db.commit()
        
        return {
            "reply": reply,
            "escalated": escalated,
            "escalation_id": escalation_id
        }

ai_tutor_service = AiTutorService()
