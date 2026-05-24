from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.assessment import assessment_service
from pydantic import BaseModel
from typing import Dict
import uuid

router = APIRouter()

from app.api.deps import get_current_user_id
from typing import Dict
import uuid

router = APIRouter()

class AttemptSubmit(BaseModel):
    answers: Dict[uuid.UUID, str]

@router.post("/{id}/start")
async def start_assessment(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await assessment_service.start_attempt(db, user_id, id)

@router.get("/course/{course_id}")
async def list_course_assessments(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await assessment_service.list_assessments_by_course(db, course_id)

@router.get("/certificates/me")
async def get_my_certificates(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await assessment_service.get_user_certificates(db, user_id)

@router.post("/attempts/{id}/submit")
async def submit_assessment(
    id: uuid.UUID,
    data: AttemptSubmit,
    db: AsyncSession = Depends(get_db)
):
    return await assessment_service.submit_attempt(db, id, data.answers)
