from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import secrets
import string
from datetime import datetime, timedelta
from database import get_db
from models.user import User, ConnectionCode, CaregiverRelationship, AuditLog, RateLimit
from dependencies import get_current_user, get_elderly_user, get_caregiver_user
from services.websocket_manager import manager
import asyncio

router = APIRouter()

class CodeRequest(BaseModel):
    code: str

def log_audit(db: Session, user_id: str, action: str, details: str = None):
    log = AuditLog(user_id=user_id, action=action, details=details)
    db.add(log)
    db.commit()

def check_rate_limit(db: Session, user_id: str, action: str):
    rate = db.query(RateLimit).filter(RateLimit.user_id == user_id, RateLimit.action == action).first()
    now = datetime.utcnow()
    if rate:
        if now - rate.window_start < timedelta(minutes=10):
            if rate.attempts >= 5:
                log_audit(db, user_id, f"{action}_rate_limited")
                raise HTTPException(status_code=429, detail="Too many attempts. Please try again later.")
            rate.attempts += 1
        else:
            rate.window_start = now
            rate.attempts = 1
    else:
        rate = RateLimit(user_id=user_id, action=action, attempts=1, window_start=now)
        db.add(rate)
    db.commit()

@router.post("/generate_code")
def generate_connection_code(current_user: User = Depends(get_elderly_user), db: Session = Depends(get_db)):
    # Invalidate old unused codes
    db.query(ConnectionCode).filter(ConnectionCode.elder_id == current_user.id).update({"is_used": True})
    
    # Cryptographically secure random code
    alphabet = string.ascii_uppercase
    digits = string.digits
    code_str = ''.join(secrets.choice(alphabet) for _ in range(4)) + "-" + ''.join(secrets.choice(digits) for _ in range(4))
    
    new_code = ConnectionCode(
        code=code_str,
        elder_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db.add(new_code)
    db.commit()
    db.refresh(new_code)
    
    log_audit(db, current_user.id, "generate_code", "Generated new connection code")
    
    return {"code": new_code.code, "expires_at": new_code.expires_at}

@router.post("/connect")
async def connect_caregiver(req: CodeRequest, current_user: User = Depends(get_caregiver_user), db: Session = Depends(get_db)):
    check_rate_limit(db, current_user.id, "code_attempt")
    
    code_record = db.query(ConnectionCode).filter(
        ConnectionCode.code == req.code,
        ConnectionCode.is_used == False,
        ConnectionCode.expires_at > datetime.utcnow()
    ).first()
    
    if not code_record:
        log_audit(db, current_user.id, "invalid_code_attempt", f"Attempted code: {req.code}")
        raise HTTPException(status_code=400, detail="Invalid or expired connection code.")
        
    existing = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == code_record.elder_id,
        CaregiverRelationship.caregiver_id == current_user.id
    ).first()
    
    if existing:
        if existing.status == "revoked" or existing.status == "rejected":
            existing.status = "pending"
        else:
            raise HTTPException(status_code=400, detail="Relationship already exists or is pending.")
    else:
        new_rel = CaregiverRelationship(
            elder_id=code_record.elder_id,
            caregiver_id=current_user.id,
            status="pending"
        )
        db.add(new_rel)
        
    code_record.is_used = True
    db.commit()
    
    log_audit(db, current_user.id, "code_used", f"Used code to request link with {code_record.elder_id}")
    
    # Send notification to elder's websocket
    await manager.send_personal_message({
        "type": "pending_request_created",
        "message": f"{current_user.name} would like to connect as your caregiver."
    }, code_record.elder_id)
    
    return {"status": "success", "message": "Link request sent to elder for approval."}

@router.get("/pending_requests")
def get_pending_requests(current_user: User = Depends(get_elderly_user), db: Session = Depends(get_db)):
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == current_user.id,
        CaregiverRelationship.status == "pending"
    ).all()
    users = db.query(User).filter(User.id.in_([r.caregiver_id for r in rels])).all()
    return {"pending_requests": [{"id": u.id, "name": u.name, "email": u.email} for u in users]}

