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
    plan_code_map = {
        "monthly": settings.PAYSTACK_MONTHLY_PLAN_CODE,
        "yearly": settings.PAYSTACK_YEARLY_PLAN_CODE,
    }
    plan_code = plan_code_map.get(plan)
    
    res = await paystack_client.initialize_transaction(
        email=current_user.email,
        amount_ngn=amount,
        callback_url=settings.PAYSTACK_CALLBACK_URL,
        plan_code=plan_code,
        metadata={"user_id": str(current_user.id), "plan": plan},
    )
    return res

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

@router.delete("/subscription")
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel auto-renewal for the current subscription."""
    await db.execute(
        update(Subscription)
        .where(Subscription.user_id == current_user.id)
        .values(status="cancelled")
    )
    await db.commit()
    return {"message": "Subscription cancelled"}

@router.get("/admin/invoices")
async def list_admin_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin/Enterprise: List past payment receipts."""
    return []
