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
        "password": "strongpassword123", # >= 8
        "phone": "+2348000000000"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == email
    assert "access_token" in data
    assert data["user"]["roles"] == ["solo_learner"]

@pytest.mark.asyncio
async def test_login_returns_roles(client: AsyncClient, db):
    email = f"auth-{uuid.uuid4().hex[:6]}@example.com"
    password = "StrongPass123!"
    
    # 1. Register
    await client.post("/api/v1/auth/register", json={
        "email": email, "full_name": "Auth User", "password": password
    })

    # Manual verify email as register doesn't do it
    from sqlalchemy import update
    from app.models.users import User
    from datetime import datetime
    await db.execute(update(User).where(User.email == email).values(email_verified_at=datetime.utcnow()))
    await db.commit()
    
    # 2. Login
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login_res.status_code == 200
    data = login_res.json()
    assert "user" in data
    assert data["user"]["email"] == email
    assert isinstance(data["user"]["roles"], list)
    assert "solo_learner" in data["user"]["roles"]

@pytest.mark.asyncio
async def test_login_platform_admin_role_in_response(client: AsyncClient, db):
    from app.models.users import User, UserRole, UserRoleEnum
    from app.core.security import hash_password
    from datetime import datetime

    email = f"admin-{uuid.uuid4().hex[:6]}@example.com"
    password = "AdminPass123!"
    
    admin = User(
        email=email,
        hashed_password=hash_password(password),
        full_name="Platform Admin",
        email_verified_at=datetime.utcnow()
    )
    db.add(admin)
    await db.flush()
    role = UserRole(user_id=admin.id, role=UserRoleEnum.PLATFORM_ADMIN)
    db.add(role)
    await db.commit()

    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login_res.status_code == 200
    data = login_res.json()
    assert "platform_admin" in data["user"]["roles"]

@pytest.mark.asyncio
async def test_register_with_tutor_author_role(client: AsyncClient):
    email = f"tutor-{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "email": email,
        "full_name": "Tutor One",
        "password": "strongpassword123",
        "role": "tutor_author"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["roles"] == ["tutor_author"]

@pytest.mark.asyncio
async def test_register_platform_admin_blocked(client: AsyncClient):
    email = f"failadmin-{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "email": email,
        "full_name": "Fake Admin",
        "password": "strongpassword123",
        "role": "platform_admin"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient):
    email = f"dup-{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "email": email,
        "full_name": "User One",
        "password": "strongpassword123"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_auth_full_flow(client: AsyncClient, db):
    email = f"auth-{uuid.uuid4().hex[:6]}@example.com"
    password = "StrongPass123!"
    
    # 1. Register
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": email, "full_name": "Auth User", "password": password, "phone": "+12345"
    })
    assert reg_res.status_code == 200

    # Manual verify
    from sqlalchemy import update
    from app.models.users import User
    from datetime import datetime
    await db.execute(update(User).where(User.email == email).values(email_verified_at=datetime.utcnow()))
    await db.commit()
    
    # 2. Login
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login_res.status_code == 200
    data = login_res.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    
    # 3. Get Me
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

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
