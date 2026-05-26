from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
import uuid
from datetime import datetime
from enum import Enum

class RegisterRole(str, Enum):
    solo_learner = "solo_learner"
    org_learner = "org_learner"
    tutor_author = "tutor_author"
    tutor_responder = "tutor_responder"
    enterprise_admin = "enterprise_admin"

class LoginUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    org_id: Optional[uuid.UUID] = None
    email_verified_at: Optional[datetime] = None
    roles: List[str]

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: LoginUserRead

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)

class UserMe(LoginUserRead):
    pass
