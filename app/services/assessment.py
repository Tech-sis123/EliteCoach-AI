from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from sqlalchemy.orm import selectinload
from app.models.assessments import Assessment, AssessmentQuestion, AssessmentAttempt, Certificate, AssessmentType
from app.models.learning import SkillScore, Skill, ReinforcementTask, LearnerProfile, PathItem
from app.models.ai_tutor import LessonSession
from app.models.content import Course, Module, Lesson
from app.services.analytics import analytics_service
from app.core.logging import logger
from app.schemas.assessment import (
    DiagnosticSubmitRequest, 
    AssessmentSubmitRequest, 
    DiagnosticStartResponse,
    AssessmentStartResponse
)
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List
from fastapi import HTTPException

class AssessmentService:
    async def get_diagnostic_questions(self, db: AsyncSession):
        query = (
            select(AssessmentQuestion)
            .join(Assessment)
            .where(Assessment.assessment_type == AssessmentType.DIAGNOSTIC)
            .order_by(AssessmentQuestion.position)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def submit_diagnostic(self, db: AsyncSession, user_id: uuid.UUID, data: DiagnosticSubmitRequest):
        diag_query = select(Assessment).where(Assessment.assessment_type == AssessmentType.DIAGNOSTIC).limit(1)
        diag = (await db.execute(diag_query)).scalar_one_or_none()
        if not diag:
            raise HTTPException(status_code=404, detail="Diagnostic assessment not found")
        
        questions_query = select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == diag.id)
        questions = (await db.execute(questions_query)).scalars().all()
        q_map = {str(q.id): q for q in questions}
        
        correct_count = 0
        total_questions = len(questions)
        for q_id, ans in data.answers.items():
            if q_id in q_map and q_map[q_id].correct_answer.strip().lower() == ans.strip().lower():
                correct_count += 1
        
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        attempt = AssessmentAttempt(
            assessment_id=diag.id,
            learner_id=user_id,
            score=score,
            passed=True,
            submitted_at=datetime.utcnow(),
            answers=data.answers
        )
        db.add(attempt)
        
        from app.worker.tasks import generate_learning_path_task
        generate_learning_path_task.delay(str(user_id))
        
        await db.commit()
        
        return {
            "score": score,
            "summary": f"Your diagnostic score is {score:.1f}%. We are tailoring your learning path.",
            "recommended_path_id": None
        }

    async def start_attempt(self, db: AsyncSession, user_id: uuid.UUID, assessment_id: uuid.UUID):
        pending_query = select(ReinforcementTask).where(
            and_(
                ReinforcementTask.learner_id == user_id,
                ReinforcementTask.assessment_id == assessment_id,
                ReinforcementTask.completed_at == None
            )
        )
        if (await db.execute(pending_query)).scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Complete your reinforcement lessons before retaking the assessment.")
        
        attempt = AssessmentAttempt(
            assessment_id=assessment_id,
            learner_id=user_id
        )
        db.add(attempt)
        await db.flush()
        
        query = select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment_id).order_by(AssessmentQuestion.position)
        result = await db.execute(query)
        questions = result.scalars().all()
        
        assessment_query = select(Assessment).where(Assessment.id == assessment_id)
        assessment = (await db.execute(assessment_query)).scalar_one()
        
        await db.commit()
        
        return {
            "attempt_id": attempt.id,
            "assessment": assessment,
            "questions": questions
        }

    async def submit_attempt(self, db: AsyncSession, user_id: uuid.UUID, attempt_id: uuid.UUID, data: AssessmentSubmitRequest):
        query = select(AssessmentAttempt).where(
            and_(AssessmentAttempt.id == attempt_id, AssessmentAttempt.learner_id == user_id)
        ).options(selectinload(AssessmentAttempt.assessment))
        result = await db.execute(query)
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")
            
        if attempt.submitted_at:
            raise HTTPException(status_code=400, detail="Already submitted")
        
        questions_query = select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == attempt.assessment_id)
        q_result = await db.execute(questions_query)
        questions = q_result.scalars().all()
        q_map = {q.id: q for q in questions}
        
        total_points = sum(q.points for q in questions)
        earned_points = 0
        submission_dict = {ans.question_id: ans.answer for ans in data.answers}
        
        for q in questions:
            user_answer = submission_dict.get(q.id)
            if user_answer and str(user_answer).strip().lower() == str(q.correct_answer).strip().lower():
                earned_points += q.points
        
        score_pct = (earned_points / total_points) * 100 if total_points > 0 else 0
        passed = score_pct >= attempt.assessment.pass_score
        
        attempt.score = score_pct
        attempt.passed = passed
        attempt.submitted_at = datetime.utcnow()
        attempt.answers = {str(k): v for k, v in submission_dict.items()}
        
        attempt.ai_feedback = f"Result: {score_pct:.1f}%. " + ("Pass! You've mastered this module." if passed else "No pass. Review reinforcement lessons.")
        
        reinforcement_lessons = []
        if not passed:
            lessons_query = select(Lesson).where(Lesson.module_id == attempt.assessment.module_id)
            lessons = (await db.execute(lessons_query)).scalars().all()
            reinforcement_lessons = [l.id for l in lessons[:2]]
            
            rt = ReinforcementTask(
                learner_id=user_id,
                assessment_id=attempt.assessment_id,
                attempt_id=attempt.id,
                lesson_ids=reinforcement_lessons,
                reason="failed_module_exam"
            )
            db.add(rt)
        
        if passed and attempt.assessment.assessment_type == AssessmentType.FINAL:
            await self.issue_certificate(db, user_id, attempt.assessment.course_id, attempt.id)
            
        await db.commit()
        
        return {
            "attempt_id": attempt.id,
            "score": score_pct,
            "is_passed": passed,
            "ai_feedback": attempt.ai_feedback,
            "reinforcement_lessons": reinforcement_lessons
        }

    async def issue_certificate(self, db: AsyncSession, learner_id: uuid.UUID, course_id: uuid.UUID, attempt_id: uuid.UUID):
        exists_query = select(Certificate).where(and_(Certificate.learner_id == learner_id, Certificate.course_id == course_id))
        cert = (await db.execute(exists_query)).scalar_one_or_none()
        if cert:
            return cert

        pdf_url = f"https://storage.elitecoach.ai/certs/{uuid.uuid4()}.pdf"
        cert = Certificate(
            learner_id=learner_id,
            course_id=course_id,
            attempt_id=attempt_id,
            pdf_url=pdf_url,
            verification_id=uuid.uuid4()
        )
        db.add(cert)
        return cert

    async def get_certificate_by_verification(self, db: AsyncSession, verification_id: uuid.UUID):
        query = select(Certificate).where(Certificate.verification_id == verification_id).options(selectinload(Certificate.course))
        result = await db.execute(query)
        cert = result.scalar_one_or_none()
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return cert

    async def get_user_certificates(self, db: AsyncSession, user_id: uuid.UUID):
        query = select(Certificate).where(Certificate.learner_id == user_id).options(selectinload(Certificate.course))
        result = await db.execute(query)
        return result.scalars().all()

    async def get_user_attempts(self, db: AsyncSession, user_id: uuid.UUID):
        query = select(AssessmentAttempt).where(AssessmentAttempt.learner_id == user_id).options(selectinload(AssessmentAttempt.assessment)).order_by(AssessmentAttempt.submitted_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def get_final_assessment_for_course(self, db: AsyncSession, course_id: uuid.UUID):
        query = select(Assessment).where(
            and_(
                Assessment.course_id == course_id,
                Assessment.assessment_type == AssessmentType.FINAL,
                Assessment.is_active == True
            )
        )
        result = await db.execute(query)
        assessment = result.scalar_one_or_none()
        if not assessment:
            raise HTTPException(status_code=404, detail="Final assessment not found for this course")
        return assessment

assessment_service = AssessmentService()
