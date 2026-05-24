from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid

class CourseBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    domain: str
    difficulty: int

class CourseCreate(CourseBase):
    pass

class CourseRead(CourseBase):
    id: uuid.UUID
    author_id: uuid.UUID
    status: str
    model_config = ConfigDict(from_attributes=True)

class LessonBase(BaseModel):
    title: str
    position: int
    estimated_minutes: int

class LessonCreate(LessonBase):
    module_id: uuid.UUID

class LessonRead(LessonBase):
    id: uuid.UUID
    status: str
    version: int
    model_config = ConfigDict(from_attributes=True)
