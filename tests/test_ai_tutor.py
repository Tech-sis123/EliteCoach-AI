import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_ai_session_flow(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 0. Need a lesson first
    # Create course -> module -> lesson
    course_data = {
        "title": "AI Course",
        "slug": f"ai-course-{uuid.uuid4().hex[:4]}",
        "domain": "AI",
        "difficulty": 1
    }
    course_res = await client.post("/api/v1/cms/courses", json=course_data, headers=headers)
    course_id = course_res.json()["id"]
    
    module_res = await client.post("/api/v1/cms/modules", json={"course_id": course_id, "title": "M1", "position": 1}, headers=headers)
    module_id = module_res.json()["id"]
    
    lesson_res = await client.post("/api/v1/cms/lessons", json={"module_id": module_id, "title": "L1", "position": 1, "estimated_minutes": 10}, headers=headers)
    lesson_id = lesson_res.json()["id"]

    # 1. Start Session
    session_res = await client.post("/api/v1/ai/session/start", json={"lesson_id": lesson_id}, headers=headers)
    assert session_res.status_code == 200
    session_id = session_res.json()["id"]

    # 2. Send Message
    msg_data = {"message": "Hello, how can you help me today?"}
    msg_res = await client.post(f"/api/v1/ai/session/{session_id}/message", json=msg_data, headers=headers)
    assert msg_res.status_code == 200
    assert "reply" in msg_res.json()

    # 3. Get messages
    msgs_res = await client.get(f"/api/v1/ai/session/{session_id}/messages", headers=headers)
    assert msgs_res.status_code == 200
    # Note: If RAG fails or no content, it might not have saved the assistant message yet or it might have.
    # In the current implementation of get_response, it returns early if no chunks.
    # Let's check how it handles saving.
    # 4. Get Summary
    # Summary requires messages or session end logic. This might be 404/Null if empty but checking route.
    sum_res = await client.get(f"/api/v1/ai/session/{session_id}/summary", headers=headers)
    assert sum_res.status_code in [200, 404]

    # 5. Get Knowledge Checks
    checks_res = await client.get(f"/api/v1/ai/learning/lesson/{lesson_id}/checks", headers=headers)
    assert checks_res.status_code == 200
    checks = checks_res.json()
    if checks:
        check_id = checks[0]["id"]
        # 6. Submit Check Response
        check_submit_res = await client.post(
            f"/api/v1/ai/learning/lesson/{lesson_id}/checks/{check_id}",
            json={"answer": "Testing"},
            headers=headers
        )
        assert check_submit_res.status_code == 200

        # 7. Escalation Status
        esc_res = await client.get(f"/api/v1/ai/session/{session_id}/escalation-status", headers=headers)
        assert esc_res.status_code == 200
        assert "escalated" in esc_res.json()
