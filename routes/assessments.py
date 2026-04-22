from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging
import json

from core.database import get_db
from core.security import get_current_learner
from models.models import Assessment
from services.ai_tutor import ai_tutor_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/assessments",
    tags=["assessments"]
)


@router.post("/generate-quiz")
async def generate_quiz(
    request: Request,
    course_id: int,
    topic: str,
    num_questions: int = 5,
    level: str = "beginner",
    db: Session = Depends(get_db)
):
    """Generate a quiz on a specific topic"""
    
    try:
        current_user = await get_current_learner(request)
        
        # Generate quiz questions using AI
        quiz_questions = await ai_tutor_service.generate_quiz(
            topic=topic,
            num_questions=num_questions,
            level=level
        )
        
        return {
            "quiz_id": f"quiz_{course_id}_{topic}",
            "topic": topic,
            "num_questions": num_questions,
            "level": level,
            "questions": quiz_questions,
            "time_limit_minutes": 30,
            "status": "ready"
        }
    
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz"
        )


@router.post("/submit")
async def submit_assessment(
    request: Request,
    assessment_data: dict,
    db: Session = Depends(get_db)
):
    """Submit assessment answers for grading"""
    
    try:
        current_user = await get_current_learner(request)
        user_id = current_user.get('id') or current_user.get('userId')
        
        # Create assessment record
        assessment = Assessment(
            student_id=str(user_id),
            course_id=assessment_data.get('course_id'),
            questions=json.dumps(assessment_data.get('questions', [])),
            answers=json.dumps(assessment_data.get('answers', [])),
            score=0.0,
            total_questions=len(assessment_data.get('answers', []))
        )
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        logger.info(f"Assessment {assessment.id} submitted for user {user_id}")
        
        return {
            "assessment_id": assessment.id,
            "submitted_at": assessment.created_at,
            "status": "submitted",
            "next_step": "We're grading your assessment..."
        }
    
    except Exception as e:
        logger.error(f"Error submitting assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit assessment"
        )


@router.get("/results/{assessment_id}")
async def get_assessment_results(
    request: Request,
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve assessment results and feedback"""
    
    try:
        current_user = await get_current_learner(request)
        user_id = current_user.get('id') or current_user.get('userId')
        
        assessment = db.query(Assessment).filter(
            Assessment.id == assessment_id,
            Assessment.student_id == str(user_id)
        ).first()
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        return {
            "assessment_id": assessment.id,
            "score": assessment.score,
            "total_questions": assessment.total_questions,
            "passed": assessment.score >= 70,
            "feedback": assessment.ai_feedback or "Assessment graded successfully",
            "created_at": assessment.created_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving assessment results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assessment results"
        )
