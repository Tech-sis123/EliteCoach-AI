from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.notification import Notification
from app.models.users import User
from sqlalchemy import select, update
import uuid
from typing import List

router = APIRouter()

@router.get("/")
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List notifications for the current user."""
    query = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    await db.execute(
        update(Notification).where(
            (Notification.id == notification_id) & (Notification.user_id == current_user.id)
        ).values(is_read=True)
    )
    await db.commit()
    return {"status": "success"}
