import httpx
from app.core.config import settings
from app.core.logging import logger

class BrevoClient:
    def __init__(self):
        self.api_key = settings.BREVO_API_KEY
        self.url = "https://api.brevo.com/v3/smtp/email"
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def send_email(self, to_email: str, subject: str, html_content: str):
        payload = {
            "sender": {"name": "Elite Coach AI", "email": "noreply@elitecoach.ai"},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, json=payload, headers=self.headers)
            if response.status_code >= 400:
                logger.error("brevo_email_failed", status=response.status_code, text=response.text)
            return response.json()

brevo_client = BrevoClient()
