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
        "model_path": wakeword_service.model_path,
        "file_exists": wakeword_service.file_exists,
        "engine_loaded": wakeword_service.is_ready,
        "load_error_message": wakeword_service.load_error
    }

import asyncio

@router.websocket("/ws")
async def wakeword_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WakeWord client connected")
    await websocket.send_text(json.dumps({"event": "engine_ready", "loaded": wakeword_service.is_ready}))
    is_first_chunk = True
    try:
        while True:
            data = await websocket.receive_bytes()
            if is_first_chunk:
                print("Wake-word listening")
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
                print("Wake word detected")
                # Send detection event back to frontend
                await websocket.send_text(json.dumps({
                    "event": "wake_word_detected",
                    "confidence": result["confidence"]
                }))
            else:
                print("Wake word detection failed")
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Wake-Word WebSocket error: {e}")
