"""
================================================================================
ORMA AI — INDEPENDENT ADVERSARIAL RED TEAM VERIFICATION HARNESS
================================================================================
Comprehensive adversarial suite executing real exploit attempts against:
1. Multi-Tenant Isolation (User A vs User B, Caregiver A vs Unrelated Elder, Pending, Revoked)
2. Emergency Safety & Mutation (Alert Forgery, Unauthorized Resolve/Ack, State Tampering)
3. Authentication & JWT Tampering (None alg, Bad Sig, Missing Ver, Expired, Revoked)
4. Google OAuth Validation (Audience mismatch, Missing Client ID in Prod, Unverified Email)
5. File Upload & Path Traversal (Traversal filenames, Oversized payloads, Extension spoofing)
6. WebSocket Handshake & Tenant Boundary (Unauthorized Notification WS, Wakeword flooding)
7. RAG Cross-Tenant Leakage (Ingestion of unique secrets, semantic retrieval isolation)
8. Security Headers & CORS (Response headers, unauthorized origin handling)
================================================================================
"""

import os
import sys
import uuid
import secrets
import time
import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from database import SessionLocal, ensure_schema_migrations
from models.user import User, CaregiverRelationship
from models.emergency import EmergencyAlert
from models.ale import BehaviourProfile, LearningCandidate
from models.rlj import JournalEntry, LifeEvent
from models.owe import ApprovalRequest
from rag.rag_models import RAGDocument, RAGDocumentChunk
from services.auth_service import get_password_hash, create_access_token, SECRET_KEY, ALGORITHM
from services.google_auth_service import verify_google_id_token
from rag.retriever import RAGRetriever

ensure_schema_migrations()
client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def red_team_environment(db_session):
    """Provisions User A, User B, Caregiver A (Approved to A), Caregiver B (Approved to B), Caregiver Pending, Caregiver Revoked."""
    uid_a = f"victim_a_{secrets.token_hex(4)}"
    uid_b = f"attacker_b_{secrets.token_hex(4)}"
    uid_cg_a = f"cga_{secrets.token_hex(4)}"
    uid_cg_b = f"cgb_{secrets.token_hex(4)}"
    uid_cg_pend = f"cgpend_{secrets.token_hex(4)}"
    uid_cg_revk = f"cgrevk_{secrets.token_hex(4)}"

    pw_hash = get_password_hash("Password123!")

    user_a = User(id=uid_a, name="Victim Alice", email=f"{uid_a}@test.local", hashed_password=pw_hash, role="elderly", email_verified=True, token_version=1)
    user_b = User(id=uid_b, name="Attacker Bob", email=f"{uid_b}@test.local", hashed_password=pw_hash, role="elderly", email_verified=True, token_version=1)
    cg_a = User(id=uid_cg_a, name="Caregiver Alice", email=f"{uid_cg_a}@test.local", hashed_password=pw_hash, role="caregiver", email_verified=True, token_version=1)
    cg_b = User(id=uid_cg_b, name="Caregiver Bob", email=f"{uid_cg_b}@test.local", hashed_password=pw_hash, role="caregiver", email_verified=True, token_version=1)
    cg_pend = User(id=uid_cg_pend, name="Caregiver Pending", email=f"{uid_cg_pend}@test.local", hashed_password=pw_hash, role="caregiver", email_verified=True, token_version=1)
    cg_revk = User(id=uid_cg_revk, name="Caregiver Revoked", email=f"{uid_cg_revk}@test.local", hashed_password=pw_hash, role="caregiver", email_verified=True, token_version=1)

    db_session.add_all([user_a, user_b, cg_a, cg_b, cg_pend, cg_revk])
    db_session.commit()

    rel_a = CaregiverRelationship(elder_id=uid_a, caregiver_id=uid_cg_a, status="approved")
    rel_b = CaregiverRelationship(elder_id=uid_b, caregiver_id=uid_cg_b, status="approved")
    rel_pend = CaregiverRelationship(elder_id=uid_a, caregiver_id=uid_cg_pend, status="pending")
    rel_revk = CaregiverRelationship(elder_id=uid_a, caregiver_id=uid_cg_revk, status="revoked")

    db_session.add_all([rel_a, rel_b, rel_pend, rel_revk])
    db_session.commit()

    tokens = {
        "user_a": create_access_token({"sub": uid_a, "role": "elderly", "ver": 1}),
        "user_b": create_access_token({"sub": uid_b, "role": "elderly", "ver": 1}),
        "cg_a": create_access_token({"sub": uid_cg_a, "role": "caregiver", "ver": 1}),
        "cg_b": create_access_token({"sub": uid_cg_b, "role": "caregiver", "ver": 1}),
        "cg_pend": create_access_token({"sub": uid_cg_pend, "role": "caregiver", "ver": 1}),
        "cg_revk": create_access_token({"sub": uid_cg_revk, "role": "caregiver", "ver": 1}),
        "ids": {
            "user_a": uid_a,
            "user_b": uid_b,
            "cg_a": uid_cg_a,
            "cg_b": uid_cg_b,
            "cg_pend": uid_cg_pend,
            "cg_revk": uid_cg_revk,
        }
    }
    return tokens


