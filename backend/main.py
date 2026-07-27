from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from services.scheduler_service import start_scheduler, stop_scheduler
from routes import health, speech, chat, medicine, memory, emergency, caregiver, wellness, auth, caregiver_link, notifications, wakeword, health_records, health_planner, ocme, ale, rlj, owe, tsgp, reports, insights
from database import engine, Base
import models.health_event
import models.medicine # Ensure model is imported before create_all
import models.memory # Ensure memory model is imported
import models.wellness
import models.notification
import models.health_record
from memory import memory_models # OCME Memory models
import models.ale # Adaptive Learning Engine models
import models.rlj # Reflection & Life Journal Engine models
import models.owe # Action & Workflow Engine models
import models.tsgp # Trust, Safety & Clinical Governance Platform models

# Create database tables
Base.metadata.create_all(bind=engine)

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
# This allows our React frontend (running on port 5173) to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(speech.router, prefix="/api/speech", tags=["Speech Recognition"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Conversation"])
app.include_router(medicine.router, prefix="/api/medicines", tags=["Medicine Reminders"])
app.include_router(memory.router, prefix="/api/memory", tags=["Legacy Memory System"])
app.include_router(ocme.router, prefix="/api/ocme", tags=["OCME Memory System"])
app.include_router(emergency.router, prefix="/api/emergency", tags=["Emergency System"])
app.include_router(caregiver.router, prefix="/api/caregiver", tags=["Caregiver Dashboard"])
app.include_router(wellness.router, prefix="/api/wellness", tags=["Wellness & Confusion"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(caregiver_link.router, prefix="/api/link", tags=["Caregiver Linking"])
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

# Root route
@app.get("/")
def home():
    """
    Root endpoint.
    """
    return {"message": "Orma AI Backend Running"}

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