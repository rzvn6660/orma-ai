import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_context
from services.insights_service import generate_insights_summary

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/summary")
def get_insights_summary(db: Session = Depends(get_db), ctx: dict = Depends(get_current_context)):
    """
    Retrieve evidence-based insights summary for the active subject.
    """
    subject = ctx['resolved_subject']
    try:
        return generate_insights_summary(db, subject["id"])
    except Exception as e:
        logger.error(f"[INSIGHTS ERROR] generate_insights_summary failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights summary.")
