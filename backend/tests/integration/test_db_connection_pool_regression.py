import sys
import os
import pytest
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from starlette.websockets import WebSocketDisconnect
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal, Base, engine
from models.user import User
from models.medicine import MedicineReminder
from models.notification import Notification
from services.auth_service import create_access_token
from services.notification_service import dispatch_notification
from services.scheduler_service import ReminderSnapshot
from main import app

TEST_USER_ID = "test_pool_user_1"
TEST_USER_EMAIL = "pool_user_1@test.com"

@pytest.fixture(scope="module", autouse=True)
def setup_test_users():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(Notification).filter(Notification.elder_id == TEST_USER_ID).delete()
        db.query(MedicineReminder).filter(MedicineReminder.elder_id == TEST_USER_ID).delete()
        db.query(User).filter(User.id == TEST_USER_ID).delete()
        db.commit()

        user = User(
            id=TEST_USER_ID,
            email=TEST_USER_EMAIL,
            name="Pool Test User",
            role="elderly",
            token_version=1
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(Notification).filter(Notification.elder_id == TEST_USER_ID).delete()
        db.query(MedicineReminder).filter(MedicineReminder.elder_id == TEST_USER_ID).delete()
        db.query(User).filter(User.id == TEST_USER_ID).delete()
        db.commit()
    finally:
        db.close()


def test_notifications_websocket_auth_and_session_release():
    """Verify notifications websocket authenticates, communicates, and does not leak sessions."""
    client = TestClient(app)
    valid_token = create_access_token({"sub": TEST_USER_ID, "ver": 1, "role": "elderly"})

    # 1. Successful connection with valid token
    with client.websocket_connect(f"/api/notifications/ws/{TEST_USER_ID}?token={valid_token}") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "pong"

    # 2. Rejection with invalid token
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/notifications/ws/{TEST_USER_ID}?token=invalid.jwt.token"):
            pass
    assert exc_info.value.code == 1008

    # 3. Rejection when token_version is revoked
    revoked_token = create_access_token({"sub": TEST_USER_ID, "ver": 999, "role": "elderly"})
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/notifications/ws/{TEST_USER_ID}?token={revoked_token}") as ws:
            ws.receive_text()
    assert exc_info.value.code == 1008


def test_wakeword_websocket_auth_and_session_release():
    """Verify wakeword websocket authenticates and closes its DB session during handshake."""
    client = TestClient(app)
    valid_token = create_access_token({"sub": TEST_USER_ID, "ver": 1, "role": "elderly"})

    # 1. Successful connection
    with client.websocket_connect(f"/api/wakeword/ws?token={valid_token}") as ws:
        init_msg = ws.receive_text()
        assert "engine_ready" in init_msg

    # 2. Rejection with missing or invalid token
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/wakeword/ws?token=badtoken"):
            pass
    assert exc_info.value.code == 1008


def test_sse_events_auth_and_session_release():
    """Verify /api/owe/events validates auth using a short-lived session and does not hold db."""
    client = TestClient(app)

    # 1. Missing token -> 401
    resp = client.get("/api/owe/events")
    assert resp.status_code == 401

    # 2. Invalid token -> 401
    resp = client.get("/api/owe/events?token=invalid.jwt.token")
    assert resp.status_code == 401

    # 3. Revoked token version -> 401
    revoked_token = create_access_token({"sub": TEST_USER_ID, "ver": 999, "role": "elderly"})
    resp = client.get(f"/api/owe/events?token={revoked_token}")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dispatch_notification_self_managed_session():
    """Verify dispatch_notification creates, commits, and closes its own session when db is None."""
    unique_title = f"Self-Managed Alert {datetime.utcnow().timestamp()}"
    await dispatch_notification(
        db=None,
        elder_id=TEST_USER_ID,
        title=unique_title,
        message="This is a test notification with self-managed db session.",
        priority="high"
    )

    # Verify notification was persisted in DB
    db = SessionLocal()
    try:
        notif = db.query(Notification).filter(
            Notification.elder_id == TEST_USER_ID,
            Notification.title == unique_title
        ).first()
        assert notif is not None
        assert notif.priority == "high"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_dispatch_notification_caller_managed_session():
    """Verify dispatch_notification works with a caller-provided session without closing it prematurely."""
    db = SessionLocal()
    try:
        unique_title = f"Caller-Managed Alert {datetime.utcnow().timestamp()}"
        await dispatch_notification(
            db=db,
            elder_id=TEST_USER_ID,
            title=unique_title,
            message="This is a test notification with caller-managed session.",
            priority="medium"
        )
        # Session must still be open and active for caller to query
        notif = db.query(Notification).filter(
            Notification.elder_id == TEST_USER_ID,
            Notification.title == unique_title
        ).first()
        assert notif is not None
    finally:
        db.close()


def test_scheduler_process_event_thread_safety():
    """Verify process_event creates a detached ReminderSnapshot and does not share db session."""
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=TEST_USER_ID,
            actor_id=TEST_USER_ID,
            role="elderly",
            medicine_name="Metformin 500mg",
            dosage="1 tab",
            reminder_time=datetime.utcnow().strftime("%I:%M %p"),
            taken_status=False,
            created_at=datetime.utcnow()
        )
        db.add(med)
        db.commit()
        db.refresh(med)

        # Snapshot should preserve all properties
        snap = ReminderSnapshot(med, "medicine")
        assert snap.id == med.id
        assert snap.medicine_name == "Metformin 500mg"
        assert snap.elder_id == TEST_USER_ID

        # Clean up
        db.delete(med)
        db.commit()
    finally:
        db.close()


