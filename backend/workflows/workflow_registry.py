import logging
from typing import Dict, Callable
from workflows.templates import medicine_workflow, appointment_workflow, emergency_workflow

logger = logging.getLogger(__name__)

class WorkflowRegistry:
    """
    Maps events to workflow templates.
    """
    def __init__(self):
        self._registry: Dict[str, Callable] = {
            "MedicineCreated": medicine_workflow,
            "MedicineModified": medicine_workflow,
            "AppointmentCreated": appointment_workflow,
            "AppointmentRescheduled": appointment_workflow,
            "EmergencyDetected": emergency_workflow,
        }

    def get_workflow(self, event_name: str) -> Callable:
        return self._registry.get(event_name)

workflow_registry = WorkflowRegistry()
