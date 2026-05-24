from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.content import content_service
from app.api.deps import get_current_user_id
import uuid

router = APIRouter()

@router.get("/")
async def list_published_courses(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await content_service.list_courses(db)

@router.get("/{id}/lessons")
async def list_course_lessons(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await content_service.list_lessons_by_course(db, id)
