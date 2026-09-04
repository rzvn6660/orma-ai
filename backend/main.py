from dotenv import load_dotenv
import os
from pathlib import Path
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)  # Load backend/.env before anything else

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from services.scheduler_service import start_scheduler, stop_scheduler
from routes import health, speech, chat, medicine, memory, emergency, caregiver, wellness, auth, caregiver_link, notifications, wakeword, health_records, health_planner, ocme, ale, rlj, owe, tsgp, reports, insights, documents
from database import engine, Base
import models.health_event
import models.medicine # Ensure model is imported before create_all
import models.memory # Ensure memory model is imported
import models.wellness
import models.notification
import models.health_record
from rag import rag_models # RAG Document models
from memory import memory_models # OCME Memory models
import models.ale # Adaptive Learning Engine models
import models.rlj # Reflection & Life Journal Engine models
import models.owe # Action & Workflow Engine models
import models.tsgp # Trust, Safety & Clinical Governance Platform models
import models.emergency # Emergency Alert models

# Create database tables
Base.metadata.create_all(bind=engine)

def run_db_migrations():
    if engine.dialect.name != "sqlite":
        return
    import sqlite3
    try:
        from database import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cur.fetchall()]
        if "phone" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN phone TEXT;")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[MIGRATION WARNING]: {e}")

run_db_migrations()

import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    start_scheduler(loop=loop)
    try:
        yield
    finally:
        stop_scheduler()

# Initialize FastAPI app
app = FastAPI(
    title="Orma AI Backend",
    description="Backend services for the Orma AI healthcare assistant.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
# In production, strictly enforce explicit origins from FRONTEND_URL and ALLOWED_ORIGINS.
# In development/test mode, allow localhost and 127.0.0.1 for local developer workflows.
env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()

allowed_origins_list = []
allow_origin_regex = None

if env_mode == "production":
    for env_key in ("FRONTEND_URL", "ALLOWED_ORIGINS"):
        val = os.getenv(env_key)
        if val:
            for url in val.split(","):
                cleaned = url.strip().rstrip("/")
                if cleaned and cleaned not in allowed_origins_list:
                    allowed_origins_list.append(cleaned)
    # Never allow localhost, 127.0.0.1, or regex wildcards in production
else:
    # Development and test environment defaults
    allowed_origins_list = [
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:8000", "http://127.0.0.1:8000"
    ]
    for env_key in ("FRONTEND_URL", "ALLOWED_ORIGINS"):
        val = os.getenv(env_key)
        if val:
            for url in val.split(","):
                cleaned = url.strip().rstrip("/")
                if cleaned and cleaned not in allowed_origins_list:
                    allowed_origins_list.append(cleaned)
    allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

cors_kwargs = {
    "allow_origins": allowed_origins_list,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"]
}
if allow_origin_regex:
    cors_kwargs["allow_origin_regex"] = allow_origin_regex

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Security Response Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
    if env_mode == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Include API routes
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(speech.router, prefix="/api/speech", tags=["Speech Recognition"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Conversation"])
app.include_router(medicine.router, prefix="/api/medicines", tags=["Medicine Reminders"])
app.include_router(memory.router, prefix="/api/memory", tags=["Legacy Memory System"])
app.include_router(ocme.router, prefix="/api/ocme", tags=["OCME Memory System"])
app.include_router(ocme.router, prefix="/api/ocme/ocme", tags=["OCME Memory System Compatibility Alias"])
app.include_router(emergency.router, prefix="/api/emergency", tags=["Emergency System"])
app.include_router(caregiver.router, prefix="/api/caregiver", tags=["Caregiver Dashboard"])
app.include_router(wellness.router, prefix="/api/wellness", tags=["Wellness & Confusion"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(caregiver_link.router, prefix="/api/link", tags=["Caregiver Linking"])
app.include_router(caregiver_link.router, prefix="/api/caregiver-link", tags=["Caregiver Linking Alias"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Real-time Notifications"])
app.include_router(wakeword.router, prefix="/api/wakeword", tags=["Wake Word"])
app.include_router(health_records.router, prefix="/api/health-records", tags=["Health Records"])
app.include_router(health_planner.router, prefix="/api/health-planner", tags=["Health Planner"])
app.include_router(ale.router, prefix="/api", tags=["Adaptive Learning Engine"])
app.include_router(rlj.router, prefix="/api", tags=["Reflection & Life Journal"])
app.include_router(owe.router, prefix="/api", tags=["Action & Workflow Engine"])
app.include_router(tsgp.router, prefix="/api", tags=["Trust, Safety & Clinical Governance"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(insights.router, prefix="/api/insights", tags=["AI Insights"])
app.include_router(documents.router, prefix="/api/documents", tags=["RAG Documents"])

from fastapi.responses import Response

# Root route
@app.get("/")
def home():
    """
    Root endpoint.
    """
    return {"message": "Orma AI Backend Running"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/status")
def status():
    """
    Test endpoint.
    """
    return {
        "status": "Backend Connected Successfully"
    }

# Placeholder stubs for future modules to maintain modularity:
# app.include_router(medicine.router, prefix="/api/medicine", tags=["Medicine Reminders"])
# app.include_router(memory.router, prefix="/api/memory", tags=["Memory System"])
# app.include_router(emergency.router, prefix="/api/emergency", tags=["Emergency Detection"])