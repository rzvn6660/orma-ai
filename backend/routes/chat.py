from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import get_db
from intelligence.orchestrator import orchestrator
from intelligence.conversation_manager import conversation_manager
from dependencies import get_current_context

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    language_preference: str = "auto"
    detected_language: str = "en"
    history: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    response: str
    language: Optional[str] = "en"

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

        # Sync recent history from client if available and session history is empty
        if request_payload.history and isinstance(request_payload.history, list):
            existing = conversation_manager.get_history(user_id)
            if not existing:
                for h_item in request_payload.history:
                    if isinstance(h_item, dict) and "role" in h_item and "content" in h_item:
                        conversation_manager.add_message(user_id, h_item["role"], h_item["content"])

        raw_pref = request_payload.language_preference
        raw_det = request_payload.detected_language
        lang_cand = raw_pref if raw_pref != "auto" else raw_det
        from services.transcription_service import normalize_language_code
        lang_to_use = normalize_language_code(lang_cand) or "en"

        import logging
        chat_logger = logging.getLogger(__name__)
        chat_logger.info(
            f"[CHAT DIAGNOSTIC] preference='{raw_pref}' | "
            f"detected='{raw_det}' | "
            f"effective_lang='{lang_to_use}' | "
            f"msg_preview='{request_payload.message[:40]}'"
        )

        detailed = await orchestrator.process_request_detailed(
            text=request_payload.message,
            user_id=user_id,
            db=db,
            language=lang_to_use,
            active_subject_id=active_subject_id
        )
        return ChatResponse(
            response=detailed["response"],
            language=detailed.get("language", "en")
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[CHAT ERROR] send_message failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@router.post("/reset")
@router.post("/clear")
async def reset_conversation(request: Request, ctx: dict = Depends(get_current_context)):
    """Resets conversational short-term context and history for the active session."""
    actor = ctx.get('authenticated_user')
    user_id = str(actor.id) if actor else "default_user"
    conversation_manager.clear_session(user_id)
    return {"status": "success", "message": "Conversation session cleared."}

