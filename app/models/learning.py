from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer, Float, DateTime, func
from typing import List, Optional
import uuid
from datetime import datetime
from app.core.database import Base
from app.models.base import BaseMixin
from sqlalchemy.dialects.postgresql import JSONB

class Skill(Base, BaseMixin):
    __tablename__ = "skills"
    
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("skills.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class LearnerProfile(Base, BaseMixin):
    __tablename__ = "learner_profiles"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    career_goal: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hours_per_week: Mapped[int] = mapped_column(Integer, default=0)
    current_role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)

class SkillScore(Base, BaseMixin):
    __tablename__ = "skill_scores"
    
    learner_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"))
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    score: Mapped[float] = mapped_column(Float) # 0-100
    last_assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class DiagnosticQuestion(Base, BaseMixin):
    __tablename__ = "diagnostic_questions"
    
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("skills.id"), nullable=True)
    question_text: Mapped[str] = mapped_column(String)
    question_type: Mapped[str] = mapped_column(String) # mcq / short
    options: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    correct_answer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)

class DiagnosticAttempt(Base, BaseMixin):
    __tablename__ = "diagnostic_attempts"
    
    learner_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"))
    answers: Mapped[dict] = mapped_column(JSONB)
    score: Mapped[float] = mapped_column(Float)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
