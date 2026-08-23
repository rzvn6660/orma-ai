import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from database import Base

class ProcessingStatus:
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    DUPLICATE_IGNORED = "DUPLICATE_IGNORED"

class RAGDocument(Base):
    """
    Authoritative record for an uploaded or ingested user document.
    Strictly isolated per user_id.
    """
    __tablename__ = "rag_documents"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    document_type = Column(String, default="general_document", index=True)
    source = Column(String, default="uploaded_file")
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    content_hash = Column(String, nullable=True, index=True)
    processing_status = Column(String, default=ProcessingStatus.UPLOADING, index=True)
    extraction_method = Column(String, default="native_text")
    ocr_used = Column(Boolean, default=False)
    ocr_confidence = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    doctor_name = Column(String, nullable=True)
    hospital_name = Column(String, nullable=True)
    document_date = Column(String, nullable=True)
    language = Column(String, default="en")
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RAGDocumentChunk(Base):
    """
    Granular chunk extracted from a document with embedding vector.
    Carries user_id directly on every chunk to enforce strict user isolation.
    """
    __tablename__ = "rag_document_chunks"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    document_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, default=0)
    page = Column(Integer, nullable=True, default=1)
    section = Column(String, nullable=True)
    page_or_section = Column(String, nullable=True)
    source_type = Column(String, default="pdf")
    text_content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON-encoded float array
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Schemas for API, Ingestion, and Retrieval Contracts

class RAGDocumentMetadata(BaseModel):
    user_id: str
    document_id: Optional[str] = None
    document_type: str = "general_document"
    source: str = "uploaded_file"
    page_or_section: Optional[str] = None
    created_at: Optional[datetime] = None

class RAGDocumentCreate(BaseModel):
    title: str
    content: str
    document_type: str = "general_document"
    source: str = "uploaded_file"
    page_or_section: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RAGChunkData(BaseModel):
    id: str
    document_id: str
    user_id: str
    chunk_index: int
    page: Optional[int] = 1
    section: Optional[str] = None
    page_or_section: Optional[str] = None
    source_type: Optional[str] = "pdf"
    text_content: str
    token_count: int = 0
    created_at: Optional[datetime] = None

class RAGRetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    user_id: str
    document_title: str
    filename: Optional[str] = None
    document_type: str = "general_document"
    source: str = "uploaded_file"
    page: Optional[int] = 1
    chunk_index: Optional[int] = 0
    section: Optional[str] = None
    page_or_section: Optional[str] = None
    text_content: str
    similarity_score: float

class DocumentUploadResponse(BaseModel):
    document_id: str
    title: str
    document_type: str
    source: str
    page_count: int
    file_size: int
    processing_status: str
    content_hash: Optional[str] = None
    chunk_count: int = 0
    extraction_method: str = "native_text"
    ocr_used: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentDetailResponse(BaseModel):
    id: str
    user_id: str
    title: str
    document_type: str
    source: str
    page_count: int
    file_size: int
    processing_status: str
    content_hash: Optional[str] = None
    chunk_count: int = 0
    extraction_method: Optional[str] = None
    ocr_used: bool = False
    error_message: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    document_date: Optional[str] = None
    language: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    documents: List[DocumentDetailResponse]
    total_count: int

class DocumentIngestionTelemetry(BaseModel):
    request_id: str
    user_id: str
    document_id: str
    file_type: str
    file_size: int
    page_count: int
    extraction_method: str
    ocr_used: bool
    chunk_count: int
    upload_time_ms: int
    extraction_time_ms: int
    ocr_time_ms: int
    chunking_time_ms: int
    embedding_time_ms: int
    total_time_ms: int
    status: str

class RAGTelemetryPayload(BaseModel):
    request_id: str
    user_id: str
    language: str = "en"
    intent: str = "DOCUMENT_QUERY"
    execution_mode: str = "RAG_WITH_LLM"
    rag_required: bool = True
    rag_called: bool = True
    retrieval_performed: bool = True
    documents_considered: int = 0
    chunks_retrieved: int = 0
    relevant_chunks: int = 0
    top_score: float = 0.0
    retrieval_latency_ms: int = 0
    context_chunks_sent: int = 0
    context_size: int = 0
    llm_called: bool = False
    llm_provider: str = "none"
    llm_model: str = "none"
    llm_latency_ms: int = 0
    fallback_used: bool = False
    grounded_response: bool = True
    total_latency_ms: int = 0
