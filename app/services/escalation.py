from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai_tutor import Escalation, LessonSession, SessionStatus
from app.core.logging import logger
import uuid

class EscalationService:
    async def create_escalation(self, db: AsyncSession, session_id: uuid.UUID, reason: str):
        # 1. Fetch session
        from sqlalchemy import select
        result = await db.execute(select(LessonSession).where(LessonSession.id == session_id))
        session = result.scalar_one()

        # 2. Create escalation
        escalation = Escalation(
            session_id=session_id,
            learner_id=session.learner_id,
            lesson_id=session.lesson_id,
            trigger_reason=reason
        )
        db.add(escalation)
        
        # 3. Update session status
        session.status = SessionStatus.ESCALATED
        
        await db.commit()
        await db.refresh(escalation)
        
        # 4. Notify (Logic for Twilio/Brevo goes here)
        logger.info("escalation_created", escalation_id=str(escalation.id), reason=reason)
        
        return escalation

escalation_service = EscalationService()
