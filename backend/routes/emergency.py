from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.emergency_service import analyze_text_for_emergency, trigger_alert

router = APIRouter()

class EmergencyRequest(BaseModel):
    text: str
    user_id: str = "default_user"

class EmergencyResponse(BaseModel):
    is_emergency: bool
    triggered_keywords: List[str]
    severity: str
    message: str

@router.post("/analyze", response_model=EmergencyResponse)
def analyze_emergency(request: EmergencyRequest):
    """
    Analyze text for emergency keywords and trigger an alert if detected.
    """
    result = analyze_text_for_emergency(request.text)
    
    if result["is_emergency"]:
        trigger_alert(
            user_id=request.user_id,
            text=request.text,
            triggered_keywords=result["triggered_keywords"]
        )
        
    return EmergencyResponse(
        is_emergency=result["is_emergency"],
        triggered_keywords=result["triggered_keywords"],
        severity=result.get("severity", "low"),
        message=result.get("message", "")
    )
