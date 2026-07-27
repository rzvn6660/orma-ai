import json
from ochr.reasoning.reasoning_types import ReasoningPlan
from ochr.knowledge.hybrid_context import HybridContext
from .execution_models import FormattedPrompt

class PromptBuilder:
    def build(self, query: str, plan: ReasoningPlan, context: HybridContext) -> FormattedPrompt:
        # Filter personal context based on required sections from plan
        personal_context_dict = {}
        for section in plan.required_context_sections:
            val = getattr(context.personal_context, section, [])
            if val:
                personal_context_dict[section] = val
                
        personal_context_str = json.dumps(personal_context_dict, default=str) if personal_context_dict else "No relevant personal context."
        
        # Build Medical context
        medical_context_dict = {}
        if context.medical_context.drugs:
            medical_context_dict["drugs"] = [d.model_dump() for d in context.medical_context.drugs]
        if context.medical_context.conditions:
            medical_context_dict["conditions"] = [c.model_dump() for c in context.medical_context.conditions]
            
        medical_context_str = json.dumps(medical_context_dict, default=str) if medical_context_dict else "No relevant medical context."
        
        # Build System instruction
        sys_instr = plan.selected_prompt_template
        if plan.clarification_needed and plan.clarification_question:
            sys_instr += f"\nNote: Missing context detected. You MUST ask this exact clarification question: '{plan.clarification_question}'"
            
        return FormattedPrompt(
            system_instruction=sys_instr,
            personal_context=personal_context_str,
            medical_context=medical_context_str,
            user_query=query,
            metadata={"safety_level": plan.safety_level.value}
        )
