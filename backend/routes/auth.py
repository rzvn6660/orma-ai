from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from database import get_db
from models.user import User, AuditLog, PasswordResetToken, RateLimit, CaregiverRelationship, ConnectionCode, NotificationPreferences, EmailVerificationOTP
from services.auth_service import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta, datetime
from dependencies import get_current_user
import re
import secrets
import time
import hashlib
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from services import google_auth_service
from services.notification_preference_service import get_user_notification_preferences

def check_resend_otp_rate_limit(db: Session, email_key: str):
    """
    Limits OTP resend requests (5 requests per 15 min).
    Anti-enumeration safe.
    """
    key = f"resend_otp:{email_key}"
    rate = db.query(RateLimit).filter(RateLimit.user_id == key, RateLimit.action == "resend_otp").first()
    now = datetime.utcnow()
    if rate:
        if now - rate.window_start < timedelta(minutes=15):
            if rate.attempts >= 5:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many verification code requests. Please try again in 15 minutes."
                )
            rate.attempts += 1
        else:
            rate.window_start = now
            rate.attempts = 1
    else:
        rate = RateLimit(user_id=key, action="resend_otp", attempts=1, window_start=now)
        db.add(rate)
    db.commit()

def check_verify_otp_rate_limit(db: Session, email_key: str):
    """
    Limits verification attempts globally per email (15 attempts per 15 min).
    Prevents mass brute-forcing across multiple codes.
    """
    key = f"verify_otp:{email_key}"
    rate = db.query(RateLimit).filter(RateLimit.user_id == key, RateLimit.action == "verify_otp").first()
    now = datetime.utcnow()
    if rate:
        if now - rate.window_start < timedelta(minutes=15):
            if rate.attempts >= 15:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many verification attempts. Please try again in 15 minutes."
                )
            rate.attempts += 1
        else:
            rate.window_start = now
            rate.attempts = 1
    else:
        rate = RateLimit(user_id=key, action="verify_otp", attempts=1, window_start=now)
        db.add(rate)
    db.commit()

def check_login_rate_limit(db: Session, email_key: str):
    """
    Limits consecutive failed login attempts (5 attempts per 15 min).
    Safe against account enumeration: tracks rate limit by normalized email string.
    """
    key = f"login:{email_key}"
    rate = db.query(RateLimit).filter(RateLimit.user_id == key, RateLimit.action == "failed_login").first()
    now = datetime.utcnow()
    if rate:
        if now - rate.window_start < timedelta(minutes=15):
            if rate.attempts >= 5:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Please try again in 15 minutes."
                )
        else:
            # Window expired, reset
            rate.window_start = now
            rate.attempts = 0
            db.commit()

def record_failed_login(db: Session, email_key: str):
    key = f"login:{email_key}"
    rate = db.query(RateLimit).filter(RateLimit.user_id == key, RateLimit.action == "failed_login").first()
    now = datetime.utcnow()
    if rate:
        if now - rate.window_start < timedelta(minutes=15):
            rate.attempts += 1
        else:
            rate.window_start = now
            rate.attempts = 1
    else:
        rate = RateLimit(user_id=key, action="failed_login", attempts=1, window_start=now)
        db.add(rate)
    db.commit()

def clear_login_rate_limit(db: Session, email_key: str):
    key = f"login:{email_key}"
    db.query(RateLimit).filter(RateLimit.user_id == key, RateLimit.action == "failed_login").delete(synchronize_session=False)
    db.commit()

def check_forgot_password_rate_limit(db: Session, email_key: str):
    """
    Limits password reset requests (3 requests per 15 min).
    Anti-enumeration safe: runs before DB account lookup.
    """
    key = f"forgot:{email_key}"
    rate = db.query(RateLimit).filter(RateLimit.user_id == key, RateLimit.action == "forgot_password").first()
    now = datetime.utcnow()
    if rate:
        if now - rate.window_start < timedelta(minutes=15):
            if rate.attempts >= 3:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many password reset requests. Please try again in 15 minutes."
                )
            rate.attempts += 1
        else:
            rate.window_start = now
            rate.attempts = 1
    else:
        rate = RateLimit(user_id=key, action="forgot_password", attempts=1, window_start=now)
        db.add(rate)
    db.commit()

def format_user_dict(user: User, db: Session) -> dict:
    prefs = get_user_notification_preferences(db, user)
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "timezone": user.timezone,
        "timezone_offset": user.timezone_offset,
        "country": user.country,
        "phone": getattr(user, "phone", None),
        "email_verified": getattr(user, "email_verified", False),
        "notification_preferences": {
            "medication_reminder_notifications": prefs.medication_reminder_notifications,
            "medication_spoken_alerts": prefs.medication_spoken_alerts,
            "missed_medication_alerts": prefs.missed_medication_alerts,
            "medication_adherence_summary": prefs.medication_adherence_summary,
            "reminder_language": getattr(prefs, "reminder_language", "en-IN") or "en-IN",
            "voice_language": getattr(prefs, "voice_language", "auto") or "auto"
        }
    }

