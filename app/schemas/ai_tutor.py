from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime

class SessionMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime
    tokens_used: int

class SessionSummaryRead(BaseModel):
    topics_covered: List[str]
    understood_well: List[str]
    needs_revisit: List[str]
    tutor_notes: str

class KnowledgeCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    section_index: int
    question_text: str

class KnowledgeCheckResponse(BaseModel):
    is_correct: bool
    explanation: Optional[str] = None
    attempts: int
    re_ask: bool
