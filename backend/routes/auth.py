from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from database import get_db
from models.user import User, AuditLog
from services.auth_service import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from dependencies import get_current_user
import re
import secrets
import time
from services import google_auth_service

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

otp_store = {}

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
        country=user.country
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(
        data={"sub": new_user.id, "role": new_user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": new_user.id, "email": new_user.email, "role": new_user.role, "name": new_user.name, "timezone": new_user.timezone, "timezone_offset": new_user.timezone_offset, "country": new_user.country}}

import uuid
import logging

logger = logging.getLogger(__name__)

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    req_id = uuid.uuid4().hex[:6]
    t0 = time.time()
    raw_email = user.email or ""
    normalized_email = raw_email.strip().lower()
    logger.info(f"[AUTH-LOGIN {req_id}] request received")
    logger.info(f"[AUTH-LOGIN {req_id}] email normalized = {normalized_email}")
    
    t_db = time.time()
    db_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    t_db_done = time.time()
    user_found = db_user is not None
    logger.info(f"[AUTH-LOGIN {req_id}] user found = {user_found} — {round((t_db_done - t_db)*1000, 2)}ms")
    
    if not db_user:
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
        log = AuditLog(user_id=db_user.id, action="failed_login", details="Incorrect password")
        db.add(log)
        db.commit()
        logger.info(f"[AUTH-LOGIN {req_id}] authentication rejected (invalid password) — total {round((time.time() - t0)*1000, 2)}ms")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    logger.info(f"[AUTH-LOGIN {req_id}] authentication accepted")
    access_token = create_access_token(
        data={"sub": db_user.id, "role": db_user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    log = AuditLog(user_id=db_user.id, action="login", details="Successful login")
    db.add(log)
    db.commit()
    
    t_done = time.time()
    logger.info(f"[AUTH-LOGIN {req_id}] response ready — total = {round((t_done - t0)*1000, 2)}ms")
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": db_user.id, "email": db_user.email, "role": db_user.role, "name": db_user.name, "timezone": db_user.timezone, "timezone_offset": db_user.timezone_offset, "country": db_user.country}}


@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "role": current_user.role, "name": current_user.name, "timezone": current_user.timezone, "timezone_offset": current_user.timezone_offset, "country": current_user.country}

@router.put("/me")
def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_update.timezone is not None:
        current_user.timezone = user_update.timezone
    if user_update.timezone_offset is not None:
        current_user.timezone_offset = user_update.timezone_offset
    if user_update.country is not None:
        current_user.country = user_update.country
    db.commit()
    db.refresh(current_user)
    return {"id": current_user.id, "email": current_user.email, "role": current_user.role, "name": current_user.name, "timezone": current_user.timezone, "timezone_offset": current_user.timezone_offset, "country": current_user.country}

@router.post("/request-otp")
def request_otp(data: PhoneAuth):
    # Simulate Twilio/SMS delivery
    otp = "123456" # Static for demo
    otp_store[data.phone] = otp
    print(f"--- SIMULATED SMS TO {data.phone}: Your Orma AI code is {otp} ---")
    return {"message": "OTP sent successfully. Code is 123456 for demo."}

@router.post("/verify-otp")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    if otp_store.get(data.phone) != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    fake_email = f"{data.phone}@phone.local"
    db_user = db.query(User).filter(User.email == fake_email).first()
    
    if not db_user:
        new_user = User(
            email=fake_email,
            hashed_password=get_password_hash("PhoneAuthSecure123!"),
            role=data.role,
            name=f"User {data.phone[-4:]}"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db_user = new_user
        
    access_token = create_access_token(
        data={"sub": db_user.id, "role": db_user.role},
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
            name=verified_name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db_user = new_user

    # Log successful audit event
    log = AuditLog(user_id=db_user.id, action="google_login", details=f"Google OAuth verified for {verified_email}")
    db.add(log)
    db.commit()

    # Issue standard ORMA access token
    access_token = create_access_token(
        data={"sub": db_user.id, "role": db_user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": {
            "id": db_user.id, 
            "email": db_user.email, 
            "role": db_user.role, 
            "name": db_user.name, 
            "timezone": db_user.timezone,
            "timezone_offset": db_user.timezone_offset,
            "country": db_user.country
        }
    }
