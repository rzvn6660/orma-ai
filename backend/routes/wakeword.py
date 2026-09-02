from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File
from services.wakeword_service import wakeword_service
import json

router = APIRouter()

@router.post("/test")
async def test_wakeword(file: UploadFile = File(...)):
    audio_data = await file.read()
    result = wakeword_service.process_audio_chunk(audio_data, threshold=0.5)
    return {
        "confidence_score": result["confidence"],
        "detection_result": "detection" if result["detected"] else "no detection",
        "model_used": "hey_orma.onnx"
    }

@router.get("/status")
async def get_wakeword_status():
    return {
        "status": wakeword_service.mode,
        "mode": wakeword_service.mode,
        "model_name": wakeword_service.model_name,
        "model_path": wakeword_service.model_path,
        "file_exists": wakeword_service.file_exists,
        "engine_loaded": wakeword_service.is_ready,
        "load_error_message": wakeword_service.load_error
    }

import asyncio

import time
from fastapi import status

MAX_WAKEWORD_CHUNK_SIZE = 65536  # 64 KB max per audio chunk
MAX_CHUNKS_PER_SECOND = 40

@router.websocket("/ws")
async def wakeword_endpoint(websocket: WebSocket):
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
    except Exception as e:
        pass
