from ochr.reasoning.reasoning_types import ReasoningPlan
from ochr.knowledge.hybrid_context import HybridContext
from ochr.execution.execution_models import ExecutionResult
from .explanation_models import ExplanationResult
from .evidence_builder import EvidenceBuilder
from .confidence_engine import ConfidenceEngine

class ExplanationEngine:
    def __init__(self):
        self.evidence_builder = EvidenceBuilder()
        self.confidence_engine = ConfidenceEngine()

    def generate_explanation(self, plan: ReasoningPlan, context: HybridContext, execution_result: ExecutionResult) -> ExplanationResult:
        evidence_items = self.evidence_builder.build_evidence(plan, context)
        confidence_score = self.confidence_engine.compute_confidence(plan, execution_result, evidence_items)
        
        medical_sources = list(set([item.source_name for item in evidence_items if item.is_medical]))
        
        summary_parts = [f"Generated response for {plan.reasoning_type.value} category."]
        if medical_sources:
            summary_parts.append(f"Supported by medical sources: {', '.join(medical_sources)}.")
        if plan.clarification_needed:
            summary_parts.append("Clarification was requested due to insufficient context.")
            
        return ExplanationResult(
            reasoning_category=plan.reasoning_type.value,
            confidence_score=round(confidence_score, 2),
            safety_level=plan.safety_level.value,
            evidence_items=evidence_items,
            contributing_context_sections=plan.required_context_sections,
            medical_sources=medical_sources,
            explanation_summary=" ".join(summary_parts)
        )
