from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str
    slug: str
    plan: str
    budget_ngn: Optional[float] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationRead(OrganizationBase):
    id: uuid.UUID
    primary_admin_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class OrgBrandingBase(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = "#000000"
    secondary_color: str = "#ffffff"
    custom_domain: Optional[str] = None

class OrgBrandingUpdate(OrgBrandingBase):
    pass

class OrgBrandingRead(OrgBrandingBase):
    id: uuid.UUID
    org_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class LearnerOrgRead(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    joined_at: datetime
    last_login_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class InvitationCreate(BaseModel):
    email: str
    team_id: Optional[uuid.UUID] = None
