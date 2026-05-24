import asyncio
import httpx
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_escalation_flow():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login
        login_data = {"username": "testuser@example.com", "password": "testpassword123"}
        login_res = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Logged in.")

        # 2. Get Course and Lesson
        courses_res = await client.get(f"{BASE_URL}/courses/", headers=headers)
        course = courses_res.json()[0]
        lessons_res = await client.get(f"{BASE_URL}/courses/{course['id']}/lessons", headers=headers)
        lesson = lessons_res.json()[0]
        print(f"Testing escalation for lesson: {lesson['title']}")

        # 3. Start Session
        start_res = await client.post(f"{BASE_URL}/ai/session/start", json={"lesson_id": lesson["id"]}, headers=headers)
        session_id = start_res.json()["id"]
        print(f"Session started: {session_id}")

        # 4. Send frustrated message
        msg = "I'm so confused, this makes no sense!"
        print(f"Sending message: {msg}")
        resp = await client.post(f"{BASE_URL}/ai/session/{session_id}/message", json={"message": msg}, headers=headers)
        
        result = resp.json()
        print(f"AI Reply: {result['reply']}")
        print(f"Escalated: {result['escalated']}")
        
        if result['escalated']:
            print("SUCCESS: Session correctly escalated!")
        else:
            print("FAILURE: Session did not escalate.")

if __name__ == "__main__":
    asyncio.run(test_escalation_flow())

if __name__ == "__main__":
    # This is a bit complex to do without the route. 
    # Let me add a route GET /courses/{id}/lessons first.
    pass
