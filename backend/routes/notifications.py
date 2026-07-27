from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from database import get_db
from models.notification import Notification
from models.user import User
from dependencies import get_current_user, SECRET_KEY, ALGORITHM
from services.websocket_manager import manager
import jwt

router = APIRouter()

@router.get("/")
def get_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.caregiver_id == current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    return [{"id": n.id, "title": n.title, "message": n.message, "priority": n.priority, "is_read": n.is_read, "created_at": n.created_at.isoformat()} for n in notifs]

@router.post("/{notif_id}/read")
def mark_read(notif_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.caregiver_id == current_user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "success"}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = Query(None)):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_user_id: str = payload.get("sub")
        if token_user_id != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except jwt.PyJWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_id)
    print("Notification WebSocket Connected")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
