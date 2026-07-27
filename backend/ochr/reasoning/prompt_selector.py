from typing import Dict
from .reasoning_types import ReasoningCategory

class PromptSelector:
    """Selects the correct prompt template based on reasoning category."""
    
    _templates: Dict[ReasoningCategory, str] = {
        ReasoningCategory.MEDICATION: "You are a healthcare assistant checking medication adherence. Given the context {context}, answer: {query}",
        ReasoningCategory.HEALTH: "You are a healthcare assistant providing health insights. Given the context {context}, answer: {query}",
        ReasoningCategory.PLANNER: "You are a schedule assistant. Given the context {context}, answer: {query}",
        ReasoningCategory.MEMORY: "You are a personal assistant. Given the context {context}, answer: {query}",
        ReasoningCategory.CONVERSATION: "You are a companion assistant. Given the context {context}, answer: {query}",
        ReasoningCategory.EMERGENCY: "CRITICAL: You are an emergency responder AI. Provide immediate, brief guidance based on {context}. Query: {query}",
        ReasoningCategory.GENERAL: "You are a helpful assistant. Answer the query: {query}",
    }

    def select(self, category: ReasoningCategory) -> str:
        return self._templates.get(category, self._templates[ReasoningCategory.GENERAL])
