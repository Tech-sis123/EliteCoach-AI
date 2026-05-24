from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.content import Course, Module, Lesson, RagChunk
from app.schemas.content import CourseCreate, LessonCreate
from app.core.logging import logger
from app.integrations.openai_client import openai_client
import uuid

class ContentService:
    async def create_course(self, db: AsyncSession, author_id: uuid.UUID, data: CourseCreate):
        course = Course(
            **data.model_dump(),
            author_id=author_id,
            status="draft"
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    async def list_courses(self, db: AsyncSession):
        query = select(Course).where(Course.status == "published")
        result = await db.execute(query)
        return result.scalars().all()

    async def list_lessons_by_course(self, db: AsyncSession, course_id: uuid.UUID):
        # Lessons are in modules. Join them.
        query = (
            select(Lesson)
            .join(Module, Lesson.module_id == Module.id)
            .where(Module.course_id == course_id)
            .order_by(Module.position, Lesson.position)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def create_lesson(self, db: AsyncSession, data: LessonCreate):
        lesson = Lesson(
            **data.model_dump(),
            status="draft",
            version=1
        )
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    async def reindex_lesson_rag(self, db: AsyncSession, lesson_id: uuid.UUID, text_content: str):
        """
        Celery task logic placeholder for re-indexing RAG chunks.
        Splits text, generates embeddings, and saves to RagChunk table.
        """
        # 1. Clear old chunks
        from sqlalchemy import delete
        await db.execute(delete(RagChunk).where(RagChunk.lesson_id == lesson_id))
        
        # 2. Simple chunking (500 tokens approx)
        chunks = [text_content[i:i+1000] for i in range(0, len(text_content), 900)]
        
        for idx, text in enumerate(chunks):
            embedding = await openai_client.get_embedding(text)
            chunk = RagChunk(
                lesson_id=lesson_id,
                chunk_index=idx,
                chunk_text=text,
                embedding=str(embedding), # Store as string for now
                token_count=len(text.split())
            )
            db.add(chunk)
        
        await db.commit()
        logger.info("content_reindexed", lesson_id=str(lesson_id))

content_service = ContentService()
