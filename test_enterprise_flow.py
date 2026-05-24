import httpx
import json
import io
import pandas as pd

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_enterprise_and_courses():
    print("\n--- Testing Enterprise & Course Admin ---")
    
    # 1. Login
    login_data = {"username": "testuser@example.com", "password": "password123"}
    resp = httpx.post(f"{BASE_URL}/auth/login", data=login_data, timeout=30.0)
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Get Courses (Learner view)
    resp = httpx.get(f"{BASE_URL}/courses/", headers=headers, timeout=30.0)
    print(f"Courses List Status: {resp.status_code}")
    courses = resp.json()
    if courses:
        print(f"Found {len(courses)} courses.")
    
    # 3. Test Enterprise Dashboard
    resp = httpx.get(f"{BASE_URL}/enterprise/dashboard", headers=headers, timeout=30.0)
    print(f"Enterprise Dashboard Status: {resp.status_code}")
    print(f"Dashboard Data: {json.dumps(resp.json(), indent=2)}")

    # 4. Test Enterprise User Import (CSV)
    df = pd.DataFrame([
        {"email": "invited1@corp.com", "full_name": "Invite One"},
        {"email": "invited2@corp.com", "full_name": "Invite Two"}
    ])
    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    
    files = {"file": ("users.csv", csv_buf, "text/csv")}
    resp = httpx.post(f"{BASE_URL}/enterprise/users/import", headers=headers, files=files, timeout=30.0)
    print(f"Enterprise Import Status: {resp.status_code}")
    print(f"Import Result: {json.dumps(resp.json(), indent=2)}")

    if resp.status_code == 200:
        print("SUCCESS: Enterprise and Course flows validated.")
    else:
        print("FAILED: Enterprise flow validation failed.")

if __name__ == "__main__":
    test_enterprise_and_courses()
