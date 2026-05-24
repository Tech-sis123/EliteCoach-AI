import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_courses_listing(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. List Published Courses
    response = await client.get("/api/v1/courses/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # 2. List Course Lessons (Mock ID)
    course_id = uuid.uuid4()
    lessons_res = await client.get(f"/api/v1/courses/{course_id}/lessons", headers=headers)
    assert lessons_res.status_code in [200, 404]

@pytest.mark.asyncio
async def test_certificates_advanced(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. List My Certificates
    res = await client.get("/api/v1/certificates/me", headers=headers)
    assert res.status_code == 200

    # 2. Verify Certificate (Mock verification ID)
    v_id = uuid.uuid4()
    verify_res = await client.get(f"/api/v1/certificates/{v_id}", headers=headers)
    assert verify_res.status_code in [200, 404]

    # 3. Download Certificate (Mock ID)
    c_id = uuid.uuid4()
    download_res = await client.post(f"/api/v1/certificates/{c_id}/download", headers=headers)
    assert download_res.status_code in [200, 404, 501]

    # 4. Share Linkedin
    share_res = await client.post(f"/api/v1/certificates/{c_id}/share/linkedin", headers=headers)
    assert share_res.status_code in [200, 404, 501]