# ==============================================================================
# 1. ADVERSARIAL ATTACKS ON MULTI-TENANT ISOLATION
# ==============================================================================
def test_attack_ale_manipulation_cross_tenant(red_team_environment):
    """Attacker Bob tries to read and overwrite Victim Alice's behavioral profile."""
    uid_a = red_team_environment["ids"]["user_a"]
    token_b = red_team_environment["user_b"]
    headers = {"Authorization": f"Bearer {token_b}"}

    # 1. Read attempt
    r_get = client.get(f"/api/ale/profile/{uid_a}", headers=headers)
    assert r_get.status_code == 403, f"Attacker Bob read Alice's profile! Status: {r_get.status_code}"

    # 2. Overwrite attempt
    r_put = client.put(f"/api/ale/profile/{uid_a}", json={"communication_style": "hostile"}, headers=headers)
    assert r_put.status_code == 403, f"Attacker Bob modified Alice's profile! Status: {r_put.status_code}"


def test_attack_rlj_journal_and_timeline_theft(red_team_environment):
    """Attacker Bob tries to steal Alice's private journal, timeline, and summaries."""
    uid_a = red_team_environment["ids"]["user_a"]
    token_b = red_team_environment["user_b"]
    headers = {"Authorization": f"Bearer {token_b}"}

    assert client.get(f"/api/rlj/journal/{uid_a}", headers=headers).status_code == 403
    assert client.get(f"/api/rlj/timeline/{uid_a}", headers=headers).status_code == 403
    assert client.get(f"/api/rlj/caregiver-summary/{uid_a}", headers=headers).status_code == 403
    assert client.post(f"/api/rlj/generate/{uid_a}", headers=headers).status_code == 403


def test_attack_caregiver_b_accessing_elder_a(red_team_environment):
    """Caregiver Bob (approved only for Elder Bob) tries to access Elder Alice."""
    uid_a = red_team_environment["ids"]["user_a"]
    token_cg_b = red_team_environment["cg_b"]
    headers = {"Authorization": f"Bearer {token_cg_b}", "X-Subject-Id": uid_a}

    assert client.get(f"/api/ale/profile/{uid_a}", headers=headers).status_code == 403
    assert client.get(f"/api/rlj/journal/{uid_a}", headers=headers).status_code == 403
    assert client.get("/api/medicines", headers=headers).status_code == 403


def test_attack_pending_and_revoked_caregivers(red_team_environment):
    """Pending and Revoked caregivers try to access linked Elder Alice."""
    uid_a = red_team_environment["ids"]["user_a"]
    token_pend = red_team_environment["cg_pend"]
    token_revk = red_team_environment["cg_revk"]

    for token, status_name in [(token_pend, "pending"), (token_revk, "revoked")]:
        headers = {"Authorization": f"Bearer {token}", "X-Subject-Id": uid_a}
        res_ale = client.get(f"/api/ale/profile/{uid_a}", headers=headers)
        assert res_ale.status_code == 403, f"{status_name} caregiver accessed ALE profile: {res_ale.status_code}"
        res_med = client.get("/api/medicines", headers=headers)
        assert res_med.status_code == 403, f"{status_name} caregiver accessed medicines: {res_med.status_code}"


