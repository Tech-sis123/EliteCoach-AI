import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_inbox_escalations(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/inbox/escalations", headers=headers)
    assert response.status_code == 200

    # 2. Get Detail
    esc_id = uuid.uuid4()
    detail_res = await client.get(f"/api/v1/inbox/escalations/{esc_id}", headers=headers)
    assert detail_res.status_code in [200, 404]

    # 3. Respond
    resp_res = await client.post(f"/api/v1/inbox/escalations/{esc_id}/respond", json={"message": "Help is on the way"}, headers=headers)
    assert resp_res.status_code in [200, 404]

    # 4. Push to RAG
    rag_res = await client.post(f"/api/v1/inbox/escalations/{esc_id}/push-to-rag", headers=headers)
    assert rag_res.status_code in [200, 404, 501]

@pytest.mark.asyncio
async def test_inbox_conversations(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # List
    response = await client.get("/api/v1/inbox/conversations", headers=headers)
    assert response.status_code == 200
    
    # Create
    other_user_id = str(uuid.uuid4())
    create_res = await client.post("/api/v1/inbox/conversations", json={"participant_ids": [other_user_id]}, headers=headers)
    assert create_res.status_code in [200, 201, 404]

@pytest.mark.asyncio
async def test_tutor_earnings(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/inbox/earnings", headers=headers)
    assert response.status_code == 200
