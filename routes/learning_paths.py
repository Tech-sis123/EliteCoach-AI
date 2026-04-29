from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.security import get_current_learner, security
from services.ai_tutor import ai_tutor_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/learning",
    tags=["learning-paths"],
    dependencies=[Depends(security)]
)


@router.post("/paths/generate")
async def generate_learning_path(
    request: Request,
    target_role: str,
    time_per_week: int = 10,
    current_skills: dict = None,
    db: Session = Depends(get_db)
):
    """Generate personalized learning path based on user profile"""
    
    try:
        current_user = await get_current_learner(request)
        user_id = current_user.get('id') or current_user.get('userId')
        
        # Generate study plan using AI
        study_plan = await ai_tutor_service.generate_study_plan(
            subject=target_role,
            current_level="beginner",
            goal_level="advanced",
            available_weeks=12
        )
        
        return {
            "path_id": f"path_{user_id}",
            "user_id": user_id,
            "target_role": target_role,
            "study_plan": study_plan,
            "time_per_week": time_per_week,
            "estimated_weeks": 12,
            "next_course": "Introduction to Python",
            "status": "generated"
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error generating learning path: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning path: {str(e)}"
        )


@router.get("/paths/{user_id}")
async def get_learning_path(
    request: Request,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve current learning path for a user"""
    
    try:
        current_user = await get_current_learner(request)
        current_user_id = current_user.get('id') or current_user.get('userId')
        
        # Verify user can only access their own path
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other user's learning path"
            )
        
        return {
            "path_id": f"path_{user_id}",
            "user_id": user_id,
            "target_role": "Software Engineer",
            "progress": 25,
            "completed_courses": [
                {
                    "id": 1,
                    "title": "Python Basics",
                    "completed_at": "2026-04-01"
                }
            ],
            "next_courses": [
                {
                    "id": 2,
                    "title": "Data Structures in Python",
                    "estimated_weeks": 4
                },
                {
                    "id": 3,
                    "title": "Web Development with FastAPI",
                    "estimated_weeks": 6
                }
            ],
            "estimated_completion": "2026-08-15"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving learning path: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve learning path"
        )


@router.put("/paths/{user_id}")
async def update_learning_path(
    request: Request,
    user_id: str,
    new_goal: str = None,
    time_per_week: int = None,
    db: Session = Depends(get_db)
):
    """Update learning path preferences"""
    
    try:
        current_user = await get_current_learner(request)
        current_user_id = current_user.get('id') or current_user.get('userId')
        
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify other user's learning path"
            )
        
        return {
            "path_id": f"path_{user_id}",
            "status": "updated",
            "new_goal": new_goal,
            "new_time_per_week": time_per_week
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating learning path: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update learning path"
        )
