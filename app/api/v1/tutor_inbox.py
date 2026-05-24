from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.ai_tutor import Escalation
from sqlalchemy import select, update
import uuid

router = APIRouter()

@router.get("/")
async def list_escalations(
    status: str = "open",
    db: AsyncSession = Depends(get_db)
):
    query = select(Escalation).where(Escalation.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{escalation_id}/respond")
async def respond_to_escalation(
    escalation_id: uuid.UUID,
    content: str,
    db: AsyncSession = Depends(get_db)
):
    # Update escalation status and notify learner
    query = update(Escalation).where(Escalation.id == escalation_id).values(status="resolved")
    await db.execute(query)
    await db.commit()
    return {"status": "resolved"}
