# ORMA AI — Authentication Architecture & Lifecycle

## 1. Overview

ORMA AI implements a secure, role-aware, zero-trust authentication architecture designed to protect sensitive elderly health and medication data while providing frictionless caregiver onboarding.

---

## 2. Authentication Methods

### 2.1 Email & Password Authentication
1. **Signup**:
   - Creates user with `email_verified=False` and `is_active=True`.
   - Passwords are encrypted using Bcrypt (`passlib.context.CryptContext` with salt rounds = 12).
   - Returns immediate JWT `access_token` and `token_type="bearer"` for immediate application access.
   - Generates a cryptographically random 6-digit Email Verification OTP.
   - Computes SHA-256 hash of OTP and stores in `email_verification_otps` table with 5-minute expiry.
   - Dispatches email via Gmail API HTTPS transport (`POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send`).

2. **Email Verification**:
   - `POST /api/auth/verify-email-otp` validates the entered OTP against `sha256(raw_otp)`.
   - Enforces a maximum of 5 failed attempts per OTP lifecycle.
   - Enforces single-use consumption (`is_used=True`).
   - Implements a 60-second cooldown on `/api/auth/resend-email-otp` to protect against mail server flooding.
   - Upon verification, sets `email_verified=True`.

3. **Login Enforcement**:
   - `POST /api/auth/login` verifies Bcrypt hash.
   - Allows login for valid credentials regardless of email verification status (immediate tester onboarding).
   - Implements failed-attempt rate limiting (5 attempts per window).
   - Issues a signed JWT Access Token with `sub=user.id`, `role=user.role`, and explicit expiration.

### 2.2 Google OAuth2
- Validates Google ID tokens via `google-auth` (`google.oauth2.id_token.verify_oauth2_token`).
- Verifies `aud` matches `GOOGLE_CLIENT_ID`.
- Auto-verifies email (`email_verified=True`) for Google-authenticated profiles.
- Preserves user roles across repeat logins.

### 2.3 Password Reset Lifecycle
1. `POST /api/auth/forgot-password`:
   - Anti-enumeration protection: Returns identical HTTP 200 response regardless of whether email exists.
   - If user exists, generates a 32-byte cryptographically secure token (`secrets.token_hex(32)`).
   - Stores only `sha256(token)` in database with a 30-minute expiry (`expires_at = utcnow() + 30m`).
   - Dispatches reset link formatted using `FRONTEND_URL`: `${FRONTEND_URL}/reset-password?token=${raw_token}`.
2. `POST /api/auth/validate-reset-token`:
   - Checks hash validity, expiry, and `is_used == False`.
3. `POST /api/auth/reset-password`:
   - Updates password hash.
   - Marks token `is_used = True`.
   - Revokes any existing sessions.

---

## 3. Session & Token Management

| Property | Value |
|---|---|
| Algorithm | HMAC-SHA256 (`HS256`) |
| Token Expiry | 1440 minutes (24 hours) |
| Production Key Constraint | Minimum 32 characters; default keys rejected at startup |
| Secret Storage | Server-side environment variable `JWT_SECRET_KEY` |

---

## 4. Role-Based Access Control (RBAC)

- **`elderly`**: Access to voice assistant, daily medication schedule, personalized reminders, personal RAG documents, and caregiver linking.
- **`caregiver`**: Access to linked elderly timelines, vitals, missed dose alerts, document uploads, and notification preference controls.
- **`doctor`**: Access to summarized clinical insights, adherence metrics, and health timeline reports.