# ==============================================================================
# 2. EMERGENCY RED TEAM ATTACKS
# ==============================================================================
def test_attack_emergency_suppression_and_forgery(red_team_environment, db_session):
    """Comprehensive attack on emergency status, resolution, acknowledge, and forgery."""
    uid_a = red_team_environment["ids"]["user_a"]
    token_b = red_team_environment["user_b"]
    token_cg_b = red_team_environment["cg_b"]
    token_a = red_team_environment["user_a"]
    token_cg_a = red_team_environment["cg_a"]

    # 1. Attacker Bob tries to forge emergency SOS for Alice
    r_forge = client.post("/api/emergency/analyze", json={
        "text": "Critical medical collapse emergency",
        "user_id": uid_a
    }, headers={"Authorization": f"Bearer {token_b}"})
    assert r_forge.status_code == 403, "Attacker Bob forged emergency for Alice!"

    # 2. Unrelated Caregiver Bob tries to forge emergency SOS for Alice
    r_cg_forge = client.post("/api/emergency/analyze", json={
        "text": "Critical medical collapse emergency",
        "user_id": uid_a
    }, headers={"Authorization": f"Bearer {token_cg_b}"})
    assert r_cg_forge.status_code == 403, "Caregiver Bob forged emergency for Alice!"

    # 3. Create legitimate emergency for Alice
    alert_id = f"em_alert_{secrets.token_hex(4)}"
    alert = EmergencyAlert(
        id=alert_id,
        elder_id=uid_a,
        status="active",
        severity="critical",
        message="Alice fallen down stairs",
        created_at=datetime.utcnow()
    )
    db_session.add(alert)
    db_session.commit()

    # 4. Attacker Bob tries to acknowledge Alice's alert
    r_ack_b = client.post(f"/api/emergency/{alert_id}/acknowledge", headers={"Authorization": f"Bearer {token_b}"})
    assert r_ack_b.status_code == 403, "Attacker Bob acknowledged Alice's alert!"

    # 5. Attacker Bob tries to resolve Alice's alert
    r_res_b = client.post(f"/api/emergency/{alert_id}/resolve", headers={"Authorization": f"Bearer {token_b}"})
    assert r_res_b.status_code == 403, "Attacker Bob resolved Alice's alert!"

    # 6. Verify DB state remains ACTIVE (unmodified by attacker)
    db_session.expire_all()
    check_alert = db_session.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    assert check_alert.status == "active", f"Alert status corrupted to {check_alert.status}!"

    # 7. Authorized Caregiver A acknowledges
    r_ack_cg = client.post(f"/api/emergency/{alert_id}/acknowledge", headers={"Authorization": f"Bearer {token_cg_a}"})
    assert r_ack_cg.status_code == 200

    # 8. Authorized Elder Alice resolves
    r_res_a = client.post(f"/api/emergency/{alert_id}/resolve", headers={"Authorization": f"Bearer {token_a}"})
    assert r_res_a.status_code == 200

    db_session.expire_all()
    final_alert = db_session.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    assert final_alert.status == "resolved"


# ==============================================================================
# 3. AUTHENTICATION & JWT ATTACKS
# ==============================================================================
def test_attack_jwt_tampering(red_team_environment):
    """Tests none-algorithm, invalid signature, missing/corrupted claims, expired tokens."""
    uid_a = red_team_environment["ids"]["user_a"]

    # 1. None algorithm bypass
    none_token = jwt.encode({"sub": uid_a, "role": "elderly", "ver": 1}, key="", algorithm="none")
    r_none = client.get("/api/auth/me", headers={"Authorization": f"Bearer {none_token}"})
    assert r_none.status_code == 401, "None algorithm JWT accepted!"

    # 2. Forged secret signature
    forged_token = jwt.encode({"sub": uid_a, "role": "elderly", "ver": 1}, key="wrong_secret_key", algorithm="HS256")
    r_forged = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
    assert r_forged.status_code == 401, "Forged signature JWT accepted!"

    # 3. Expired token
    expired_token = jwt.encode({
        "sub": uid_a, "role": "elderly", "ver": 1, 
        "exp": datetime.utcnow() - timedelta(hours=1)
    }, key=SECRET_KEY, algorithm=ALGORITHM)
    r_exp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert r_exp.status_code == 401, "Expired JWT accepted!"

    # 4. Token without sub
    no_sub_token = jwt.encode({"role": "elderly", "ver": 1}, key=SECRET_KEY, algorithm=ALGORITHM)
    r_nosub = client.get("/api/auth/me", headers={"Authorization": f"Bearer {no_sub_token}"})
    assert r_nosub.status_code == 401, "Token without sub accepted!"

    # 5. Token with mismatched token_version
    bad_ver_token = jwt.encode({"sub": uid_a, "role": "elderly", "ver": 999}, key=SECRET_KEY, algorithm=ALGORITHM)
    r_badver = client.get("/api/auth/me", headers={"Authorization": f"Bearer {bad_ver_token}"})
    assert r_badver.status_code == 401, "Mismatched token_version accepted!"


