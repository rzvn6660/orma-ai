from pydantic import BaseModel
from ochr.context.context_models import UnifiedContext
from .medical_context import MedicalContext

class HybridContext(BaseModel):
    """
    Strict separation between personal and medical knowledge contexts.
    """
    personal_context: UnifiedContext
    medical_context: MedicalContext
