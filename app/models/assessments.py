from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer, Float, Boolean, DateTime, func, Enum as SQLEnum
from typing import List, Optional
from app.core.database import Base
from app.models.base import BaseMixin
from sqlalchemy.dialects.postgresql import JSONB, UUID
import enum
import uuid
from datetime import datetime

class AssessmentType(str, enum.Enum):
    DIAGNOSTIC = "diagnostic"
    MODULE = "module"
    FINAL = "final"
    PRACTICAL = "practical"

class Assessment(Base, BaseMixin):
    __tablename__ = "assessments"

    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    module_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("modules.id"), nullable=True)
    assessment_type: Mapped[AssessmentType] = mapped_column(SQLEnum(AssessmentType))
    title: Mapped[str] = mapped_column(String)
    pass_score: Mapped[float] = mapped_column(Float, default=70.0)
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class AssessmentQuestion(Base, BaseMixin):
    __tablename__ = "assessment_questions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id"))
    question_text: Mapped[str] = mapped_column(String)
    question_type: Mapped[str] = mapped_column(String) # mcq, short, practical
    options: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True) # For MCQ
    correct_answer: Mapped[str] = mapped_column(String)
    explanation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=1)
    position: Mapped[int] = mapped_column(Integer)

class AssessmentAttempt(Base, BaseMixin):
    __tablename__ = "assessment_attempts"

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id"))
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_feedback: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    answers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

class Certificate(Base, BaseMixin):
    __tablename__ = "certificates"

    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_attempts.id"))
    verification_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    pdf_url: Mapped[str] = mapped_column(String)
    linkedin_share_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    course: Mapped["Course"] = relationship("Course")
    learner: Mapped["User"] = relationship("User")
