from typing import Dict, Any
from ochr.knowledge.medical_context import MedicalKnowledgeItem
from .explanation_models import EvidenceItem

class ProvenanceTracker:
    def track_personal_evidence(self, category: str, item: Dict[str, Any]) -> EvidenceItem:
        return EvidenceItem(
            category=category,
            content=item,
            source_name=item.get("_source", "unknown_personal_source"),
            provider="orma_database",
            confidence=item.get("confidence", 1.0),
            timestamp=item.get("date") or item.get("time") or item.get("taken_at") or item.get("reminder_time"),
            is_medical=False
        )

    def track_medical_evidence(self, item: MedicalKnowledgeItem) -> EvidenceItem:
        return EvidenceItem(
            category=f"medical_{item.category}",
            content=item.content,
            source_name=item.metadata.source_name,
            provider=item.metadata.provider,
            confidence=item.metadata.confidence,
            timestamp=item.metadata.publication_date,
            is_medical=True
        )
