from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Boolean, func
from typing import List, Optional
import uuid
from datetime import datetime
from app.core.database import Base
from app.models.base import BaseMixin

class Conversation(Base, BaseMixin):
    __tablename__ = "conversations"
    
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    participants: Mapped[List["ConversationParticipant"]] = relationship(back_populates="conversation")
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation")

class ConversationParticipant(Base, BaseMixin):
    __tablename__ = "conversation_participants"
    
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    conversation: Mapped["Conversation"] = relationship(back_populates="participants")

class Message(Base, BaseMixin):
    __tablename__ = "messages"
    
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"))
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
