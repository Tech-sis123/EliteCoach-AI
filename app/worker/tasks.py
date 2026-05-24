from app.worker.celery_app import celery_app
from app.core.config import settings
import logging
import httpx
from twilio.rest import Client

logger = logging.getLogger(__name__)

@celery_app.task(name="send_whatsapp_notification")
def send_whatsapp_notification(phone: str, message: str):
    """Task to send WhatsApp message via Twilio"""
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_NUMBER]):
        logger.warning("Twilio keys not configured. Skipping WhatsApp.")
        return False
        
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # Ensure phone is in E.164 format and prefix with whatsapp:
        to_number = f"whatsapp:{phone}" if not phone.startswith("whatsapp:") else phone
        
        message = client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            body=message,
            to=to_number
        )
        logger.info(f"WhatsApp sent: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp: {str(e)}")
        return False

@celery_app.task(name="send_email_notification")
def send_email_notification(email: str, subject: str, body: str):
    """Task to send email via Brevo (formerly Sendinblue)"""
    if not settings.BREVO_API_KEY:
        logger.warning("Brevo API key not configured. Skipping Email.")
        return False
        
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": settings.BREVO_API_KEY
        }
        data = {
            "sender": {"name": settings.PROJECT_NAME, "email": "notifications@elitecoach.ai"},
            "to": [{"email": email}],
            "subject": subject,
            "htmlContent": body
        }
        
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
        logger.info(f"Email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Email: {str(e)}")
        return False

@celery_app.task(name="generate_weekly_digest")
def generate_weekly_digest():
    """Scheduled task to generate learner progress digests"""
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.models.users import User, UserRole
    from app.models.learning import LearningPath, PathItem
    from sqlalchemy import select, func
    from datetime import datetime, timedelta

    async def _process():
        async with AsyncSessionLocal() as db:
            # Get all learners
            query = select(User).where(User.role == UserRole.LEARNER)
            result = await db.execute(query)
            learners = result.scalars().all()
            
            for learner in learners:
                # Get progress in last 7 days
                week_ago = datetime.utcnow() - timedelta(days=7)
                progress_query = select(func.count(PathItem.id)).join(LearningPath).where(
                    LearningPath.learner_profile_id == learner.id,
                    PathItem.status == "completed",
                    PathItem.unlocked_at >= week_ago
                )
                count_res = await db.execute(progress_query)
                completed_count = count_res.scalar() or 0
                
                if completed_count > 0:
                    send_email_notification.delay(
                        email=learner.email,
                        subject="Your Weekly Learning Progress",
                        body=f"Hi {learner.full_name}, you completed {completed_count} lessons this week! Keep it up."
                    )
    
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.run_until_complete(_process())
    else:
        return asyncio.run(_process())

@celery_app.task(name="process_payouts")
def process_payouts():
    """Scheduled task to process tutor earnings payouts via Paystack"""
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.models.users import User, UserRole
    from app.models.ai_tutor import Escalation
    from sqlalchemy import select, update
    
    async def _process():
        async with AsyncSessionLocal() as db:
            # Find tutors with resolved but unpaid escalations
            # Simplified: process all resolved escalations
            query = select(User).where(User.role == UserRole.TUTOR)
            result = await db.execute(query)
            tutors = result.scalars().all()
            
            for tutor in tutors:
                esc_query = select(func.count(Escalation.id)).where(
                    Escalation.assigned_tutor_id == tutor.id,
                    Escalation.status == "resolved"
                )
                esc_count_res = await db.execute(esc_query)
                count = esc_count_res.scalar() or 0
                
                if count > 0:
                    amount = count * settings.TUTOR_PER_CASE_NGN
                    logger.info(f"Processing payout of {amount} NGN for tutor {tutor.email}")
                    # Integration with Paystack Transfer API would go here
                    # For now, mark as processed or log
                    pass

    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.run_until_complete(_process())
    else:
        return asyncio.run(_process())

@celery_app.task(name="send_learning_reminders")
def send_learning_reminders():
    """Scheduled task to nudge inactive learners"""
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.models.users import User, UserRole
    from app.models.ai_tutor import LessonSession
    from sqlalchemy import select, func
    from datetime import datetime, timedelta

    async def _process():
        async with AsyncSessionLocal() as db:
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            # Find learners with no session in 3 days
            # Subquery for last session
            subq = select(LessonSession.learner_id).where(LessonSession.started_at >= three_days_ago)
            query = select(User).where(
                User.role == UserRole.LEARNER,
                ~User.id.in_(subq)
            )
            result = await db.execute(query)
            inactive_users = result.scalars().all()
            
            for user in inactive_users:
                msg = f"Hi {user.full_name}, we missed you! Jump back into your learning path on Elite Coach AI."
                if user.phone:
                    send_whatsapp_notification.delay(user.phone, msg)
                send_email_notification.delay(user.email, "Come back and learn!", msg)

    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.run_until_complete(_process())
    else:
        return asyncio.run(_process())

@celery_app.task(name="generate_learning_path_task")
def generate_learning_path_task(user_id: str):
    """Refined task to generate learning path using AI and learner profile."""
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.services.onboarding import onboarding_service
    import uuid

    async def _async_run():
        async with AsyncSessionLocal() as db:
            await onboarding_service.generate_learning_path(db, uuid.UUID(user_id))

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(_async_run()) # In a worker, we might be in an async loop
    else:
        asyncio.run(_async_run())

@celery_app.task(name="trigger_escalation_check_task")
def trigger_escalation_check_task(session_id: str, latest_message: str):
    """Check if a session should be escalated based on latest message."""
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.services.ai_tutor import ai_tutor_service
    import uuid

    async def _async_run():
        async with AsyncSessionLocal() as db:
            from sqlalchemy.orm import selectinload
            from sqlalchemy import select
            from app.models.ai_tutor import LessonSession, SessionMessage
            
            # Load message history
            query = select(SessionMessage).where(SessionMessage.session_id == uuid.UUID(session_id)).order_by(SessionMessage.created_at.asc())
            result = await db.execute(query)
            history = result.scalars().all()
            
            await ai_tutor_service.escalation_trigger_service(db, uuid.UUID(session_id), latest_message, history)

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(_async_run())
    else:
        asyncio.run(_async_run())

@celery_app.task(name="track_event_task")
def track_event_task(event_type: str, actor_id: str = None, entity_type: str = None, entity_id: str = None, metadata: dict = None):
    """Background task to record analytics events."""
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.models.analytics import Event
    import uuid

    async def _async_record():
        async with AsyncSessionLocal() as db:
            event = Event(
                event_type=event_type,
                actor_id=uuid.UUID(actor_id) if actor_id else None,
                entity_type=entity_type,
                entity_id=uuid.UUID(entity_id) if entity_id else None,
                payload=metadata
            )
            db.add(event)
            await db.commit()

    loop = asyncio.get_event_loop()
    if loop.is_running():
        # In a worker, the loop might be running if using some async drivers
        return loop.run_until_complete(_async_record())
    else:
        return asyncio.run(_async_record())
