"""
Caregiver Data Isolation Tests
================================
Covers the data-isolation fix for the caregiver dashboard fabricated-data bug.

Test matrix:
  A. Caregiver with ZERO linked patients:
     - /api/caregiver/summary    → 404 (no linked patient)
     - /api/caregiver/adherence  → 404
     - /api/caregiver/behavior   → 404
     - /api/caregiver/emergencies → 404
     - /api/medicines            → 404
     - /api/wellness/summary     → 404

  B. Caregiver with ONE approved linked elderly:
     - All above endpoints → 200 with real (zero/empty) data from the DB
     - No hardcoded values (88%, 92, Fall Detected, Amlodipine, etc.)

  C. Caregiver CANNOT access another unlinked elderly's data:
     - Sending X-Subject-Id for an unlinked elderly → 403

  D. No hardcoded demo patient data in backend service responses:
     - get_emergencies returns empty recent_triggers list
     - get_adherence returns consistency_score 0 when no meds
     - get_behavior returns empty insights list when no meds
"""

import pytest
import sys
import os
import uuid
from unittest.mock import patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models.user import User, CaregiverRelationship, AuditLog, NotificationPreferences, ConnectionCode, RateLimit
from models.medicine import MedicineReminder
from routes.caregiver import router as caregiver_router
from routes.medicine import router as medicine_router
from routes.wellness import router as wellness_router
from services import caregiver_service
from context.subject_resolver import NO_LINKED_PATIENT_SENTINEL

# ── App under test ─────────────────────────────────────────────────────────────
app = FastAPI()
app.include_router(caregiver_router, prefix="/api/caregiver")
app.include_router(medicine_router, prefix="/api/medicines")
app.include_router(wellness_router, prefix="/api/wellness")

client = TestClient(app, raise_server_exceptions=True)

# ── Test constants ─────────────────────────────────────────────────────────────
CAREGIVER_EMAIL = f"cg_isolation_{uuid.uuid4().hex[:8]}@test.com"
ELDER_EMAIL     = f"el_isolation_{uuid.uuid4().hex[:8]}@test.com"
UNLINKED_EMAIL  = f"ul_isolation_{uuid.uuid4().hex[:8]}@test.com"

CAREGIVER_ID = f"cg-{uuid.uuid4().hex[:12]}"
ELDER_ID     = f"el-{uuid.uuid4().hex[:12]}"
UNLINKED_ID  = f"ul-{uuid.uuid4().hex[:12]}"


# ── Fixtures ───────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def caregiver_user(db: Session):
    user = User(id=CAREGIVER_ID, name="Test Caregiver", email=CAREGIVER_EMAIL,
                role="caregiver", email_verified=True, hashed_password="x")
    db.add(user)
    db.commit()
    yield user
    db.query(AuditLog).filter(AuditLog.user_id == CAREGIVER_ID).delete()
    db.delete(user)
    db.commit()


@pytest.fixture(scope="module")
def elder_user(db: Session):
    user = User(id=ELDER_ID, name="Test Elder", email=ELDER_EMAIL,
                role="elderly", email_verified=True, hashed_password="x")
    db.add(user)
    db.commit()
    yield user
    db.query(MedicineReminder).filter(MedicineReminder.elder_id == ELDER_ID).delete()
    db.delete(user)
    db.commit()


@pytest.fixture(scope="module")
def unlinked_elder(db: Session):
    user = User(id=UNLINKED_ID, name="Unlinked Elder", email=UNLINKED_EMAIL,
                role="elderly", email_verified=True, hashed_password="x")
    db.add(user)
    db.commit()
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture(scope="module")
def approved_relationship(db: Session, caregiver_user, elder_user):
    rel = CaregiverRelationship(
        caregiver_id=CAREGIVER_ID,
        elder_id=ELDER_ID,
        status="approved"
    )
    db.add(rel)
    db.commit()
    yield rel
    db.delete(rel)
    db.commit()


def auth_header(user_id: str, role: str, db: Session):
    """Generate a real JWT for the given user and ensure token_version is None so it passes."""
    from services.auth_service import create_access_token
    # Reset token_version to None so JWT (which has no ver claim) is not revoked.
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.token_version = None
        db.commit()
    token = create_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════════════════════════════════════════
