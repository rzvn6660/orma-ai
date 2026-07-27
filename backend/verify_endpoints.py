import requests
import sys
import uuid
import datetime
from jose import jwt
from database import SessionLocal
from models.user import User

BASE_URL = "http://localhost:8000"
SECRET_KEY = "your-secret-key-for-orma-ai"
ALGORITHM = "HS256"

def get_token():
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        # Create a mock user
        user = User(id=str(uuid.uuid4()), email="test@orma.ai", role="elderly")
        db.add(user)
        db.commit()
    db.close()
    
    # Generate token
    to_encode = {"sub": user.email, "role": user.role, "id": user.id}
    to_encode.update({"exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=300)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def test_endpoints():
    token = get_token()
    if not token:
        print("Token generation failed")
        return
        
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
        if res.status_code == 500:
            print(f"FAILED: {ep} returned 500")
            print(res.text)
            sys.exit(1)
        else:
            print(f"OK: {ep} returned {res.status_code}")

if __name__ == "__main__":
    test_endpoints()

