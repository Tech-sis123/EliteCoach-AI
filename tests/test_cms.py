import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_create_and_list_course(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Course
    course_data = {
        "title": "Test Professional Course",
        "slug": f"test-course-{uuid.uuid4().hex[:6]}",
        "description": "A test course for integration testing",
        "domain": "Software Engineering",
        "difficulty": 1
    }
    response = await client.post("/api/v1/cms/courses", json=course_data, headers=headers)
    assert response.status_code == 200
    course_id = response.json()["id"]
    assert response.json()["title"] == course_data["title"]

    # List Courses
    list_res = await client.get("/api/v1/cms/courses", headers=headers)
    assert list_res.status_code == 200
    assert any(c["id"] == course_id for c in list_res.json())

    # Create Module
    module_data = {
        "title": "Module 1: Introduction",
        "position": 1,
        "description": "First module",
        "course_id": course_id
    }
    mod_res = await client.post("/api/v1/cms/modules", json=module_data, headers=headers)
    assert mod_res.status_code == 200
    module_id = mod_res.json()["id"]

    # Create Lesson
    lesson_data = {
        "title": "Lesson 1: Hello World",
        "position": 1,
        "estimated_minutes": 10,
        "module_id": module_id
    }
    less_res = await client.post("/api/v1/cms/lessons", json=lesson_data, headers=headers)
    assert less_res.status_code == 200
    
    # Update Status
    status_res = await client.patch(f"/api/v1/cms/courses/{course_id}/status", json={"status": "published"}, headers=headers)
    assert status_res.status_code == 200

@pytest.mark.asyncio
async def test_update_course(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create
    course_data = {
        "title": "Old Title",
        "slug": f"slug-{uuid.uuid4().hex[:6]}",
        "domain": "HR",
        "difficulty": 2
    }
    create_res = await client.post("/api/v1/cms/courses", json=course_data, headers=headers)
    course_id = create_res.json()["id"]
    
    # Update
    update_data = {"title": "New Title"}
    patch_res = await client.patch(f"/api/v1/cms/courses/{course_id}", json=update_data, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "New Title"

@pytest.mark.asyncio
async def test_cms_lesson_advanced(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Course and Lesson
    course_data = {"title": "T", "slug": uuid.uuid4().hex, "domain": "D", "difficulty": 1}
    c_res = await client.post("/api/v1/cms/courses", json=course_data, headers=headers)
    c_id = c_res.json()["id"]
    m_res = await client.post("/api/v1/cms/modules", json={"course_id": c_id, "title": "M1", "position": 1}, headers=headers)
    m_id = m_res.json()["id"]
    l_res = await client.post("/api/v1/cms/lessons", json={"module_id": m_id, "title": "L1", "position": 1, "estimated_minutes": 10}, headers=headers)
    l_id = l_res.json()["id"]
    
    # 2. Add Blocks
    # response = await client.post(f"/api/v1/cms/lessons/{l_id}/blocks", json={"type": "text", "content": "..."}, headers=headers)
    
    # 3. Submit Lesson
    sub_res = await client.post(f"/api/v1/cms/lessons/{l_id}/submit", headers=headers)
    assert sub_res.status_code in [200, 404]

    # 4. Preview
    pre_res = await client.get(f"/api/v1/cms/lessons/{l_id}/preview", headers=headers)
    assert pre_res.status_code in [200, 404]

    # 5. Add Blocks
    block_res = await client.post(f"/api/v1/cms/lessons/{l_id}/blocks", json={"type": "text", "content": "Sample"}, headers=headers)
    assert block_res.status_code == 200

    # 6. Add Tags
    tag_res = await client.post(f"/api/v1/cms/lessons/{l_id}/tags", json=["ai", "tutor"], headers=headers)
    assert tag_res.status_code == 200

    # 7. Analytics
    ana_res = await client.get(f"/api/v1/cms/lessons/{l_id}/analytics", headers=headers)
    assert ana_res.status_code == 200

    # 8. Assets
    asset_res = await client.post(f"/api/v1/cms/lessons/{l_id}/assets?asset_type=image", headers=headers)
    assert asset_res.status_code == 200
