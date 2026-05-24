from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.assessment import (
    DiagnosticSubmitRequest, 
    DiagnosticSubmitResponse, 
    DiagnosticStartResponse,
    AssessmentStartResponse,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse
)
from app.services.assessment import assessment_service
from app.models.users import User
from app.models.assessments import Assessment, AssessmentType
from sqlalchemy import select, and_
import uuid

router = APIRouter()

@router.get("/diagnostic", response_model=DiagnosticStartResponse)
async def get_diagnostic_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the pre-course diagnostic questions."""
    questions = await assessment_service.get_diagnostic_questions(db)
    return {"questions": questions}

@router.post("/diagnostic/submit", response_model=DiagnosticSubmitResponse)
async def submit_diagnostic(
    data: DiagnosticSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit diagnostic answers and trigger learning path generation."""
    return await assessment_service.submit_diagnostic(db, current_user.id, data)

@router.get("/my-attempts")
async def get_my_attempts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all assessment attempts for the current user."""
    return await assessment_service.get_user_attempts(db, current_user.id)

@router.get("/certificates/me")
async def get_my_certificates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all certificates for the current user."""
    return await assessment_service.get_user_certificates(db, current_user.id)

@router.post("/{assessment_id}/start", response_model=AssessmentStartResponse)
async def start_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a module or final assessment."""
    return await assessment_service.start_attempt(db, current_user.id, assessment_id)

@router.post("/attempt/{attempt_id}/submit", response_model=AssessmentSubmitResponse)
async def submit_assessment(
    attempt_id: uuid.UUID,
    data: AssessmentSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit assessment answers for grading."""
    return await assessment_service.submit_attempt(db, current_user.id, attempt_id, data)

@router.get("/course/{course_id}")
async def list_course_assessments(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all assessments for a course."""
    query = select(Assessment).where(and_(Assessment.course_id == course_id, Assessment.is_active == True))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/course/{course_id}/final")
async def get_course_final_assessment(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the final assessment for a course."""
    return await assessment_service.get_final_assessment_for_course(db, course_id)

@router.get("/module/{module_id}")
async def get_module_assessment_info(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assessment info for a specific module."""
    query = select(Assessment).where(and_(Assessment.module_id == module_id, Assessment.assessment_type == AssessmentType.MODULE))
    result = await db.execute(query)
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="No assessment found for this module")
    return assessment
