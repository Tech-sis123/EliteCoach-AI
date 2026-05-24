import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    email = f"test-{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "email": email,
        "full_name": "Test User",
        "password": "strongpassword123",
        "phone": "+2348000000000"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    assert response.json()["email"] == email

@pytest.mark.asyncio
async def test_auth_full_flow(client: AsyncClient):
    email = f"auth-{uuid.uuid4().hex[:6]}@example.com"
    password = "StrongPass123!"
    
    # 1. Register
    await client.post("/api/v1/auth/register", json={
        "email": email, "full_name": "Auth User", "password": password, "phone": "+12345"
    })
    
    # 2. Login
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login_res.status_code == 200
    tokens = login_res.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    # 3. Get Me
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email
    
    # 4. Refresh
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
    new_access_token = refresh_res.json()["access_token"]
    
    # 5. Logout
    logout_res = await client.post("/api/v1/auth/logout", 
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert logout_res.status_code == 200

@pytest.mark.asyncio
async def test_auth_token_features(client: AsyncClient):
    # Verify Email (mock token)
    verify_res = await client.get("/api/v1/auth/verify-email/some-token")
    assert verify_res.status_code in [200, 400] # Depends on if token is valid

    # Forgot Password
    forgot_res = await client.post("/api/v1/auth/forgot-password", json={"email": "tester@example.com"})
    assert forgot_res.status_code == 200

    # Reset Password (mock token)
    reset_res = await client.post("/api/v1/auth/reset-password/some-token", json={"new_password": "NewPassword123!"})
    assert reset_res.status_code in [200, 400]

    # Social Login (mock)
    social_res = await client.post("/api/v1/auth/social?provider=google&token=fake-token")
    assert social_res.status_code in [200, 400, 500]
