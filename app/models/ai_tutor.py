from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, func, Integer, Boolean, Enum as SQLEnum
from typing import List, Optional
from datetime import datetime
from app.core.database import Base
from app.models.base import BaseMixin
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
import enum
import uuid

class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"

class LessonSession(Base, BaseMixin):
    __tablename__ = "lesson_sessions"
    
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE)

class SessionMessage(Base, BaseMixin):
    __tablename__ = "session_messages"
    
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lesson_sessions.id"))
    role: Mapped[str] = mapped_column(String) # user, assistant, system
    content: Mapped[str] = mapped_column(String)
    rag_chunks_used: Mapped[Optional[List[uuid.UUID]]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)

class Escalation(Base, BaseMixin):
    __tablename__ = "escalations"
    
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lesson_sessions.id"))
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id"))
    trigger_reason: Mapped[str] = mapped_column(String) # repeat_question, frustrated_language
    status: Mapped[str] = mapped_column(String, default="open") # open, in_progress, resolved
    assigned_tutor_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

class KnowledgeCheck(Base, BaseMixin):
    __tablename__ = "knowledge_checks"
    
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id"))
    section_index: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(String)
    correct_answer: Mapped[str] = mapped_column(String)
    rag_chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("rag_chunks.id"), nullable=True)

class KnowledgeCheckResponse(Base, BaseMixin):
    __tablename__ = "knowledge_check_responses"
    
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lesson_sessions.id"))
    knowledge_check_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_checks.id"))
    learner_answer: Mapped[str] = mapped_column(String)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default={})
