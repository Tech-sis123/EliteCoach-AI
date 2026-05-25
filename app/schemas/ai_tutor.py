from pydantic import BaseModel, ConfigDict, Field
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

class ManualEscalateRequest(BaseModel):
    reason: str = Field(default="Learner requested human assistance", max_length=500)

class EscalationCreatedResponse(BaseModel):
    escalation_id: uuid.UUID
    status: str
    assigned_tutor_name: Optional[str] = None
    message: str

class AssignedTutorRead(BaseModel):
    name: str
    avatar_url: Optional[str] = None

class EscalationStatusRead(BaseModel):
    escalated: bool
    escalation_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    trigger_reason: Optional[str] = None
    assigned_tutor: Optional[AssignedTutorRead] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    can_cancel: bool = False
