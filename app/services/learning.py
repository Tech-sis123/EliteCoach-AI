from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from app.models.content import Course, Module, Lesson
from app.models.learning import PathItem, LearnerProfile, LearningPath
from app.models.ai_tutor import LessonSession
from app.models.users import User
from app.models.ai_tutor import SessionStatus, KnowledgeCheck
from app.models.analytics import Event
from fastapi import HTTPException
import uuid
from datetime import datetime
import asyncio

class LearningService:
    async def get_course_detail(self, db: AsyncSession, course_id: uuid.UUID):
        query = (
            select(Course, User.full_name.label("author_name"))
            .join(User, Course.author_id == User.id)
            .where(Course.id == course_id)
        )
        result = await db.execute(query)
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Course not found")
        
        course, author_name = row
        
        modules_query = (
            select(Module, func.count(Lesson.id).label("lesson_count"))
            .outerjoin(Lesson, Module.id == Lesson.module_id)
            .where(Module.course_id == course_id)
            .group_by(Module.id)
            .order_by(Module.position.asc())
        )
        modules_result = await db.execute(modules_query)
        modules_data = []
        total_lessons = 0
        
        for m, count in modules_result.all():
            modules_data.append({
                "id": m.id,
                "title": m.title,
                "position": m.position,
                "lesson_count": count
            })
            total_lessons += count
            
        mins_query = select(func.sum(Lesson.estimated_minutes)).where(
            Lesson.module_id.in_(select(Module.id).where(Module.course_id == course_id))
        )
        total_minutes = (await db.execute(mins_query)).scalar() or 0
        
        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "domain": course.domain,
            "difficulty": course.difficulty,
            "author_name": author_name,
            "total_lessons": total_lessons,
            "total_minutes": total_minutes,
            "modules": modules_data
        }

    async def start_lesson(self, db: AsyncSession, user_id: uuid.UUID, lesson_id: uuid.UUID):
        # 1. Reuse or Create Session
        from app.services.ai_tutor import ai_tutor_service
        session = await ai_tutor_service.start_session(db, user_id, lesson_id)
        
        lesson_query = select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.module))
        lesson = (await db.execute(lesson_query)).scalar_one()
        course_id = lesson.module.course_id
        
        path_query = select(PathItem).join(LearningPath).where(
            and_(
                LearningPath.learner_profile_id.in_(
                    select(LearnerProfile.id).where(LearnerProfile.user_id == user_id)
                ),
                LearningPath.status == "active",
                PathItem.course_id == course_id,
                PathItem.status == "available"
            )
        )
        item_result = await db.execute(path_query)
        item = item_result.scalar_one_or_none()
        if item:
            item.status = "in_progress"
        
        checks_count_query = select(func.count(KnowledgeCheck.id)).where(KnowledgeCheck.lesson_id == lesson_id)
        checks_count = (await db.execute(checks_count_query)).scalar() or 0
            
        event = Event(
            event_type="lesson.started",
            actor_id=user_id,
            entity_type="lesson",
            entity_id=lesson_id
        )
        db.add(event)
        await db.commit()
        
        return {
            "session_id": session.id,
            "lesson": lesson,
            "checks_count": checks_count
        }

    async def complete_lesson(self, db: AsyncSession, user_id: uuid.UUID, lesson_id: uuid.UUID):
        query = select(LessonSession).where(
            and_(
                LessonSession.learner_id == user_id,
                LessonSession.lesson_id == lesson_id,
                LessonSession.status == SessionStatus.ACTIVE
            )
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=400, detail="No active session found for this lesson")
        
        session.status = SessionStatus.COMPLETED
        session.ended_at = datetime.utcnow()
        
        # Background task for summary
        from app.services.ai_tutor import ai_tutor_service
        asyncio.create_task(ai_tutor_service.get_summary(db, session.id))
        
        # Check if course is complete
        lesson_query = select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.module))
        lesson = (await db.execute(lesson_query)).scalar_one()
        
        next_lesson_query = select(Lesson).where(
            and_(
                Lesson.module_id == lesson.module_id,
                Lesson.position > lesson.position
            )
        ).order_by(Lesson.position.asc()).limit(1)
        next_lesson = (await db.execute(next_lesson_query)).scalar_one_or_none()
        
        event = Event(
            event_type="lesson.completed",
            actor_id=user_id,
            entity_type="lesson",
            entity_id=lesson_id
        )
        db.add(event)
        await db.commit()
        
        return {
            "session_id": session.id,
            "completed_at": session.ended_at,
            "next_lesson_id": next_lesson.id if next_lesson else None,
            "module_assessment_unlocked": next_lesson is None,
            "final_exam_unlocked": False # Final exam logic needed
        }

learning_service = LearningService()
