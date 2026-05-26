from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
import uuid
from datetime import datetime

class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class UserBase(SchemaBase):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: Optional[str] = "solo_learner"

class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

class Token(SchemaBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
