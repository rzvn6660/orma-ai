import pytest
from models.memory import MemoryEvent
from models.health_event import HealthEvent
from models.medicine import MedicineReminder
from models.owe import WorkflowAuditLog
from models.audit import AuditLog
from models.notification import Notification
from context.permission_manager import PermissionManager

def test_asif_memory_ownership():
    mem = MemoryEvent(actor_id="c1", subject_id="e1", created_by="c1", owned_by="e1", visibility="shared")
    assert mem.actor_id == "c1"
    assert mem.subject_id == "e1"
    assert mem.owned_by == "e1"

def test_asif_reminder_ownership():
    reminder = MedicineReminder(actor_id="c1", subject_id="e1", created_by="c1", owned_by="e1")
    assert reminder.subject_id == "e1"
    assert reminder.owned_by == "e1"

def test_asif_planner_ownership():
    planner = HealthEvent(actor_id="c1", subject_id="e1", created_by="c1", owned_by="e1")
    assert planner.subject_id == "e1"

def test_asif_workflow_ownership():
    workflow = WorkflowAuditLog(actor_id="sys", subject_id="e1")
    assert workflow.subject_id == "e1"

def test_asif_audit_ownership():
    audit = AuditLog(actor_id="c1", subject_id="e1", action="read", resource="memory")
    assert audit.action == "read"
    assert audit.resource == "memory"
    assert audit.actor_id == "c1"

def test_asif_notification_ownership():
    notif = Notification(actor_id="c1", subject_id="e1", message="Reminder")
    assert notif.actor_id == "c1"

def test_caregiver_permissions():
    assert PermissionManager.can("caregiver", "add_medicine")
    assert PermissionManager.canWrite("caregiver", "medicine") == False # Since we mapped specific actions not wildcard. Wait, earlier we used canWrite logic. Let's check.

def test_elderly_permissions():
    assert PermissionManager.can("elderly", "manage_own_health")
    
def test_doctor_permissions():
    assert PermissionManager.can("doctor", "view_patient")
