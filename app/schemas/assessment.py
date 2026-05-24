from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

class DiagnosticQuestionRead(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    difficulty: int

    class Config:
        from_attributes = True

class DiagnosticStartResponse(BaseModel):
    questions: List[DiagnosticQuestionRead]

class DiagnosticSubmitRequest(BaseModel):
    answers: Dict[str, str] # question_id: answer

class DiagnosticSubmitResponse(BaseModel):
    score: float
    summary: str
    recommended_path_id: Optional[uuid.UUID] = None

class AssessmentRead(BaseModel):
    id: uuid.UUID
    title: str
    assessment_type: str
    passing_score: float

    class Config:
        from_attributes = True

class AssessmentQuestionRead(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: str
    options: Optional[Dict[str, str]] = None
    points: int

    class Config:
        from_attributes = True

class AssessmentStartResponse(BaseModel):
    attempt_id: uuid.UUID
    assessment: AssessmentRead
    questions: List[AssessmentQuestionRead]

class QuestionAnswer(BaseModel):
    question_id: uuid.UUID
    answer: str

class AssessmentSubmitRequest(BaseModel):
    answers: List[QuestionAnswer]

class AssessmentSubmitResponse(BaseModel):
    attempt_id: uuid.UUID
    score: float
    is_passed: bool
    ai_feedback: Optional[str] = None
    reinforcement_lessons: Optional[List[uuid.UUID]] = None
