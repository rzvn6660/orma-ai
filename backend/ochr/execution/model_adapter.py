from typing import Optional
from .provider_interface import LLMProvider
from .execution_models import FormattedPrompt, LLMResponse

class ModelAdapter:
    """Provides a single interface to interact with whichever LLM provider is active."""
    
    def __init__(self, default_provider: Optional[LLMProvider] = None):
        self.provider = default_provider
        
    def has_provider(self) -> bool:
        return self.provider is not None

    def generate_response(self, prompt: FormattedPrompt, **kwargs) -> LLMResponse:
        if not self.has_provider():
            return LLMResponse(
                text="No AI provider is configured.",
                metadata={"status": "not_configured", "provider": None}
            )
        return self.provider.generate(prompt, **kwargs)
