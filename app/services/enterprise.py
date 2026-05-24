import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, func
from app.models.users import User, UserRole, UserRoleEnum
from app.models.enterprise import OrgMembership, Organization, Team
from app.core.security import hash_password
from app.core.logging import logger
import uuid
import io

class EnterpriseService:
    async def import_users_from_csv(self, db: AsyncSession, org_id: uuid.UUID, csv_content: bytes):
        df = pd.read_csv(io.BytesIO(csv_content))
        results = {"success": [], "errors": []}
        
        for index, row in df.iterrows():
            email = row.get('email')
            full_name = row.get('full_name')
            
            if not email or not full_name:
                results["errors"].append({"row": index, "reason": "Missing email or full_name"})
                continue
            
            try:
                # 1. Create User
                user = User(
                    email=email,
                    full_name=full_name,
                    hashed_password=hash_password("elitecoach123"), # Default password for invited users
                )
                db.add(user)
                await db.flush()
                
                # 2. Add Role
                role = UserRole(user_id=user.id, role=UserRoleEnum.ORG_LEARNER)
                db.add(role)
                
                # 3. Add Org Membership
                # membership = OrgMembership(org_id=org_id, user_id=user.id)
                # db.add(membership)
                
                results["success"].append(email)
            except Exception as e:
                await db.rollback()
                results["errors"].append({"row": index, "reason": str(e)})
                continue
        
        await db.commit()
        return results

    async def get_org_dashboard(self, db: AsyncSession, org_id: uuid.UUID):
        # Multi-tenant scoped query
        query = select(func.count(OrgMembership.id)).where(OrgMembership.org_id == org_id)
        result = await db.execute(query)
        total_learners = result.scalar()
        
        return {
            "total_learners": total_learners,
            "pct_completed": 0, # To be linked with analytics/assessments
            "pct_at_risk": 0
        }

enterprise_service = EnterpriseService()
