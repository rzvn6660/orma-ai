import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from main import app
from database import get_db, Base, SessionLocal, engine, ensure_schema_migrations
from models.user import User, NotificationPreferences
from dependencies import get_current_user

ensure_schema_migrations()
TestingSessionLocal = SessionLocal

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user(db = Depends(override_get_db)):
    u = db.query(User).filter(User.id == "elder_lang_user_1").first()
    if not u:
        u = User(
            id="elder_lang_user_1",
            email="elderlang@orma.test",
            hashed_password="hash",
            role="elderly",
            name="Grandma Mary"
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    db = TestingSessionLocal()
    db.query(NotificationPreferences).delete()
    db.query(User).delete()
    
    user = User(
        id="elder_lang_user_1",
        email="elderlang@orma.test",
        hashed_password="hash",
        role="elderly",
        name="Grandma Mary"
    )
    db.add(user)
    db.commit()
    yield
    db.close()

def test_default_reminder_language_is_en_in():
    res = client.get("/api/notifications/preferences")
    assert res.status_code == 200
    data = res.json()
    assert data["reminder_language"] == "en-IN"

def test_update_reminder_language_to_malayalam():
    res = client.put("/api/notifications/preferences", json={"reminder_language": "ml-IN"})
    assert res.status_code == 200
    data = res.json()
    assert data["reminder_language"] == "ml-IN"

    # Verify GET persistence
    res_get = client.get("/api/notifications/preferences")
    assert res_get.status_code == 200
    assert res_get.json()["reminder_language"] == "ml-IN"

def test_update_reminder_language_to_arabic_and_hindi():
    client.put("/api/notifications/preferences", json={"reminder_language": "hi-IN"})
    assert client.get("/api/notifications/preferences").json()["reminder_language"] == "hi-IN"

    client.put("/api/notifications/preferences", json={"reminder_language": "ar-SA"})
    assert client.get("/api/notifications/preferences").json()["reminder_language"] == "ar-SA"