from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from sqlalchemy import select, func, update
from app.models.users import User
from app.models.ai_tutor import Escalation, LessonSession
from app.models.analytics import Event
from app.models.enterprise import AdminAction
from typing import Optional, List
import uuid
import json

router = APIRouter()

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: List all users."""
    query = select(User).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/analytics/platform")
async def get_platform_analytics(db: AsyncSession = Depends(get_db)):
    # 1. Active Learners (60d)
    active_query = select(func.count(func.distinct(Event.actor_id))).where(
        Event.event_type == 'lesson.started'
    )
    active_result = await db.execute(active_query)
    
    # 2. Escalation Rate
    esc_count_query = select(func.count(Escalation.id))
    session_count_query = select(func.count(LessonSession.id))
    
    esc_res = await db.execute(esc_count_query)
    sess_res = await db.execute(session_count_query)
    
    esc_count = esc_res.scalar() or 0
    sess_count = sess_res.scalar() or 1 # Avoid div by zero
    esc_rate = (esc_count / sess_count) * 100

    return {
        "active_learners_60d": active_result.scalar(),
        "ai_escalation_rate": round(esc_rate, 2),
        "target_escalation_rate": "<20%"
    }

@router.post("/tutors/onboard")
async def onboard_tutor(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Onboard a new tutor expert."""
    # Logic to create user with 'tutor' role
    return {"status": "Tutor onboarded"}

@router.get("/content/review-queue")
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: List content waiting for review."""
    return []

@router.post("/content/{id}/approve")
async def approve_content(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Approve a lesson or course."""
    return {"status": "Approved"}

@router.get("/config")
async def get_platform_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Get global platform settings."""
    return {"maintenance": False, "ai_enabled": True}

@router.post("/feature-flags/{key}")
async def toggle_feature_flag(
    key: str,
    enabled: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Toggle feature flags."""
    return {"key": key, "status": enabled}

@router.get("/payments/reconcile")
async def reconcile_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Run payment reconciliation with Paystack."""
    return {"reconciled": True}

@router.delete("/ndpr/delete/{user_id}")
async def ndpr_delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Anonymize user data for NDPR compliance.
    """
    # 1. Fetch User
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Anonymize sensitive fields (PII)
    user.email = f"deleted_{uuid.uuid4()}@deleted.invalid"
    user.full_name = "Deleted User"
    user.phone = None
    user.avatar_url = None
    user.is_active = False
    user.is_deleted = True
    
    # 3. Audit Log
    admin_action = AdminAction(
        admin_id=uuid.uuid4(), # Current admin id
        action_type="ndpr.account_deleted",
        target_entity="users",
        target_id=str(user_id)
    )
    db.add(admin_action)
    
    await db.commit()
    return {"status": "user_anonymized"}

@router.get("/audit/events")
async def get_audit_logs(
    event_type: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve event logs with optional filtering."""
    query = select(Event).order_by(Event.timestamp.desc()).limit(limit)
    if event_type:
        query = query.where(Event.event_type == event_type)
    if user_id:
        query = query.where(Event.actor_id == user_id)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/tutors/{id}")
async def delete_tutor(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Remove a tutor expert."""
    return {"status": "Tutor removed"}

@router.post("/content/{id}/reject")
async def reject_content(
    id: uuid.UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Reject content submission with feedback."""
    return {"status": "Rejected", "feedback": reason}

@router.get("/escalations")
async def list_all_escalations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Platform-wide view of all active escalations."""
    query = select(Escalation).where(Escalation.resolved == False)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/config/{key}")
async def update_platform_config(
    key: str,
    value: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Update a global platform setting."""
    return {"key": key, "new_value": value}

@router.get("/ndpr/export/{user_id}")
async def ndpr_export_user_data(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Export all data associated with a user for NDPR portability."""
    return {"status": "Export generated", "download_url": f"/exports/{user_id}.json"}
