import logging
from typing import List, Optional, Dict
from .medical_sources import MedicalSourceProvider, MockMedicalProvider
from .medical_context import MedicalContext
from .citation_engine import CitationEngine

logger = logging.getLogger(__name__)

class MedicalRetriever:
    """Coordinates medical knowledge retrieval across providers."""
    
    def __init__(self, provider: Optional[MedicalSourceProvider] = None):
        # Allow injecting any provider (e.g., OpenFDA API later), default to mock
        self.provider = provider or MockMedicalProvider()
        self.citation_engine = CitationEngine()

    def retrieve(self, queries: List[Dict[str, str]]) -> MedicalContext:
        """
        Retrieves medical knowledge for a list of queries.
        queries format: [{"type": "drug", "query": "Aspirin"}, {"type": "condition", "query": "Hypertension"}]
        """
        context = MedicalContext()
        
        for q in queries:
            q_type = q.get("type")
            q_val = q.get("query", "")
            
            if q_type == "drug":
                raw_data = self.provider.retrieve_drug_info(q_val)
                if raw_data:
                    item = self.citation_engine.attach_metadata(
                        raw_data, query=q_val, category="drug", provider_name=self.provider.provider_name
                    )
                    context.drugs.append(item)
            elif q_type == "condition":
                raw_data = self.provider.retrieve_condition_info(q_val)
                if raw_data:
                    item = self.citation_engine.attach_metadata(
                        raw_data, query=q_val, category="condition", provider_name=self.provider.provider_name
                    )
                    context.conditions.append(item)
                    
        return context
