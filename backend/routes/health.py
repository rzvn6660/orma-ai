from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from database import engine, DB_PATH
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check route to verify backend process, database connectivity, and storage availability.
    Used by orchestrators (Render/Docker) and frontend to confirm service availability.
    """
    db_ok = False
    storage_ok = False

    # 1. Verify Database Connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        db_ok = True
    except Exception as e:
        logger.error(f"[HEALTH-CHECK ERROR] Database probe failed: {type(e).__name__}")

    # 2. Verify Storage Availability (local filesystem check for SQLite; remote managed for PostgreSQL)
    if engine.dialect.name == "sqlite":
        try:
            db_dir = os.path.dirname(os.path.abspath(DB_PATH))
            if os.path.exists(db_dir) and os.access(db_dir, os.W_OK):
                storage_ok = True
        except Exception as e:
            logger.error(f"[HEALTH-CHECK ERROR] SQLite storage probe failed: {type(e).__name__}")
    else:
        # For PostgreSQL/Supabase, database storage durability is managed remotely
        storage_ok = True

    is_healthy = db_ok and storage_ok
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    payload = {
        "status": "online" if is_healthy else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "storage": "writable" if storage_ok else "unavailable",
        "service": "Orma AI Core"
    }
    return JSONResponse(status_code=status_code, content=payload)
