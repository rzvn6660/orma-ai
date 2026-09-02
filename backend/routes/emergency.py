from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from models.emergency import EmergencyAlert
from models.notification import Notification
from models.user import User, CaregiverRelationship
from dependencies import get_current_user
from services.websocket_manager import manager
from services.emergency_service import analyze_text_for_emergency

router = APIRouter()

class EmergencyRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    severity: Optional[str] = "critical"
    alert_source: Optional[str] = "Emergency SOS"
    location: Optional[str] = None

class EmergencyResponse(BaseModel):
    is_emergency: bool
    status: str
    alert_id: Optional[str] = None
    triggered_keywords: List[str] = []
    severity: str
    notified_caregivers_count: int = 0
    message: str

@router.post("/analyze", response_model=EmergencyResponse)
async def analyze_emergency(
    request: EmergencyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers and records an emergency alert, notifies linked caregivers in DB and over real-time WebSocket.
    """
    analysis = analyze_text_for_emergency(request.text)
    is_emergency = analysis["is_emergency"] or "emergency" in request.text.lower() or "sos" in request.text.lower()
    
    if not is_emergency:
        return EmergencyResponse(
            is_emergency=False,
            status="safe",
            alert_id=None,
            triggered_keywords=[],
            severity="none",
            notified_caregivers_count=0,
            message="No emergency detected."
        )
    
    # Resolve Elder User: prioritize authenticated user; only approved caregivers may trigger on behalf of linked elders
    elder_user = current_user
    if request.user_id and request.user_id != current_user.id:
        if current_user.role != "caregiver":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Non-caregivers cannot trigger emergencies for other users."
            )
        # Check approved caregiver relationship
        rel = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.elder_id == request.user_id,
            CaregiverRelationship.status == "approved"
        ).first()
        if not rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have an approved caregiver relationship with this user."
            )
        target_elder = db.query(User).filter(User.id == request.user_id).first()
        if not target_elder:
            raise HTTPException(status_code=404, detail="Target elder user not found.")
        elder_user = target_elder

    elder_id = elder_user.id
    elder_name = elder_user.name or "Family Member"
    elder_phone = getattr(elder_user, "phone", None)

    # Persist EmergencyAlert in DB
    alert_id = str(uuid.uuid4())
    severity = request.severity or analysis.get("severity", "critical")
    
    new_alert = EmergencyAlert(
        id=alert_id,
        elder_id=elder_id,
        status="active",
        severity=severity,
        alert_source=request.alert_source or "Emergency SOS",
        message=request.text or f"{elder_name} triggered Emergency SOS.",
        location=request.location,
        created_at=datetime.utcnow()
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    # Find linked caregivers
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == elder_id,
        CaregiverRelationship.status == "approved"
    ).all()
    
    created_at_iso = f"{new_alert.created_at.isoformat()}Z"
    notified_count = 0
    for rel in rels:
        cg_id = rel.caregiver_id
        # 1. Create or update persistent database Notification for caregiver (prevent duplicate active emergency rows)
        existing_notif = db.query(Notification).filter(
            Notification.caregiver_id == cg_id,
            Notification.elder_id == elder_id,
            Notification.priority == "high",
            Notification.is_read == False
        ).first()

        if not existing_notif:
            notif = Notification(
                caregiver_id=cg_id,
                elder_id=elder_id,
                title=f"Emergency Alert: {elder_name}",
                message=f"{elder_name} may need immediate assistance.",
                priority="high",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notif)
            db.flush()
            notif_id = notif.id
        else:
            notif_id = existing_notif.id

        notified_count += 1

        # 2. Dispatch Real-time WebSocket Event to Caregiver
        await manager.send_personal_message({
            "type": "emergency_alert",
            "alert_id": alert_id,
            "notif_id": notif_id,
            "elder_id": elder_id,
            "elder_name": elder_name,
            "elder_phone": elder_phone,
            "severity": severity,
            "status": "active",
            "message": f"{elder_name} may need immediate assistance.",
            "created_at": created_at_iso,
            "location_available": bool(request.location)
        }, cg_id)

    db.commit()

    return EmergencyResponse(
        is_emergency=True,
        status="success",
        alert_id=alert_id,
        triggered_keywords=analysis.get("triggered_keywords", ["sos"]),
        severity=severity,
        notified_caregivers_count=notified_count,
        message=f"Emergency alert recorded. {notified_count} linked caregiver(s) notified."
    )

@router.get("/active")
def get_active_emergencies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves active or acknowledged emergency alerts for the authenticated user.
    """
    if current_user.role == "caregiver":
        rels = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.status == "approved"
        ).all()
        elder_ids = [r.elder_id for r in rels]
        if not elder_ids:
            return {"active_emergencies": []}
        
        alerts = db.query(EmergencyAlert).filter(
            EmergencyAlert.elder_id.in_(elder_ids),
            EmergencyAlert.status.in_(["active", "acknowledged"])
        ).order_by(EmergencyAlert.created_at.desc()).all()
    else:
        alerts = db.query(EmergencyAlert).filter(
            EmergencyAlert.elder_id == current_user.id,
            EmergencyAlert.status.in_(["active", "acknowledged"])
        ).order_by(EmergencyAlert.created_at.desc()).all()

    result = []
    for a in alerts:
        elder = db.query(User).filter(User.id == a.elder_id).first()
        created_str = f"{a.created_at.isoformat()}Z" if a.created_at else None
        acked_str = f"{a.acknowledged_at.isoformat()}Z" if a.acknowledged_at else None
        result.append({
            "id": a.id,
            "elder_id": a.elder_id,
            "elder_name": elder.name if elder else "Elderly User",
            "elder_phone": getattr(elder, "phone", None) if elder else None,
            "status": a.status,
            "severity": a.severity,
            "alert_source": a.alert_source,
            "message": a.message,
            "location": a.location,
            "acknowledged_at": acked_str,
            "acknowledged_by": a.acknowledged_by,
            "created_at": created_str
        })
    return {"active_emergencies": result}