def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[@$!%*?&]", password):
        raise ValueError("Password must contain at least one special character (@$!%*?&)")

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str
    role: str
    name: str
    timezone: str = "UTC"
    timezone_offset: str = None
    country: str = None

class UserUpdate(BaseModel):
    timezone: str = None
    timezone_offset: str = None
    country: str = None
    phone: str = None
    name: str = None

class UserLogin(BaseModel):
    email: str
    password: str

class PhoneAuth(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str
    role: str = "elderly"

class GoogleAuth(BaseModel):
    id_token: str = None
    email: str = None
    name: str = None
    role: str = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class VerifyEmailOTPRequest(BaseModel):
    email: str
    otp: str

class ResendEmailOTPRequest(BaseModel):
    email: str

class VerifyEmailTokenRequest(BaseModel):
    token: str

otp_store = {}

def _send_verification_otp_email(to_email: str, otp: str):
    """
    Sends 6-digit email verification OTP via Resend API (primary) or SMTP (secondary).
    Never logs the raw OTP or keys in production.
    """
    subject = "Verify your ORMA AI account"
    body_text = f"""ORMA AI

Verify your email address

Your ORMA AI verification code is:

{otp}

This code expires in 5 minutes.

If you did not create an ORMA AI account, you can safely ignore this email.

—
ORMA AI — Care. Connect. Remember.
"""
    body_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify your ORMA AI account</title>
</head>
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f8fafc;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:520px;background-color:#ffffff;border-radius:16px;border:1px solid #e2e8f0;padding:36px 32px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
          <tr>
            <td>
              <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#7c3aed;letter-spacing:-0.025em;">ORMA AI</h1>
              <h2 style="margin:0 0 20px;font-size:20px;font-weight:700;color:#0f172a;">Verify your email address</h2>
              <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#334155;">Hello,</p>
              <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#334155;">Thank you for joining ORMA AI. Please use the verification code below to verify your email address:</p>
              <div style="margin:28px 0;text-align:center;">
                <div style="display:inline-block;padding:16px 36px;background:#f1f5f9;border:2px dashed #94a3b8;border-radius:12px;font-size:32px;font-weight:800;letter-spacing:8px;color:#1e293b;font-family:ui-monospace,Menlo,Monaco,Consolas,monospace;">
                  {otp}
                </div>
              </div>
              <p style="margin:24px 0 8px;font-size:13px;line-height:1.6;color:#64748b;">This code expires in <strong>5 minutes</strong> and can only be used once.</p>
              <p style="margin:0 0 28px;font-size:13px;line-height:1.6;color:#64748b;">If you did not create an ORMA AI account, you can safely ignore this email.</p>
              <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;" />
              <p style="margin:0;font-size:12px;color:#94a3b8;text-align:center;">ORMA AI — Care. Connect. Remember.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    # 1. Primary: Resend API
    resend_api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if resend_api_key and not resend_api_key.startswith("re_xxxxxxxxx"):
        try:
            import resend
            resend.api_key = resend_api_key
            resend_from = os.environ.get("RESEND_FROM", "").strip() or "onboarding@resend.dev"
            params = {
                "from": resend_from,
                "to": [to_email],
                "subject": subject,
                "html": body_html,
                "text": body_text
            }
            resend_resp = resend.Emails.send(params)
            logger.info(f"[EMAIL-VERIFICATION] Verification OTP email delivered via Resend API to {to_email}")
            return
        except Exception as e:
            logger.error(f"[EMAIL-VERIFICATION] Resend API delivery failed: {type(e).__name__} ({str(e)}). Attempting SMTP fallback...")

    # 2. Secondary: SMTP
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    smtp_from = os.environ.get("SMTP_FROM", "").strip() or smtp_user or "noreply@orma.ai"
    env_mode = os.environ.get("ENVIRONMENT", os.environ.get("ENV", "development")).strip().lower()

    if not smtp_host or not smtp_user or not smtp_pass:
        if env_mode == "production":
            logger.error("[EMAIL-VERIFICATION] Neither Resend nor SMTP credentials configured in production.")
        else:
            logger.warning("[EMAIL-VERIFICATION] Development mode — email simulation.")
            print(f"\n{'='*60}")
            print(f"[ORMA EMAIL VERIFICATION] Development mode — email simulation.")
            print(f"Verification Code for {to_email}: {otp}")
            print(f"{'='*60}\n")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [to_email], msg.as_string())

        logger.info(f"[EMAIL-VERIFICATION] Verification OTP delivered via SMTP to {to_email}")
    except Exception as e:
        logger.error(f"[EMAIL-VERIFICATION] SMTP send failed: {type(e).__name__}")


