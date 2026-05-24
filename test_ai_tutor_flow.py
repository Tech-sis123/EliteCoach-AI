import asyncio
import uuid
import json
import logging
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import AsyncSessionLocal, engine
from sqlalchemy import select, delete
from app.models.users import User, UserRole
from app.models.content import Course, Lesson

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_ai_test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register/Login
        email = f"ai_tester_{uuid.uuid4().hex[:4]}@example.com"
        logger.info(f"Registering {email}...")
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "password123",
            "full_name": "AI Tester"
        })
        
        login_res = await client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get a lesson to test with
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Lesson).limit(1))
            lesson = result.scalar_one_or_none()
            if not lesson:
                logger.error("No lessons found in DB. Run seed_data.py first.")
                return

        logger.info(f"Starting AI session for lesson: {lesson.title}")
        
        # 3. Start AI Session
        start_res = await client.post(
            "/api/v1/ai/session/start", 
            json={"lesson_id": str(lesson.id)},
            headers=headers
        )
        if start_res.status_code != 200:
            logger.error(f"Failed to start session: {start_res.text}")
            return
            
        session_data = start_res.json()
        session_id = session_data.get("id")
        
        logger.info(f"Session started: {session_id}")

        # 4. Send Message
        logger.info("Sending message to AI Tutor...")
        msg_res = await client.post(
            f"/api/v1/ai/session/{session_id}/message",
            json={"message": "What is coaching?"},
            headers=headers
        )
        
        if msg_res.status_code == 200:
            logger.info(f"AI Response: {msg_res.json()['reply']}")
            logger.info(f"Escalated: {msg_res.json()['escalated']}")
        else:
            logger.error(f"Failed to send message: {msg_res.text}")

if __name__ == "__main__":
    from unittest import mock
    # Mock anthropic to avoid API calls
    with mock.patch("app.integrations.anthropic_client.anthropic_client.get_completion", return_value="Coaching is a partnership."):
         # Mock analytics to avoid background task complexity
         with mock.patch("app.services.analytics.analytics_service.track", return_value=None):
            asyncio.run(run_ai_test())
