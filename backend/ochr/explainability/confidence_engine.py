from typing import List
from ochr.reasoning.reasoning_types import ReasoningPlan
from ochr.execution.execution_models import ExecutionResult
from .explanation_models import EvidenceItem

class ConfidenceEngine:
    def compute_confidence(self, plan: ReasoningPlan, execution_result: ExecutionResult, evidence: List[EvidenceItem]) -> float:
        base_confidence = execution_result.confidence
        
        # Penalize if clarification was needed
        if plan.clarification_needed:
            base_confidence -= 0.3
            
        # Average confidence of evidence items
        if evidence:
            avg_evidence_confidence = sum(item.confidence for item in evidence) / len(evidence)
            # Combine execution confidence with evidence confidence
            base_confidence = (base_confidence + avg_evidence_confidence) / 2.0
        elif not plan.clarification_needed and plan.required_context_sections:
            # Missing context but no clarification flagged? Strong penalty
            base_confidence -= 0.4
            
        # Hard bounds
        return max(0.0, min(1.0, base_confidence))
