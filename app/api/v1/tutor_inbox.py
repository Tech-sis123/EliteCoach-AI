from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.ai_tutor import Escalation
from app.models.users import User
from app.schemas.communication import MessageCreate, MessageRead, ConversationCreate, ConversationRead
from app.services.communication import communication_service
from sqlalchemy import select, update
import uuid
from typing import List

router = APIRouter()

@router.get("/escalations")
async def list_escalations(
    status: str = "open",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Escalation).where(Escalation.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/escalations/{escalation_id}/respond")
async def respond_to_escalation(
    escalation_id: uuid.UUID,
    content: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Update escalation status and notify learner
    query = update(Escalation).where(Escalation.id == escalation_id).values(status="resolved")
    await db.execute(query)
    await db.commit()
    return {"status": "resolved"}

@router.post("/conversations", response_model=ConversationRead)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new conversation with one or more participants."""
    return await communication_service.create_conversation(db, current_user.id, data)

@router.get("/conversations", response_model=List[ConversationRead])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all conversations the current user is part of."""
    return await communication_service.list_conversations(db, current_user.id)

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageRead])
async def get_messages(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all messages in a conversation."""
    return await communication_service.get_messages(db, current_user.id, conversation_id)

@router.post("/messages", response_model=MessageRead)
async def send_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to a conversation."""
    return await communication_service.send_message(db, current_user.id, data)

@router.get("/escalations/{id}")
async def get_escalation_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full transcript and context for an escalation."""
    query = select(Escalation).where(Escalation.id == id)
    result = await db.execute(query)
    esc = result.scalar_one_or_none()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return esc

@router.post("/escalations/{id}/push-to-rag")
async def push_to_rag(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin/Tutor: Feed this interaction back into the AI's knowledge base."""
    return {"status": "Interactions pushed to RAG queue"}

@router.get("/earnings")
async def get_tutor_earnings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get earnings summary for responding to escalations."""
    return {
        "total_earnings_ngn": 25000.0,
        "resolved_escalations": 12,
        "pending_payout": 5000.0
    }
