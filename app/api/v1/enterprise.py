from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.enterprise import enterprise_service
import uuid

router = APIRouter()

# In a real app, this org_id would come from the JWT claims of the enterprise_admin
async def get_current_org_id():
    # Placeholder: Use the seeded org ID for testing
    return uuid.UUID("021389de-3617-43f1-b1e6-23f2f89c6759")

@router.post("/users/import")
async def import_users(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    content = await file.read()
    return await enterprise_service.import_users_from_csv(db, org_id, content)

@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    return await enterprise_service.get_org_dashboard(db, org_id)
