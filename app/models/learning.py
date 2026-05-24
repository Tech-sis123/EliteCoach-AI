from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer, Float, DateTime, Boolean, func
from typing import List, Optional
import uuid
from datetime import datetime
from app.core.database import Base
from app.models.base import BaseMixin
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID

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

class LearningPath(Base, BaseMixin):
    __tablename__ = "learning_paths"
    
    learner_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"))
    status: Mapped[str] = mapped_column(String, default="active") # active, archived
    version: Mapped[int] = mapped_column(Integer, default=1)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    learner_profile: Mapped["LearnerProfile"] = relationship()
    items: Mapped[List["PathItem"]] = relationship("PathItem", back_populates="learning_path", cascade="all, delete-orphan")

class PathItem(Base, BaseMixin):
    __tablename__ = "path_items"
    
    learning_path_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learning_paths.id"))
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    position: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="available") # available, in_progress, completed, locked
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    learning_path: Mapped["LearningPath"] = relationship("LearningPath", back_populates="items")
    course: Mapped["Course"] = relationship("Course")

class ReinforcementTask(Base, BaseMixin):
    __tablename__ = "reinforcement_tasks"
    
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id"))
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_attempts.id"))
    lesson_ids: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    reason: Mapped[str] = mapped_column(String) # assessment_failed
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
