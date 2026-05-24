import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_admin_analytics():
    print("\n--- Testing Admin Analytics ---")
    
    # 1. Login
    login_data = {"username": "testuser@example.com", "password": "password123"}
    resp = httpx.post(f"{BASE_URL}/auth/login", data=login_data, timeout=30.0)
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Platform Analytics
    resp = httpx.get(f"{BASE_URL}/admin/analytics/platform", headers=headers, timeout=30.0)
    print(f"Analytics Status: {resp.status_code}")
    print(f"Analytics Data: {json.dumps(resp.json(), indent=2)}")

    if resp.status_code == 200:
        print("SUCCESS: Platform analytics fetched correctly.")
    else:
        print("FAILED: Platform analytics fetch failed.")

if __name__ == "__main__":
    test_admin_analytics()
