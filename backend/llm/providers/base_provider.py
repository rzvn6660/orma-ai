from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAIProvider(ABC):
    """
    Abstract Base Class for ORMA AI Language Model Providers.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and available."""
        pass
        
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 150,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generates text response from the provider.
        Returns dict with keys:
          - text (str)
          - provider (str)
          - model (str)
          - success (bool)
          - error (Optional[str])
        """
        pass
