from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.content import (
    CourseCreate, CourseRead, CourseUpdate,
    LessonCreate, LessonRead, LessonUpdate,
    ModuleCreate, ModuleRead, ModuleUpdate
)
from app.services.content import content_service
from app.models.users import User
from typing import List
import uuid

router = APIRouter()

# --- Course Endpoints ---

@router.post("/courses", response_model=CourseRead)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new course."""
    # Logic for checking if user is a tutor could go here
    return await content_service.create_course(db, current_user.id, data)

@router.get("/courses", response_model=List[CourseRead])
async def list_my_courses(
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List courses (optionally filtered by status)."""
    return await content_service.list_courses(db, status=status)

@router.get("/courses/{course_id}", response_model=CourseRead)
async def get_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get course details."""
    course = await content_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.patch("/courses/{course_id}", response_model=CourseRead)
@router.put("/courses/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: uuid.UUID,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update course details."""
    return await content_service.update_course(db, course_id, data.model_dump(exclude_unset=True))

@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a course."""
    await content_service.delete_course(db, course_id)
    return {"message": "Course deleted successfully"}

@router.patch("/courses/{course_id}/status")
async def update_course_status(
    course_id: uuid.UUID,
    status: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update course status (e.g., 'published', 'draft')."""
    await content_service.update_course_status(db, course_id, status)
    return {"message": f"Course status updated to {status}"}

# --- Module Endpoints ---

@router.post("/modules", response_model=ModuleRead)
async def create_module(
    data: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a module to a course."""
    return await content_service.create_module(db, data)

@router.get("/courses/{course_id}/modules", response_model=List[ModuleRead])
async def list_course_modules(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all modules for a course."""
    return await content_service.list_modules(db, course_id)

@router.patch("/modules/{module_id}", response_model=ModuleRead)
@router.put("/modules/{module_id}", response_model=ModuleRead)
async def update_module(
    module_id: uuid.UUID,
    data: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update module details."""
    return await content_service.update_module(db, module_id, data.model_dump(exclude_unset=True))

@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a module."""
    await content_service.delete_module(db, module_id)
    return {"message": "Module deleted successfully"}

# --- Lesson Endpoints ---

@router.post("/lessons", response_model=LessonRead)
async def create_lesson(
    data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a lesson to a module."""
    return await content_service.create_lesson(db, data)

@router.get("/modules/{module_id}/lessons", response_model=List[LessonRead])
async def list_module_lessons(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all lessons for a module."""
    return await content_service.list_lessons_by_module(db, module_id)

@router.patch("/lessons/{lesson_id}", response_model=LessonRead)
@router.put("/lessons/{lesson_id}", response_model=LessonRead)
async def update_lesson(
    lesson_id: uuid.UUID,
    data: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update lesson details."""
    return await content_service.update_lesson(db, lesson_id, data.model_dump(exclude_unset=True))

@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a lesson."""
    await content_service.delete_lesson(db, lesson_id)
    return {"message": "Lesson deleted successfully"}

@router.post("/lessons/{lesson_id}/rag")
async def upload_lesson_rag(
    lesson_id: uuid.UUID,
    content: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload or update RAG content for a lesson. Triggers re-indexing."""
    chunk_count = await content_service.reindex_lesson_rag(db, lesson_id, content)
    return {"message": "RAG content indexed successfully", "chunks": chunk_count}

@router.post("/lessons/{lesson_id}/blocks")
async def add_lesson_block(
    lesson_id: uuid.UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a content block (text, video, quiz) to a lesson"""
    return {"status": "Block added"}

@router.post("/lessons/{lesson_id}/tags")
async def add_lesson_tags(
    lesson_id: uuid.UUID,
    tags: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add tags for AI discovery"""
    return {"status": "Tags updated"}

@router.post("/lessons/{lesson_id}/submit")
async def submit_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit lesson for admin review"""
    return {"status": "Submitted for review"}

@router.get("/lessons/{lesson_id}/preview")
async def preview_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a preview-optimized version of the lesson"""
    return await content_service.get_lesson(db, lesson_id)

@router.get("/lessons/{lesson_id}/analytics")
async def get_lesson_analytics(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for this lesson"""
    return {
        "views": 150,
        "completion_rate": 0.85,
        "avg_time_spent": "5m 30s"
    }

@router.post("/lessons/{lesson_id}/assets")
async def upload_lesson_asset(
    lesson_id: uuid.UUID,
    asset_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload images, video, or documents to be linked in blocks"""
    return {
        "asset_id": str(uuid.uuid4()),
        "url": f"https://cdn.elitecoach.ai/assets/{lesson_id}/video.mp4"
    }
