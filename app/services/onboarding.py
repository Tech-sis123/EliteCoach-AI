from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.models.learning import LearnerProfile, DiagnosticQuestion, DiagnosticAttempt, SkillScore, Skill
from app.models.content import Course
from app.schemas.learning import OnboardingStart, DiagnosticSubmit
from fastapi import HTTPException
import uuid

class OnboardingService:
    async def start_onboarding(self, db: AsyncSession, user_id: uuid.UUID, data: OnboardingStart):
        # Create or update learner profile
        query = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        
        if profile:
            profile.current_role = data.current_role
            profile.years_experience = data.years_experience
            profile.career_goal = data.career_goal
            profile.hours_per_week = data.hours_per_week
        else:
            profile = LearnerProfile(
                user_id=user_id,
                current_role=data.current_role,
                years_experience=data.years_experience,
                career_goal=data.career_goal,
                hours_per_week=data.hours_per_week
            )
            db.add(profile)
        
        await db.flush()
        await db.commit()
        
        # Get diagnostic questions (Simplified: 5 random for demo)
        questions_query = select(DiagnosticQuestion).limit(10)
        questions_result = await db.execute(questions_query)
        return questions_result.scalars().all()

    async def submit_diagnostic(self, db: AsyncSession, user_id: uuid.UUID, data: DiagnosticSubmit):
        query = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Score logic (placeholder)
        score = 0.0 # Calculate based on data.answers
        
        # Convert UUID keys to strings for JSON serialization
        safe_answers = {str(k): v for k, v in data.answers.items()}
        
        attempt = DiagnosticAttempt(
            learner_profile_id=profile.id,
            answers=safe_answers,
            score=score
        )
        db.add(attempt)
        await db.commit()
        
        return await self.generate_learning_path(db, profile.id)

    async def generate_learning_path(self, db: AsyncSession, profile_id: uuid.UUID):
        # Fetch some courses to return a semi-valid path
        from app.models.content import Course
        result = await db.execute(select(Course).limit(2))
        courses = result.scalars().all()
        
        items = []
        for i, course in enumerate(courses):
            items.append({
                "course_id": course.id,
                "title": course.title,
                "position": i + 1,
                "status": "NOT_STARTED"
            })
            
        return {
            "id": uuid.uuid4(),
            "items": items
        }

onboarding_service = OnboardingService()