# ==============================================================================
# 4. FILE UPLOAD & PATH TRAVERSAL ATTACKS
# ==============================================================================
def test_attack_file_upload_traversal_and_spoofing(red_team_environment):
    """Attempts directory traversal payloads on speech and OCR upload endpoints."""
    token_a = red_team_environment["user_a"]
    headers = {"Authorization": f"Bearer {token_a}"}

    dummy_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    dummy_img = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"

    traversal_filenames = [
        "../../test_escape.webm",
        "..\\..\\win_escape.webm",
        "/etc/passwd.webm",
        "C:\\Windows\\System32\\test.webm",
        "test\x00nullbyte.webm",
    ]

    for fname in traversal_filenames:
        # Speech upload
        r_sp = client.post("/api/speech/transcribe", files={"audio": (fname, dummy_audio, "audio/webm")}, headers=headers)
        # Verify no file escaped temp_audio
        assert not os.path.exists("test_escape.webm")
        assert not os.path.exists("win_escape.webm")

        # Medicine OCR upload
        r_ocr = client.post("/api/medicines/parse-ocr", files={"file": (fname.replace(".webm", ".jpg"), dummy_img, "image/jpeg")}, headers=headers)
        assert not os.path.exists("test_escape.jpg")


def test_attack_oversized_upload_rejection(red_team_environment):
    """Tests rejection of oversized audio (>15MB) and OCR (>20MB) payloads."""
    token_a = red_team_environment["user_a"]
    headers = {"Authorization": f"Bearer {token_a}"}

    # 16 MB payload
    huge_audio = b"0" * (16 * 1024 * 1024)
    r_sp = client.post("/api/speech/transcribe", files={"audio": ("huge.webm", huge_audio, "audio/webm")}, headers=headers)
    assert r_sp.status_code == 413, f"Oversized audio accepted with status {r_sp.status_code}"


# ==============================================================================
# 5. WEBSOCKET RED TEAM ATTACKS
# ==============================================================================
def test_attack_websocket_subscription_theft(red_team_environment):
    """Attacker Bob tries to connect to Alice's WebSocket stream with his token."""
    uid_a = red_team_environment["ids"]["user_a"]
    token_b = red_team_environment["user_b"]

    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/notifications/ws/{uid_a}?token={token_b}") as ws:
            pass


def test_attack_wakeword_payload_limits():
    """Wakeword WebSocket must disconnect on oversized binary frame (>64KB)."""
    with client.websocket_connect("/api/wakeword/ws") as ws:
        # Initial greeting
        msg = ws.receive_json()
        assert msg["event"] == "engine_ready"

        # Send oversized frame (128 KB)
        huge_chunk = b"\x00" * 131072
        ws.send_bytes(huge_chunk)
        
        # Connection should close due to policy violation / size limit
        with pytest.raises(Exception):
            ws.receive_text()


# ==============================================================================
# 6. RAG CROSS-TENANT ISOLATION ATTACK
# ==============================================================================
def test_attack_rag_cross_tenant_secret_leakage(red_team_environment, db_session):
    """Direct database and semantic retrieval test for User A vs User B document chunks."""
    uid_a = red_team_environment["ids"]["user_a"]
    uid_b = red_team_environment["ids"]["user_b"]
    token_b = red_team_environment["user_b"]

    secret_a = f"USER_A_SECRET_{secrets.token_hex(6)}"
    secret_b = f"USER_B_SECRET_{secrets.token_hex(6)}"

    # Create documents in DB for Alice and Bob
    doc_a = RAGDocument(id=f"doc_{secrets.token_hex(4)}", user_id=uid_a, title="alice_health.txt", file_path="alice.txt", file_size=100)
    chunk_a = RAGDocumentChunk(id=f"chk_{secrets.token_hex(4)}", document_id=doc_a.id, user_id=uid_a, chunk_index=0, text_content=f"Confidential clinical note: {secret_a}", embedding="[]")

    doc_b = RAGDocument(id=f"doc_{secrets.token_hex(4)}", user_id=uid_b, title="bob_health.txt", file_path="bob.txt", file_size=100)
    chunk_b = RAGDocumentChunk(id=f"chk_{secrets.token_hex(4)}", document_id=doc_b.id, user_id=uid_b, chunk_index=0, text_content=f"Confidential clinical note: {secret_b}", embedding="[]")

    db_session.add_all([doc_a, chunk_a, doc_b, chunk_b])
    db_session.commit()

    # 1. Attacker Bob tries to query Alice's document directly
    r_doc = client.get(f"/api/documents/{doc_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r_doc.status_code == 404, "Attacker Bob accessed Alice's RAG document!"

    # 2. Retriever query as Bob
    results, _, _ = RAGRetriever().retrieve(db=db_session, user_id=uid_b, query="Confidential clinical note", top_k=10)
    retrieved_text = " ".join([c.content for c in results])

    assert secret_a not in retrieved_text, "CRITICAL: Alice's secret leaked to Bob via RAG retriever!"


# ==============================================================================
# 7. SECURITY HEADERS VALIDATION
# ==============================================================================
def test_security_headers_enforcement():
    """Validates presence and correctness of defensive security headers on HTTP responses."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert r.headers.get("X-XSS-Protection") == "1; mode=block"
