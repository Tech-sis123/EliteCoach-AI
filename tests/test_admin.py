import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_platform_analytics(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/admin/analytics/platform", headers=headers)
    assert response.status_code == 200
    assert "active_learners_60d" in response.json()

@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_admin_config(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get Config
    config_res = await client.get("/api/v1/admin/config", headers=headers)
    assert config_res.status_code == 200
    
    # Audit Logs
    audit_res = await client.get("/api/v1/admin/audit/events", headers=headers)
    assert audit_res.status_code == 200

@pytest.mark.asyncio
async def test_admin_advanced_ops(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Onboard Tutor
    onboard_res = await client.post("/api/v1/admin/tutors/onboard", json={"email": "newtutor@example.com"}, headers=headers)
    assert onboard_res.status_code in [200, 400]

    # 2. Content Review Queue
    queue_res = await client.get("/api/v1/admin/content/review-queue", headers=headers)
    assert queue_res.status_code == 200

    # 3. Approve/Reject Content (Mock ID)
    c_id = str(uuid.uuid4())
    app_res = await client.post(f"/api/v1/admin/content/{c_id}/approve", headers=headers)
    assert app_res.status_code in [200, 404]

    # 4. Feature Flags
    ff_res = await client.post("/api/v1/admin/feature-flags/ai_tutor_enabled?enabled=true", headers=headers)
    assert ff_res.status_code == 200

    # 5. Reconcile Payments
    rec_res = await client.get("/api/v1/admin/payments/reconcile", headers=headers)
    assert rec_res.status_code == 200

    # 6. NDPR Export/Delete (Mock user_id)
    u_id = str(uuid.uuid4())
    exp_res = await client.get(f"/api/v1/admin/ndpr/export/{u_id}", headers=headers)
    assert exp_res.status_code in [200, 404]