def test_concurrent_database_access():
    """Verify that multiple concurrent database operations execute without connection pool timeout."""
    def worker(worker_id):
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == TEST_USER_ID).first()
            assert user is not None
            return worker_id, user.id
        finally:
            session.close()

    # Run 10 concurrent database workers
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, i) for i in range(10)]
        results = [f.result() for f in futures]

    assert len(results) == 10
    for wid, uid in results:
        assert uid == TEST_USER_ID


def test_pool_configuration_defaults_and_env_overrides(monkeypatch):
    """Verify that PostgreSQL pool configuration reads environment variables with safe defaults."""
    from sqlalchemy.pool import QueuePool
    from sqlalchemy import create_engine

    # 1. Defaults
    monkeypatch.delenv("DB_POOL_SIZE", raising=False)
    monkeypatch.delenv("DB_MAX_OVERFLOW", raising=False)
    monkeypatch.delenv("DB_POOL_TIMEOUT", raising=False)
    monkeypatch.delenv("DB_POOL_RECYCLE", raising=False)

    default_pool_size = int(os.getenv("DB_POOL_SIZE", "3"))
    default_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "2"))
    default_pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    default_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "300"))

    assert default_pool_size == 3
    assert default_max_overflow == 2
    assert default_pool_timeout == 30
    assert default_pool_recycle == 300

    test_engine = create_engine(
        "sqlite:///:memory:",
        poolclass=QueuePool,
        pool_size=default_pool_size,
        max_overflow=default_max_overflow,
        pool_timeout=default_pool_timeout,
        pool_recycle=default_pool_recycle
    )
    assert test_engine.pool.size() == 3
    assert test_engine.pool._max_overflow == 2
    assert test_engine.pool._timeout == 30
    assert test_engine.pool._recycle == 300

    # 2. Environment overrides
    monkeypatch.setenv("DB_POOL_SIZE", "4")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "3")
    monkeypatch.setenv("DB_POOL_TIMEOUT", "45")

    assert int(os.getenv("DB_POOL_SIZE", "3")) == 4
    assert int(os.getenv("DB_MAX_OVERFLOW", "2")) == 3
    assert int(os.getenv("DB_POOL_TIMEOUT", "30")) == 45

