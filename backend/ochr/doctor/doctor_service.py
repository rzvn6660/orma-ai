import logging
from ochr.context.context_models import UnifiedContext
from .doctor_models import DoctorSummary
from .doctor_summary_engine import DoctorSummaryEngine

logger = logging.getLogger(__name__)

class DoctorService:
    def __init__(self):
        self.engine = DoctorSummaryEngine()
        logger.info("DoctorService initialized.")

    def generate_summary(self, context: UnifiedContext) -> DoctorSummary:
        """Generates a structured Doctor Visit summary."""
        logger.info("Generating Doctor Visit Summary.")
        return self.engine.generate(context)
