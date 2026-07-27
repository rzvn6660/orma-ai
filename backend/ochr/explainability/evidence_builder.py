from typing import List
from ochr.reasoning.reasoning_types import ReasoningPlan
from ochr.knowledge.hybrid_context import HybridContext
from .explanation_models import EvidenceItem
from .provenance_tracker import ProvenanceTracker

class EvidenceBuilder:
    def __init__(self):
        self.tracker = ProvenanceTracker()

    def build_evidence(self, plan: ReasoningPlan, context: HybridContext) -> List[EvidenceItem]:
        evidence = []
        
        # Extract Personal Evidence only from required sections
        for section in plan.required_context_sections:
            items = getattr(context.personal_context, section, [])
            for item in items:
                evidence.append(self.tracker.track_personal_evidence(section, item))
                
        # Extract Medical Evidence
        for drug in context.medical_context.drugs:
            evidence.append(self.tracker.track_medical_evidence(drug))
            
        for cond in context.medical_context.conditions:
            evidence.append(self.tracker.track_medical_evidence(cond))
            
        return evidence
