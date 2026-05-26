from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.models.content import Course, Module, Lesson, RagChunk
from app.schemas.content import CourseCreate, LessonCreate, ModuleCreate
from app.core.logging import logger
from app.integrations.openai_client import openai_client
import uuid

class ContentService:
    # --- Course CRUD ---
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

    async def get_course(self, db: AsyncSession, course_id: uuid.UUID):
        query = select(Course).where(Course.id == course_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_course(self, db: AsyncSession, course_id: uuid.UUID, data: dict):
        query = update(Course).where(Course.id == course_id).values(**data)
        await db.execute(query)
        await db.commit()
        return await self.get_course(db, course_id)

    async def delete_course(self, db: AsyncSession, course_id: uuid.UUID):
        query = delete(Course).where(Course.id == course_id)
        await db.execute(query)
        await db.commit()
        return True

    async def update_course_status(self, db: AsyncSession, course_id: uuid.UUID, status: str):
        query = update(Course).where(Course.id == course_id).values(status=status)
        await db.execute(query)
        await db.commit()
        return True

    async def list_courses(self, db: AsyncSession, status: str = None):
        if status:
            query = select(Course).where(Course.status == status)
        else:
            query = select(Course)
        result = await db.execute(query)
        return result.scalars().all()

    # --- Module CRUD ---
    async def create_module(self, db: AsyncSession, data: ModuleCreate):
        module = Module(**data.model_dump())
        db.add(module)
        await db.commit()
        await db.refresh(module)
        return module

    async def get_module(self, db: AsyncSession, module_id: uuid.UUID):
        query = select(Module).where(Module.id == module_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_modules(self, db: AsyncSession, course_id: uuid.UUID):
        query = select(Module).where(Module.course_id == course_id).order_by(Module.position)
        result = await db.execute(query)
        return result.scalars().all()

    async def update_module(self, db: AsyncSession, module_id: uuid.UUID, data: dict):
        query = update(Module).where(Module.id == module_id).values(**data)
        await db.execute(query)
        await db.commit()
        return await self.get_module(db, module_id)

    async def delete_module(self, db: AsyncSession, module_id: uuid.UUID):
        query = delete(Module).where(Module.id == module_id)
        await db.execute(query)
        await db.commit()
        return True

    # --- Lesson CRUD ---
    async def create_lesson(self, db: AsyncSession, data: LessonCreate):
        lesson = Lesson(
            **data.model_dump(),
            status="draft",
            version=1
        )
        db.add(lesson)
        await db.commit()
        
        # Load content_blocks explicitly to avoid lazy loading issues in the response
        query = select(Lesson).where(Lesson.id == lesson.id).options(selectinload(Lesson.content_blocks))
        result = await db.execute(query)
        return result.scalar_one()

    async def get_lesson(self, db: AsyncSession, lesson_id: uuid.UUID):
        query = select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.content_blocks))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_lessons_by_course(self, db: AsyncSession, course_id: uuid.UUID):
        query = (
            select(Lesson)
            .join(Module)
            .where(Module.course_id == course_id)
            .options(selectinload(Lesson.content_blocks))
            .order_by(Module.position, Lesson.position)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def list_lessons_by_module(self, db: AsyncSession, module_id: uuid.UUID):
        query = select(Lesson).where(Lesson.module_id == module_id).options(selectinload(Lesson.content_blocks)).order_by(Lesson.position)
        result = await db.execute(query)
        return result.scalars().all()

    async def update_lesson(self, db: AsyncSession, lesson_id: uuid.UUID, data: dict):
        query = update(Lesson).where(Lesson.id == lesson_id).values(**data)
        await db.execute(query)
        await db.commit()
        return await self.get_lesson(db, lesson_id)

    async def delete_lesson(self, db: AsyncSession, lesson_id: uuid.UUID):
        query = delete(Lesson).where(Lesson.id == lesson_id)
        await db.execute(query)
        await db.commit()
        return True

    async def reindex_lesson_rag(self, db: AsyncSession, lesson_id: uuid.UUID, text_content: str):
        """
        Splits text, generates embeddings, and saves to RagChunk table.
        """
        await db.execute(delete(RagChunk).where(RagChunk.lesson_id == lesson_id))
        
        chunks = [text_content[i:i+1000] for i in range(0, len(text_content), 900)]
        for idx, text in enumerate(chunks):
            embedding = await openai_client.get_embedding(text)
            chunk = RagChunk(
                lesson_id=lesson_id,
                chunk_index=idx,
                chunk_text=text,
                embedding=str(embedding),
                token_count=len(text.split())
            )
            db.add(chunk)
        
        await db.commit()
        logger.info(f"Lesson {lesson_id} reindexed with {len(chunks)} chunks")
        return len(chunks)

content_service = ContentService()