# A. CAREGIVER WITH ZERO LINKED PATIENTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaregiverNoLinkedPatient:
    """
    A caregiver with zero approved relationships must receive 404 (no linked patient)
    for every patient-scoped dashboard endpoint.
    No mock/fabricated data must be returned.
    """

    def test_summary_returns_404_no_linked_patient(self, caregiver_user, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/caregiver/summary", headers=headers)
        assert resp.status_code == 404, f"Expected 404 got {resp.status_code}: {resp.text}"
        assert "no_linked_patient" in resp.headers.get("x-orma-hint", "").lower() \
               or "no linked patient" in resp.json().get("detail", "").lower()

    def test_adherence_returns_404_no_linked_patient(self, caregiver_user, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/caregiver/adherence", headers=headers)
        assert resp.status_code == 404

    def test_behavior_returns_404_no_linked_patient(self, caregiver_user, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/caregiver/behavior", headers=headers)
        assert resp.status_code == 404

    def test_emergencies_returns_404_no_linked_patient(self, caregiver_user, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/caregiver/emergencies", headers=headers)
        assert resp.status_code == 404

    def test_medicines_returns_404_no_linked_patient(self, caregiver_user, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/medicines", headers=headers)
        assert resp.status_code == 404

    def test_wellness_returns_404_no_linked_patient(self, caregiver_user, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/wellness/summary", headers=headers)
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# B. CAREGIVER WITH ONE APPROVED LINKED ELDERLY — REAL DATA, NO MOCK VALUES
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaregiverWithLinkedPatient:
    """
    A caregiver with one approved relationship must receive real (zero/empty)
    data — never hardcoded mock values like 88%, 92, Fall Detected, etc.
    """

    def test_summary_returns_200_with_real_zeros(self, caregiver_user, elder_user, approved_relationship, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/caregiver/summary", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # No meds for this elder yet → all zeros
        assert data["medicines_taken"] == 0
        assert data["missed_medicines"] == 0
        assert data["pending_medicines"] == 0
        assert data["completion_percentage"] == 0

    def test_adherence_no_hardcoded_score(self, caregiver_user, elder_user, approved_relationship, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/caregiver/adherence", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # No meds → consistency_score must be 0 (not 92)
        assert data["consistency_score"] == 0, (
            f"Expected 0 (no meds), got {data['consistency_score']}. "
            "Hardcoded mock value detected."
        )
        # weekly_trends should be empty or contain only real data
        assert isinstance(data["weekly_trends"], list)

    def test_emergencies_returns_empty_not_mock(self, caregiver_user, elder_user, approved_relationship, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/caregiver/emergencies", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["recent_triggers"] == [], (
            f"Expected empty list, got: {data['recent_triggers']}. "
            "Hardcoded emergency records detected (Fall Detected / Missed multiple meds)."
        )
        assert data["total_history"] == 0

    def test_behavior_no_hardcoded_insights(self, caregiver_user, elder_user, approved_relationship, db):
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/caregiver/behavior", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # No meds → insights must be empty (not hardcoded narrative strings)
        assert data["insights"] == [], (
            f"Expected empty insights, got: {data['insights']}. "
            "Hardcoded insight strings detected."
        )
        # suspicious must be 0 (not hardcoded 1)
        assert data["confirmation_stats"]["suspicious"] == 0

    def test_no_hardcoded_medication_names_in_response(self, caregiver_user, elder_user, approved_relationship, db):
        """Backend must never return Amlodipine / Vitamin D3 / Metformin as fabricated data."""
        headers = auth_header(CAREGIVER_ID, "caregiver", db)
        resp = client.get("/api/medicines", headers=headers)
        assert resp.status_code == 200
        medicines = resp.json()
        medicine_names = [m.get("medicine_name", "").lower() for m in (medicines if isinstance(medicines, list) else [])]
        forbidden = ["amlodipine", "vitamin d3", "metformin"]
        for name in forbidden:
            assert name not in medicine_names, (
                f"Hardcoded demo medication '{name}' found in API response."
            )


# ═══════════════════════════════════════════════════════════════════════════════
# C. CAREGIVER CANNOT ACCESS UNLINKED ELDERLY VIA X-SUBJECT-ID
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaregiverCrossPatientIsolation:
    """
    A caregiver must not be able to read another elderly's data
    by supplying an arbitrary X-Subject-Id header.
    """

    def test_cannot_access_unlinked_elder_summary(self, caregiver_user, elder_user,
                                                   approved_relationship, unlinked_elder, db):
        headers = {
            **auth_header(CAREGIVER_ID, "caregiver", db),
            "X-Subject-Id": UNLINKED_ID
        }
        resp = client.get("/api/caregiver/summary", headers=headers)
        assert resp.status_code == 403, (
            f"Expected 403 for unlinked elder access, got {resp.status_code}."
        )

    def test_cannot_access_unlinked_elder_medicines(self, caregiver_user, elder_user,
                                                     approved_relationship, unlinked_elder, db):
        headers = {
            **auth_header(CAREGIVER_ID, "caregiver", db),
            "X-Subject-Id": UNLINKED_ID
        }
        resp = client.get("/api/medicines", headers=headers)
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# D. SUBJECT RESOLVER — SENTINEL BEHAVIOR
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
class TestSubjectResolverSentinel:
    """
    SubjectResolver must return NO_LINKED_PATIENT_SENTINEL (not "default_elderly" / "John")
    when a caregiver has zero approved relationships.
    Uses a fresh caregiver ID that has no relationships in the DB.
    """
    # Use IDs that are NOT the module-scoped CAREGIVER_ID (which has an approved link by now)
    FRESH_CG_ID = f"cg-fresh-{uuid.uuid4().hex[:8]}"
    FRESH_CG_EMAIL = f"cg_fresh_{uuid.uuid4().hex[:8]}@test.com"

    @pytest.fixture(autouse=True)
    def fresh_caregiver(self, db):
        user = User(id=self.FRESH_CG_ID, name="Fresh Caregiver",
                    email=self.FRESH_CG_EMAIL, role="caregiver",
                    email_verified=True, hashed_password="x", token_version=None)
        db.add(user)
        db.commit()
        yield user
        db.query(AuditLog).filter(AuditLog.user_id == self.FRESH_CG_ID).delete()
        db.delete(user)
        db.commit()

    def test_sentinel_returned_for_zero_links(self, db):
        from context.subject_resolver import SubjectResolver, NO_LINKED_PATIENT_SENTINEL
        actor = {"id": self.FRESH_CG_ID, "name": "Fresh Caregiver", "role": "caregiver"}
        result = SubjectResolver.resolve(actor, "", db_session=db)
        assert result["id"] == NO_LINKED_PATIENT_SENTINEL, (
            f"Expected sentinel, got: '{result['id']}'. "
            "Hardcoded fallback 'default_elderly' or 'John' detected."
        )

    def test_no_default_elderly_fallback(self, db):
        from context.subject_resolver import SubjectResolver
        actor = {"id": self.FRESH_CG_ID, "name": "Fresh Caregiver", "role": "caregiver"}
        result = SubjectResolver.resolve(actor, "", db_session=db)
        assert result["id"] != "default_elderly"
        assert result["name"] != "John"
        assert result["name"] != "Test11"

    def test_real_patient_resolved_when_linked(self, db, approved_relationship, elder_user):
        from context.subject_resolver import SubjectResolver, NO_LINKED_PATIENT_SENTINEL
        # Use the module-scoped CAREGIVER_ID which has one approved link
        actor = {"id": CAREGIVER_ID, "name": "Test Caregiver", "role": "caregiver"}
        result = SubjectResolver.resolve(actor, "", db_session=db)
        assert result["id"] != NO_LINKED_PATIENT_SENTINEL
        assert result["id"] == ELDER_ID
        assert result["name"] == "Test Elder"



# ═══════════════════════════════════════════════════════════════════════════════
# E. CAREGIVER SERVICE UNIT TESTS — NO MOCK DATA
# ═══════════════════════════════════════════════════════════════════════════════

class TestCaregiverServiceNoMockData:
    """
    Unit tests directly against caregiver_service functions to verify
    no hardcoded values are present.
    """

    def test_get_emergencies_always_returns_empty(self, db):
        result = caregiver_service.get_emergencies(db, elder_ids=["any-id"])
        assert result["recent_triggers"] == [], (
            "get_emergencies must return empty list — hardcoded incidents detected."
        )
        assert result["total_history"] == 0

    def test_get_emergencies_none_elder_ids_returns_empty(self, db):
        result = caregiver_service.get_emergencies(db, elder_ids=None)
        assert result["recent_triggers"] == []

    def test_get_adherence_returns_zero_for_no_meds(self, db):
        result = caregiver_service.get_adherence(db, elder_ids=[UNLINKED_ID])
        assert result["consistency_score"] == 0, (
            f"Expected 0, got {result['consistency_score']}. Hardcoded 92 detected."
        )
        assert result["confidence_average"] == 0
        assert result["missed_reminders_this_week"] == 0

    def test_get_behavior_returns_empty_insights_for_no_meds(self, db):
        result = caregiver_service.get_behavior(db, elder_ids=[UNLINKED_ID])
        assert result["insights"] == [], (
            f"Expected empty insights, got: {result['insights']}. Hardcoded strings detected."
        )
        assert result["confirmation_stats"]["suspicious"] == 0, (
            "suspicious must be 0, not hardcoded 1."
        )

    def test_get_summary_returns_zero_for_no_meds(self, db):
        result = caregiver_service.get_summary(db, elder_ids=[UNLINKED_ID])
        assert result["completion_percentage"] == 0
        assert result["medicines_taken"] == 0
