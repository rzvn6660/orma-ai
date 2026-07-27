from abc import ABC, abstractmethod
from typing import Any
from .execution_models import FormattedPrompt, LLMResponse

class LLMProvider(ABC):
    """Abstract interface for interacting with any Large Language Model."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def generate(self, prompt: FormattedPrompt, **kwargs: Any) -> LLMResponse:
        pass
