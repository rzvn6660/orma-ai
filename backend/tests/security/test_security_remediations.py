import os
import sys
import uuid
import secrets
import pytest
from pathlib import Path
from unittest.mock import patch

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, ensure_schema_migrations
from models.user import User, CaregiverRelationship
from models.tsgp import TSGPAuditLog
from models.ale import BehaviourProfile
from memory.memory_models import OCMEMemory
from services.auth_service import get_password_hash, create_access_token

ensure_schema_migrations()
client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_synthetic_user(db, role="elderly"):
    suffix = secrets.token_hex(4)
    uid = f"test_{role}_{suffix}"
    email = f"{uid}@test.local"
    user = User(
        id=uid,
        email=email,
        name=f"Test {role.title()} {suffix}",
        hashed_password=get_password_hash("TestPassword123!"),
        role=role,
        token_version=1,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(data={"sub": uid, "role": role, "ver": 1})
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers, token


# ==============================================================================
# 1. TSGP AUDIT CROSS-USER ISOLATION (ORMA-SEC-01)
# ==============================================================================
def test_tsgp_audit_cross_user_isolation(db_session):
    user_a, headers_a, _ = create_synthetic_user(db_session, "elderly")
    user_b, headers_b, _ = create_synthetic_user(db_session, "elderly")
    caregiver, headers_cg, _ = create_synthetic_user(db_session, "caregiver")

    try:
        # Create audit entry for User A
        audit_a = TSGPAuditLog(
            user_id=user_a.id,
            intent="GeneralChat",
            request_text="SECRET_QUERY_USER_A",
            risk_score="Low",
            action_taken="allowed",
            explainability="Standard safe test intent."
        )
        db_session.add(audit_a)
        db_session.commit()

        # 1. User A can retrieve their own audit log
        resp_a = client.get("/api/tsgp/audit", headers=headers_a)
        assert resp_a.status_code == 200
        logs_a = resp_a.json()
        assert any(log.get("request_text") == "SECRET_QUERY_USER_A" for log in logs_a)

        # 2. User B calling /api/tsgp/audit CANNOT see User A's logs
        resp_b = client.get("/api/tsgp/audit", headers=headers_b)
        assert resp_b.status_code == 200
        logs_b = resp_b.json()
        assert not any(log.get("request_text") == "SECRET_QUERY_USER_A" for log in logs_b)
        assert all(log.get("user_id") == user_b.id for log in logs_b)

        # 3. User B attempting to bypass via X-Subject-ID: user_a receives 403 Forbidden
        resp_b_spoof = client.get("/api/tsgp/audit", headers={**headers_b, "x-subject-id": user_a.id})
        assert resp_b_spoof.status_code == 403

        # 4. Caregiver with approved relationship CAN view User A's audits
        rel = CaregiverRelationship(
            caregiver_id=caregiver.id,
            elder_id=user_a.id,
            status="approved"
        )
        db_session.add(rel)
        db_session.commit()

        resp_cg = client.get("/api/tsgp/audit", headers={**headers_cg, "x-subject-id": user_a.id})
        assert resp_cg.status_code == 200
        logs_cg = resp_cg.json()
        assert any(log.get("request_text") == "SECRET_QUERY_USER_A" for log in logs_cg)

    finally:
        # Cleanup
        db_session.query(TSGPAuditLog).filter(TSGPAuditLog.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
        db_session.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id == user_a.id).delete(synchronize_session=False)
        db_session.query(User).filter(User.id.in_([user_a.id, user_b.id, caregiver.id])).delete(synchronize_session=False)
        db_session.commit()


# ==============================================================================
# 2. WAKE WORD AUTHENTICATION & DIAGNOSTIC SANITIZATION (ORMA-SEC-02)
# ==============================================================================
def test_wakeword_unauthenticated_requests_blocked(db_session):
    # Test POST /api/wakeword/test without token
    dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    resp_test_unauth = client.post(
        "/api/wakeword/test",
        files={"file": ("test.wav", dummy_wav, "audio/wav")}
    )
    assert resp_test_unauth.status_code in [401, 403]

    # Test GET /api/wakeword/status without token
    resp_status_unauth = client.get("/api/wakeword/status")
    assert resp_status_unauth.status_code in [401, 403]

    # Test WebSocket /api/wakeword/ws without token
    ws_rejected = False
    try:
        with client.websocket_connect("/api/wakeword/ws") as ws:
            ws.receive_json()
    except Exception:
        ws_rejected = True
    assert ws_rejected, "WebSocket should reject unauthenticated connections"


def test_wakeword_authenticated_status_sanitized(db_session):
    user, headers, token = create_synthetic_user(db_session, "elderly")
    try:
        # Authenticated status request
        resp = client.get("/api/wakeword/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "model_name" in data
        assert "engine_loaded" in data
        # CRITICAL: sensitive diagnostics must NOT be present
        assert "model_path" not in data, "model_path must not be exposed"
        assert "load_error_message" not in data, "load_error_message must not be exposed"
    finally:
        db_session.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db_session.commit()


def test_wakeword_authenticated_websocket(db_session):
    user, headers, token = create_synthetic_user(db_session, "elderly")
    try:
        with client.websocket_connect(f"/api/wakeword/ws?token={token}") as ws:
            msg = ws.receive_json()
            assert msg.get("event") == "engine_ready"
    finally:
        db_session.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db_session.commit()


def test_wakeword_production_guard(db_session):
    user, headers, _ = create_synthetic_user(db_session, "elderly")
    try:
        dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            resp = client.post(
                "/api/wakeword/test",
                files={"file": ("test.wav", dummy_wav, "audio/wav")},
                headers=headers
            )
            assert resp.status_code == 404, "Test endpoint must be disabled (404) in production"
    finally:
        db_session.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db_session.commit()


# ==============================================================================
# 3. OCME MASS ASSIGNMENT PROTECTION (ORMA-SEC-03)
# ==============================================================================
def test_ocme_mass_assignment_protection(db_session):
    user_a, headers_a, _ = create_synthetic_user(db_session, "elderly")
    user_b, headers_b, _ = create_synthetic_user(db_session, "elderly")

    created_mem_id = None
    try:
        # Create memory
        mem = OCMEMemory(
            user_id=user_a.id,
            category="general",
            title="Initial Title",
            value="Initial Value",
            importance=50,
            confidence=1.0,
            visibility="private",
            verified=False,
            trust_score=50.0,
            source="system"
        )
        db_session.add(mem)
        db_session.commit()
        db_session.refresh(mem)
        created_mem_id = mem.id

        # 1. Update allowed field
        resp_update = client.put(
            f"/api/ocme/{created_mem_id}",
            json={"title": "Legitimate Title Update"},
            headers=headers_a
        )
        assert resp_update.status_code == 200
        assert resp_update.json().get("title") == "Legitimate Title Update"

        # 2. Attempt mass assignment on trust_score, verified, confidence
        resp_mass = client.put(
            f"/api/ocme/{created_mem_id}",
            json={
                "title": "Title After Attack",
                "trust_score": 99.9,
                "verified": True,
                "confidence": 0.05,
                "user_id": user_b.id
            },
            headers=headers_a
        )
        assert resp_mass.status_code == 200

        # Verify DB directly: trust_score and verified MUST NOT have changed
        db_session.expire_all()
        re_queried = db_session.query(OCMEMemory).filter(OCMEMemory.id == created_mem_id).first()
        assert re_queried.title == "Title After Attack"
        assert re_queried.trust_score == 50.0, "trust_score must remain 50.0"
        assert re_queried.verified is False, "verified must remain False"
        assert re_queried.confidence == 1.0, "confidence must remain 1.0"
        assert re_queried.user_id == user_a.id, "user_id must remain user_a.id"

        # 3. Cross-user update blocked
        resp_cross = client.put(
            f"/api/ocme/{created_mem_id}",
            json={"title": "Hacked by User B"},
            headers=headers_b
        )
        assert resp_cross.status_code == 404

    finally:
        if created_mem_id:
            db_session.query(OCMEMemory).filter(OCMEMemory.id == created_mem_id).delete(synchronize_session=False)
        db_session.query(User).filter(User.id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
        db_session.commit()


# ==============================================================================
# 4. ALE MASS ASSIGNMENT PROTECTION (ORMA-SEC-04)
# ==============================================================================
def test_ale_mass_assignment_protection(db_session):
    user_a, headers_a, _ = create_synthetic_user(db_session, "elderly")
    user_b, headers_b, _ = create_synthetic_user(db_session, "elderly")

    try:
        # Initialize profile
        client.get(f"/api/ale/profile/{user_a.id}", headers=headers_a)

        # 1. Update legitimate preferences
        resp_norm = client.put(
            f"/api/ale/profile/{user_a.id}",
            json={"speaking_speed": "slow", "preferred_language": "hi"},
            headers=headers_a
        )
        assert resp_norm.status_code == 200
        assert resp_norm.json().get("speaking_speed") == "slow"
        assert resp_norm.json().get("preferred_language") == "hi"

        # 2. Attempt mass-assignment overwrite of IdentityMixin / sensitive fields
        resp_attack = client.put(
            f"/api/ale/profile/{user_a.id}",
            json={
                "speaking_speed": "fast",
                "role": "SECURITY_EXPLOIT_ROLE",
                "permission_scope": "system_admin",
                "actor_id": "malicious_actor"
            },
            headers=headers_a
        )
        assert resp_attack.status_code == 200

        # Verify DB directly: role and permission_scope MUST NOT have been overwritten
        db_session.expire_all()
        prof = db_session.query(BehaviourProfile).filter(BehaviourProfile.user_id == user_a.id).first()
        assert prof.speaking_speed == "fast"
        assert getattr(prof, "role", None) != "SECURITY_EXPLOIT_ROLE", "role must not be overwritten"
        assert getattr(prof, "permission_scope", None) != "system_admin", "permission_scope must not be overwritten"

        # 3. Cross-user update blocked (User B attempting to modify User A's profile)
        resp_cross = client.put(
            f"/api/ale/profile/{user_a.id}",
            json={"speaking_speed": "normal"},
            headers=headers_b
        )
        assert resp_cross.status_code == 403

    finally:
        db_session.query(BehaviourProfile).filter(BehaviourProfile.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
        db_session.query(User).filter(User.id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
        db_session.commit()


# ==============================================================================
# 5. CLIENT-FACING EXCEPTION LEAKAGE SANITIZATION (ORMA-SEC-05)
# ==============================================================================
def test_exception_leakage_sanitization(db_session):
    user, headers, _ = create_synthetic_user(db_session, "elderly")

    try:
        # 1. Document upload error sanitization
        corrupt_pdf = b"%PDF-1.4\nCorrupted invalid binary structure %%EOF"
        resp_doc = client.post(
            "/api/documents/upload",
            files={"file": ("corrupt.pdf", corrupt_pdf, "application/pdf")},
            data={"document_type": "general_document"},
            headers=headers
        )
        assert resp_doc.status_code in [400, 500]
        # Must not leak PyMuPDF exception names, memory pointers, or file paths
        assert "cannot open broken document" not in resp_doc.text
        assert "fitz" not in resp_doc.text
        assert "pymupdf" not in resp_doc.text
        assert "Traceback" not in resp_doc.text

        # 2. Speech transcription error sanitization
        corrupt_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00INVALID_DATA"
        resp_speech = client.post(
            "/api/speech/transcribe",
            files={"audio": ("corrupt.wav", corrupt_audio, "audio/wav")},
            data={"language": "en"},
            headers=headers
        )
        assert "Traceback" not in resp_speech.text
        if resp_speech.status_code == 500:
            assert resp_speech.json().get("detail") == "Audio transcription failed. Please try again."

        # 3. Medicine parse-voice error sanitization
        with patch("routes.medicine.parse_medicine_text", side_effect=RuntimeError("Internal LLM parser connection died at /var/secrets")):
            resp_voice = client.post(
                "/api/medicines/parse-voice",
                data={"text": "Paracetamol 500mg"},
                headers=headers
            )
            assert resp_voice.status_code == 500
            assert resp_voice.json().get("detail") == "Failed to parse medicine from voice input."
            assert "/var/secrets" not in resp_voice.text

        # 4. Medicine parse-ocr error sanitization
        with patch("routes.medicine.extract_text_from_image", side_effect=RuntimeError("Tesseract OCR binary segfault at 0x7fff")):
            corrupt_img = b"\x89PNG\r\n\x1a\nCorrupted image content"
            resp_ocr = client.post(
                "/api/medicines/parse-ocr",
                files={"file": ("rx.png", corrupt_img, "image/png")},
                headers=headers
            )
            assert resp_ocr.status_code == 500
            assert resp_ocr.json().get("detail") == "Failed to parse medicine from image."
            assert "0x7fff" not in resp_ocr.text

        # 5. Insights summary error sanitization
        with patch("routes.insights.generate_insights_summary", side_effect=Exception("Database syntax error at line 42 SELECT * FROM secrets")):
            resp_insights = client.get("/api/insights/summary", headers=headers)
            assert resp_insights.status_code == 500
            assert resp_insights.json().get("detail") == "Failed to generate insights summary."
            assert "SELECT * FROM secrets" not in resp_insights.text

        # 6. Chat error sanitization
        with patch("routes.chat.orchestrator.process_request_detailed", side_effect=RuntimeError("AI cluster gateway timeout in /etc/hosts")):
            resp_chat = client.post(
                "/api/chat",
                json={"message": "Hello ORMA"},
                headers=headers
            )
            assert resp_chat.status_code == 500
            assert resp_chat.json().get("detail") == "Failed to process chat message."
            assert "/etc/hosts" not in resp_chat.text

    finally:
        db_session.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db_session.commit()
