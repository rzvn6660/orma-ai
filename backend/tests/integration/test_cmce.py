import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
import pytest
from models.user import User
from context.context_resolver import ContextResolver
from context.permission_manager import PermissionManager
from models.memory import MemoryEvent
from models.health_record import HealthRecord

def test_elderly_conversation_resolution():
    class MockElderly:
        id = "e1"
        name = "John"
        role = "elderly"
    
    ctx = ContextResolver.resolve(MockElderly(), "Did I take my medicine?", None)
    
    assert ctx.actor_id == "e1"
    assert ctx.actor_role == "elderly"
    assert ctx.subject_id == "e1"
    assert ctx.subject_role == "elderly"
    assert not ctx.requires_clarification
    assert "manage_own_health" in ctx.permissions

def test_caregiver_conversation_resolution():
    class MockCaregiver:
        id = "c1"
        name = "Sarah"
        role = "caregiver"
        
    # Unambiguous
    ctx = ContextResolver.resolve(MockCaregiver(), "Did John take his medicine?", None)
    
    assert ctx.actor_id == "c1"
    assert ctx.actor_role == "caregiver"
    assert ctx.subject_id == "default_elderly"
    assert ctx.subject_name == "John"
    assert not ctx.requires_clarification
    assert "add_medicine" in ctx.permissions

def test_ambiguous_pronouns_clarification():
    class MockCaregiver:
        id = "c1"
        name = "Sarah"
        role = "caregiver"
        
    # Ambiguous
    ctx = ContextResolver.resolve(MockCaregiver(), "Did I take my medicine?", None)
    
    assert ctx.requires_clarification is True
    assert "Are you referring to your own health" in ctx.clarification_message

def test_doctor_conversation_resolution():
    class MockDoctor:
        id = "d1"
        name = "Dr. Ahmed"
        role = "doctor"
        
    # Ambiguous
    ctx1 = ContextResolver.resolve(MockDoctor(), "Show me the records", None)
    assert ctx1.actor_role == "doctor"
    assert ctx1.requires_clarification is True  # Should prompt which patient
    assert "Which patient" in ctx1.clarification_message

    # Clear
    ctx2 = ContextResolver.resolve(MockDoctor(), "Show me John's records", None)
    assert ctx2.subject_name == "John"
    assert ctx2.requires_clarification is False

def test_memory_ownership_fields():
    mem = MemoryEvent(
        owned_by="e1",
        created_by="c1",
        visibility="shared",
        content="John's daughter visited"
    )
    assert mem.owned_by == "e1"
    assert mem.created_by == "c1"
    assert mem.visibility == "shared"

def test_health_record_ownership_fields():
    hr = HealthRecord(
        subject_id="e1",
        created_by="c1",
        source="Caregiver",
        vital_type="blood_pressure"
    )
    assert hr.subject_id == "e1"
    assert hr.created_by == "c1"
    assert hr.source == "Caregiver"