@router.get("/history")
def get_emergency_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves past resolved emergency alerts.
    """
    if current_user.role == "caregiver":
        rels = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.status == "approved"
        ).all()
        elder_ids = [r.elder_id for r in rels]
        if not elder_ids:
            return {"history": []}
        alerts = db.query(EmergencyAlert).filter(
            EmergencyAlert.elder_id.in_(elder_ids)
        ).order_by(EmergencyAlert.created_at.desc()).limit(20).all()
    else:
        alerts = db.query(EmergencyAlert).filter(
            EmergencyAlert.elder_id == current_user.id
        ).order_by(EmergencyAlert.created_at.desc()).limit(20).all()

    result = []
    for a in alerts:
        elder = db.query(User).filter(User.id == a.elder_id).first()
        created_str = f"{a.created_at.isoformat()}Z" if a.created_at else None
        acked_str = f"{a.acknowledged_at.isoformat()}Z" if a.acknowledged_at else None
        res_str = f"{a.resolved_at.isoformat()}Z" if a.resolved_at else None
        result.append({
            "id": a.id,
            "elder_id": a.elder_id,
            "elder_name": elder.name if elder else "Elderly User",
            "status": a.status,
            "severity": a.severity,
            "alert_source": a.alert_source,
            "message": a.message,
            "acknowledged_at": acked_str,
            "resolved_at": res_str,
            "created_at": created_str
        })
    return {"history": result}

@router.post("/{alert_id}/acknowledge")
async def acknowledge_emergency(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Caregiver or Elder acknowledges an emergency alert.
    Updates DB status and notifies Elder & all linked caregivers via real-time WebSocket.
    """
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Emergency alert not found.")

    # Authorization Check: User must be the elder or an approved linked caregiver
    if current_user.id != alert.elder_id:
        rel = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.elder_id == alert.elder_id,
            CaregiverRelationship.status == "approved"
        ).first()
        if not rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not authorized to acknowledge this emergency alert."
            )

    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.name
    db.commit()

    # Mark caregiver's notifications as read for this elder
    db.query(Notification).filter(
        Notification.elder_id == alert.elder_id,
        Notification.priority == "high"
    ).update({"is_read": True})
    db.commit()

    ack_time_iso = f"{alert.acknowledged_at.isoformat()}Z"
    ack_event = {
        "type": "emergency_acknowledged",
        "alert_id": alert_id,
        "elder_id": alert.elder_id,
        "caregiver_name": current_user.name,
        "caregiver_id": current_user.id,
        "acknowledged_at": ack_time_iso
    }

    # Dispatch real-time WebSocket event to Elder
    await manager.send_personal_message(ack_event, alert.elder_id)

    # Dispatch to all linked caregivers to synchronize UI and stop alert tones
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == alert.elder_id,
        CaregiverRelationship.status == "approved"
    ).all()
    for rel in rels:
        await manager.send_personal_message(ack_event, rel.caregiver_id)

    return {"status": "success", "message": "Emergency alert acknowledged.", "acknowledged_at": ack_time_iso}

@router.post("/{alert_id}/resolve")
async def resolve_emergency(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resolves an emergency alert and marks corresponding notifications as read.
    """
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Emergency alert not found.")

    # Authorization Check: User must be the elder or an approved linked caregiver
    if current_user.id != alert.elder_id:
        rel = db.query(CaregiverRelationship).filter(
            CaregiverRelationship.caregiver_id == current_user.id,
            CaregiverRelationship.elder_id == alert.elder_id,
            CaregiverRelationship.status == "approved"
        ).first()
        if not rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not authorized to resolve this emergency alert."
            )

    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.name
    db.commit()

    # Mark all emergency notifications as read for this elder
    db.query(Notification).filter(
        Notification.elder_id == alert.elder_id,
        Notification.priority == "high"
    ).update({"is_read": True})
    db.commit()

    res_time_iso = f"{alert.resolved_at.isoformat()}Z"
    # Notify Elder & all linked caregivers
    msg = {
        "type": "emergency_resolved",
        "alert_id": alert_id,
        "resolved_by": current_user.name,
        "resolved_at": res_time_iso
    }
    await manager.send_personal_message(msg, alert.elder_id)
    rels = db.query(CaregiverRelationship).filter(
        CaregiverRelationship.elder_id == alert.elder_id,
        CaregiverRelationship.status == "approved"
    ).all()
    for rel in rels:
        await manager.send_personal_message(msg, rel.caregiver_id)

    return {"status": "success", "message": "Emergency alert marked as resolved.", "resolved_at": res_time_iso}
