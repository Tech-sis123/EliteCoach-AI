from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    conversation_id: uuid.UUID

class MessageRead(MessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    created_at: datetime
    is_read: bool
    model_config = ConfigDict(from_attributes=True)

class ConversationRead(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConversationCreate(BaseModel):
    participant_ids: List[uuid.UUID]
    title: Optional[str] = None
