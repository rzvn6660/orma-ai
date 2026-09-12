import sys
import os
from pathlib import Path
import pytest

# Add backend directory to sys.path for pytest discovery
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models.user import RateLimit


@pytest.fixture(autouse=True)
def isolate_rate_limits():
    """
    Ensure rate-limit database state is isolated between tests so
    unrelated tests cannot consume each other's quota (e.g. signup rate limit).
    """
    db = SessionLocal()
    try:
        db.query(RateLimit).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(RateLimit).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
