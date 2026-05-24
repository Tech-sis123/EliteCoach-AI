from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.learning import OnboardingStart, DiagnosticQuestionRead, DiagnosticSubmit, LearningPathRead
from app.services.onboarding import onboarding_service
from app.api.deps import get_current_user_id
from typing import List
import uuid

router = APIRouter()

@router.post("/start", response_model=List[DiagnosticQuestionRead])
async def start_onboarding(
    data: OnboardingStart, 
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await onboarding_service.start_onboarding(db, user_id, data)

@router.post("/submit", response_model=LearningPathRead)
async def submit_onboarding(
    data: DiagnosticSubmit, 
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await onboarding_service.submit_diagnostic(db, user_id, data)
