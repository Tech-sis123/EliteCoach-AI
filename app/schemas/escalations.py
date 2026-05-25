from pydantic import BaseModel
import uuid
from typing import Optional

class EscalationUpdateRequest(BaseModel):
    status: str # cancelled, in_progress, resolved, etc.

class EscalationUpdateResponse(BaseModel):
    escalation_id: uuid.UUID
    status: str
    message: str
