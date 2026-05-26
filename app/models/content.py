from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer, Float, Enum as SQLEnum
from typing import List, Optional
import uuid
from app.core.database import Base
from app.models.base import BaseMixin
from sqlalchemy.dialects.postgresql import JSONB

class Course(Base, BaseMixin):
    __tablename__ = "courses"
    
    title: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    domain: Mapped[str] = mapped_column(String) # Finance/Tech/etc
    difficulty: Mapped[int] = mapped_column(Integer) # 1-5
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String, default="draft") # draft, in_review, published

    modules: Mapped[List[Module]] = relationship("Module", back_populates="course", cascade="all, delete-orphan")

class Module(Base, BaseMixin):
    __tablename__ = "modules"
    
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    course: Mapped[Course] = relationship("Course", back_populates="modules")
    lessons: Mapped[List[Lesson]] = relationship("Lesson", back_populates="module")

class Lesson(Base, BaseMixin):
    __tablename__ = "lessons"
    
    module_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("modules.id"))
    title: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    module: Mapped[Module] = relationship("Module", back_populates="lessons")
    content_blocks: Mapped[List[ContentBlock]] = relationship("ContentBlock", back_populates="lesson", cascade="all, delete-orphan")

class ContentBlock(Base, BaseMixin):
    __tablename__ = "content_blocks"
    
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id"))
    position: Mapped[int] = mapped_column(Integer)
    block_type: Mapped[str] = mapped_column(String) # text, video, image, code
    content: Mapped[str] = mapped_column(String)
    
    lesson: Mapped[Lesson] = relationship("Lesson", back_populates="content_blocks")

class RagChunk(Base, BaseMixin):
    __tablename__ = "rag_chunks"
    
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(String)
    embedding: Mapped[list] = mapped_column(String) # Placeholder until pgvector is fully set up in DB
    token_count: Mapped[int] = mapped_column(Integer)
