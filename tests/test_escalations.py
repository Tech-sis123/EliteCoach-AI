import pytest
from httpx import AsyncClient
import uuid
from app.models.ai_tutor import SessionStatus, Escalation
from app.models.users import UserRoleEnum
from sqlalchemy import select, func
from datetime import datetime

@pytest.mark.asyncio
async def test_get_active_sessions_empty(client: AsyncClient, token: str):
    response = await client.get(
        "/api/v1/learning/sessions/active",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"active_sessions": []}

@pytest.mark.asyncio
async def test_get_active_sessions_returns_correct_data(client: AsyncClient, token: str, db):
    # Setup: Create course, module, lesson, and session
    from app.models.content import Course, Module, Lesson
    from app.models.ai_tutor import LessonSession
    from app.models.users import User
    
    # Get user id from token (or just use the one we created in conftest if we knew it)
    # For tests, we'll just create a session for the user who registered
    user_res = (await db.execute(select(User).limit(1))).scalar()
    
    course = Course(title="Test Course", slug=f"test-{uuid.uuid4().hex}", domain="Finance", difficulty=1, author_id=user_res.id)
    db.add(course)
    await db.flush()
    
    module = Module(course_id=course.id, title="Test Module", position=1)
    db.add(module)
    await db.flush()
    
    lesson = Lesson(module_id=module.id, title="Test Lesson", position=1, estimated_minutes=10)
    db.add(lesson)
    await db.flush()
    
    session = LessonSession(learner_id=user_res.id, lesson_id=lesson.id, status=SessionStatus.ACTIVE)
    db.add(session)
    await db.commit()

    response = await client.get(
        "/api/v1/learning/sessions/active",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["active_sessions"]) == 1
    assert data["active_sessions"][0]["lesson_title"] == "Test Lesson"
    assert data["active_sessions"][0]["course_title"] == "Test Course"

