import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_org_onboarding_and_invite(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Organization
    org_data = {
        "name": "Acme Corp",
        "slug": f"acme-{uuid.uuid4().hex[:4]}",
        "plan": "enterprise_gold",
        "budget_ngn": 1000000.0
    }
    response = await client.post("/api/v1/enterprise/organizations", json=org_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Acme Corp"

    # 2. Get Dashboard
    dash_res = await client.get("/api/v1/enterprise/dashboard", headers=headers)
    assert dash_res.status_code == 200
    assert "learners" in dash_res.json()

    # 3. Update Branding
    brand_data = {
        "primary_color": "#FF0000",
        "logo_url": "https://example.com/logo.png"
    }
    brand_res = await client.patch("/api/v1/enterprise/branding", json=brand_data, headers=headers)
    assert brand_res.status_code == 200
    assert brand_res.json()["primary_color"] == "#FF0000"

    # 4. Invite Employee (requires another user to exist)
    # First register another user
    other_email = f"emp-{uuid.uuid4().hex[:4]}@acme.com"
    await client.post("/api/v1/auth/register", json={
        "email": other_email,
        "password": "password123",
        "full_name": "Employee One",
        "phone": "+2347000000001"
    })
    
    invite_res = await client.post("/api/v1/enterprise/invite", json={"email": other_email}, headers=headers)
    assert invite_res.status_code == 200

    # 5. Get Branding by Slug
    slug = org_data["slug"]
    slug_res = await client.get(f"/api/v1/enterprise/branding/{slug}", headers=headers)
    assert slug_res.status_code == 200

    # 6. Get Budget
    budget_res = await client.get("/api/v1/enterprise/budget", headers=headers)
    assert budget_res.status_code == 200

@pytest.mark.asyncio
async def test_enterprise_assignments(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. List Assignments
    res = await client.get("/api/v1/enterprise/assignments", headers=headers)
    assert res.status_code == 200

    # 2. Create Assignment (Mock IDs)
    course_id = uuid.uuid4()
    user_id = uuid.uuid4()
    assign_res = await client.post("/api/v1/enterprise/assignments", json={
        "course_id": str(course_id),
        "user_id": str(user_id)
    }, headers=headers)
    assert assign_res.status_code in [200, 404, 422]

@pytest.mark.asyncio
async def test_enterprise_teams(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # List teams
    teams_res = await client.get("/api/v1/enterprise/teams", headers=headers)
    assert teams_res.status_code == 200
    
    # Create team
    new_team = await client.post("/api/v1/enterprise/teams", json={"name": "Engineering", "description": "Tech team"}, headers=headers)
    assert new_team.status_code == 200

@pytest.mark.asyncio
async def test_enterprise_users(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # List users
    users_res = await client.get("/api/v1/enterprise/users", headers=headers)
    assert users_res.status_code == 200
    
    # Export reports
    export_res = await client.get("/api/v1/enterprise/reports/export", headers=headers)
    assert export_res.status_code == 200
