from fastapi import APIRouter, Depends, Request, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.integrations.paystack import paystack_client
from app.models.users import User
from app.models.payments import Subscription
from sqlalchemy import select, update, and_
import hmac
import hashlib
import json
from datetime import datetime, timedelta

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
    data = event_data.get("data")
    
    if event_type == "charge.success":
        email = data.get("customer", {}).get("email")
        
        user_query = select(User).where(User.email == email)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if user:
            # Update or create subscription
            sub_query = select(Subscription).where(Subscription.user_id == user.id)
            sub = (await db.execute(sub_query)).scalar_one_or_none()
            
            if not sub:
                sub = Subscription(
                    user_id=user.id,
                    plan="monthly",
                    status="active",
                    current_period_end=datetime.utcnow() + timedelta(days=30)
                )
                db.add(sub)
            else:
                sub.status = "active"
                sub.current_period_end = datetime.utcnow() + timedelta(days=30)
            
            await db.commit()
    
    return {"status": "success"}

@router.get("/status")
async def get_subscription_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check subscription status for the current user."""
    query = select(Subscription).where(Subscription.user_id == current_user.id)
    result = await db.execute(query)
    sub = result.scalar_one_or_none()
    
    if not sub:
        return {"status": "none", "active": False}
        
    is_active = sub.status == "active" and sub.current_period_end > datetime.utcnow()
    return {
        "status": sub.status,
        "active": is_active,
        "current_period_end": sub.current_period_end,
        "plan": sub.plan
    }

@router.post("/subscribe")
async def create_subscription(
    plan: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize a Paystack transaction."""
    amount_map = {"monthly": 5000, "yearly": 50000}
    amount = amount_map.get(plan, 5000)
    
    res = await paystack_client.initialize_transaction(
        current_user.email, 
        amount, 
        callback_url=f"{settings.FRONTEND_URL}/payment/verify"
    )
    return res

@router.delete("/subscription")
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel active subscription."""
    from app.models.payments import Subscription
    query = update(Subscription).where(
        and_(Subscription.user_id == current_user.id, Subscription.is_active == True)
    ).values(is_active=False)
    await db.execute(query)
    await db.commit()
    return {"message": "Subscription cancelled"}

@router.get("/invoices")
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List payment history/invoices."""
    return []

@router.get("/verify/{reference}")
async def verify_payment(
    reference: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify a Paystack transaction and activate subscription."""
    res = await paystack_client.verify_transaction(reference)
    if res.get("status") and res.get("data", {}).get("status") == "success":
        # Activate sub
        sub_query = select(Subscription).where(Subscription.user_id == current_user.id)
        sub = (await db.execute(sub_query)).scalar_one_or_none()
        
        if not sub:
            sub = Subscription(
                user_id=current_user.id,
                plan="monthly",
                status="active",
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            db.add(sub)
        else:
            sub.status = "active"
            sub.current_period_end = datetime.utcnow() + timedelta(days=30)
        
        await db.commit()
        return {"message": "Payment verified and subscription activated"}
    
    raise HTTPException(status_code=400, detail="Payment verification failed")
