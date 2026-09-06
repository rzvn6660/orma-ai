import os
import sys
import secrets
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from database import SessionLocal, ensure_schema_migrations
from models.user import User, CaregiverRelationship, ConnectionCode

ensure_schema_migrations()
client = TestClient(app)

def test_elderly_caregiver_connection_flow():
    db = SessionLocal()
    tag = secrets.token_hex(4)
    elder_email = f"elder_conn_{tag}@orma.test"
    caregiver_email = f"cg_conn_{tag}@orma.test"
    password = "SecurePassword123!"

    elder_user = None
    cg_user = None

    try:
        # 1. Create Elderly user
        signup_elder = client.post("/api/auth/signup", json={
            "name": f"Elderly {tag}",
            "email": elder_email,
            "password": password,
            "role": "elderly"
        })
        assert signup_elder.status_code in [200, 201]
        elder_token = signup_elder.json().get("access_token")
        if not elder_token:
            # Login if signup doesn't return token
            login_e = client.post("/api/auth/login", json={"email": elder_email, "password": password})
            assert login_e.status_code == 200
            elder_token = login_e.json()["access_token"]

        elder_user = db.query(User).filter(User.email == elder_email).first()
        assert elder_user is not None
        assert elder_user.role == "elderly"

        # 2. Create Caregiver user
        signup_cg = client.post("/api/auth/signup", json={
            "name": f"Caregiver {tag}",
            "email": caregiver_email,
            "password": password,
            "role": "caregiver"
        })
        assert signup_cg.status_code in [200, 201]
        cg_token = signup_cg.json().get("access_token")
        if not cg_token:
            login_c = client.post("/api/auth/login", json={"email": caregiver_email, "password": password})
            assert login_c.status_code == 200
            cg_token = login_c.json()["access_token"]

        cg_user = db.query(User).filter(User.email == caregiver_email).first()
        assert cg_user is not None
        assert cg_user.role == "caregiver"

        elder_headers = {"Authorization": f"Bearer {elder_token}"}
        cg_headers = {"Authorization": f"Bearer {cg_token}"}

        # 3. Verify Caregiver CANNOT generate code (elderly role required)
        cg_gen = client.post("/api/link/generate_code", headers=cg_headers)
        assert cg_gen.status_code == 403

        # 4. Elderly generates connection code
        gen_res = client.post("/api/link/generate_code", headers=elder_headers)
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert "code" in gen_data
        assert "expires_at" in gen_data
        code = gen_data["code"]
        assert len(code) >= 8

        # 5. Elderly views active code via GET /api/link/active_code
        active_res = client.get("/api/link/active_code", headers=elder_headers)
        assert active_res.status_code == 200
        active_data = active_res.json()
        assert active_data["code"] == code

        # 6. Caregiver attempts to connect with invalid code
        invalid_res = client.post("/api/link/connect", json={"code": "INVALID-9999"}, headers=cg_headers)
        assert invalid_res.status_code == 400

        # 7. Caregiver attempts to access elder before approval -> 403 Forbidden
        unauth_dash = client.get("/api/caregiver/summary", headers={**cg_headers, "X-Subject-ID": elder_user.id})
        assert unauth_dash.status_code == 403

        # 8. Caregiver connects using the valid code
        connect_res = client.post("/api/link/connect", json={"code": code}, headers=cg_headers)
        assert connect_res.status_code == 200
        assert connect_res.json().get("status") == "success"

        # 9. Code is single-use: second attempt with same code fails
        reuse_res = client.post("/api/link/connect", json={"code": code}, headers=cg_headers)
        assert reuse_res.status_code == 400

        # 10. Status is pending: Caregiver still CANNOT access elder data
        pending_dash = client.get("/api/caregiver/summary", headers={**cg_headers, "X-Subject-ID": elder_user.id})
        assert pending_dash.status_code == 403

        # 11. Elderly views pending requests
        pending_res = client.get("/api/link/pending_requests", headers=elder_headers)
        assert pending_res.status_code == 200
        requests = pending_res.json().get("pending_requests", [])
        assert any(r["id"] == cg_user.id for r in requests)

        # 12. Elderly approves the caregiver connection
        approve_res = client.post(f"/api/link/approve/{cg_user.id}", headers=elder_headers)
        assert approve_res.status_code == 200

        # 13. Both parties see each other in linked_users
        elder_linked = client.get("/api/link/linked_users", headers=elder_headers).json()
        assert any(u["id"] == cg_user.id for u in elder_linked.get("linked_caregivers", []))

        cg_linked = client.get("/api/link/linked_users", headers=cg_headers).json()
        assert any(u["id"] == elder_user.id for u in cg_linked.get("linked_users", []))

        # 14. Caregiver CAN now access authorized elderly data
        auth_dash = client.get("/api/caregiver/summary", headers={**cg_headers, "X-Subject-ID": elder_user.id})
        assert auth_dash.status_code == 200

        # 15. Either party can revoke access - Elderly revokes caregiver access
        revoke_res = client.post(f"/api/link/revoke/{cg_user.id}", headers=elder_headers)
        assert revoke_res.status_code == 200

        # 16. Caregiver access is immediately revoked
        revoked_dash = client.get("/api/caregiver/summary", headers={**cg_headers, "X-Subject-ID": elder_user.id})
        assert revoked_dash.status_code == 403

    finally:
        # Cleanup test records using authenticated account deletion
        if elder_token:
            try:
                client.delete("/api/auth/me", headers={"Authorization": f"Bearer {elder_token}"})
            except Exception:
                pass
        if cg_token:
            try:
                client.delete("/api/auth/me", headers={"Authorization": f"Bearer {cg_token}"})
            except Exception:
                pass
        try:
            db.close()
        except Exception:
            pass
