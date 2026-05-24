import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_diagnostic_and_onboarding(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start Onboarding (Get Diagnostic Questions)
    start_payload = {
        "current_role": "Junior Coach",
        "years_experience": 2,
        "career_goal": "Senior Executive Coach",
        "hours_per_week": 10
    }
    diag_res = await client.post("/api/v1/onboarding/start", json=start_payload, headers=headers)
    assert diag_res.status_code == 200
    questions = diag_res.json()
    assert isinstance(questions, list)

    # 2. Submit Diagnostic Answers
    # We need to answer the questions we got
    answers = {}
    for q in questions:
        q_id = q.get("id")
        if q_id:
            answers[q_id] = "Sample Answer"
    
    submit_res = await client.post("/api/v1/onboarding/submit", json={"answers": answers}, headers=headers)
    assert submit_res.status_code == 200
    assert "id" in submit_res.json()
    assert "items" in submit_res.json()

    # 3. Get Initial Path
    path_res = await client.get("/api/v1/onboarding/path", headers=headers)
    assert path_res.status_code == 200
    assert "items" in path_res.json()

    # 4. Regenerate Path
    regen_res = await client.post("/api/v1/onboarding/path/regenerate", headers=headers)
    assert regen_res.status_code == 200
    assert "id" in regen_res.json()

