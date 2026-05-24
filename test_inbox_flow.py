import asyncio
import httpx
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_inbox_flow():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login (as anyone for now, logic isn't strictly tutor-protected yet in router)
        login_data = {"username": "testuser@example.com", "password": "testpassword123"}
        login_res = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. List escalations
        resp = await client.get(f"{BASE_URL}/inbox/", headers=headers)
        escalations = resp.json()
        print(f"Found {len(escalations)} open escalations.")
        
        if not escalations:
            print("No escalations found. Run test_escalation_flow.py first.")
            return
            
        esc = escalations[0]
        esc_id = esc["id"]
        print(f"Responding to escalation: {esc_id}")

        # 3. Respond
        # Note: the endpoint expects 'content' but maybe it should be in JSON body?
        # Let's check the endpoint definition: @router.post("/{escalation_id}/respond") async def respond_to_escalation(escalation_id: uuid.UUID, content: str, ...)
        # FastAPI will expect 'content' as a query param or part of JSON if it's a model.
        # Since it's a simple 'content: str', it's likely a query param or expected in body.
        # Actually, if it's not a Pydantic model, FastAPI often defaults to query param for POST if not specified.
        
        # Let's try query param first.
        respond_res = await client.post(f"{BASE_URL}/inbox/{esc_id}/respond?content=We are here to help!", headers=headers)
        print(f"Respond result: {respond_res.status_code} - {respond_res.text}")
        
        if respond_res.status_code == 200:
            print("SUCCESS: Escalation responded to.")

if __name__ == "__main__":
    asyncio.run(test_inbox_flow())
