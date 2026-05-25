from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.users import User
from app.services.escalation import escalation_service
from app.schemas.escalations import EscalationUpdateRequest, EscalationUpdateResponse
import uuid

router = APIRouter()

@router.patch("/{escalation_id}", response_model=EscalationUpdateResponse)
async def update_escalation_status(
    escalation_id: uuid.UUID,
    data: EscalationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the status of an escalation."""
    return await escalation_service.update_escalation_status(
        db, escalation_id, current_user, data.status
    )
