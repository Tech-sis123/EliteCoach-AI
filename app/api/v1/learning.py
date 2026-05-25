from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.learning import CourseDetailResponse, LessonStartResponse, LessonCompleteResponse, LearningPathRead, ActiveSessionRead
from app.services.learning import learning_service
from app.services.onboarding import onboarding_service
from app.models.users import User
import uuid

router = APIRouter()

@router.get("/course/{course_id}", response_model=CourseDetailResponse)
async def get_course_detail(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a course, including its modules.
    Used for the learning interface.
    """
    return await learning_service.get_course_detail(db, course_id)

@router.post("/lesson/{lesson_id}/start", response_model=LessonStartResponse)
async def start_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a lesson session and initialize/resume AI Tutor session.
    """
    return await learning_service.start_lesson(db, current_user.id, lesson_id)

@router.post("/lesson/{lesson_id}/complete", response_model=LessonCompleteResponse)
async def complete_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a lesson as complete and check for unlocked content.
    """
    return await learning_service.complete_lesson(db, current_user.id, lesson_id)

@router.get("/sessions/active", response_model=ActiveSessionRead)
async def get_active_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current learner's in-progress lesson sessions.
    """
    return await learning_service.get_active_sessions(db, current_user.id)

@router.get("/path", response_model=LearningPathRead)
async def get_learning_path(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Learner's homepage data source - shows their generated learning path.
    """
    return await onboarding_service.get_learning_path(db, current_user.id)
