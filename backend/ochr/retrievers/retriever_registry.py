from typing import Dict
from .retriever_base import BaseRetriever

class RetrieverRegistry:
    """Registry to dynamically manage and invoke retrievers."""
    
    _retrievers: Dict[str, BaseRetriever] = {}

    @classmethod
    def register(cls, name: str, retriever: BaseRetriever):
        cls._retrievers[name] = retriever

    @classmethod
    def get_retriever(cls, name: str) -> BaseRetriever:
        return cls._retrievers.get(name)

    @classmethod
    def get_all_registered_names(cls) -> list[str]:
        return list(cls._retrievers.keys())
