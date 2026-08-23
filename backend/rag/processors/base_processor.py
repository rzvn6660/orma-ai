from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ProcessedDocument(BaseModel):
    """
    Standardized payload returned by all document format processors.
    """
    text_by_page: Dict[int, str] = Field(default_factory=dict, description="1-indexed map from page number to text")
    full_text: str = ""
    page_count: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_method: str = "native_text"
    ocr_used: bool = False
    ocr_confidence: Optional[float] = None
    source_type: str = "pdf"
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    document_date: Optional[str] = None
    language: Optional[str] = "en"

class BaseDocumentProcessor(ABC):
    """
    Abstract Base Class for format-specific document processors (PDF, DOCX, Images).
    """

    @abstractmethod
    def process_bytes(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        """Processes document from in-memory byte buffer."""
        pass

    @abstractmethod
    def process_file(self, file_path: str, filename: str) -> ProcessedDocument:
        """Processes document from local filesystem path."""
        pass
