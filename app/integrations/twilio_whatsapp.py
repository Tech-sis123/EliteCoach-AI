from twilio.rest import Client
from app.core.config import settings
from app.core.logging import logger

class TwilioWhatsappClient:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER
        self.client = Client(self.account_sid, self.auth_token)

    def send_whatsapp_message(self, to_number: str, body: str):
        try:
            # Twilio sandbox requires numbers in 'whatsapp:+123...' format
            message = self.client.messages.create(
                from_=self.from_number,
                body=body,
                to=f"whatsapp:{to_number}"
            )
            return message.sid
        except Exception as e:
            logger.error("twilio_whatsapp_failed", error=str(e))
            raise

twilio_whatsapp_client = TwilioWhatsappClient()
