from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check route to verify backend status.
    Used by the frontend to confirm connection.
    """
    return {
        "status": "online",
        "message": "Backend Connected Successfully",
        "service": "Orma AI Core"
    }
