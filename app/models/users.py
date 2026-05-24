from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Enum as SQLEnum
import enum
import uuid
from datetime import datetime
from typing import List, Optional
from app.core.database import Base
from app.models.base import BaseMixin

class UserRoleEnum(str, enum.Enum):
    SOLO_LEARNER = "solo_learner"
    ORG_LEARNER = "org_learner"
    TUTOR_AUTHOR = "tutor_author"
    TUTOR_RESPONDER = "tutor_responder"
    ENTERPRISE_ADMIN = "enterprise_admin"
    PLATFORM_ADMIN = "platform_admin"

class User(Base, BaseMixin):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reset_token_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_token_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    roles: Mapped[List["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class UserRole(Base, BaseMixin):
    __tablename__ = "user_roles"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    role: Mapped[UserRoleEnum] = mapped_column(SQLEnum(UserRoleEnum))
    
    user: Mapped["User"] = relationship(back_populates="roles")

class RefreshToken(Base, BaseMixin):
    __tablename__ = "refresh_tokens"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
