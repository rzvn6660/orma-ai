import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from rag.rag_models import RAGDocument, RAGDocumentChunk, RAGDocumentCreate
from rag.embeddings import BaseEmbeddingProvider, default_embedding_provider

logger = logging.getLogger(__name__)

class DocumentStore:
    """
    Manages document ingestion, chunking, embedding serialization,
    and storage in SQLite. Strictly enforces user isolation.
    """
    
    def __init__(self, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or default_embedding_provider

    def chunk_text(self, text: str, chunk_size: int = 350, chunk_overlap: int = 50) -> List[str]:
        """
        Splits raw document text into overlapping coherent chunks.
        Preserves sentence boundaries where possible.
        """
        cleaned = text.strip()
        if not cleaned:
            return []

        # Split into paragraphs or sentences
        paragraphs = [p.strip() for p in cleaned.split("\n") if p.strip()]
        if not paragraphs:
            paragraphs = [cleaned]

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 <= chunk_size:
                current_chunk = f"{current_chunk}\n{para}".strip() if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If paragraph itself is longer than chunk_size, split by sentences or sliding window
                if len(para) > chunk_size:
                    sentences = [s.strip() for s in para.replace(". ", ".\n").split("\n") if s.strip()]
                    temp_chunk = ""
                    for s in sentences:
                        if len(temp_chunk) + len(s) + 1 <= chunk_size:
                            temp_chunk = f"{temp_chunk} {s}".strip() if temp_chunk else s
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk)
                            temp_chunk = s
                    if temp_chunk:
                        chunks.append(temp_chunk)
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # Apply overlap if chunks were split linearly
        if len(chunks) == 1:
            return chunks

        final_chunks = []
        for i, c in enumerate(chunks):
            if i > 0 and chunk_overlap > 0 and len(chunks[i - 1]) > chunk_overlap:
                overlap_prefix = chunks[i - 1][-chunk_overlap:].strip()
                final_chunks.append(f"...{overlap_prefix} {c}")
            else:
                final_chunks.append(c)

        return final_chunks

    def ingest_document(
        self,
        db: Session,
        user_id: str,
        title: str,
        content: str,
        document_type: str = "general_document",
        source: str = "uploaded_file",
        page_or_section: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RAGDocument:
        """
        Ingests a document for a specific user:
        1. Creates RAGDocument record scoped to user_id.
        2. Chunks document text.
        3. Computes vector embeddings for each chunk.
        4. Persists chunks with user_id for strict isolation.
        """
        uid = str(user_id)
        doc_id = str(uuid.uuid4())

        doc = RAGDocument(
            id=doc_id,
            user_id=uid,
            title=title,
            document_type=document_type,
            source=source,
            file_path=file_path,
            metadata_json=json.dumps(metadata) if metadata else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(doc)

        chunks = self.chunk_text(content)
        for idx, chunk_str in enumerate(chunks):
            embed_input = f"Document: {title}\n{chunk_str}"
            embedding_vec = self.embedding_provider.embed_text(embed_input)
            chunk_obj = RAGDocumentChunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                user_id=uid,  # Crucial: Chunk-level user isolation
                chunk_index=idx,
                text_content=chunk_str,
                page_or_section=page_or_section,
                embedding=json.dumps(embedding_vec),
                token_count=len(chunk_str.split()),
                created_at=datetime.utcnow()
            )
            db.add(chunk_obj)

        db.commit()
        db.refresh(doc)
        logger.info(f"[DocumentStore] Ingested document '{title}' (id={doc_id}, chunks={len(chunks)}) for user {uid}")
        return doc

    def delete_document(self, db: Session, user_id: str, document_id: str) -> bool:
        """Deletes a document and all associated chunks for a specific user."""
        uid = str(user_id)
        doc = db.query(RAGDocument).filter(RAGDocument.id == document_id, RAGDocument.user_id == uid).first()
        if not doc:
            return False

        db.query(RAGDocumentChunk).filter(RAGDocumentChunk.document_id == document_id, RAGDocumentChunk.user_id == uid).delete()
        db.delete(doc)
        db.commit()
        logger.info(f"[DocumentStore] Deleted document {document_id} for user {uid}")
        return True

    def get_user_documents(self, db: Session, user_id: str) -> List[RAGDocument]:
        """Returns list of documents owned by the specified user."""
        uid = str(user_id)
        return db.query(RAGDocument).filter(RAGDocument.user_id == uid).order_by(RAGDocument.created_at.desc()).all()

document_store = DocumentStore()
