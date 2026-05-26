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

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    difficulty: Optional[int] = None
    status: Optional[str] = None

class CourseRead(CourseBase):
    id: uuid.UUID
    author_id: uuid.UUID
    status: str
    model_config = ConfigDict(from_attributes=True)

class ModuleBase(BaseModel):
    title: str
    position: int
    description: Optional[str] = None

class ModuleCreate(ModuleBase):
    course_id: uuid.UUID

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[int] = None
    description: Optional[str] = None

class ModuleRead(ModuleBase):
    id: uuid.UUID
    course_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class LessonBase(BaseModel):
    title: str
    position: int
    estimated_minutes: int

class ContentBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    position: int
    block_type: str
    content: str

class LessonCreate(LessonBase):
    module_id: uuid.UUID

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[int] = None
    estimated_minutes: Optional[int] = None
    status: Optional[str] = None

class LessonRead(LessonBase):
    id: uuid.UUID
    status: str
    version: int
    module_id: uuid.UUID
    content_blocks: List[ContentBlockRead] = []
    model_config = ConfigDict(from_attributes=True)