@router.post("/signup")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    raw_email = user.email or ""
    normalized_email = raw_email.strip().lower()
    logger.info(f"[AUTH-SIGNUP] email normalized = {normalized_email}")
    
    db_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if db_user:
        logger.info(f"[AUTH-SIGNUP] existing user lookup = True, conflicting field = email, result = 409")
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
        
    if user.role not in ['elderly', 'caregiver']:
        raise HTTPException(status_code=422, detail="Role must be 'elderly' or 'caregiver'")
        
    try:
        validate_password(user.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=normalized_email,
        hashed_password=hashed_password,
        role=user.role,
        name=user.name,
        timezone=user.timezone,
        timezone_offset=user.timezone_offset,
        country=user.country,
        token_version=1,
        email_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log = AuditLog(user_id=new_user.id, action="signup", details=f"User signed up as {user.role}, pending email verification")
    db.add(log)
    
    # Generate random 6-digit OTP (5-minute expiry)
    raw_otp = f"{secrets.randbelow(900000) + 100000:06d}"
    otp_hash = hashlib.sha256(raw_otp.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    otp_record = EmailVerificationOTP(
        user_id=new_user.id,
        email=normalized_email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        max_attempts=5,
        is_used=False,
        created_at=datetime.utcnow(),
        last_sent_at=datetime.utcnow()
    )
    db.add(otp_record)
    db.commit()
    
    _send_verification_otp_email(normalized_email, raw_otp)
    
    return {
        "message": "Account created. Please verify your email address to continue.",
        "email": normalized_email,
        "requires_verification": True,
        "requires_email_verification": True,
        "user": format_user_dict(new_user, db)
    }

@router.post("/verify-email-otp")
def verify_email_otp(data: VerifyEmailOTPRequest, db: Session = Depends(get_db)):
    normalized_email = (data.email or "").strip().lower()
    raw_otp = (data.otp or "").strip()
    
    if not normalized_email or not raw_otp:
        raise HTTPException(status_code=400, detail="Email and verification code are required.")
        
    check_verify_otp_rate_limit(db, normalized_email)
    
    # Find latest pending OTP record for this email
    otp_record = db.query(EmailVerificationOTP).filter(
        EmailVerificationOTP.email == normalized_email,
        EmailVerificationOTP.is_used == False
    ).order_by(EmailVerificationOTP.created_at.desc()).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="Verification code has expired or is invalid. Please request a new code."
        )
        
    # Check expiration
    if datetime.utcnow() > otp_record.expires_at:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="Verification code has expired. Please request a new code."
        )
        
    # Check attempt limit
    if otp_record.attempts >= otp_record.max_attempts:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. This code is no longer valid. Please request a new code."
        )
        
    candidate_hash = hashlib.sha256(raw_otp.encode()).hexdigest()
    if candidate_hash != otp_record.otp_hash:
        otp_record.attempts += 1
        remaining = otp_record.max_attempts - otp_record.attempts
        db.commit()
        if remaining <= 0:
            otp_record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many incorrect attempts. This code is no longer valid. Please request a new code."
            )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid verification code. {remaining} attempt(s) remaining."
        )
        
    # Valid OTP
    otp_record.is_used = True
    otp_record.used_at = datetime.utcnow()
    
    db_user = db.query(User).filter(User.id == otp_record.user_id).first()
    if not db_user:
        db_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
        
    if db_user:
        db_user.email_verified = True
        
    # Invalidate any other pending OTPs for this user
    if db_user:
        db.query(EmailVerificationOTP).filter(
            EmailVerificationOTP.user_id == db_user.id,
            EmailVerificationOTP.id != otp_record.id,
            EmailVerificationOTP.is_used == False
        ).update({"is_used": True}, synchronize_session=False)
        
    log = AuditLog(user_id=db_user.id if db_user else "unknown", action="email_verified", details="Email successfully verified via OTP")
    db.add(log)
    db.commit()
    
    logger.info(f"[EMAIL-VERIFICATION] Email verified successfully for {normalized_email}")
    return {"message": "Email verified successfully. You can now sign in with your password."}

