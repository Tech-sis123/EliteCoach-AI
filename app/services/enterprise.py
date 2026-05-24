from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.models.enterprise import Organization, OrgMembership, OrgBranding, Team
from app.models.users import User
from app.schemas.enterprise import OrganizationCreate, OrgBrandingUpdate
from fastapi import HTTPException
import uuid
from typing import List

class EnterpriseService:
    async def create_organization(self, db: AsyncSession, admin_id: uuid.UUID, data: OrganizationCreate):
        org = Organization(
            **data.model_dump(),
            primary_admin_id=admin_id
        )
        db.add(org)
        await db.flush()
        
        # Create default branding
        branding = OrgBranding(org_id=org.id)
        db.add(branding)
        
        await db.commit()
        await db.refresh(org)
        return org

    async def get_org_dashboard(self, db: AsyncSession, admin_id: uuid.UUID):
        org_query = select(Organization).where(Organization.primary_admin_id == admin_id)
        org = (await db.execute(org_query)).first()
        if org:
            org = org[0]
        if not org:
            raise HTTPException(status_code=403, detail="Not an organization administrator")
            
        learners_query = (
            select(User, OrgMembership.joined_at)
            .join(OrgMembership, User.id == OrgMembership.user_id)
            .where(OrgMembership.org_id == org.id)
        )
        result = await db.execute(learners_query)
        learners = []
        for user, joined_at in result.all():
            learners.append({
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "joined_at": joined_at
            })
            
        return {
            "organization": org,
            "learner_count": len(learners),
            "learners": learners
        }

    async def get_org_branding(self, db: AsyncSession, slug: str):
        query = (
            select(OrgBranding)
            .join(Organization, OrgBranding.org_id == Organization.id)
            .where(Organization.slug == slug)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_org_branding(self, db: AsyncSession, admin_id: uuid.UUID, data: OrgBrandingUpdate):
        # Find org
        org_query = select(Organization).where(Organization.primary_admin_id == admin_id)
        org = (await db.execute(org_query)).scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=403, detail="Not an organization administrator")
            
        query = update(OrgBranding).where(OrgBranding.org_id == org.id).values(**data.model_dump(exclude_unset=True))
        await db.execute(query)
        await db.commit()
        
        res = await db.execute(select(OrgBranding).where(OrgBranding.org_id == org.id))
        return res.scalar_one_or_none()

    async def add_member(self, db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, team_id: uuid.UUID = None):
        membership = OrgMembership(
            org_id=org_id,
            user_id=user_id,
            team_id=team_id
        )
        db.add(membership)
        await db.commit()
        return membership

    async def list_teams(self, db: AsyncSession, org_id: uuid.UUID):
        query = select(Team).where(Team.org_id == org_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_org_users(self, db: AsyncSession, admin_id: uuid.UUID):
        org_query = select(Organization).where(Organization.primary_admin_id == admin_id)
        org = (await db.execute(org_query)).scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=403, detail="Not an organization administrator")
            
        users_query = (
            select(User)
            .join(OrgMembership, User.id == OrgMembership.user_id)
            .where(OrgMembership.org_id == org.id)
        )
        result = await db.execute(users_query)
        return result.scalars().all()

    async def create_team(self, db: AsyncSession, admin_id: uuid.UUID, name: str):
        org_query = select(Organization).where(Organization.primary_admin_id == admin_id)
        org = (await db.execute(org_query)).scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=403, detail="Not an organization administrator")
            
        team = Team(name=name, org_id=org.id)
        db.add(team)
        await db.commit()
        await db.refresh(team)
        return team

    async def add_team_member(self, db: AsyncSession, admin_id: uuid.UUID, team_id: uuid.UUID, user_id: uuid.UUID):
        org_query = select(Organization).where(Organization.primary_admin_id == admin_id)
        org = (await db.execute(org_query)).scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=403, detail="Not an organization administrator")
            
        # Verify team belongs to org
        team_query = select(Team).where(and_(Team.id == team_id, Team.org_id == org.id))
        team = (await db.execute(team_query)).scalar_one_or_none()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found in your organization")
            
        # Update or create membership
        membership_query = select(OrgMembership).where(and_(OrgMembership.org_id == org.id, OrgMembership.user_id == user_id))
        membership = (await db.execute(membership_query)).scalar_one_or_none()
        
        if membership:
            membership.team_id = team_id
        else:
            membership = OrgMembership(org_id=org.id, user_id=user_id, team_id=team_id)
            db.add(membership)
            
        await db.commit()
        return {"status": "success"}

    async def deactivate_user(self, db: AsyncSession, admin_id: uuid.UUID, user_id: uuid.UUID):
        org_query = select(Organization).where(Organization.primary_admin_id == admin_id)
        org = (await db.execute(org_query)).scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=403, detail="Not an organization administrator")
            
        # Check if user is in org
        membership_query = select(OrgMembership).where(and_(OrgMembership.org_id == org.id, OrgMembership.user_id == user_id))
        membership = (await db.execute(membership_query)).scalar_one_or_none()
        if not membership:
            raise HTTPException(status_code=404, detail="User not found in your organization")
            
        await db.execute(update(User).where(User.id == user_id).values(is_active=False))
        await db.commit()
        return {"status": "deactivated"}

    async def import_users(self, db: AsyncSession, admin_id: uuid.UUID, users_data: List):
        # Placeholder for bulk user creation logic
        # In a real app, this would involve creating users, sending welcome emails, and assigning to teams
        return {"imported_count": len(users_data)}

    async def get_budget(self, db: AsyncSession, admin_id: uuid.UUID):
        org_query = select(Organization).where(Organization.primary_admin_id == admin_id)
        org = (await db.execute(org_query)).scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=403, detail="Not an organization administrator")
        
        return {
            "total_budget_ngn": org.budget_ngn or 0.0,
            "spent_ngn": (org.budget_ngn or 0.0) * 0.45, # Mock calc
            "remaining_ngn": (org.budget_ngn or 0.0) * 0.55
        }

enterprise_service = EnterpriseService()
