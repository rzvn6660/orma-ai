import logging
from ochr.context.context_models import UnifiedContext
from .timeline_models import TimelineResult
from .timeline_engine import TimelineEngine

logger = logging.getLogger(__name__)

class TimelineService:
    def __init__(self):
        self.engine = TimelineEngine()
        logger.info("TimelineService initialized.")

    def generate_timeline(self, context: UnifiedContext) -> TimelineResult:
        """Generates a health timeline from a UnifiedContext object."""
        logger.info("Generating health timeline.")
        return self.engine.generate(context)
