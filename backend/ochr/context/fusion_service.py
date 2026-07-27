import logging
from typing import Dict, Any
from .context_models import UnifiedContext
from .context_fusion import ContextFusionEngine
from .context_ranker import ContextRanker

logger = logging.getLogger(__name__)

class FusionService:
    """
    Service layer to coordinate the fusion and ranking of retrieved contexts.
    """
    def __init__(self):
        self.fusion_engine = ContextFusionEngine()
        self.ranker = ContextRanker()
        logger.info("FusionService initialized.")

    def build_context(self, retrieved_data: Dict[str, Dict[str, Any]]) -> UnifiedContext:
        """
        Takes raw output from multiple retrievers, fuses them, removes duplicates,
        and ranks them by relevance.
        
        Args:
            retrieved_data: Mapping of retriever names to their respective output dictionaries.
        """
        if not retrieved_data:
            logger.warning("No retrieved data provided to FusionService.")
            return UnifiedContext()

        logger.info(f"Fusing context from sources: {list(retrieved_data.keys())}")
        
        # 1. Merge all data into a unified object, handling duplicates
        unified_context = self.fusion_engine.fuse(retrieved_data)
        
        # 2. Rank the context elements based on relevance heuristics
        ranked_context = self.ranker.rank(unified_context)
        
        return ranked_context
