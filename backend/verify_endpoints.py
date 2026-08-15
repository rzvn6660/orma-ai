import requests
import sys

BASE_URL = "http://localhost:8000"

def get_token():
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "test1@gmail.com", "password": "Password123!"})
    if res.status_code == 200:
        return res.json()["access_token"]
    print(f"Login failed with status {res.status_code}: {res.text}")
    return None

def test_endpoints():
    token = get_token()
    if not token:
        print("Token generation failed")
        sys.exit(1)
        
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/notifications/",
        "/api/insights/summary",
        "/api/medicines/",
        "/api/health-records/",
        "/api/health-planner/",
        "/api/caregiver/summary",
        "/api/caregiver/adherence",
        "/api/caregiver/behavior",
        "/api/wellness/summary",
        "/api/reports/download"
    ]
    
    for ep in endpoints:
        res = requests.get(f"{BASE_URL}{ep}", headers=headers)
        if res.status_code != 200:
            print(f"FAILED: {ep} returned {res.status_code}")
            print(res.text)
            sys.exit(1)
        else:
            print(f"SUCCESS 200 OK: {ep}")

if __name__ == "__main__":
    test_endpoints()

