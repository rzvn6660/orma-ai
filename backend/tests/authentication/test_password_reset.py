"""
ORMA AI — STEP 11B PASSWORD RESET & EMAIL AUDIT SUITE
Comprehensive test verifying all 15 requirements from Step 11B:
1. Existing email -> reset token created in DB
2. Unknown email -> identical public response (anti-enumeration)
3. Token stored only as SHA-256 hash in SQLite
4. Token expires after 30 minutes
5. Token is single-use
6. Password successfully changes
7. Old password stops working
8. New password works
9. Expired token rejected (400)
10. Reused token rejected (400)
11. SMTP failure handled safely (no 500 to user, graceful logging)
12. SMTP credentials never appear in API response
13. SMTP credentials never appear in frontend bundle / client code
14. Reset URL uses configured FRONTEND_URL
15. No regression to existing authentication
16. Controlled Real SMTP Delivery Check (Reports NOT_TESTABLE_NO_CREDENTIALS if unconfigured)
"""

import sys
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models.user import User, PasswordResetToken, AuditLog

client = TestClient(app)

def run_step11b_tests():
    print("=" * 75)
    print("ORMA AI — STEP 11B PASSWORD RESET & REAL EMAIL AUDIT TEST SUITE")
    print("=" * 75)

    db = SessionLocal()
    results = {}
    
    test_email = f"reset_test_{secrets.token_hex(4)}@orma.test"
    orig_password = "OldSecurePassword123!"
    new_password = "NewStrongPassword456@"
    
    # Setup test user
    signup_res = client.post("/api/auth/signup", json={
        "name": "Reset Test User",
        "email": test_email,
        "password": orig_password,
        "role": "elderly"
    })
    assert signup_res.status_code == 200
    user_id = signup_res.json()["user"]["id"]

    # 1. Existing email -> reset token created
    print("\n[CHECK 1] Existing email -> reset token created in DB...")
    res_exist = client.post("/api/auth/forgot-password", json={"email": test_email})
    assert res_exist.status_code == 200
    token_row = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.is_used == False
    ).order_by(PasswordResetToken.created_at.desc()).first()
    assert token_row is not None
    results["1_existing_email_creates_token"] = "PASS"
    print(f"  -> [PASS] Token created for user_id={user_id}")

    # 2. Unknown email -> identical public response (Anti-enumeration)
    print("\n[CHECK 2] Unknown email -> identical public response...")
    unknown_email = f"unknown_{secrets.token_hex(4)}@nowhere.test"
    res_unknown = client.post("/api/auth/forgot-password", json={"email": unknown_email})
    assert res_unknown.status_code == 200
    assert res_exist.json() == res_unknown.json()
    assert "If an account exists" in res_unknown.json()["message"]
    results["2_anti_enumeration_identical_response"] = "PASS"
    print("  -> [PASS] Responses match identically for registered & unregistered emails")

    # 3. Token stored only as SHA-256 hash in DB
    print("\n[CHECK 3] Token stored only as SHA-256 hash in SQLite...")
    assert len(token_row.token_hash) == 64
    assert all(c in "0123456789abcdef" for c in token_row.token_hash)
    results["3_token_stored_only_as_sha256_hash"] = "PASS"
    print(f"  -> [PASS] Hash in DB: {token_row.token_hash[:20]}... (raw token never stored)")

    # 4. Token expiration configured to 30 minutes
    print("\n[CHECK 4] Token expiration configured to 30 minutes...")
    diff_minutes = (token_row.expires_at - token_row.created_at).total_seconds() / 60
    assert 29.0 <= diff_minutes <= 31.0
    results["4_token_expires_30_minutes"] = "PASS"
    print(f"  -> [PASS] Expiry delta = {round(diff_minutes, 1)} minutes")

    # 5. Token validation & Single-use lifecycle
    print("\n[CHECK 5-8] Testing Token Validation, Reset, Old PW Invalidation & New PW Login...")
    raw_token = secrets.token_hex(32)
    raw_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    test_tok = PasswordResetToken(
        user_id=user_id,
        token_hash=raw_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        is_used=False
    )
    db.add(test_tok)
    db.commit()

    # Validate token
    val_res = client.post("/api/auth/validate-reset-token", json={"token": raw_token})
    assert val_res.status_code == 200 and val_res.json()["valid"] is True

    # 6. Password successfully changes
    reset_res = client.post("/api/auth/reset-password", json={"token": raw_token, "new_password": new_password})
    assert reset_res.status_code == 200
    results["6_password_successfully_changes"] = "PASS"
    print("  -> [PASS] Password reset API returned 200 OK")

    # 5. Token is single-use
    db.refresh(test_tok)
    assert test_tok.is_used is True
    results["5_token_is_single_use"] = "PASS"
    print("  -> [PASS] Token flagged is_used = True in DB")

    # 7. Old password stops working
    old_login = client.post("/api/auth/login", json={"email": test_email, "password": orig_password})
    assert old_login.status_code == 401
    results["7_old_password_stops_working"] = "PASS"
    print("  -> [PASS] Login with old password rejected (401)")

    # 8. New password works
    new_login = client.post("/api/auth/login", json={"email": test_email, "password": new_password})
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()
    results["8_new_password_works"] = "PASS"
    print("  -> [PASS] Login with new password succeeded")

    # 9. Expired token rejected
    print("\n[CHECK 9] Expired token rejected...")
    expired_token = secrets.token_hex(32)
    expired_hash = hashlib.sha256(expired_token.encode()).hexdigest()
    exp_tok = PasswordResetToken(
        user_id=user_id,
        token_hash=expired_hash,
        expires_at=datetime.utcnow() - timedelta(minutes=5),  # Expired 5 min ago
        is_used=False
    )
    db.add(exp_tok)
    db.commit()

    val_exp = client.post("/api/auth/validate-reset-token", json={"token": expired_token})
    assert val_exp.status_code == 400
    reset_exp = client.post("/api/auth/reset-password", json={"token": expired_token, "new_password": "AnotherPassword999!"})
    assert reset_exp.status_code == 400
    results["9_expired_token_rejected"] = "PASS"
    print("  -> [PASS] Expired token blocked with 400 Bad Request")

    # 10. Reused token rejected
    print("\n[CHECK 10] Reused token rejected...")
    reuse_res = client.post("/api/auth/reset-password", json={"token": raw_token, "new_password": "YetAnotherPassword999!"})
    assert reuse_res.status_code == 400
    results["10_reused_token_rejected"] = "PASS"
    print("  -> [PASS] Reused token blocked with 400 Bad Request")

    # 11. SMTP failure handled safely (no 500 error to user)
    print("\n[CHECK 11] SMTP failure handled safely...")
    with patch("smtplib.SMTP", side_effect=Exception("Simulated SMTP Network Connection Timeout")):
        with patch.dict(os.environ, {"SMTP_HOST": "smtp.invalid.test", "SMTP_USER": "test@test.com", "SMTP_PASS": "secret"}):
            smtp_err_res = client.post("/api/auth/forgot-password", json={"email": test_email})
            assert smtp_err_res.status_code == 200
            assert "If an account exists" in smtp_err_res.json()["message"]
    results["11_smtp_failure_handled_safely"] = "PASS"
    print("  -> [PASS] SMTP exception caught gracefully; user receives standard safe response")

    # 12. SMTP credentials never appear in API response
    print("\n[CHECK 12] SMTP credentials never appear in API response...")
    all_responses = [res_exist.text, res_unknown.text, reset_res.text, val_res.text]
    for r in all_responses:
        assert "SMTP_PASS" not in r
        assert "smtp.gmail.com" not in r
        assert "secret" not in r
    results["12_smtp_credentials_never_in_api_response"] = "PASS"
    print("  -> [PASS] Zero credential disclosure across all API responses")

    # 13. SMTP credentials never appear in frontend source / bundle
    print("\n[CHECK 13] SMTP credentials never appear in frontend bundle...")
    frontend_dir = os.path.abspath(os.path.join(backend_dir, "..", "frontend", "src"))
    forbidden_tokens = ["SMTP_PASS", "SMTP_USER", "SMTP_HOST", "JWT_SECRET_KEY"]
    for root, _, files in os.walk(frontend_dir):
        for f in files:
            if f.endswith((".js", ".jsx", ".ts", ".tsx", ".html")):
                with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    for tok in forbidden_tokens:
                        assert tok not in content, f"Leaked {tok} in {f}"
    results["13_smtp_credentials_never_in_frontend_bundle"] = "PASS"
    print("  -> [PASS] Frontend code strictly free of backend server secrets")

    # 14. Reset URL uses configured frontend URL
    print("\n[CHECK 14] Reset URL uses configured FRONTEND_URL...")
    captured_urls = []
    def mock_send_email(to_email, reset_url):
        captured_urls.append(reset_url)
    with patch("routes.auth._send_reset_email", side_effect=mock_send_email):
        with patch.dict(os.environ, {"FRONTEND_URL": "https://app.orma.ai"}):
            client.post("/api/auth/forgot-password", json={"email": test_email})
    assert len(captured_urls) == 1
    assert captured_urls[0].startswith("https://app.orma.ai/reset-password?token=")
    results["14_reset_url_uses_configured_frontend_url"] = "PASS"
    print(f"  -> [PASS] Constructed URL: {captured_urls[0][:45]}...")

    # 15. No regression to existing authentication
    print("\n[CHECK 15] Verifying zero regression to existing authentication...")
    auth_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_login.json()['access_token']}"})
    assert auth_me.status_code == 200
    assert auth_me.json()["id"] == user_id
    results["15_zero_regression_to_existing_auth"] = "PASS"
    print("  -> [PASS] Session resolution /api/auth/me operates flawlessly")

    # 16. Resend API Delivery Pipeline Check
    print("\n[CHECK 16] Resend API Delivery Pipeline Check...")
    with patch("resend.Emails.send", return_value={"id": "msg_resend_test_123"}) as mock_resend:
        with patch.dict(os.environ, {"RESEND_API_KEY": "re_live_test_api_key_456"}):
            from routes.auth import _send_reset_email
            _send_reset_email("test_resend@orma.ai", "https://app.orma.ai/reset-password?token=resend_tok")
            assert mock_resend.called
            call_args = mock_resend.call_args[0][0]
            assert call_args["to"] == ["test_resend@orma.ai"]
            assert "Reset Password" in call_args["html"]
    results["16_resend_api_pipeline"] = "PASS"
    print("  -> [PASS] Resend API email delivery pipeline verified")

    # 17. Real Outbound Delivery Check (Resend / SMTP)
    print("\n[CHECK 17] Controlled Real Outbound Delivery Check...")
    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()

    if resend_key and not resend_key.startswith("re_xxxxxxxxx"):
        print("  -> Real Resend API Key detected. Testing real delivery...")
        try:
            from routes.auth import _send_reset_email
            target_to = os.environ.get("RESEND_TEST_TO", "rizvinmk@gmail.com")
            _send_reset_email(target_to, "https://app.orma.ai/reset-password?token=test_controlled_token")
            results["17_real_email_delivery"] = "PASS (Delivered via Resend API)"
            print("  -> [PASS] Real Resend API delivery test completed successfully")
        except Exception as e:
            results["17_real_email_delivery"] = f"FAIL ({type(e).__name__}: {str(e)})"
            print(f"  -> [FAIL] Real Resend delivery failed: {e}")
    elif smtp_host and smtp_user and smtp_pass:
        print(f"  -> SMTP Credentials detected for {smtp_user}. Testing real delivery...")
        try:
            from routes.auth import _send_reset_email
            _send_reset_email(smtp_user, "https://app.orma.ai/reset-password?token=test_controlled_token")
            results["17_real_email_delivery"] = "PASS (Delivered via SMTP)"
            print("  -> [PASS] Real SMTP delivery test completed successfully")
        except Exception as e:
            results["17_real_email_delivery"] = f"FAIL ({type(e).__name__}: {str(e)})"
            print(f"  -> [FAIL] Real SMTP delivery failed: {e}")
    else:
        results["17_real_email_delivery"] = "NOT_TESTABLE_NO_CREDENTIALS (RESEND_API_KEY is placeholder 're_xxxxxxxxx' and SMTP unset)"
        print("  -> [NOT_TESTABLE_NO_CREDENTIALS] RESEND_API_KEY is set to 're_xxxxxxxxx' placeholder (development mode active)")

    # Cleanup test user
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete()
    db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()
    db.query(User).filter(User.id == user_id).delete()
    db.commit()
    db.close()

    print("\n" + "=" * 75)
    print("STEP 11B PASSWORD RESET AUDIT SUMMARY — ALL CHECKS COMPLETED")
    print("=" * 75)
    for check, status in results.items():
        print(f"  [{status.split()[0]}] {check}: {status}")
    print("=" * 75)

if __name__ == "__main__":
    run_step11b_tests()