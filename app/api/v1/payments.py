from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.integrations.paystack import paystack_client
import hmac
import hashlib
import json

router = APIRouter()

@router.post("/webhook")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # 1. Verify Signature
    payload = await request.body()
    signature = request.headers.get("x-paystack-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
        
    hash_val = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    if hash_val != signature:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Process Event
    event_data = json.loads(payload)
    event_type = event_data.get("event")
    
    # Process subscription.create, charge.success, etc.
    # Logic here to update DB
    
    return {"status": "success"}

@router.post("/subscribe")
async def create_subscription(email: str, plan: str, db: AsyncSession = Depends(get_db)):
    amount = 5000 if plan == "monthly" else 50000
    res = await paystack_client.initialize_transaction(
        email, 
        amount, 
        callback_url=f"{settings.FRONTEND_URL}/payment/verify"
    )
    return res
