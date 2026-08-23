import pytest
import sys
import os
from unittest.mock import patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal
from models.user import User
from routes.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router, prefix="/api/auth")

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Clean up test users
    db.query(User).filter(User.email.in_(["google_test_existing@gmail.com", "google_test_new@gmail.com"])).delete(synchronize_session=False)
    db.commit()
    yield
    db.query(User).filter(User.email.in_(["google_test_existing@gmail.com", "google_test_new@gmail.com"])).delete(synchronize_session=False)
    db.commit()
    db.close()

def test_google_auth_missing_token():
    """Verify that empty/missing id_token requests are rejected with 400 Bad Request."""
    response = client.post("/api/auth/google", json={})
    assert response.status_code == 400
    assert "Simulated authentication is disabled" in response.json()["detail"] or "required" in response.json()["detail"]

def test_google_auth_invalid_token():
    """Verify that unverified/malformed ID tokens raise 400 Bad Request."""
    with patch("services.google_auth_service.verify_google_id_token", side_effect=ValueError("Invalid Google ID token signature.")):
        response = client.post("/api/auth/google", json={"id_token": "invalid_fake_token"})
        assert response.status_code == 400
        assert "Invalid Google ID token signature" in response.json()["detail"]

def test_google_auth_new_user_creation():
    """Verify that valid Google auth for a new user creates user with selected role and returns valid token."""
    mock_payload = {
        "email": "google_test_new@gmail.com",
        "sub": "google-sub-12345",
        "name": "New Google User",
        "email_verified": True
    }
    with patch("services.google_auth_service.verify_google_id_token", return_value=mock_payload):
        response = client.post("/api/auth/google", json={"id_token": "valid_token_123", "role": "caregiver"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "google_test_new@gmail.com"
        assert data["user"]["role"] == "caregiver"

def test_google_auth_existing_user_preserves_role():
    """Verify that logging in with Google for an existing user preserves the existing ORMA role."""
    # Pre-create an existing user with role='elderly'
    db = SessionLocal()
    existing_user = User(
        email="google_test_existing@gmail.com",
        hashed_password="somepasswordhash",
        role="elderly",
        name="Existing Elderly User"
    )
    db.add(existing_user)
    db.commit()
    db.close()

    mock_payload = {
        "email": "google_test_existing@gmail.com",
        "sub": "google-sub-67890",
        "name": "Existing Google User",
        "email_verified": True
    }
    with patch("services.google_auth_service.verify_google_id_token", return_value=mock_payload):
        # Frontend sends role="caregiver" attempt during login, but existing user's role MUST be preserved as "elderly"
        response = client.post("/api/auth/google", json={"id_token": "valid_token_456", "role": "caregiver"})
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "google_test_existing@gmail.com"
        assert data["user"]["role"] == "elderly"  # Preserved!