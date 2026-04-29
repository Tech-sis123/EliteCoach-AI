from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging
import json

logger = logging.getLogger(__name__)

from core.database import get_db
from core.security import get_current_learner, security
from models.models import Assessment
from schemas.schemas import AssessmentSubmission
from services.ai_tutor import ai_tutor_service
from services.event_publisher import event_publisher

router = APIRouter(
    prefix="/api/v1/assessments",
    tags=["assessments"],
    dependencies=[Depends(security)]
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
    submission: AssessmentSubmission,
    db: Session = Depends(get_db)
):
    """Submit assessment answers for grading"""
    
    try:
        current_user = await get_current_learner(request)
        user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        # Simple grading logic
        correct_count = 0
        total_questions = len(submission.questions)
        
        # submission.answers is expected to be a list of strings or dicts matching questions
        # Frontend usually sends { question_id: answer } or just a list of answers
        # For simplicity, let's assume answers match the questions index or ID
        
        for i, q in enumerate(submission.questions):
            student_ans = submission.answers[i] if i < len(submission.answers) else None
            # Handle case where student_ans might be a dict {"id": "...", "answer": "..."}
            actual_answer = student_ans.get("answer") if isinstance(student_ans, dict) else student_ans
            
            if q.get("correct_answer") == actual_answer:
                correct_count += 1
        
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        passed = score >= 70
        
        # Create assessment record
        assessment = Assessment(
            student_id=user_id,
            course_id=submission.course_id,
            questions=json.dumps(submission.questions),
            answers=json.dumps(submission.answers),
            score=score,
            total_questions=total_questions,
            ai_feedback=f"You got {correct_count} out of {total_questions} correct."
        )
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        logger.info(f"Assessment {assessment.id} graded. Score: {score} for user {user_id}")
        
        # If passed, trigger course completion event (which should trigger ACS for certificate)
        if passed:
            await event_publisher.publish_learner_course_completed(
                learner_id=user_id,
                course_id=str(submission.course_id),
                score=score,
                time_taken_hours=1.0 # Placeholder
            )
        
        return {
            "assessment_id": assessment.id,
            "submitted_at": assessment.created_at,
            "status": "completed",
            "score": score,
            "passed": passed,
            "total_questions": total_questions,
            "correct_answers": correct_count,
            "next_step": "Certificate generated" if passed else "Try again to earn your certificate"
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
        user_id = str(current_user.get('id') or current_user.get('userId') or current_user.get('email'))
        
        assessment = db.query(Assessment).filter(
            Assessment.id == assessment_id,
            Assessment.student_id == user_id
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