@pytest.mark.asyncio
async def test_lesson_start_is_idempotent(client: AsyncClient, token: str, db):
    # Setup: Create course, module, lesson
    from app.models.content import Course, Module, Lesson
    from app.models.users import User
    from app.models.ai_tutor import LessonSession

    user_res = (await db.execute(select(User).limit(1))).scalar()
    course = Course(title="Test Course", slug=f"test-idemp-{uuid.uuid4().hex}", domain="Finance", difficulty=1, author_id=user_res.id)
    db.add(course)
    await db.flush()
    module = Module(course_id=course.id, title="Test Module", position=1)
    db.add(module)
    await db.flush()
    lesson = Lesson(module_id=module.id, title="Test Lesson", position=1)
    db.add(lesson)
    await db.commit()

    # Call start twice
    res1 = await client.post(f"/api/v1/learning/lesson/{lesson.id}/start", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200
    id1 = res1.json()["session_id"]

    res2 = await client.post(f"/api/v1/learning/lesson/{lesson.id}/start", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    id2 = res2.json()["session_id"]

    assert id1 == id2

    # Verify only one row
    count = (await db.execute(select(func.count(LessonSession.id)).where(LessonSession.lesson_id == lesson.id))).scalar()
    assert count == 1

@pytest.mark.asyncio
async def test_manual_escalate_success(client: AsyncClient, token: str, db):
    from app.models.content import Course, Module, Lesson
    from app.models.ai_tutor import LessonSession, Escalation
    from app.models.users import User

    user_res = (await db.execute(select(User).limit(1))).scalar()
    course = Course(title="Test Course", slug=f"test-esc-{uuid.uuid4().hex}", domain="Finance", difficulty=1, author_id=user_res.id)
    db.add(course)
    await db.flush()
    module = Module(course_id=course.id, title="Test Module", position=1)
    db.add(module)
    await db.flush()
    lesson = Lesson(module_id=module.id, title="Test Lesson", position=1)
    db.add(lesson)
    await db.flush()
    session = LessonSession(learner_id=user_res.id, lesson_id=lesson.id, status=SessionStatus.ACTIVE)
    db.add(session)
    await db.commit()

    # Create a tutor to match the domain
    from app.models.users import UserRole, UserRoleEnum
    tutor = User(email=f"tutor-{uuid.uuid4().hex}@example.com", hashed_password="pw", full_name="Tutor One", subject_area="Finance")
    db.add(tutor)
    await db.flush()
    tutor_role = UserRole(user_id=tutor.id, role=UserRoleEnum.TUTOR_RESPONDER)
    db.add(tutor_role)
    await db.commit()

    response = await client.post(
        f"/api/v1/ai/session/{session.id}/escalate",
        json={"reason": "Need help"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["open", "assigned"]
    assert "escalation_id" in data

    # Verify session status
    await db.refresh(session)
    assert session.status == SessionStatus.ESCALATED

@pytest.mark.asyncio
async def test_manual_escalate_duplicate_returns_409(client: AsyncClient, token: str, db):
    from app.models.content import Course, Module, Lesson
    from app.models.ai_tutor import LessonSession
    from app.models.users import User

    user_res = (await db.execute(select(User).limit(1))).scalar()
    course = Course(title="Test Course", slug=f"test-esc-409-{uuid.uuid4().hex}", domain="Finance", difficulty=1, author_id=user_res.id)
    db.add(course)
    await db.flush()
    module = Module(course_id=course.id, title="Test Module", position=1)
    db.add(module)
    await db.flush()
    lesson = Lesson(module_id=module.id, title="Test Lesson", position=1)
    db.add(lesson)
    await db.flush()
    session = LessonSession(learner_id=user_res.id, lesson_id=lesson.id, status=SessionStatus.ACTIVE)
    db.add(session)
    await db.commit()

    await client.post(f"/api/v1/ai/session/{session.id}/escalate", json={"reason": "Need help"}, headers={"Authorization": f"Bearer {token}"})
    
    # Second call
    response = await client.post(f"/api/v1/ai/session/{session.id}/escalate", json={"reason": "Need help"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_cancel_escalation_as_learner(client: AsyncClient, token: str, db):
    from app.models.content import Course, Module, Lesson
    from app.models.ai_tutor import LessonSession, Escalation
    from app.models.users import User

    user_res = (await db.execute(select(User).limit(1))).scalar()
    course = Course(title="Test Course", slug=f"test-cancel-{uuid.uuid4().hex}", domain="Finance", difficulty=1, author_id=user_res.id)
    db.add(course)
    await db.flush()
    module = Module(course_id=course.id, title="Test Module", position=1)
    db.add(module)
    await db.flush()
    lesson = Lesson(module_id=module.id, title="Test Lesson", position=1)
    db.add(lesson)
    await db.flush()
    session = LessonSession(learner_id=user_res.id, lesson_id=lesson.id, status=SessionStatus.ACTIVE)
    db.add(session)
    await db.commit()

    resp = await client.post(f"/api/v1/ai/session/{session.id}/escalate", json={"reason": "Need help"}, headers={"Authorization": f"Bearer {token}"})
    esc_id = resp.json()["escalation_id"]

    # Cancel
    cancel_resp = await client.patch(
        f"/api/v1/escalations/{esc_id}",
        json={"status": "cancelled"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # Verify session status reverted
    await db.refresh(session)
    assert session.status == SessionStatus.ACTIVE

@pytest.mark.asyncio
async def test_cancel_escalation_in_progress_returns_403(client: AsyncClient, token: str, db):
    from app.models.content import Course, Module, Lesson
    from app.models.ai_tutor import LessonSession, Escalation
    from app.models.users import User

    user_res = (await db.execute(select(User).limit(1))).scalar()
    course = Course(title="Test Course", slug=f"test-cancel-403-{uuid.uuid4().hex}", domain="Finance", difficulty=1, author_id=user_res.id)
    db.add(course)
    await db.flush()
    module = Module(course_id=course.id, title="Test Module", position=1)
    db.add(module)
    await db.flush()
    lesson = Lesson(module_id=module.id, title="Test Lesson", position=1)
    db.add(lesson)
    await db.flush()
    session = LessonSession(learner_id=user_res.id, lesson_id=lesson.id, status=SessionStatus.ESCALATED)
    db.add(session)
    await db.flush()
    
    escalation = Escalation(session_id=session.id, learner_id=user_res.id, lesson_id=lesson.id, trigger_reason="manual_request", status="in_progress")
    db.add(escalation)
    await db.commit()

    cancel_resp = await client.patch(
        f"/api/v1/escalations/{escalation.id}",
        json={"status": "cancelled"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cancel_resp.status_code == 403

@pytest.mark.asyncio
async def test_escalation_status_enhanced_response(client: AsyncClient, token: str, db):
    from app.models.content import Course, Module, Lesson
    from app.models.ai_tutor import LessonSession, Escalation
    from app.models.users import User

    user_res = (await db.execute(select(User).limit(1))).scalar()
    course = Course(title="Test Course", slug=f"test-enhanced-{uuid.uuid4().hex}", domain="Finance", difficulty=1, author_id=user_res.id)
    db.add(course)
    await db.flush()
    module = Module(course_id=course.id, title="Test Module", position=1)
    db.add(module)
    await db.flush()
    lesson = Lesson(module_id=module.id, title="Test Lesson", position=1)
    db.add(lesson)
    await db.flush()
    session = LessonSession(learner_id=user_res.id, lesson_id=lesson.id, status=SessionStatus.ESCALATED)
    db.add(session)
    await db.flush()
    
    escalation = Escalation(session_id=session.id, learner_id=user_res.id, lesson_id=lesson.id, trigger_reason="manual_request", status="open")
    db.add(escalation)
    await db.commit()

    response = await client.get(
        f"/api/v1/ai/session/{session.id}/escalation-status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["can_cancel"] is True
    assert data["trigger_reason"] == "manual_request"
    assert "assigned_tutor" in data

@pytest.mark.asyncio
async def test_escalation_status_can_cancel_false_when_resolved(client: AsyncClient, token: str, db):
    from app.models.content import Course, Module, Lesson
    from app.models.ai_tutor import LessonSession, Escalation
    from app.models.users import User

    user_res = (await db.execute(select(User).limit(1))).scalar()
    course = Course(title="Test Course", slug=f"test-resolved-{uuid.uuid4().hex}", domain="Finance", difficulty=1, author_id=user_res.id)
    db.add(course)
    await db.flush()
    module = Module(course_id=course.id, title="Test Module", position=1)
    db.add(module)
    await db.flush()
    lesson = Lesson(module_id=module.id, title="Test Lesson", position=1)
    db.add(lesson)
    await db.flush()
    session = LessonSession(learner_id=user_res.id, lesson_id=lesson.id, status=SessionStatus.COMPLETED)
    db.add(session)
    await db.flush()
    
    escalation = Escalation(session_id=session.id, learner_id=user_res.id, lesson_id=lesson.id, trigger_reason="manual_request", status="resolved")
    db.add(escalation)
    await db.commit()

    response = await client.get(
        f"/api/v1/ai/session/{session.id}/escalation-status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["can_cancel"] is False
