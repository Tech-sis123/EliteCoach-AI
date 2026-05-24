from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, desc, func, and_, update
from sqlalchemy.orm import selectinload
from app.models.ai_tutor import LessonSession, SessionMessage, SessionStatus, Escalation, KnowledgeCheck, KnowledgeCheckResponse
from app.models.content import RagChunk, Lesson, Module
from app.models.learning import LearnerProfile, SkillScore, Skill
from app.models.analytics import Event
from app.services.analytics import analytics_service
# Removed app.services.escalation.escalation_service as we'll implement fire_escalation here or import it correctly
from app.integrations.anthropic_client import anthropic_client
from app.integrations.openai_client import openai_client
from app.core.logging import logger
from app.core.config import settings
import uuid
import json
import asyncio
import numpy as np

def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

class AiTutorService:
    async def start_session(self, db: AsyncSession, user_id: uuid.UUID, lesson_id: uuid.UUID):
        # Reuse existing active session if available
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
            session = LessonSession(
                learner_id=user_id,
                lesson_id=lesson_id,
                status=SessionStatus.ACTIVE
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
        
        return session

    async def get_response(self, db: AsyncSession, session_id: uuid.UUID, user_message: str):
        # 1. Load session and context
        query = select(LessonSession).where(LessonSession.id == session_id).options(selectinload(LessonSession.lesson))
        result = await db.execute(query)
        session = result.scalar_one()
        
        if session.status == SessionStatus.ESCALATED:
            esc_query = select(Escalation).where(Escalation.session_id == session_id)
            esc_result = await db.execute(esc_query)
            esc = esc_result.scalar_one_or_none()
            return {
                "reply": "Your session has been escalated to a human tutor. You will be notified soon.",
                "escalated": True,
                "escalation_id": esc.id if esc else None,
                "rag_sources": 0
            }

        # 2. Get history (last 20)
        history_query = select(SessionMessage).where(SessionMessage.session_id == session_id).order_by(SessionMessage.created_at.asc()).limit(20)
        history_result = await db.execute(history_query)
        history = history_result.scalars().all()
        
        # 3. Load learner profile
        profile_query = select(LearnerProfile).where(LearnerProfile.user_id == session.learner_id)
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()
        
        # 4. Embed message
        embedding = await openai_client.get_embedding(user_message)
        
        # 5. RAG - Vector Search
        # Using string representation for now since pgvector isn't fully set up in the model
        # In production this would be: .order_by(RagChunk.embedding.cosine_distance(embedding))
        rag_query = select(RagChunk).where(RagChunk.lesson_id == session.lesson_id).limit(5)
        rag_result = await db.execute(rag_query)
        chunks = rag_result.scalars().all()
        
        if not chunks:
            return {
                "reply": "I don't have content loaded for this lesson yet. Please check back later.",
                "escalated": False,
                "rag_sources": 0
            }

        context_text = "\n".join([c.chunk_text for c in chunks])
        
        # 6. Build System Prompt
        weak_skills_query = select(Skill.name).join(SkillScore).where(
            SkillScore.learner_profile_id == profile.id if profile else None,
            SkillScore.score < 60
        )
        weak_skills = (await db.execute(weak_skills_query)).scalars().all() if profile else []
        
        system_prompt = f"""You are an AI tutor for the lesson: "{session.lesson.title}".

STRICT RULE: You must ONLY answer using the lesson context provided below.
If the learner's question cannot be answered from the context, respond EXACTLY with:
"I can't find that in this lesson's content. Would you like me to escalate to a human tutor?"
Do NOT make up information. Do NOT use outside knowledge.

Learner profile:
- Career goal: {profile.career_goal if profile else 'Not set'}
- Areas to reinforce: {', '.join(weak_skills) or 'None identified yet'}

Lesson context:
{context_text}
"""
        
        messages = [{"role": m.role, "content": m.content} for m in history]
        messages.append({"role": "user", "content": user_message})

        # 7. Call Anthropic
        # We need usage info, so we'll use a local instance of the client or update the integration
        try:
            # Updating anthropic_client.client directly to get usage
            response = await anthropic_client.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            reply_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
        except Exception as e:
            logger.error("anthropic_error", error=str(e))
            reply_text = "I'm currently having trouble connecting to my brain. Would you like me to escalate this?"
            tokens_used = 0

        # 8. Save messages
        user_msg = SessionMessage(session_id=session_id, role="user", content=user_message, tokens_used=0)
        assistant_msg = SessionMessage(
            session_id=session_id, 
            role="assistant", 
            content=reply_text, 
            rag_chunks_used=[c.id for c in chunks],
            tokens_used=tokens_used
        )
        db.add(user_msg)
        db.add(assistant_msg)
        
        # 9. Background Escalation Check
        from app.worker.tasks import trigger_escalation_check_task
        trigger_escalation_check_task.delay(str(session_id), user_message)

        # 10. Log Event
        event = Event(
            event_type="ai.message_sent",
            actor_id=session.learner_id,
            entity_type="lesson_session",
            entity_id=session_id,
            payload={"tokens": tokens_used, "rag_chunks": len(chunks)}
        )
        db.add(event)
        await db.commit()

        return {
            "reply": reply_text,
            "escalated": False,
            "escalation_id": None,
            "rag_sources": len(chunks)
        }

    async def escalation_trigger_service(self, db: AsyncSession, session_id: uuid.UUID, latest_message: str, all_messages: list):
        query = select(LessonSession).where(LessonSession.id == session_id).options(selectinload(LessonSession.lesson))
        result = await db.execute(query)
        session = result.scalar_one()
        
        if session.status == SessionStatus.ESCALATED:
            return

            # TRIGGER 1: Repeat question
            user_messages = [m for m in all_messages if m.role == "user"]
            if len(user_messages) >= 3:
                latest_embedding = await openai_client.get_embedding(latest_message)
                similar_count = 0
                for prev_msg in user_messages[:-1]: # Check previous ones
                    prev_embedding = await openai_client.get_embedding(prev_msg.content)
                    if cosine_similarity(latest_embedding, prev_embedding) > 0.92:
                        similar_count += 1
                if similar_count >= 2: # Total 3 similar messages
                    await self.fire_escalation(db, session, reason="repeat_question")
                    return

            # TRIGGER 2: Frustrated language
            FRUSTRATION_KEYWORDS = [
                'i dont understand', "i don't understand", "don't get it",
                'this makes no sense', 'confused', 'lost', 'i give up',
                'this is confusing', 'not making sense', 'still confused'
            ]
            if any(kw in latest_message.lower() for kw in FRUSTRATION_KEYWORDS):
                await self.fire_escalation(db, session, reason="frustrated_language")
                return

            # TRIGGER 3: AI offered escalation
            last_ai_reply = next((m.content for m in reversed(all_messages) if m.role == "assistant"), "")
            if "escalate to a human tutor" in last_ai_reply.lower():
                await self.fire_escalation(db, session, reason="ai_offered_escalation")
                return

    async def fire_escalation(self, db: AsyncSession, session: LessonSession, reason: str):
        session.status = SessionStatus.ESCALATED
        
        # Find tutor
        from app.models.users import UserRole, UserRoleEnum
        from app.models.content import ContentTag # If it exists
        
        # Simple assignment for now: find any tutor_responder
        tutor_query = select(UserRole.user_id).where(UserRole.role == UserRoleEnum.TUTOR_RESPONDER).limit(1)
        tutor_id = (await db.execute(tutor_query)).scalar()
        
        escalation = Escalation(
            session_id=session.id,
            learner_id=session.learner_id,
            lesson_id=session.lesson_id,
            trigger_reason=reason,
            status="assigned" if tutor_id else "open",
            assigned_tutor_id=tutor_id
        )
        db.add(escalation)
        
        # Log event
        event = Event(
            event_type="escalation.created",
            actor_id=session.learner_id,
            entity_type="escalation",
            entity_id=session.id, # Using session_id as anchor
            payload={"reason": reason, "tutor_id": str(tutor_id) if tutor_id else None}
        )
        db.add(event)
        
        # TODO: Notifications (WhatsApp/Brevo)
        
        await db.commit()

    async def get_messages(self, db: AsyncSession, session_id: uuid.UUID):
        query = select(SessionMessage).where(SessionMessage.session_id == session_id).order_by(SessionMessage.created_at.asc())
        result = await db.execute(query)
        return result.scalars().all()

    async def get_summary(self, db: AsyncSession, session_id: uuid.UUID):
        query = select(LessonSession).where(LessonSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one()
        
        if session.summary:
            return session.summary
            
        # Generate summary on demand
        history = await self.get_messages(db, session_id)
        history_text = "\n".join([f"{m.role}: {m.content}" for m in history])
        
        prompt = f"""Given this tutoring conversation, return a JSON object with ONLY these keys:
topics_covered (list of strings), understood_well (list of strings),
needs_revisit (list of strings), tutor_notes (str).
Respond with raw JSON only, no markdown fences.

Conversation:
{history_text}
"""
        try:
            summary_text = await anthropic_client.get_completion(prompt, [])
            summary_json = json.loads(summary_text)
            session.summary = summary_json
            await db.commit()
            return summary_json
        except Exception as e:
            logger.error("summary_generation_error", error=str(e))
            return {
                "topics_covered": [],
                "understood_well": [],
                "needs_revisit": [],
                "tutor_notes": "Summary failed to generate."
            }

    async def get_knowledge_checks(self, db: AsyncSession, lesson_id: uuid.UUID):
        query = select(KnowledgeCheck).where(KnowledgeCheck.lesson_id == lesson_id).order_by(KnowledgeCheck.section_index.asc())
        result = await db.execute(query)
        return result.scalars().all()

    async def submit_knowledge_check(self, db: AsyncSession, session_id: uuid.UUID, check_id: uuid.UUID, answer: str):
        check_query = select(KnowledgeCheck).where(KnowledgeCheck.id == check_id)
        check = (await db.execute(check_query)).scalar_one()
        
        is_correct = answer.strip().lower() == check.correct_answer.strip().lower()
        
        # Find existing response
        resp_query = select(KnowledgeCheckResponse).where(
            and_(
                KnowledgeCheckResponse.session_id == session_id,
                KnowledgeCheckResponse.knowledge_check_id == check_id
            )
        )
        response = (await db.execute(resp_query)).scalar_one_or_none()
        
        if response:
            response.learner_answer = answer
            response.is_correct = is_correct
            response.attempts += 1
        else:
            response = KnowledgeCheckResponse(
                session_id=session_id,
                knowledge_check_id=check_id,
                learner_answer=answer,
                is_correct=is_correct,
                attempts=1
            )
            db.add(response)
            
        explanation = None
        re_ask = not is_correct and response.attempts < 3
        
        if not is_correct:
            # Generate alternate explanation
            # Load RAG chunk if available
            rag_chunk_text = ""
            if check.rag_chunk_id:
                chunk = (await db.execute(select(RagChunk).where(RagChunk.id == check.rag_chunk_id))).scalar_one_or_none()
                if chunk:
                    rag_chunk_text = chunk.chunk_text
            
            prompt = f"""The learner answered '{answer}'. The correct answer is '{check.correct_answer}'.
Explain why in a different way using ONLY this context: {rag_chunk_text}.
Be concise (3-4 sentences max)."""
            
            explanation = await anthropic_client.get_completion(prompt, [])
            
        if response.attempts >= 3 and not is_correct:
            response.extra_metadata = {**response.extra_metadata, "escalation_candidate": True}
            
        await db.commit()
        return {
            "is_correct": is_correct,
            "explanation": explanation,
            "attempts": response.attempts,
            "re_ask": re_ask
        }

ai_tutor_service = AiTutorService()
        
