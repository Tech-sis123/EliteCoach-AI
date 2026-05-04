from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging
import json

from core.database import get_db
from core.security import get_current_learner, security
from services.ai_tutor import ai_tutor_service
from models.models import LearningPath

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/learning",
    tags=["learning-paths"],
    dependencies=[Depends(security)]
)


@router.post("/paths/generate", status_code=status.HTTP_201_CREATED)
async def generate_learning_path(
    request: Request,
    target_role: str,
    time_per_week: int = 10,
    current_skills: dict = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_learner)
):
    """Generate personalized learning path based on user profile"""
    
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not authenticate user."
            )
        user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        # Generate study plan using AI
        study_plan = await ai_tutor_service.generate_study_plan(
            subject=target_role,
            current_level="beginner",
            goal_level="advanced",
            available_weeks=12
        )
        
        # Persist correctly in DB
        db_path = db.query(LearningPath).filter(LearningPath.user_id == user_id).first()
        if db_path:
            db_path.target_role = target_role
            db_path.study_plan = study_plan
            db_path.time_per_week = time_per_week
        else:
            db_path = LearningPath(
                user_id=user_id,
                target_role=target_role,
                study_plan=study_plan,
                time_per_week=time_per_week
            )
            db.add(db_path)
        
        db.commit()
        db.refresh(db_path)
        
        return {
            "path_id": db_path.id,
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
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_learner)
):
    """Retrieve current learning path for a user"""
    
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not authenticate user."
            )
        current_user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        # Verify user can only access their own path
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other user's learning path"
            )
        
        db_path = db.query(LearningPath).filter(LearningPath.user_id == user_id).first()
        
        if not db_path:
            return None # Frontend handles null as "no path yet"

        return {
            "path_id": db_path.id,
            "user_id": user_id,
            "target_role": db_path.target_role,
            "study_plan": db_path.study_plan,
            "time_per_week": db_path.time_per_week,
            "progress": db_path.progress,
            "completed_courses": [],
            "next_courses": [
                {
                    "id": 2,
                    "title": "Data Structures in Python",
                    "estimated_weeks": 4
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
        current_user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify other user's learning path"
            )
        
        db_path = db.query(LearningPath).filter(LearningPath.user_id == user_id).first()
        if not db_path:
            raise HTTPException(status_code=404, detail="Learning path not found")
        
        if new_goal:
            db_path.target_role = new_goal
        if time_per_week:
            db_path.time_per_week = time_per_week
            
        db.commit()
        
        return {
            "path_id": db_path.id,
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
