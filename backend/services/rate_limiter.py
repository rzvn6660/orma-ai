import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from models.user import RateLimit

logger = logging.getLogger(__name__)

def get_client_ip(request: Request) -> str:
    """
    Safely resolves the client IP address from the request.
    Handles forwarded proxy headers and falls back to socket connection host.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip.strip():
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host.strip()

    return "127.0.0.1"


def enforce_rate_limit(
    db: Session,
    identifier: str,
    action: str,
    max_requests: int,
    window_seconds: int,
    error_message: Optional[str] = None
) -> None:
    """
    Database-backed rate limiter using the existing RateLimit model.
    Enforces a sliding or fixed-window rate limit per (identifier, action).
    If exceeded, raises an HTTP 429 Too Many Requests exception with a Retry-After header.
    """
    now = datetime.utcnow()
    key = f"{action}:{identifier}"

    rate = db.query(RateLimit).filter(
        RateLimit.user_id == key,
        RateLimit.action == action
    ).first()

    if rate:
        elapsed = (now - rate.window_start).total_seconds()
        if elapsed < window_seconds:
            if rate.attempts >= max_requests:
                retry_after = max(1, int(window_seconds - elapsed))
                msg = error_message or f"Too many {action.replace('_', ' ')} requests. Please try again in {retry_after} seconds."
                logger.warning(f"[RATE_LIMIT] Blocked request for {key} (action={action}, attempts={rate.attempts}/{max_requests})")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=msg,
                    headers={"Retry-After": str(retry_after)}
                )
            rate.attempts += 1
        else:
            # Window expired, reset
            rate.window_start = now
            rate.attempts = 1
    else:
        rate = RateLimit(
            user_id=key,
            action=action,
            attempts=1,
            window_start=now
        )
        db.add(rate)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[RATE_LIMIT] Failed to persist rate limit for {key}: {e}")
