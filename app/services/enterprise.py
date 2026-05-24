from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.models.enterprise import Organization, OrgMembership, OrgBranding, Team
from app.models.users import User
from app.schemas.enterprise import OrganizationCreate, OrgBrandingUpdate
from fastapi import HTTPException
import uuid

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
        org = (await db.execute(org_query)).scalar_one_or_none()
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
                "joined_at": joined_at,
                "last_login_at": user.last_login_at
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

enterprise_service = EnterpriseService()
