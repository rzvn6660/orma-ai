import os
import io
import time
import uuid
import re
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from rag.rag_models import (
    RAGDocument,
    RAGDocumentChunk,
    ProcessingStatus,
    DocumentUploadResponse,
    DocumentDetailResponse,
    DocumentIngestionTelemetry
)
from rag.embeddings import BaseEmbeddingProvider, default_embedding_provider
from rag.processors import get_document_processor, ALLOWED_EXTENSIONS
from rag.processors.normalizer import normalize_text

logger = logging.getLogger(__name__)

# Base upload directory inside backend (outside source code packages, configurable via env)
UPLOAD_BASE_DIR = os.getenv("RAG_UPLOAD_DIR") or os.getenv("UPLOAD_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "documents")
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB max

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes untrusted filename to prevent directory traversal and invalid characters.
    """
    # Remove directory separators and null bytes
    clean = re.sub(r'[/\\:\0]', '_', filename)
    # Remove traversal patterns
    clean = clean.replace('..', '_')
    # Keep alphanumeric, dot, underscore, hyphen
    clean = re.sub(r'[^a-zA-Z0-9._\- ]', '', clean).strip()
    return clean or f"doc_{uuid.uuid4().hex[:8]}"

class DocumentIngestionService:
    """
    End-to-End Authenticated Document Ingestion Pipeline for ORMA AI RAG.
    
    Phases:
    1. Validate (Extension, Size, Path Traversal)
    2. Deduplication Check (SHA-256 Content Hash)
    3. Persist Initial Metadata (Status: UPLOADING -> PROCESSING)
    4. Deterministic Text Extraction (PDF / DOCX / Image OCR)
    5. Multilingual Text Normalization
    6. Page-aware Structured Chunking
    7. Local Semantic Embedding (0 LLM calls)
    8. Persist User-Isolated Chunks
    9. Transition Status to READY (or FAILED on error)
    10. Safe Telemetry Logging
    """

    def __init__(self, embedding_provider: Optional[BaseEmbeddingProvider] = None, upload_dir: str = UPLOAD_BASE_DIR):
        self.embedding_provider = embedding_provider or default_embedding_provider
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def compute_content_hash(self, file_bytes: bytes) -> str:
        """Computes deterministic SHA-256 hash of file content."""
        return hashlib.sha256(file_bytes).hexdigest()

    def chunk_document_by_pages(
        self,
        text_by_page: Dict[int, str],
        doc_title: str,
        chunk_size: int = 350,
        chunk_overlap: int = 50,
        source_type: str = "pdf"
    ) -> List[Dict[str, Any]]:
        """
        Page-aware structured chunker preserving page numbers, section headers,
        and semantic blocks (e.g. medication schedules).
        """
        all_chunks: List[Dict[str, Any]] = []
        chunk_counter = 0

        for page_num in sorted(text_by_page.keys()):
            page_text = text_by_page[page_num].strip()
            if not page_text:
                continue

            # Split page into sections or paragraphs
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [page_text]

            current_chunk = ""
            current_section = None

            for para in paragraphs:
                # Detect section header
                if para.startswith("## ") or para.isupper() and len(para) < 50:
                    current_section = para.lstrip("#").strip()

                if len(current_chunk) + len(para) + 1 <= chunk_size:
                    current_chunk = f"{current_chunk}\n{para}".strip() if current_chunk else para
                else:
                    if current_chunk:
                        all_chunks.append({
                            "chunk_index": chunk_counter,
                            "page": page_num,
                            "section": current_section,
                            "page_or_section": f"Page {page_num}" + (f", {current_section}" if current_section else ""),
                            "source_type": source_type,
                            "text_content": current_chunk
                        })
                        chunk_counter += 1

                    # If paragraph itself is larger than chunk_size, split by sentences
                    if len(para) > chunk_size:
                        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', para) if s.strip()]
                        temp_chunk = ""
                        for sent in sentences:
                            if len(temp_chunk) + len(sent) + 1 <= chunk_size:
                                temp_chunk = f"{temp_chunk} {sent}".strip() if temp_chunk else sent
                            else:
                                if temp_chunk:
                                    all_chunks.append({
                                        "chunk_index": chunk_counter,
                                        "page": page_num,
                                        "section": current_section,
                                        "page_or_section": f"Page {page_num}" + (f", {current_section}" if current_section else ""),
                                        "source_type": source_type,
                                        "text_content": temp_chunk
                                    })
                                    chunk_counter += 1
                                temp_chunk = sent
                        if temp_chunk:
                            current_chunk = temp_chunk
                        else:
                            current_chunk = ""
                    else:
                        current_chunk = para

            if current_chunk:
                all_chunks.append({
                    "chunk_index": chunk_counter,
                    "page": page_num,
                    "section": current_section,
                    "page_or_section": f"Page {page_num}" + (f", {current_section}" if current_section else ""),
                    "source_type": source_type,
                    "text_content": current_chunk
                })
                chunk_counter += 1

        return all_chunks

    def ingest_file(
        self,
        db: Session,
        user_id: str,
        file_bytes: bytes,
        original_filename: str,
        content_type: Optional[str] = None,
        document_type: str = "general_document",
        source: str = "uploaded_file"
    ) -> Tuple[RAGDocument, DocumentIngestionTelemetry]:
        """
        Executes full authenticated ingestion pipeline.
        Never calls Gemini/Groq LLMs.
        """
        t0 = time.perf_counter()
        req_id = str(uuid.uuid4())
        uid = str(user_id)

        # -------------------------------------------------------------
        # 1. Validation
        # -------------------------------------------------------------
        file_size = len(file_bytes)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB (received {file_size / (1024*1024):.2f} MB).")

        if file_size == 0:
            raise ValueError("Uploaded file is empty (0 bytes).")

        safe_name = sanitize_filename(original_filename)
        ext = os.path.splitext(safe_name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

        # -------------------------------------------------------------
        # 2. Deduplication Check
        # -------------------------------------------------------------
        content_hash = self.compute_content_hash(file_bytes)
        existing_doc = (
            db.query(RAGDocument)
            .filter(RAGDocument.user_id == uid, RAGDocument.content_hash == content_hash)
            .first()
        )
        if existing_doc:
            logger.info(f"[IngestionService] Duplicate document detected for user {uid} (hash={content_hash[:8]}). Returning existing doc {existing_doc.id}")
            chunk_cnt = db.query(RAGDocumentChunk).filter(RAGDocumentChunk.document_id == existing_doc.id).count()
            t_total_ms = int((time.perf_counter() - t0) * 1000)
            telemetry = DocumentIngestionTelemetry(
                request_id=req_id,
                user_id=uid,
                document_id=existing_doc.id,
                file_type=ext.lstrip('.'),
                file_size=file_size,
                page_count=existing_doc.page_count or 1,
                extraction_method=existing_doc.extraction_method or "duplicate_bypassed",
                ocr_used=existing_doc.ocr_used or False,
                chunk_count=chunk_cnt,
                upload_time_ms=0,
                extraction_time_ms=0,
                ocr_time_ms=0,
                chunking_time_ms=0,
                embedding_time_ms=0,
                total_time_ms=t_total_ms,
                status=ProcessingStatus.DUPLICATE_IGNORED
            )
            return existing_doc, telemetry

        # -------------------------------------------------------------
        # 3. Store Initial Metadata & Save File Securely
        # -------------------------------------------------------------
        t_upload_start = time.perf_counter()
        doc_id = str(uuid.uuid4())
        user_folder = os.path.join(self.upload_dir, uid)
        os.makedirs(user_folder, exist_ok=True)
        saved_file_path = os.path.join(user_folder, f"{doc_id}_{safe_name}")

        with open(saved_file_path, "wb") as f:
            f.write(file_bytes)

        upload_time_ms = int((time.perf_counter() - t_upload_start) * 1000)

        # Title formatting from filename
        base_title = os.path.splitext(safe_name)[0].replace('_', ' ').replace('-', ' ').strip().title()

        rag_doc = RAGDocument(
            id=doc_id,
            user_id=uid,
            title=base_title,
            document_type=document_type,
            source=source,
            file_path=saved_file_path,
            file_size=file_size,
            page_count=1,
            content_hash=content_hash,
            processing_status=ProcessingStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(rag_doc)
        db.commit()
        db.refresh(rag_doc)

        extraction_time_ms = 0
        ocr_time_ms = 0
        chunking_time_ms = 0
        embedding_time_ms = 0

        # -------------------------------------------------------------
        # 4. Text Extraction & Processing
        # -------------------------------------------------------------
        try:
            t_extract_start = time.perf_counter()
            processor = get_document_processor(safe_name, content_type)
            
            t_proc_start = time.perf_counter()
            processed_data = processor.process_bytes(file_bytes, safe_name)
            extraction_time_ms = int((time.perf_counter() - t_proc_start) * 1000)

            if processed_data.ocr_used:
                ocr_time_ms = extraction_time_ms

            # ---------------------------------------------------------
            # 5. Chunking
            # ---------------------------------------------------------
            t_chunk_start = time.perf_counter()
            chunks_to_create = self.chunk_document_by_pages(
                text_by_page=processed_data.text_by_page,
                doc_title=rag_doc.title,
                chunk_size=350,
                chunk_overlap=50,
                source_type=processed_data.source_type
            )
            chunking_time_ms = int((time.perf_counter() - t_chunk_start) * 1000)

            # ---------------------------------------------------------
            # 6. Embedding & Persistence (0 LLM Calls)
            # ---------------------------------------------------------
            t_embed_start = time.perf_counter()
            for c_info in chunks_to_create:
                text_snippet = c_info["text_content"]
                embed_context = f"Document: {rag_doc.title}\n{text_snippet}"
                embedding_vector = self.embedding_provider.embed_text(embed_context)

                chunk_obj = RAGDocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    user_id=uid,  # Crucial: User isolation directly on chunk
                    chunk_index=c_info["chunk_index"],
                    page=c_info["page"],
                    section=c_info["section"],
                    page_or_section=c_info["page_or_section"],
                    source_type=c_info["source_type"],
                    text_content=text_snippet,
                    embedding=json.dumps(embedding_vector),
                    token_count=len(text_snippet.split()),
                    created_at=datetime.utcnow()
                )
                db.add(chunk_obj)

            embedding_time_ms = int((time.perf_counter() - t_embed_start) * 1000)

            # ---------------------------------------------------------
            # 7. Finalize Document Status -> READY
            # ---------------------------------------------------------
            rag_doc.page_count = processed_data.page_count
            rag_doc.extraction_method = processed_data.extraction_method
            rag_doc.ocr_used = processed_data.ocr_used
            rag_doc.ocr_confidence = processed_data.ocr_confidence
            rag_doc.doctor_name = processed_data.doctor_name
            rag_doc.document_date = processed_data.document_date
            rag_doc.metadata_json = json.dumps(processed_data.metadata) if processed_data.metadata else None
            rag_doc.processing_status = ProcessingStatus.READY
            rag_doc.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(rag_doc)

            total_time_ms = int((time.perf_counter() - t0) * 1000)

            telemetry = DocumentIngestionTelemetry(
                request_id=req_id,
                user_id=uid,
                document_id=doc_id,
                file_type=ext.lstrip('.'),
                file_size=file_size,
                page_count=processed_data.page_count,
                extraction_method=processed_data.extraction_method,
                ocr_used=processed_data.ocr_used,
                chunk_count=len(chunks_to_create),
                upload_time_ms=upload_time_ms,
                extraction_time_ms=extraction_time_ms,
                ocr_time_ms=ocr_time_ms,
                chunking_time_ms=chunking_time_ms,
                embedding_time_ms=embedding_time_ms,
                total_time_ms=total_time_ms,
                status=ProcessingStatus.READY
            )
            logger.info(f"[IngestionService] Successfully ingested document '{rag_doc.title}' ({len(chunks_to_create)} chunks, {total_time_ms}ms) for user {uid}")
            return rag_doc, telemetry

        except Exception as e:
            db.rollback()
            logger.error(f"[IngestionService] Processing failed for document {doc_id} ('{safe_name}'): {e}", exc_info=True)
            
            # Explicitly record FAILED status in database
            rag_doc.processing_status = ProcessingStatus.FAILED
            rag_doc.error_message = str(e)
            rag_doc.updated_at = datetime.utcnow()
            db.add(rag_doc)
            db.commit()

            total_time_ms = int((time.perf_counter() - t0) * 1000)
            telemetry = DocumentIngestionTelemetry(
                request_id=req_id,
                user_id=uid,
                document_id=doc_id,
                file_type=ext.lstrip('.'),
                file_size=file_size,
                page_count=1,
                extraction_method="failed",
                ocr_used=False,
                chunk_count=0,
                upload_time_ms=upload_time_ms,
                extraction_time_ms=extraction_time_ms,
                ocr_time_ms=0,
                chunking_time_ms=0,
                embedding_time_ms=0,
                total_time_ms=total_time_ms,
                status=ProcessingStatus.FAILED
            )
            raise e

ingestion_service = DocumentIngestionService()
