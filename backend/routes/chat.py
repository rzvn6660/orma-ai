from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from ai.conversation import conversation_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    language: str = "en"

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint to send user text to the AI and get a conversational response.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        reply = await conversation_service.generate_response(
            text=request.message,
            user_id=request.user_id,
            language=request.language,
            db=db
        )
        return ChatResponse(response=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
