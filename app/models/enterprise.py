from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional
from app.core.database import Base
from app.models.base import BaseMixin
from datetime import datetime
import uuid

class Organization(Base, BaseMixin):
    __tablename__ = "organizations"
    
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    plan: Mapped[str] = mapped_column(String) # e.g. seat_count
    budget_ngn: Mapped[Optional[float]] = mapped_column(nullable=True)
    paystack_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    primary_admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
class OrgBranding(Base, BaseMixin):
    __tablename__ = "org_branding"
    
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    primary_color: Mapped[str] = mapped_column(String, default="#000000")
    secondary_color: Mapped[str] = mapped_column(String, default="#ffffff")
    custom_domain: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)

class Team(Base, BaseMixin):
    __tablename__ = "teams"
    
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class OrgMembership(Base, BaseMixin):
    __tablename__ = "org_memberships"
    
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("teams.id"), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class AdminAction(Base, BaseMixin):
    __tablename__ = "admin_actions"
    
    admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String)
    target_entity: Mapped[str] = mapped_column(String)
    target_id: Mapped[uuid.UUID] = mapped_column(String) # Stored as string to handle various types if needed
    diff: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
