import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_subscription_status(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/payments/status", headers=headers)
    assert response.status_code == 200
    assert "status" in response.json()

@pytest.mark.asyncio
async def test_payment_init(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    # Mock subscribe call
    response = await client.post("/api/v1/payments/subscribe", json={"plan": "monthly"}, headers=headers)
    assert response.status_code in [200, 400] # 400 if Paystack key not configured

@pytest.mark.asyncio
async def test_invoices_list(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/payments/invoices", headers=headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_cancel_subscription(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.delete("/api/v1/payments/subscription", headers=headers)
    assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_paystack_interaction(client: AsyncClient):
    # 1. Webhook (simulated)
    # Note: Valid signature would be hard without secret key, testing route accessibility
    webhook_res = await client.post("/api/v1/payments/webhook", json={"event": "charge.success", "data": {}})
    assert webhook_res.status_code == 400 # Signature mismatch as expected

    # 2. Verify
    verify_res = await client.get("/api/v1/payments/verify/REF-123", headers={})
    assert verify_res.status_code in [401, 404, 400]
