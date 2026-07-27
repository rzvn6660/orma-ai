from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from services.auth_service import SECRET_KEY, ALGORITHM
from context.context_resolver import ContextResolver
import uuid
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        jwt_role: str = payload.get("role")
        print(f"DEBUG [JWT]: decoded sub={user_id}, role={jwt_role}")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        print(f"DEBUG [JWT ERROR]: {str(e)}")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"DEBUG [DB]: User not found for id {user_id}")
        raise credentials_exception
    
    # Attach jwt_role to user object temporarily for debugging down the chain
    user.jwt_role = jwt_role
    print(f"DEBUG [DB]: Found user {user.id} with DB role: '{user.role}'")
    return user

def get_caregiver_user(current_user: User = Depends(get_current_user)):
    print(f"DEBUG [AuthCheck - Caregiver]: User={current_user.id}, JWT_Role={getattr(current_user, 'jwt_role', None)}, DB_Role={current_user.role}, Expected='caregiver'")
    if current_user.role != "caregiver":
        print(f"DEBUG [AuthCheck - Caregiver]: FAILED. DB Role '{current_user.role}' != 'caregiver'")
        raise HTTPException(status_code=403, detail="Access denied. Caregiver role required.")
    return current_user

def get_elderly_user(current_user: User = Depends(get_current_user)):
    print(f"DEBUG [AuthCheck - Elderly]: User={current_user.id}, JWT_Role={getattr(current_user, 'jwt_role', None)}, DB_Role={current_user.role}, Expected='elderly'")
    if current_user.role not in ["elderly", "elder", "patient"]:
        print(f"DEBUG [AuthCheck - Elderly]: FAILED. DB Role '{current_user.role}' not in allowed roles")
        raise HTTPException(status_code=403, detail="Access denied. Elderly user role required.")
    return current_user

from models.user import User, CaregiverRelationship

def get_current_context(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Standardize Request Context for all routes
    text_placeholder = "" # API calls might not have text, they just need subject resolution
    ctx = ContextResolver.resolve(current_user, text_placeholder, db)
    
    subject_id = ctx.subject_id
    subject_name = ctx.subject_name
    
    # Support explicit Subject switching via header (for multi-patient Caregivers/Doctors)
    header_subject_id = request.headers.get("x-subject-id")
    if header_subject_id:
        subject_id = header_subject_id
        subject_user = db.query(User).filter(User.id == subject_id).first()
        if subject_user:
            subject_name = subject_user.name

    # SECURE RELATIONSHIP AUTHORIZATION ENFORCEMENT
    if current_user.role == "caregiver":
        if subject_id != current_user.id:
            rel = db.query(CaregiverRelationship).filter(
                CaregiverRelationship.caregiver_id == current_user.id,
                CaregiverRelationship.elder_id == subject_id,
                CaregiverRelationship.status == "approved"
            ).first()
            if not rel:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Caregiver relationship is not active or has been revoked."
                )
    elif current_user.role in ["elderly", "elder", "patient"]:
        if subject_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Elderly users cannot access other users' health information."
            )

    return {
        "authenticated_user": current_user,
        "resolved_subject": {
            "id": subject_id,
            "name": subject_name,
            "role": ctx.subject_role
        },
        "permissions": ctx.permissions,
        "organization_id": None, # Future
        "request_id": str(uuid.uuid4())
    }

