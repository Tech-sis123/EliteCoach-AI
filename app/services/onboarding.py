from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, func, desc, update, and_
from sqlalchemy.orm import selectinload
from app.models.learning import LearnerProfile, DiagnosticQuestion, DiagnosticAttempt, SkillScore, Skill, LearningPath, PathItem, ReinforcementTask
from app.models.content import Course, Lesson, Module
from app.models.analytics import Event
from app.schemas.learning import OnboardingStart, DiagnosticSubmit
from fastapi import HTTPException
import uuid
from datetime import datetime, timedelta

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
        
        # Get diagnostic questions (Simplified: 10 random for demo)
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
        await db.flush()
        
        # Generate the path
        await self.generate_learning_path(db, profile.id)
        await db.commit()
        
        # Re-fetch the newly generated path with full data
        path_data = await self.get_learning_path_raw(db, profile.id)
        if not path_data:
             raise HTTPException(status_code=500, detail="Failed to generate learning path")
        return path_data

    async def get_learning_path_raw(self, db: AsyncSession, profile_id: uuid.UUID):
        # We need the learner_profile_id to find the path
        query = select(LearningPath).where(
            LearningPath.learner_profile_id == profile_id,
            LearningPath.status == "active"
        ).options(
            selectinload(LearningPath.items).selectinload(PathItem.course)
        ).order_by(desc(LearningPath.version)) # Get newest version
        
        result = await db.execute(query)
        path = result.scalar_one_or_none()
        
        if not path:
            return None
            
        # Manually ensure items are loaded to avoid MissingGreenlet in response validation
        formatted_items = []
        for item in path.items:
            # Subquery to get total minutes for the course
            minutes_query = select(func.sum(Lesson.estimated_minutes)).join(Module).where(Module.course_id == item.course_id)
            minutes_result = await db.execute(minutes_query)
            total_minutes = minutes_result.scalar() or 0
            
            formatted_items.append({
                "id": item.id,
                "position": item.position,
                "status": item.status,
                "course_id": item.course_id,
                "course_title": item.course.title,
                "course_domain": item.course.domain,
                "course_difficulty": item.course.difficulty,
                "total_minutes": total_minutes,
                "unlocked_at": item.unlocked_at
            })
            
        # Get active reinforcement tasks
        tasks_query = select(ReinforcementTask).where(
            and_(
                ReinforcementTask.learner_id == path.learner_profile.user_id,
                ReinforcementTask.completed_at == None
            )
        )
        tasks_result = await db.execute(tasks_query)
        tasks = tasks_result.scalars().all()
        
        reinforcement_data = []
        for t in tasks:
            # Fetch lesson details for titles
            lessons_query = select(Lesson).where(Lesson.id.in_(t.lesson_ids))
            lessons_res = await db.execute(lessons_query)
            lessons = lessons_res.scalars().all()
            
            reinforcement_data.append({
                "id": t.id,
                "reason": t.reason,
                "lessons": [{"id": l.id, "title": l.title} for l in lessons]
            })

        return {
            "id": path.id,
            "generated_at": path.generated_at,
            "version": path.version,
            "status": path.status,
            "items": formatted_items,
            "reinforcement_tasks": reinforcement_data
        }

    async def get_learning_path(self, db: AsyncSession, user_id: uuid.UUID):
        query = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        if not profile:
             raise HTTPException(status_code=404, detail="No active learning path found. Complete onboarding to generate your path.")
        
        path_data = await self.get_learning_path_raw(db, profile.id)
        if not path_data:
            raise HTTPException(status_code=404, detail="No active learning path found. Complete onboarding to generate your path.")
        
        return path_data

    async def regenerate_learning_path(self, db: AsyncSession, user_id: uuid.UUID):
        query = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Rate limit check: max 3 per 24h from events table
        limit_query = select(func.count(Event.id)).where(
            Event.actor_id == user_id,
            Event.event_type == "path.regenerated",
            Event.occurred_at > datetime.utcnow() - timedelta(hours=24)
        )
        limit_count = (await db.execute(limit_query)).scalar()
        if limit_count >= 3:
            raise HTTPException(status_code=429, detail="You can regenerate your path at most 3 times per day")

        # Archive old path
        await db.execute(
            update(LearningPath)
            .where(LearningPath.learner_profile_id == profile.id, LearningPath.status == "active")
            .values(status="archived")
        )
        
        # Log event
        event = Event(
            event_type="path.regenerated",
            actor_id=user_id,
            entity_type="learning_path",
            payload={"reason": "user_request"}
        )
        db.add(event)
        
        await self.generate_learning_path(db, profile.id)
        await db.commit()
        
        # Re-fetch new path decorated
        return await self.get_learning_path(db, user_id)

    async def generate_learning_path(self, db: AsyncSession, profile_id: uuid.UUID):
        # Fetch some courses (Simplified for now)
        result = await db.execute(select(Course).where(Course.status == "published").limit(3))
        courses = result.scalars().all()
        
        if not courses:
            # Fallback for testing if no courses are published
            result = await db.execute(select(Course).limit(3))
            courses = result.scalars().all()

        version_query = select(func.max(LearningPath.version)).where(LearningPath.learner_profile_id == profile_id)
        max_version = (await db.execute(version_query)).scalar() or 0
        
        path = LearningPath(
            learner_profile_id=profile_id,
            status="active",
            version=max_version + 1
        )
        db.add(path)
        await db.flush()
        
        for i, course in enumerate(courses):
            item = PathItem(
                learning_path_id=path.id,
                course_id=course.id,
                position=i + 1,
                status="available" if i == 0 else "locked",
                unlocked_at=datetime.utcnow() if i == 0 else None
            )
            db.add(item)
            
        await db.commit()
        return path

onboarding_service = OnboardingService()
