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
from models.user import User, AuditLog, NotificationPreferences, EmailVerificationOTP, PasswordResetToken
from routes.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router, prefix="/api/auth")

client = TestClient(app)

# ── Test email constants ─────────────────────────────────────────────────────
EXISTING_EMAIL = "google_test_existing@gmail.com"
NEW_EMAIL = "google_test_new@gmail.com"

MOCK_NEW_PAYLOAD = {
    "email": NEW_EMAIL,
    "sub": "google-sub-12345",
    "name": "New Google User",
    "email_verified": True
}

MOCK_EXISTING_PAYLOAD = {
    "email": EXISTING_EMAIL,
    "sub": "google-sub-67890",
    "name": "Existing Google User",
    "email_verified": True
}


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    def _cleanup():
        test_emails = [EXISTING_EMAIL, NEW_EMAIL]
        users = db.query(User).filter(User.email.in_(test_emails)).all()
        for u in users:
            db.query(EmailVerificationOTP).filter(EmailVerificationOTP.user_id == u.id).delete()
            db.query(PasswordResetToken).filter(PasswordResetToken.user_id == u.id).delete()
            db.query(AuditLog).filter(AuditLog.user_id == u.id).delete()
            try:
                db.query(NotificationPreferences).filter(NotificationPreferences.user_id == u.id).delete()
            except Exception:
                pass
            db.delete(u)
        db.commit()

    _cleanup()
    yield
    _cleanup()
    db.close()


# ── J: Missing id_token → 422 (Pydantic validation) ─────────────────────────
def test_google_auth_missing_token():
    """J: Empty payload missing required id_token must return 422."""
    response = client.post("/api/auth/google", json={})
    assert response.status_code == 422
    assert "detail" in response.json()


# ── K: Invalid Google token → 400 ────────────────────────────────────────────
def test_google_auth_invalid_token():
    """K: Unverifiable ID token must return 400."""
    with patch("services.google_auth_service.verify_google_id_token",
               side_effect=ValueError("Invalid Google ID token signature.")):
        response = client.post("/api/auth/google", json={"id_token": "bad_token", "intent": "login"})
        assert response.status_code == 400
        assert "Invalid Google ID token signature" in response.json()["detail"]


# ── A: Login intent + existing account → 200 ─────────────────────────────────
def test_google_login_existing_account_returns_200():
    """A: Login intent with a known Google email must authenticate and return JWT."""
    db = SessionLocal()
    db.add(User(email=EXISTING_EMAIL, hashed_password="hash", role="elderly", name="Existing User"))
    db.commit()
    db.close()

    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_EXISTING_PAYLOAD):
        response = client.post("/api/auth/google", json={"id_token": "valid_token", "intent": "login"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == EXISTING_EMAIL


# ── B: Login intent + existing elderly + request role=caregiver → role stays elderly ─
def test_google_login_preserves_elderly_role():
    """B: Login must never mutate role from elderly to caregiver."""
    db = SessionLocal()
    db.add(User(email=EXISTING_EMAIL, hashed_password="hash", role="elderly", name="Elderly User"))
    db.commit()
    db.close()

    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_EXISTING_PAYLOAD):
        response = client.post("/api/auth/google", json={
            "id_token": "valid_token",
            "intent": "login",
            "role": "caregiver"  # should be ignored
        })
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "elderly"


# ── C: Login intent + existing caregiver + request role=elderly → role stays caregiver ─
def test_google_login_preserves_caregiver_role():
    """C: Login must never mutate role from caregiver to elderly."""
    db = SessionLocal()
    db.add(User(email=EXISTING_EMAIL, hashed_password="hash", role="caregiver", name="Caregiver User"))
    db.commit()
    db.close()

    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_EXISTING_PAYLOAD):
        response = client.post("/api/auth/google", json={
            "id_token": "valid_token",
            "intent": "login",
            "role": "elderly"  # should be ignored
        })
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "caregiver"


# ── D: Login intent + unknown email → 404 ────────────────────────────────────
def test_google_login_unknown_account_returns_404():
    """D: Login intent for an email with no ORMA account must return 404, never auto-create."""
    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_NEW_PAYLOAD):
        response = client.post("/api/auth/google", json={"id_token": "valid_token", "intent": "login"})
        assert response.status_code == 404
        body = response.json()
        assert "detail" in body
        # Ensure no account was silently created
        db = SessionLocal()
        user = db.query(User).filter(User.email == NEW_EMAIL).first()
        db.close()
        assert user is None, "Backend must NOT create an account for login intent on unknown email"


# ── E: Signup intent + new email + role=elderly → 200 ───────────────────────
def test_google_signup_new_user_elderly():
    """E: Signup intent with new email and role=elderly must create account and return JWT."""
    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_NEW_PAYLOAD):
        response = client.post("/api/auth/google", json={
            "id_token": "valid_token",
            "intent": "signup",
            "role": "elderly"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == NEW_EMAIL
        assert data["user"]["role"] == "elderly"
        assert data["user"]["email_verified"] is True


# ── F: Signup intent + new email + role=caregiver → 200 ─────────────────────
def test_google_signup_new_user_caregiver():
    """F: Signup intent with new email and role=caregiver must create account and return JWT."""
    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_NEW_PAYLOAD):
        response = client.post("/api/auth/google", json={
            "id_token": "valid_token",
            "intent": "signup",
            "role": "caregiver"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "caregiver"


# ── G: Signup intent + existing email → 409 ──────────────────────────────────
def test_google_signup_existing_account_returns_409():
    """G: Signup intent for an already-registered email must return 409, not duplicate."""
    db = SessionLocal()
    db.add(User(email=EXISTING_EMAIL, hashed_password="hash", role="elderly", name="Existing User"))
    db.commit()
    db.close()

    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_EXISTING_PAYLOAD):
        response = client.post("/api/auth/google", json={
            "id_token": "valid_token",
            "intent": "signup",
            "role": "elderly"
        })
        assert response.status_code == 409
        assert "detail" in response.json()


# ── H: Signup intent + new email + missing role → 400 ───────────────────────
def test_google_signup_missing_role_returns_400():
    """H: Signup intent with null role must be rejected with 400, never default to elderly."""
    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_NEW_PAYLOAD):
        response = client.post("/api/auth/google", json={
            "id_token": "valid_token",
            "intent": "signup",
            "role": None
        })
        assert response.status_code == 400
        # Ensure no account was created
        db = SessionLocal()
        user = db.query(User).filter(User.email == NEW_EMAIL).first()
        db.close()
        assert user is None, "Backend must NOT create an account when role is missing"


# ── I: Signup intent + new email + invalid role → 400 ───────────────────────
def test_google_signup_invalid_role_returns_400():
    """I: Signup intent with an unrecognised role string must return 400."""
    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_NEW_PAYLOAD):
        response = client.post("/api/auth/google", json={
            "id_token": "valid_token",
            "intent": "signup",
            "role": "admin"
        })
        assert response.status_code == 400


# ── Extra: invalid intent → 400 ──────────────────────────────────────────────
def test_google_auth_invalid_intent_returns_400():
    """Non-login/signup intent values must return 400."""
    with patch("services.google_auth_service.verify_google_id_token", return_value=MOCK_NEW_PAYLOAD):
        response = client.post("/api/auth/google", json={
            "id_token": "valid_token",
            "intent": "delete"
        })
        assert response.status_code == 400