import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import logger

class PaystackClient:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    async def initialize_transaction(
        self,
        email: str,
        amount_ngn: int,
        callback_url: str,
        plan_code: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        # Paystack expects amount in kobo
        amount_kobo = amount_ngn * 100
        url = f"{self.base_url}/transaction/initialize"
        payload = {
            "email": email,
            "amount": amount_kobo,
            "callback_url": callback_url,
            "metadata": metadata or {},
        }
        if plan_code:
            payload["plan"] = plan_code

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=payload,
                headers=self.headers
            )
            return response.json()

    async def verify_transaction(self, reference: str):
        url = f"{self.base_url}/transaction/verify/{reference}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            return response.json()

paystack_client = PaystackClient()
