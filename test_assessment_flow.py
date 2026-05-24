import asyncio
import httpx
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_assessment_flow():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login to get token
        login_data = {
            "username": "testuser@example.com",
            "password": "testpassword123"
        }
        login_res = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        if login_res.status_code != 200:
            # Maybe need to register first if DB was wiped
            reg_data = {
                "email": "testuser@example.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
            await client.post(f"{BASE_URL}/auth/register", json=reg_data)
            login_res = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Logged in successfully.")

        # 2. Get Courses to find our seeded course
        courses_res = await client.get(f"{BASE_URL}/courses/", headers=headers)
        courses = courses_res.json()
        if not courses:
            print("No courses found. Seeding might have failed or list endpoint is empty.")
            return
        
        course = courses[0]
        course_id = course["id"]
        print(f"Testing for course: {course['title']} ({course_id})")

        # 3. Get Assessment for the course
        # Note: We need a route to get assessments for a course. 
        # Looking at app/api/v1/assessments.py or similar.
        assessments_res = await client.get(f"{BASE_URL}/assessments/course/{course_id}", headers=headers)
        if assessments_res.status_code != 200:
            print(f"Failed to fetch assessments: {assessments_res.text}")
            return
        
        assessments = assessments_res.json()
        if not assessments:
            print("No assessments found for this course.")
            return
        
        assessment = assessments[0]
        assessment_id = assessment["id"]
        print(f"Starting assessment: {assessment['title']} ({assessment_id})")

        # 4. Start Attempt
        start_res = await client.post(f"{BASE_URL}/assessments/{assessment_id}/start", headers=headers)
        if start_res.status_code != 200:
            print(f"Failed to start assessment: {start_res.text}")
            return
        
        attempt = start_res.json()
        attempt_id = attempt["id"]
        questions = attempt["questions"]
        print(f"Assessment started. Attempt ID: {attempt_id}. Questions: {len(questions)}")

        # 5. Submit Attempt
        # We need to provide answers. Let's look at the questions and provide correct answers.
        # Based on seed_data.py:
        # Q1: "Is coaching the same as mentoring?" -> "B" (No)
        # Q2: "What is the G in GROW?" -> "A" (Goal)
        
        # We need the question IDs from the attempt response.
        answers = {}
        for q in questions:
            if "mentoring" in q["question_text"].lower():
                answers[q["id"]] = "B"
            elif "grow" in q["question_text"].lower():
                answers[q["id"]] = "A"
        
        submit_data = {
            "answers": answers
        }
        print(f"Submitting answers: {answers}")
        submit_res = await client.post(f"{BASE_URL}/assessments/attempts/{attempt_id}/submit", json=submit_data, headers=headers)
        
        if submit_res.status_code != 200:
            print(f"Failed to submit assessment: {submit_res.text}")
            return
        
        result = submit_res.json()
        print(f"Result: Score={result['score']}, Passed={result['passed']}")
        
        if result['passed']:
            print("PASSED! Checking for certificate...")
            # 6. Check for certificate
            cert_res = await client.get(f"{BASE_URL}/assessments/certificates/me", headers=headers)
            if cert_res.status_code == 200:
                certs = cert_res.json()
                print(f"Found {len(certs)} certificates.")
                for c in certs:
                    print(f"Certificate: {c['course_title']} - URL: {c['pdf_url']}")
            else:
                print(f"Failed to fetch certificates: {cert_res.text}")

if __name__ == "__main__":
    asyncio.run(test_assessment_flow())
