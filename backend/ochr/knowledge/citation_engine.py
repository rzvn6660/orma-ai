from typing import Dict, Any, Optional
from .medical_context import MedicalSourceMetadata, MedicalKnowledgeItem

class CitationEngine:
    """Attaches trusted source provenance to retrieved medical knowledge."""
    
    def attach_metadata(self, raw_data: Dict[str, Any], query: str, category: str, provider_name: str, confidence: float = 1.0) -> MedicalKnowledgeItem:
        metadata = MedicalSourceMetadata(
            source_name=raw_data.get("source_name", "Unknown Source"),
            provider=provider_name,
            confidence=confidence,
            publication_date=raw_data.get("publication_date")
        )
        
        # Clean up data to avoid duplicating metadata fields in content
        content = {k: v for k, v in raw_data.items() if k not in ["source_name", "publication_date"]}
        
        return MedicalKnowledgeItem(
            query=query,
            category=category,
            content=content,
            metadata=metadata
        )
