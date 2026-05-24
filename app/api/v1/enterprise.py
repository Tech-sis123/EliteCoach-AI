from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.api.deps import get_db, get_current_user
from typing import List
from app.schemas.enterprise import (
    OrganizationCreate, OrganizationRead,
    OrgBrandingRead, OrgBrandingUpdate,
    InvitationCreate, TeamCreate, TeamRead, UserImport
)
from app.services.enterprise import enterprise_service
from app.models.users import User
from app.models.enterprise import Organization
import uuid

router = APIRouter()

@router.post("/organizations", response_model=OrganizationRead)
async def create_organization(
    data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new organization (Enterprise Admin)"""
    return await enterprise_service.create_organization(db, current_user.id, data)

@router.get("/dashboard")
async def get_org_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get enterprise dashboard data"""
    return await enterprise_service.get_org_dashboard(db, current_user.id)

@router.get("/branding/{slug}", response_model=OrgBrandingRead)
async def get_org_branding(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get branding details for an organization by slug"""
    branding = await enterprise_service.get_org_branding(db, slug)
    if not branding:
        raise HTTPException(status_code=404, detail="Branding not found for this organization")
    return branding

@router.patch("/branding", response_model=OrgBrandingRead)
async def update_org_branding(
    data: OrgBrandingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update organization branding"""
    return await enterprise_service.update_org_branding(db, current_user.id, data)

@router.post("/invite")
async def invite_employee(
    data: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invite an employee to the organization"""
    # In a real app, this would send an email. For now, we'll just check if user exists.
    from sqlalchemy import select, update
    user_query = select(User).where(User.email == data.email)
    user = (await db.execute(user_query)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found. They must register first.")
    
    # Get the admin's org
    from app.models.enterprise import Organization
    org_query = select(Organization).where(Organization.primary_admin_id == current_user.id)
    org = (await db.execute(org_query)).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=403, detail="Only org admins can invite members")
        
    await enterprise_service.add_member(db, org.id, user.id, data.team_id)
    return {"message": f"User {data.email} added to organization successfully"}

@router.get("/teams")
async def list_org_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List teams in the organization"""
    from app.models.enterprise import Organization
    org_query = select(Organization).where(Organization.primary_admin_id == current_user.id)
    org = (await db.execute(org_query)).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=403, detail="Only org admins can view teams")
    return await enterprise_service.list_teams(db, org.id)

@router.get("/users")
async def list_org_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all learners in the organization"""
    return await enterprise_service.get_org_users(db, current_user.id)

@router.post("/users/import")
async def import_org_users(
    users: List[UserImport],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk import users to organization"""
    return await enterprise_service.import_users(db, current_user.id, users)

@router.post("/users/{user_id}/deactivate")
async def deactivate_org_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate a learner's access to organization resources"""
    return await enterprise_service.deactivate_user(db, current_user.id, user_id)

@router.post("/teams", response_model=TeamRead)
async def create_org_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a team within the organization"""
    return await enterprise_service.create_team(db, current_user.id, data.name)

@router.post("/teams/{team_id}/members")
async def add_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a user to a specific team"""
    return await enterprise_service.add_team_member(db, current_user.id, team_id, user_id)

@router.post("/onboard")
async def onboard_organization(
    data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initial organization onboarding (alias for create account)"""
    return await enterprise_service.create_organization(db, current_user.id, data)