@router.post("/approve/{target_id}")
async def approve_request(target_id: str, current_user: User = Depends(get_elderly_user), db: Session = Depends(get_db)):
    rel = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == current_user.id,
        CaregiverRelationship.caregiver_id == target_id,
        CaregiverRelationship.status == "pending"
    ).first()
    if rel:
        rel.status = "approved"
        db.commit()
        log_audit(db, current_user.id, "approve_connection", f"Approved caregiver {target_id}")
        
        # Notify the caregiver that they were approved
        await manager.send_personal_message({
            "type": "caregiver_linked",
            "message": f"{current_user.name} approved your link request."
        }, target_id)
        
        # Also broadcast to elder's own sessions so other tabs can update
        await manager.send_personal_message({
            "type": "pending_request_approved",
            "message": "Caregiver approved."
        }, current_user.id)
        
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Request not found")

@router.post("/decline/{target_id}")
def decline_request(target_id: str, current_user: User = Depends(get_elderly_user), db: Session = Depends(get_db)):
    rel = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == current_user.id,
        CaregiverRelationship.caregiver_id == target_id,
        CaregiverRelationship.status == "pending"
    ).first()
    if rel:
        rel.status = "rejected"
        db.commit()
        log_audit(db, current_user.id, "reject_connection", f"Rejected caregiver {target_id}")
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Request not found")

@router.get("/linked_users")
def get_linked_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "caregiver":
        rels = db.query(CaregiverRelationship).filter(CaregiverRelationship.caregiver_id == current_user.id, CaregiverRelationship.status == "approved").all()
        users = db.query(User).filter(User.id.in_([r.elder_id for r in rels])).all()
        return {"linked_users": [{"id": u.id, "name": u.name, "email": u.email} for u in users]}
    elif current_user.role == "elderly":
        rels = db.query(CaregiverRelationship).filter(CaregiverRelationship.elder_id == current_user.id, CaregiverRelationship.status == "approved").all()
        users = db.query(User).filter(User.id.in_([r.caregiver_id for r in rels])).all()
        return {"linked_caregivers": [{"id": u.id, "name": u.name, "email": u.email} for u in users]}
    
    return {"linked_users": []}

@router.post("/revoke/{target_id}")
async def revoke_access(target_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rel = None
    target_int_id = int(target_id) if target_id.isdigit() else -1

    if current_user.role == "caregiver":
        rel = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            ((CaregiverRelationship.elder_id == target_id) | (CaregiverRelationship.id == target_int_id)),
            CaregiverRelationship.status == "approved"
        ).first()
    elif current_user.role in ["elderly", "elder", "patient"]:
        rel = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.elder_id == current_user.id,
            ((CaregiverRelationship.caregiver_id == target_id) | (CaregiverRelationship.id == target_int_id)),
            CaregiverRelationship.status == "approved"
        ).first()

    if not rel:
        existing_any = db.query(CaregiverRelationship).filter(
            (CaregiverRelationship.caregiver_id == current_user.id) | (CaregiverRelationship.elder_id == current_user.id)
        ).filter(
            (CaregiverRelationship.caregiver_id == target_id) | (CaregiverRelationship.elder_id == target_id) | (CaregiverRelationship.id == target_int_id)
        ).first()
        
        if existing_any:
            if existing_any.status == "revoked":
                return {"status": "success", "message": "Access was already revoked."}
            raise HTTPException(status_code=403, detail="You don't have permission to change this relationship.")
        raise HTTPException(status_code=404, detail="Caregiver connection no longer exists.")

    rel.status = "revoked"
    db.commit()

    other_user_id = rel.elder_id if current_user.role == "caregiver" else rel.caregiver_id
    log_audit(db, current_user.id, "revoke_connection", f"Revoked relationship between {current_user.id} and {other_user_id}")

    msg_payload = {
        "type": "caregiver_removed",
        "message": f"Caregiver connection was unlinked.",
        "caregiver_id": rel.caregiver_id,
        "elder_id": rel.elder_id
    }
    await manager.send_personal_message(msg_payload, rel.caregiver_id)
    await manager.send_personal_message(msg_payload, rel.elder_id)

    return {"status": "success", "message": "Access revoked successfully."}
