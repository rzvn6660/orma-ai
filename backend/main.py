from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from services.scheduler_service import start_scheduler
from routes import health, speech, chat, medicine, memory, emergency
from database import engine, Base
import models.medicine # Ensure model is imported before create_all
import models.memory # Ensure memory model is imported

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

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
app.include_router(memory.router, prefix="/api/memory", tags=["Memory System"])
app.include_router(emergency.router, prefix="/api/emergency", tags=["Emergency System"])

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