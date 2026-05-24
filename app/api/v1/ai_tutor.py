from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.ai_tutor import ai_tutor_service
from pydantic import BaseModel
import uuid

router = APIRouter()

class SessionStart(BaseModel):
    lesson_id: uuid.UUID

class MessageIn(BaseModel):
    message: str

from app.api.deps import get_current_user_id
import uuid

router = APIRouter()

class SessionStart(BaseModel):
    lesson_id: uuid.UUID

class MessageIn(BaseModel):
    message: str

@router.post("/session/start")
async def start_session(
    data: SessionStart,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await ai_tutor_service.start_session(db, user_id, data.lesson_id)

@router.post("/session/{id}/message")
async def send_message(
    id: uuid.UUID,
    data: MessageIn,
    db: AsyncSession = Depends(get_db)
):
    return await ai_tutor_service.get_response(db, id, data.message)
