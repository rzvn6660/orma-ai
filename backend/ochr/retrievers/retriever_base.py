from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseRetriever(ABC):
    """
    Base class for all retrievers in the ORMA Contextual Hybrid Retrieval system.
    """
    
    @abstractmethod
    def retrieve(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve structured information based on the given context.
        Returns a dictionary containing structured data.
        """
        pass
