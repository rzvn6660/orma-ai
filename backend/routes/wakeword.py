import os
import json
import asyncio
import time
from typing import Optional
import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models.user import User
from dependencies import get_current_user, SECRET_KEY, ALGORITHM
from services.wakeword_service import wakeword_service

router = APIRouter()

@router.post("/test")
async def test_wakeword(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
    if env_mode == "production":
        raise HTTPException(status_code=404, detail="Test endpoints are disabled in production.")

    audio_data = await file.read()
    result = wakeword_service.process_audio_chunk(audio_data, threshold=0.5)
    return {
        "confidence_score": result["confidence"],
        "detection_result": "detection" if result["detected"] else "no detection",
        "model_used": "hey_orma.onnx"
    }

@router.get("/status")
async def get_wakeword_status(current_user: User = Depends(get_current_user)):
    return {
        "status": wakeword_service.mode,
        "mode": wakeword_service.mode,
        "model_name": wakeword_service.model_name,
        "file_exists": wakeword_service.file_exists,
        "engine_loaded": wakeword_service.is_ready,
    }

MAX_WAKEWORD_CHUNK_SIZE = 65536  # 64 KB max per audio chunk
MAX_CHUNKS_PER_SECOND = 40

@router.websocket("/ws")
async def wakeword_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    # Resolve token from query parameter or authorization header
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_sub = payload.get("sub")
        if not token_sub:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == str(token_sub)).first()
            if not user or not getattr(user, "is_active", True):
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            # Check token version revocation
            token_ver = payload.get("ver")
            if getattr(user, "token_version", None) is not None:
                if token_ver is None or token_ver != user.token_version:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return
        finally:
            db.close()
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await websocket.send_text(json.dumps({"event": "engine_ready", "loaded": wakeword_service.is_ready}))
    is_first_chunk = True
    chunk_counter = 0
    second_start = time.time()

    try:
        while True:
            data = await websocket.receive_bytes()
            
            # 1. Enforce payload size limit
            if len(data) > MAX_WAKEWORD_CHUNK_SIZE:
                await websocket.close(code=status.WS_1009_MESSAGE_TOO_BIG)
                break
                
            # 2. Enforce frequency throttling
            chunk_counter += 1
            now = time.time()
            if now - second_start >= 1.0:
                chunk_counter = 1
                second_start = now
            elif chunk_counter > MAX_CHUNKS_PER_SECOND:
                # Rate limit exceeded — slight pause or close
                await asyncio.sleep(0.05)

            if is_first_chunk:
                is_first_chunk = False
            
            result = await asyncio.to_thread(wakeword_service.process_audio_chunk, data, 0.5)
            
            # Send status update for the debug panel
            await websocket.send_text(json.dumps({
                "event": "wake_word_status",
                "confidence": result["confidence"],
                "threshold": 0.5,
                "result": "detection" if result["detected"] else "no detection",
                "model_name": "hey_orma.onnx",
                "engine_loaded": wakeword_service.is_ready,
                "chunk_size": len(data)
            }))
            
            if result["detected"]:
                # Send detection event back to frontend
                await websocket.send_text(json.dumps({
                    "event": "wake_word_detected",
                    "confidence": result["confidence"]
                }))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
