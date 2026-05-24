import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_notifications_list(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/notifications/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_mark_individual_read(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    import uuid
    notif_id = uuid.uuid4()
    response = await client.post(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert response.status_code in [200, 404]
