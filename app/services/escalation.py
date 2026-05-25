from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from app.models.ai_tutor import Escalation, LessonSession, SessionStatus
from app.models.users import User, UserRole, UserRoleEnum
from app.models.content import Lesson, Course, Module
from app.core.logging import logger
from fastapi import HTTPException
from datetime import datetime
import uuid

class EscalationService:
    async def create_escalation(self, db: AsyncSession, session_id: uuid.UUID, reason: str, manual_reason: str = None):
        """Creates an escalation and updates session status."""
        result = await db.execute(select(LessonSession).where(LessonSession.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
             raise HTTPException(status_code=404, detail="Session not found")

        escalation = Escalation(
            session_id=session_id,
            learner_id=session.learner_id,
            lesson_id=session.lesson_id,
            trigger_reason=reason,
            manual_reason=manual_reason
        )
        db.add(escalation)
        
        session.status = SessionStatus.ESCALATED
        
        await db.commit()
        await db.refresh(escalation)
        
        logger.info("escalation_created", escalation_id=str(escalation.id), reason=reason)
        return escalation

    async def assign_tutor(self, db: AsyncSession, escalation: Escalation):
        """Finds a tutor_responder whose subject area matches the lesson domain."""
        # Get lesson domain
        domain_query = (
            select(Course.domain)
            .join(Module, Module.course_id == Course.id)
            .join(Lesson, Lesson.module_id == Module.id)
            .where(Lesson.id == escalation.lesson_id)
        )
        domain = (await db.execute(domain_query)).scalar()
        
        if not domain:
            logger.error("domain_not_found_for_assignment", lesson_id=str(escalation.lesson_id))
            return

        # Find tutor with matching subject area
        tutor_query = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .where(
                and_(
                    UserRole.role == UserRoleEnum.TUTOR_RESPONDER,
                    User.subject_area == domain,
                    User.is_active == True
                )
            )
            .limit(1)
        )
        tutor = (await db.execute(tutor_query)).scalar_one_or_none()

        if tutor:
            escalation.assigned_tutor_id = tutor.id
            escalation.status = "assigned"
            logger.info("tutor_assigned", escalation_id=str(escalation.id), tutor_id=str(tutor.id))
        
        return tutor

    async def update_escalation_status(
        self, 
        db: AsyncSession, 
        escalation_id: uuid.UUID, 
        user: User,
        new_status: str
    ):
        """Updates escalation status with RBAC checks."""
        # Fetch escalation with session
        query = (
            select(Escalation)
            .where(Escalation.id == escalation_id)
            .options(selectinload(Escalation.session))
        )
        result = await db.execute(query)
        escalation = result.scalar_one_or_none()

        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")

        # Fetch roles to avoid MissingGreenlet
        roles_query = select(UserRole.role).where(UserRole.user_id == user.id)
        user_roles = (await db.execute(roles_query)).scalars().all()
        
        is_learner = any(r in [UserRoleEnum.SOLO_LEARNER, UserRoleEnum.ORG_LEARNER] for r in user_roles)
        is_staff = any(r in [UserRoleEnum.PLATFORM_ADMIN, UserRoleEnum.TUTOR_RESPONDER] for r in user_roles)

        old_status = escalation.status

        if new_status == "cancelled":
            if is_learner:
                if escalation.learner_id != user.id:
                    raise HTTPException(status_code=403, detail="Not authorized to cancel this request")
                if escalation.status not in ["open", "assigned"]:
                    raise HTTPException(status_code=403, detail="Cannot cancel an escalation that is already being handled")
            elif not is_staff:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            # Revert session status
            if escalation.session:
                escalation.session.status = SessionStatus.ACTIVE
            
            # Notify tutor if assigned
            if escalation.assigned_tutor_id:
                try:
                    from app.services.notification import notification_service
                    await notification_service.send_in_app(
                        db,
                        escalation.assigned_tutor_id,
                        "Escalation Cancelled",
                        "The learner has resolved their question and cancelled the request."
                    )
                except ImportError:
                    pass

        elif new_status == "resolved":
            if not is_staff:
                raise HTTPException(status_code=403, detail="Only staff can resolve escalations")
            escalation.resolved_at = datetime.utcnow()
            if escalation.session:
                escalation.session.status = SessionStatus.COMPLETED

        elif new_status == "in_progress":
            if not is_staff:
                 raise HTTPException(status_code=403, detail="Only staff can mark escalation as in_progress")

        # Update status
        escalation.status = new_status
        escalation.updated_at = datetime.utcnow()

        # Track event
        try:
            from app.services.analytics import analytics_service
            analytics_service.track(
                event_type="escalation.status_updated",
                actor_id=user.id,
                entity_type="escalation",
                entity_id=escalation_id,
                metadata={"old_status": old_status, "new_status": new_status}
            )
        except ImportError:
            pass

        await db.commit()
        await db.refresh(escalation)
        
        message = "Status updated."
        if new_status == "cancelled":
            message = "Escalation cancelled. You can continue chatting with the AI tutor."

        return {
            "escalation_id": str(escalation_id),
            "status": new_status,
            "message": message
        }

escalation_service = EscalationService()

