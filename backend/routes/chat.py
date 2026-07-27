from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from intelligence.orchestrator import orchestrator

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    language_preference: str = "auto"
    detected_language: str = "en"

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def send_message(request_payload: ChatRequest, request: Request, db: Session = Depends(get_db)):
    """
    Endpoint to send user text to the AI and get a conversational response.
    """
    if not request_payload.message or not request_payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        active_subject_id = request.headers.get("x-subject-id")
        
        reply = await orchestrator.process_request(
            text=request_payload.message,
            user_id=request_payload.user_id,
            db=db,
            language=request_payload.language_preference if request_payload.language_preference != "auto" else request_payload.detected_language,
            active_subject_id=active_subject_id
        )
        return ChatResponse(response=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
