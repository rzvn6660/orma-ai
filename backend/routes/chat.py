from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from intelligence.orchestrator import orchestrator
from dependencies import get_current_context

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    language_preference: str = "auto"
    detected_language: str = "en"

class ChatResponse(BaseModel):
    response: str

@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
async def send_message(request_payload: ChatRequest, request: Request, db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Endpoint to send user text to the AI and get a conversational response.
    Uses authenticated user context & resolved subject from JWT.
    """
    if not request_payload.message or not request_payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        actor = ctx.get('authenticated_user')
        subject = ctx.get('resolved_subject')
        active_subject_id = subject["id"] if subject else None

        user_id = str(actor.id) if actor else (request_payload.user_id or "default_user")

        reply = await orchestrator.process_request(
            text=request_payload.message,
            user_id=user_id,
            db=db,
            language=request_payload.language_preference if request_payload.language_preference != "auto" else request_payload.detected_language,
            active_subject_id=active_subject_id
        )
        return ChatResponse(response=reply)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[CHAT ERROR] send_message failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