@router.post("/resend-verification-otp")
@router.post("/resend-email-otp")
def resend_verification_otp(data: ResendEmailOTPRequest, db: Session = Depends(get_db)):
    GENERIC_RESPONSE = {
        "message": "If an account exists with this email, a new verification code has been sent."
    }
    normalized_email = (data.email or "").strip().lower()
    if not normalized_email:
        return GENERIC_RESPONSE
        
    check_resend_otp_rate_limit(db, normalized_email)
    
    # Check 60-second cooldown from last sent OTP
    latest_otp = db.query(EmailVerificationOTP).filter(
        EmailVerificationOTP.email == normalized_email
    ).order_by(EmailVerificationOTP.created_at.desc()).first()
    
    if latest_otp and latest_otp.last_sent_at:
        elapsed = (datetime.utcnow() - latest_otp.last_sent_at).total_seconds()
        if elapsed < 60:
            remaining_secs = int(60 - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {max(1, remaining_secs)} seconds before requesting a new verification code."
            )
            
    db_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not db_user:
        return GENERIC_RESPONSE
        
    if db_user.email_verified:
        return {"message": "This account is already verified. Please sign in."}
        
    # Invalidate previous unused OTPs
    db.query(EmailVerificationOTP).filter(
        EmailVerificationOTP.user_id == db_user.id,
        EmailVerificationOTP.is_used == False
    ).update({"is_used": True}, synchronize_session=False)
    db.commit()
    
    # Generate new random 6-digit OTP (5-minute expiry)
    raw_otp = f"{secrets.randbelow(900000) + 100000:06d}"
    otp_hash = hashlib.sha256(raw_otp.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    new_otp_record = EmailVerificationOTP(
        user_id=db_user.id,
        email=normalized_email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        max_attempts=5,
        is_used=False,
        created_at=datetime.utcnow(),
        last_sent_at=datetime.utcnow()
    )
    db.add(new_otp_record)
    
    log = AuditLog(user_id=db_user.id, action="resend_verification_otp", details="New verification OTP dispatched")
    db.add(log)
    db.commit()
    
    _send_verification_otp_email(normalized_email, raw_otp)
    
    return {"message": "A new verification code has been sent to your email."}

@router.post("/verify-email")
def verify_email_token(data: VerifyEmailTokenRequest, db: Session = Depends(get_db)):
    raw_token = (data.token or "").strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")
        
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    otp_record = db.query(EmailVerificationOTP).filter(
        EmailVerificationOTP.otp_hash == token_hash,
        EmailVerificationOTP.is_used == False
    ).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")
        
    if datetime.utcnow() > otp_record.expires_at:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(status_code=400, detail="This verification link has expired. Please request a new one.")
        
    otp_record.is_used = True
    otp_record.used_at = datetime.utcnow()
    
    db_user = db.query(User).filter(User.id == otp_record.user_id).first()
    if db_user:
        db_user.email_verified = True
        
    log = AuditLog(user_id=otp_record.user_id, action="email_verified", details="Email verified via link token")
    db.add(log)
    db.commit()
    return {"message": "Your email has been verified successfully. You can now sign in."}

import uuid
import logging

logger = logging.getLogger(__name__)

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    req_id = str(uuid.uuid4())[:8]
    t0 = time.time()
    raw_email = user.email or ""
    normalized_email = raw_email.strip().lower()
    logger.info(f"[AUTH-LOGIN {req_id}] started, email normalized = {normalized_email}")
    
    # 1. Rate limiting check (anti-enumeration safe: runs before user check)
    check_login_rate_limit(db, normalized_email)
    
    t_db = time.time()
    db_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    t_db_done = time.time()
    user_found = db_user is not None
    logger.info(f"[AUTH-LOGIN {req_id}] user found = {user_found} — {round((t_db_done - t_db)*1000, 2)}ms")
    
    if not db_user:
        record_failed_login(db, normalized_email)
        logger.info(f"[AUTH-LOGIN {req_id}] active = false")
        logger.info(f"[AUTH-LOGIN {req_id}] authentication rejected (user not found) — total {round((time.time() - t0)*1000, 2)}ms")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    logger.info(f"[AUTH-LOGIN {req_id}] user id = {db_user.id}")
    logger.info(f"[AUTH-LOGIN {req_id}] role = {db_user.role}")
    logger.info(f"[AUTH-LOGIN {req_id}] active = true")
    
    hash_prefix = db_user.hashed_password[:7] if db_user.hashed_password else "none"
    logger.info(f"[AUTH-LOGIN {req_id}] password hash present = {db_user.hashed_password is not None}")
    logger.info(f"[AUTH-LOGIN {req_id}] hash algorithm/prefix = {hash_prefix}")
    
    t_pw = time.time()
    logger.info(f"[AUTH-LOGIN {req_id}] password verification started")
    pw_valid = verify_password(user.password, db_user.hashed_password)
    t_pw_done = time.time()
    logger.info(f"[AUTH-LOGIN {req_id}] password verification result = {pw_valid} — {round((t_pw_done - t_pw)*1000, 2)}ms")
    
    if not pw_valid:
        record_failed_login(db, normalized_email)
        log = AuditLog(user_id=db_user.id, action="failed_login", details="Incorrect password")
        db.add(log)
        db.commit()
        logger.info(f"[AUTH-LOGIN {req_id}] authentication rejected (invalid password) — total {round((time.time() - t0)*1000, 2)}ms")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    # 2. Check email verification status for email/password accounts
    if not getattr(db_user, "email_verified", True):
        logger.info(f"[AUTH-LOGIN {req_id}] authentication rejected (email not verified)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before signing in."
        )

    # Clear rate limit counter on successful login
    clear_login_rate_limit(db, normalized_email)
    
    logger.info(f"[AUTH-LOGIN {req_id}] authentication accepted")
    access_token = create_access_token(
        data={"sub": db_user.id, "role": db_user.role, "ver": db_user.token_version or 1},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    log = AuditLog(user_id=db_user.id, action="login", details="Successful login")
    db.add(log)
    db.commit()
    
    t_done = time.time()
    logger.info(f"[AUTH-LOGIN {req_id}] response ready — total = {round((t_done - t0)*1000, 2)}ms")
    return {"access_token": access_token, "token_type": "bearer", "user": format_user_dict(db_user, db)}


@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return format_user_dict(current_user, db)

@router.put("/me")
def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_update.timezone is not None:
        current_user.timezone = user_update.timezone
    if user_update.timezone_offset is not None:
        current_user.timezone_offset = user_update.timezone_offset
    if user_update.country is not None:
        current_user.country = user_update.country
    if user_update.phone is not None:
        clean_phone = user_update.phone.strip()
        current_user.phone = clean_phone if clean_phone != "" else None
    if user_update.name is not None:
        current_user.name = user_update.name
    db.commit()
    db.refresh(current_user)
    return format_user_dict(current_user, db)

@router.post("/change-password")
def change_password(data: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not data.current_password or not data.new_password:
        raise HTTPException(status_code=400, detail="All fields are required.")
        
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
        
    try:
        validate_password(data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    current_user.hashed_password = get_password_hash(data.new_password)
    # Revoke all existing sessions on password change
    current_user.token_version = (current_user.token_version or 1) + 1
    
    log = AuditLog(user_id=current_user.id, action="change_password", details="Password changed; sessions revoked")
    db.add(log)
    db.commit()
    
    logger.info(f"[AUTH-CHANGE-PASSWORD] Password changed successfully for user_id={current_user.id}")
    return {"message": "Password changed successfully."}

@router.post("/logout-all")
def logout_all_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.token_version = (current_user.token_version or 1) + 1
    log = AuditLog(user_id=current_user.id, action="logout_all", details="All active sessions revoked")
    db.add(log)
    db.commit()
    return {"message": "All sessions have been successfully logged out."}

@router.post("/request-otp")
def request_otp(data: PhoneAuth):
    env_mode = os.environ.get("ENVIRONMENT", os.environ.get("ENV", "development")).strip().lower()
    if env_mode == "production":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMS Phone OTP authentication is not configured for production environment."
        )
    clean_phone = (data.phone or "").strip()
    if not clean_phone:
        raise HTTPException(status_code=400, detail="Phone number is required.")
    otp = "123456" # Static demo code for development
    otp_store[clean_phone] = {
        "otp": otp,
        "expires_at": time.time() + 300, # 5 min TTL
        "attempts": 0
    }
    print(f"--- [DEMO MODE] SIMULATED SMS TO {clean_phone}: Your Orma AI code is {otp} (valid 5 min) ---")
    return {
        "message": "[DEMO MODE] OTP sent successfully. Code is 123456 (valid for 5 minutes).",
        "is_demo": True,
        "expires_in_seconds": 300
    }

@router.post("/verify-otp")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    env_mode = os.environ.get("ENVIRONMENT", os.environ.get("ENV", "development")).strip().lower()
    if env_mode == "production":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMS Phone OTP authentication is not configured for production environment."
        )
    clean_phone = (data.phone or "").strip()
    otp_entry = otp_store.get(clean_phone)
    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP. Please request a new code.")
    
    # Check TTL
    if time.time() > otp_entry.get("expires_at", 0):
        otp_store.pop(clean_phone, None)
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new code.")
        
    # Check attempts
    if otp_entry.get("attempts", 0) >= 3:
        otp_store.pop(clean_phone, None)
        raise HTTPException(status_code=429, detail="Too many failed OTP attempts. Please request a new code.")
        
    if otp_entry.get("otp") != data.otp:
        otp_entry["attempts"] = otp_entry.get("attempts", 0) + 1
        rem = 3 - otp_entry["attempts"]
        if rem <= 0:
            otp_store.pop(clean_phone, None)
            raise HTTPException(status_code=429, detail="Too many failed OTP attempts. Please request a new code.")
        raise HTTPException(status_code=400, detail=f"Invalid OTP code. {rem} attempt(s) remaining.")
        
    # Successful verification - consume single-use OTP
    otp_store.pop(clean_phone, None)
    
    fake_email = f"{clean_phone}@phone.local"
    db_user = db.query(User).filter(User.email == fake_email).first()
    
    if not db_user:
        new_user = User(
            email=fake_email,
            hashed_password=get_password_hash("PhoneAuthSecure123!"),
            role=data.role,
            name=f"User {clean_phone[-4:]}",
            token_version=1
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db_user = new_user
        
    access_token = create_access_token(
        data={"sub": db_user.id, "role": db_user.role, "ver": db_user.token_version or 1},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": db_user.id, "email": db_user.email, "role": db_user.role, "name": db_user.name, "timezone": db_user.timezone}}

@router.post("/google")
def google_auth(data: GoogleAuth, db: Session = Depends(get_db)):
    verified_payload = None

    if data.id_token:
        try:
            verified_payload = google_auth_service.verify_google_id_token(data.id_token)
        except ValueError as val_err:
            raise HTTPException(status_code=400, detail=str(val_err))
    else:
        raise HTTPException(
            status_code=400, 
            detail="Simulated authentication is disabled. A valid Google ID Token is required."
        )

    verified_email = verified_payload["email"]
    verified_name = verified_payload["name"]

    # Match existing user or create linked account
    db_user = db.query(User).filter(User.email == verified_email).first()
    
    if not db_user:
        # Role handling for genuine new Google user:
        # Preserve user-selected role if valid ('elderly' or 'caregiver'), otherwise default to 'elderly'
        user_role = data.role if data.role in ['elderly', 'caregiver'] else 'elderly'
        
        # Generate secure random password
        random_password = secrets.token_urlsafe(32)
        hashed_pass = get_password_hash(random_password)

        new_user = User(
            email=verified_email,
            hashed_password=hashed_pass,
            role=user_role,
            name=verified_name,
            email_verified=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db_user = new_user
    else:
        if not getattr(db_user, "email_verified", True):
            db_user.email_verified = True
            db.commit()

    # Log successful audit event
    log = AuditLog(user_id=db_user.id, action="google_login", details=f"Google OAuth verified for {verified_email}")
    db.add(log)
    db.commit()

    # Issue standard ORMA access token
    access_token = create_access_token(
        data={"sub": db_user.id, "role": db_user.role, "ver": db_user.token_version or 1},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": format_user_dict(db_user, db)
    }


# ──────────────────────────────────────────────────────────────
# PASSWORD RESET — Pydantic models
# ──────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str

class ValidateResetTokenRequest(BaseModel):
    token: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

RESET_TOKEN_EXPIRE_MINUTES = 30


def _send_reset_email(to_email: str, reset_url: str):
    """
    Send reset email via SMTP if env vars are configured.
    Falls back to printing reset URL to server console (development mode).
    NEVER logs passwords, tokens, or credentials.
    """
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    smtp_from = os.environ.get("SMTP_FROM", "").strip() or smtp_user or "noreply@orma.ai"
    env_mode = os.environ.get("ENVIRONMENT", os.environ.get("ENV", "development")).strip().lower()

    subject = "Reset your ORMA AI password"

    body_text = f"""Hello,

You requested a password reset for your ORMA AI account.

Click or copy the link below to set a new password:
{reset_url}

This link expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes and can only be used once.

If you did not request this, you can safely ignore this email. Your password will not change.

—
ORMA AI — Care. Connect. Remember.
"""

    body_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset your ORMA AI password</title>
</head>
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f8fafc;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:520px;background-color:#ffffff;border-radius:16px;border:1px solid #e2e8f0;padding:36px 32px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
          <tr>
            <td>
              <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#7c3aed;letter-spacing:-0.025em;">ORMA AI</h1>
              <h2 style="margin:0 0 20px;font-size:20px;font-weight:700;color:#0f172a;">Reset your password</h2>
              <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#334155;">Hello,</p>
              <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#334155;">You requested a password reset for your ORMA AI account.</p>
              <div style="margin:28px 0;text-align:center;">
                <a href="{reset_url}" style="display:inline-block;padding:14px 32px;background:#2563eb;color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;border-radius:10px;box-shadow:0 4px 12px rgba(37,99,235,0.25);">Reset Password</a>
              </div>
              <p style="margin:24px 0 8px;font-size:13px;line-height:1.6;color:#64748b;">This link expires in <strong>{RESET_TOKEN_EXPIRE_MINUTES} minutes</strong> and can only be used once.</p>
              <p style="margin:0 0 28px;font-size:13px;line-height:1.6;color:#64748b;">If you did not request this, you can safely ignore this email. Your password will not change.</p>
              <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;" />
              <p style="margin:0;font-size:12px;color:#94a3b8;text-align:center;">ORMA AI — Care. Connect. Remember.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    # 1. Primary Email Delivery: Resend API (if configured)
    resend_api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if resend_api_key and not resend_api_key.startswith("re_xxxxxxxxx"):
        try:
            import resend
            resend.api_key = resend_api_key
            resend_from = os.environ.get("RESEND_FROM", "").strip() or "onboarding@resend.dev"
            params = {
                "from": resend_from,
                "to": [to_email],
                "subject": subject,
                "html": body_html,
                "text": body_text
            }
            resend_resp = resend.Emails.send(params)
            logger.info(f"[PASSWORD-RESET] Reset email delivered via Resend API to {to_email} (id={getattr(resend_resp, 'id', resend_resp.get('id', 'ok') if isinstance(resend_resp, dict) else 'ok')})")
            return
        except Exception as e:
            logger.error(f"[PASSWORD-RESET] Resend API delivery failed: {type(e).__name__} ({str(e)}). Attempting SMTP fallback...")

    # 2. Secondary Email Delivery: SMTP
    if not smtp_host or not smtp_user or not smtp_pass:
        if env_mode == "production":
            logger.error("[PASSWORD-RESET] Neither Resend nor SMTP credentials configured in production. Email not sent.")
        else:
            logger.warning("[PASSWORD-RESET] Resend/SMTP not configured. Development mode — email not sent.")
            print(f"\n{'='*60}")
            print(f"[ORMA PASSWORD RESET] Development mode — email not sent.")
            print(f"Reset URL for {to_email}:")
            print(f"  {reset_url}")
            print(f"{'='*60}\n")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [to_email], msg.as_string())

        logger.info(f"[PASSWORD-RESET] Reset email delivered via SMTP to {to_email}")
    except Exception as e:
        logger.error(f"[PASSWORD-RESET] SMTP send failed: {type(e).__name__}")


# ──────────────────────────────────────────────────────────────
# POST /api/auth/forgot-password
# Account-enumeration safe: same response for registered & unregistered emails.
# ──────────────────────────────────────────────────────────────
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    SAFE_RESPONSE = {
        "message": "If an account exists for that email address, we'll send instructions to reset your password."
    }

    normalized_email = (data.email or "").strip().lower()
    if not normalized_email:
        return SAFE_RESPONSE

    # Rate limiting protection — anti-enumeration preserved (runs for all inputs)
    check_forgot_password_rate_limit(db, normalized_email)

    db_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()

    if not db_user:
        # Respond identically — do NOT reveal whether email exists
        return SAFE_RESPONSE

    # Invalidate any existing unused tokens for this user (prevent token accumulation)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == db_user.id,
        PasswordResetToken.is_used == False
    ).delete(synchronize_session=False)
    db.commit()

    # Generate cryptographically secure raw token (32 bytes → 64 hex chars)
    raw_token = secrets.token_hex(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)

    reset_token = PasswordResetToken(
        user_id=db_user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(reset_token)
    db.commit()

    # Build reset URL — FRONTEND_URL from .env (no VITE_ prefix on backend vars)
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url}/reset-password?token={raw_token}"

    _send_reset_email(normalized_email, reset_url)

    log = AuditLog(user_id=db_user.id, action="forgot_password", details="Reset email triggered")
    db.add(log)
    db.commit()

    return SAFE_RESPONSE


# ──────────────────────────────────────────────────────────────
# POST /api/auth/validate-reset-token
# Used by frontend to check if a token URL is still valid before
# showing the reset form (prevents showing the form for expired tokens).
# ──────────────────────────────────────────────────────────────
@router.post("/validate-reset-token")
def validate_reset_token(data: ValidateResetTokenRequest, db: Session = Depends(get_db)):
    raw_token = (data.token or "").strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.is_used == False
    ).first()

    if not db_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    if datetime.utcnow() > db_token.expires_at:
        raise HTTPException(status_code=400, detail="This reset link has expired. Please request a new one.")

    return {"valid": True}


# ──────────────────────────────────────────────────────────────
# POST /api/auth/reset-password
# Validates token, enforces password policy, hashes & saves, invalidates token.
# ──────────────────────────────────────────────────────────────
@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    raw_token = (data.token or "").strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.is_used == False
    ).first()

    if not db_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    if datetime.utcnow() > db_token.expires_at:
        raise HTTPException(status_code=400, detail="This reset link has expired. Please request a new one.")

    # Enforce existing password policy
    try:
        validate_password(data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_user = db.query(User).filter(User.id == db_token.user_id).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    # Update password
    db_user.hashed_password = get_password_hash(data.new_password)
    # Revoke any older sessions on password reset
    db_user.token_version = (db_user.token_version or 1) + 1
    # Resetting password via email verification link implicitly verifies email ownership
    db_user.email_verified = True

    # Invalidate the token (single-use)
    db_token.is_used = True

    # Also invalidate any other unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == db_user.id,
        PasswordResetToken.id != db_token.id,
        PasswordResetToken.is_used == False
    ).delete(synchronize_session=False)

    log = AuditLog(user_id=db_user.id, action="password_reset", details="Password reset via email token; sessions revoked")
    db.add(log)
    db.commit()

    logger.info(f"[PASSWORD-RESET] Password reset successful for user_id={db_user.id}")
    return {"message": "Your password has been reset successfully. You can now sign in with your new password."}


# ──────────────────────────────────────────────────────────────
# DELETE /api/auth/me
# Authenticated user account deletion. Safely cascades user-owned data.
# ──────────────────────────────────────────────────────────────
@router.delete("/delete-account")
@router.delete("/me")
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    user_email = current_user.email
    logger.info(f"[AUTH-DELETE-ACCOUNT] User account deletion requested for user_id={user_id}")

    # 1. RAG documents, chunks, and storage objects
    try:
        from rag.rag_models import RAGDocument, RAGDocumentChunk
        from infrastructure.storage_service import storage_service
        bucket = getattr(storage_service, "default_bucket", "medical-documents")
        rag_docs = db.query(RAGDocument).filter(RAGDocument.user_id == user_id).all()
        for doc in rag_docs:
            if doc.file_path:
                try:
                    storage_service.delete_file(bucket=bucket, object_path=doc.file_path)
                except Exception as del_err:
                    logger.warning(f"[AUTH-DELETE-ACCOUNT] Storage object cleanup warning: {del_err}")
                if os.path.exists(doc.file_path):
                    try:
                        os.remove(doc.file_path)
                    except Exception:
                        pass
        # Clean user storage folder prefix: {user_id}/
        try:
            storage_service.delete_folder(bucket=bucket, folder_prefix=f"{user_id}/")
        except Exception:
            pass

        db.query(RAGDocumentChunk).filter(RAGDocumentChunk.user_id == user_id).delete(synchronize_session=False)
        db.query(RAGDocument).filter(RAGDocument.user_id == user_id).delete(synchronize_session=False)
    except Exception as e:
        logger.warning(f"[AUTH-DELETE-ACCOUNT] RAG cleanup note: {e}")

    # 2. Memories (OCME & general)
    try:
        from models.memory import MemoryEvent
        db.query(MemoryEvent).filter(MemoryEvent.user_id == user_id).delete(synchronize_session=False)
    except Exception:
        pass
    try:
        from memory.memory_models import OCMEMemory
        db.query(OCMEMemory).filter(OCMEMemory.user_id == user_id).delete(synchronize_session=False)
    except Exception:
        pass

    # 3. Medicines & Reminders
    try:
        from models.medicine import MedicineReminder
        db.query(MedicineReminder).filter(MedicineReminder.elder_id == user_id).delete(synchronize_session=False)
    except Exception as e:
        logger.warning(f"[AUTH-DELETE-ACCOUNT] Medicine cleanup note: {e}")

    # 4. Health Records & Events
    try:
        from models.health_record import HealthRecord
        db.query(HealthRecord).filter(HealthRecord.user_id == user_id).delete(synchronize_session=False)
    except Exception:
        pass
    try:
        from models.health_event import HealthEvent
        db.query(HealthEvent).filter(HealthEvent.elder_id == user_id).delete(synchronize_session=False)
    except Exception:
        pass

    # 5. Notifications & Emergency Alerts
    try:
        from models.notification import Notification
        db.query(Notification).filter((Notification.caregiver_id == user_id) | (Notification.elder_id == user_id)).delete(synchronize_session=False)
    except Exception:
        pass
    try:
        from models.emergency import EmergencyAlert
        db.query(EmergencyAlert).filter((EmergencyAlert.elder_id == user_id) | (EmergencyAlert.caregiver_id == user_id)).delete(synchronize_session=False)
    except Exception:
        pass

    # 6. Caregiver Relationships & Connection Codes
    db.query(CaregiverRelationship).filter(
        (CaregiverRelationship.elder_id == user_id) | (CaregiverRelationship.caregiver_id == user_id)
    ).delete(synchronize_session=False)
    db.query(ConnectionCode).filter(ConnectionCode.elder_id == user_id).delete(synchronize_session=False)

    # 7. Preferences, Reset Tokens, Email OTPs, Rate Limits
    db.query(NotificationPreferences).filter(NotificationPreferences.user_id == user_id).delete(synchronize_session=False)
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete(synchronize_session=False)
    db.query(EmailVerificationOTP).filter(
        (EmailVerificationOTP.user_id == user_id) | (EmailVerificationOTP.email == user_email)
    ).delete(synchronize_session=False)
    db.query(RateLimit).filter(
        (RateLimit.user_id == user_id) | 
        (RateLimit.user_id == f"login:{user_email}") | 
        (RateLimit.user_id == f"forgot:{user_email}") |
        (RateLimit.user_id == f"resend_otp:{user_email}") |
        (RateLimit.user_id == f"verify_otp:{user_email}")
    ).delete(synchronize_session=False)

    # 8. User Audit Logs
    db.query(AuditLog).filter(AuditLog.user_id == user_id).delete(synchronize_session=False)

    # 9. Delete User record
    db.delete(current_user)
    db.commit()

    logger.info(f"[AUTH-DELETE-ACCOUNT] Account for user_id={user_id} successfully deleted.")
    return {"message": "Account and all associated personal data have been permanently deleted."}

