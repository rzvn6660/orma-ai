import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from rag.rag_models import RAGDocument, RAGDocumentChunk, RAGRetrievalResult
from rag.embeddings import BaseEmbeddingProvider, default_embedding_provider, compute_cosine_similarity

logger = logging.getLogger(__name__)

class RAGRetriever:
    """
    User-Isolated Semantic Retriever.
    Searches only within the authenticated user's indexed document chunks.
    Scores relevance using cosine similarity and enforces strict thresholding.
    """

    def __init__(self, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or default_embedding_provider

    def retrieve(
        self,
        db: Session,
        user_id: str,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.20,
        document_id: Optional[str] = None
    ) -> Tuple[List[RAGRetrievalResult], int, int]:
        """
        Retrieves top relevant chunks for a specific user.
        
        Returns:
            Tuple: (results: List[RAGRetrievalResult], total_chunks_considered: int, retrieval_latency_ms: int)
        
        Strict User Isolation Guarantee:
            The SQL query explicitly filters by `user_id == user_id`.
            No chunks from any other user are ever loaded or compared.
        """
        t_start = time.perf_counter()
        uid = str(user_id)
        cleaned_query = query.strip()

        if not cleaned_query:
            return [], 0, 0

        # Embed user's query
        query_vec = self.embedding_provider.embed_text(cleaned_query)

        # Query only chunks owned by this specific user
        query_builder = (
            db.query(RAGDocumentChunk, RAGDocument)
            .join(RAGDocument, RAGDocumentChunk.document_id == RAGDocument.id)
            .filter(RAGDocumentChunk.user_id == uid)
            .filter(RAGDocument.user_id == uid)
        )
        if document_id:
            query_builder = query_builder.filter(RAGDocument.id == str(document_id))

        chunks_with_docs = query_builder.all()

        total_chunks = len(chunks_with_docs)
        if total_chunks == 0:
            latency_ms = int((time.perf_counter() - t_start) * 1000)
            logger.info(f"[RAGRetriever] No documents/chunks found for user {uid}")
            return [], 0, latency_ms

        scored_results: List[RAGRetrievalResult] = []

        for chunk, doc in chunks_with_docs:
            if not chunk.embedding:
                continue

            try:
                chunk_vec = json.loads(chunk.embedding)
            except Exception:
                continue

            score = compute_cosine_similarity(query_vec, chunk_vec)
            if score >= similarity_threshold:
                result_item = RAGRetrievalResult(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    user_id=chunk.user_id,
                    document_title=doc.title,
                    filename=doc.source or doc.title,
                    document_type=doc.document_type or "general_document",
                    source=doc.source or "uploaded_file",
                    page=chunk.page or 1,
                    chunk_index=chunk.chunk_index or 0,
                    section=chunk.section,
                    page_or_section=chunk.page_or_section or (f"Page {chunk.page}" if chunk.page else None),
                    text_content=chunk.text_content,
                    similarity_score=round(score, 4)
                )
                scored_results.append(result_item)

        # Sort descending by similarity score
        scored_results.sort(key=lambda r: r.similarity_score, reverse=True)
        
        # Deduplicate identical text chunks in top_k to protect LLM context window
        unique_results: List[RAGRetrievalResult] = []
        seen_texts = set()
        for r in scored_results:
            normalized_text = " ".join(r.text_content.lower().split())
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_results.append(r)
            if len(unique_results) >= top_k:
                break

        top_results = unique_results

        latency_ms = int((time.perf_counter() - t_start) * 1000)
        logger.info(f"[RAGRetriever] User {uid}: Considered {total_chunks} chunks, found {len(scored_results)} matching, returning top {len(top_results)} (latency={latency_ms}ms)")

        return top_results, total_chunks, latency_ms

rag_retriever = RAGRetriever()
