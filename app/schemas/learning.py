from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid

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
    course_id: uuid.UUID
    title: str
    position: int
    status: str

class LearningPathRead(BaseModel):
    id: uuid.UUID
    items: List[PathItemRead]
