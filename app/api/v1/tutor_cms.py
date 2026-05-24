from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.content import CourseCreate, CourseRead, LessonCreate, LessonRead
from app.services.content import content_service
from app.core.rbac import RoleChecker
import uuid

router = APIRouter()

# Dependency for Tutor roles
# tutor_only = Depends(RoleChecker(['tutor_author', 'platform_admin']))

@router.post("/courses", response_model=CourseRead)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db)
):
    # Dummy user_id until Auth is fully wired
    author_id = uuid.uuid4()
    return await content_service.create_course(db, author_id, data)

@router.post("/lessons", response_model=LessonRead)
async def create_lesson(
    data: LessonCreate,
    db: AsyncSession = Depends(get_db)
):
    return await content_service.create_lesson(db, data)
