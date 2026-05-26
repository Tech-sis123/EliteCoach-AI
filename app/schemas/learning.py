from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime
from app.schemas.content import LessonRead

class OnboardingStart(BaseModel):
    current_role: str
    years_experience: int
    career_goal: str
    hours_per_week: int

class DiagnosticQuestionRead(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: str
    options: Optional[List[str]] = None

class DiagnosticSubmit(BaseModel):
    answers: Dict[uuid.UUID, str]

class PathItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position: int
    status: str
    course_id: uuid.UUID
    course_title: str
    course_domain: Optional[str] = None
    course_difficulty: Optional[int] = None
    total_minutes: int = 0
    unlocked_at: Optional[datetime] = None

class LearningPathRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    generated_at: datetime
    version: int
    status: str
    items: List[PathItemRead]
    reinforcement_tasks: Optional[List[Dict]] = None

class ModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    position: int
    lesson_count: int = 0

class ActiveSessionItem(BaseModel):
    session_id: uuid.UUID
    lesson_id: uuid.UUID
    lesson_title: str
    estimated_minutes: int
    module_id: uuid.UUID
    module_title: str
    course_id: uuid.UUID
    course_title: str
    domain: str
    message_count: int
    last_active_at: datetime

class ActiveSessionRead(BaseModel):
    active_sessions: List[ActiveSessionItem]

class CourseDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: Optional[str]
    domain: str
    difficulty: int
    author_name: str
    total_lessons: int
    total_minutes: int
    modules: List[ModuleRead]

class LessonStartResponse(BaseModel):
    session_id: uuid.UUID
    lesson: LessonRead 
    checks_count: int

class LessonCompleteResponse(BaseModel):
    session_id: uuid.UUID
    completed_at: datetime
    next_lesson_id: Optional[uuid.UUID] = None
    module_assessment_unlocked: bool = False
    final_exam_unlocked: bool = False
