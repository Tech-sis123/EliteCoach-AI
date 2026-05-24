from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload
from app.models.communication import Conversation, ConversationParticipant, Message
from app.schemas.communication import MessageCreate, ConversationCreate
from fastapi import HTTPException
import uuid
from datetime import datetime

class CommunicationService:
    async def create_conversation(self, db: AsyncSession, user_id: uuid.UUID, data: ConversationCreate):
        # 1. Check if direct conversation already exists (if only 2 participants)
        # For now, just create a new one
        conv = Conversation(title=data.title)
        db.add(conv)
        await db.flush()
        
        # Add creator
        db.add(ConversationParticipant(conversation_id=conv.id, user_id=user_id))
        # Add others
        for p_id in data.participant_ids:
            if p_id != user_id:
                db.add(ConversationParticipant(conversation_id=conv.id, user_id=p_id))
        
        await db.commit()
        await db.refresh(conv)
        return conv

    async def list_conversations(self, db: AsyncSession, user_id: uuid.UUID):
        query = (
            select(Conversation)
            .join(ConversationParticipant)
            .where(ConversationParticipant.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_messages(self, db: AsyncSession, user_id: uuid.UUID, conversation_id: uuid.UUID):
        # Verify access
        access_query = select(ConversationParticipant).where(
            and_(ConversationParticipant.conversation_id == conversation_id, ConversationParticipant.user_id == user_id)
        )
        access = (await db.execute(access_query)).scalar_one_or_none()
        if not access:
            raise HTTPException(status_code=403, detail="Not a participant in this conversation")
            
        messages_query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await db.execute(messages_query)
        return result.scalars().all()

    async def send_message(self, db: AsyncSession, user_id: uuid.UUID, data: MessageCreate):
        # Verify access
        access_query = select(ConversationParticipant).where(
            and_(ConversationParticipant.conversation_id == data.conversation_id, ConversationParticipant.user_id == user_id)
        )
        access = (await db.execute(access_query)).scalar_one_or_none()
        if not access:
            raise HTTPException(status_code=403, detail="Not a participant")
            
        message = Message(
            conversation_id=data.conversation_id,
            sender_id=user_id,
            content=data.content
        )
        db.add(message)
        
        # Update conversation timestamp
        await db.execute(
            update(Conversation).where(Conversation.id == data.conversation_id).values(updated_at=datetime.utcnow())
        )
        
        await db.commit()
        await db.refresh(message)
        return message

communication_service = CommunicationService()
