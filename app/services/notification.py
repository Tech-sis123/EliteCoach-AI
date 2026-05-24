from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification
from app.integrations.brevo_email import brevo_client
from app.integrations.twilio_whatsapp import twilio_whatsapp_client
from app.core.logging import logger
import uuid

class NotificationService:
    async def send_in_app(self, db: AsyncSession, user_id: uuid.UUID, title: str, message: str, link: str = None):
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.add(notification)
        await db.commit()
        return notification

    async def send_email(self, email: str, subject: str, html_content: str):
        try:
            await brevo_client.send_email(email, subject, html_content)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    async def send_whatsapp(self, to_number: str, message: str):
        try:
            # Twilio's python client is synchronous normally, but we call it here.
            # In a real async app we'd use a thread or an async client.
            twilio_whatsapp_client.send_whatsapp_message(to_number, message)
        except Exception as e:
            logger.error(f"Failed to send WhatsApp: {e}")

notification_service = NotificationService()
