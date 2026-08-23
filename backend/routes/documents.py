import os
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, get_current_context
from models.user import User
from rag.rag_models import (
    RAGDocument,
    RAGDocumentChunk,
    ProcessingStatus,
    DocumentUploadResponse,
    DocumentDetailResponse,
    DocumentListResponse
)
from rag.ingestion_service import ingestion_service, sanitize_filename
from rag.processors import ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("general_document"),
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db)
):
    """
    Authenticated Document Ingestion Endpoint.
    Derives user_id strictly from authenticated session/context.
    Never trusts user_id from frontend parameters.
    """
    # Authoritatively resolve authenticated target subject
    target_user_id = str(context["resolved_subject"]["id"])
    auth_user = context["authenticated_user"]

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    safe_name = sanitize_filename(file.filename)
    ext = os.path.splitext(safe_name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read bytes safely
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {e}")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    if len(file_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size limit of 20 MB.")

    try:
        doc, telemetry = ingestion_service.ingest_file(
            db=db,
            user_id=target_user_id,
            file_bytes=file_bytes,
            original_filename=safe_name,
            content_type=file.content_type,
            document_type=document_type,
            source="api_upload"
        )

        chunk_count = db.query(RAGDocumentChunk).filter(RAGDocumentChunk.document_id == doc.id).count()

        return DocumentUploadResponse(
            document_id=doc.id,
            title=doc.title,
            document_type=doc.document_type or "general_document",
            source=doc.source or "api_upload",
            page_count=doc.page_count or 1,
            file_size=doc.file_size or len(file_bytes),
            processing_status=doc.processing_status or ProcessingStatus.READY,
            content_hash=doc.content_hash,
            chunk_count=chunk_count,
            extraction_method=doc.extraction_method or "native_text",
            ocr_used=doc.ocr_used or False,
            created_at=doc.created_at
        )

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as proc_err:
        logger.error(f"[DocumentUploadRouter] Ingestion failure: {proc_err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(proc_err)}")

@router.get("", response_model=DocumentListResponse)
def list_user_documents(
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db)
):
    """
    List all documents owned by the authenticated user.
    Strictly isolated: users can never see other users' documents.
    """
    target_user_id = str(context["resolved_subject"]["id"])
    docs = db.query(RAGDocument).filter(RAGDocument.user_id == target_user_id).order_by(RAGDocument.created_at.desc()).all()

    detail_list = []
    for d in docs:
        c_count = db.query(RAGDocumentChunk).filter(RAGDocumentChunk.document_id == d.id).count()
        detail_list.append(DocumentDetailResponse(
            id=d.id,
            user_id=d.user_id,
            title=d.title,
            document_type=d.document_type or "general_document",
            source=d.source or "uploaded_file",
            page_count=d.page_count or 1,
            file_size=d.file_size or 0,
            processing_status=d.processing_status or ProcessingStatus.READY,
            content_hash=d.content_hash,
            chunk_count=c_count,
            extraction_method=d.extraction_method,
            ocr_used=d.ocr_used or False,
            error_message=d.error_message,
            doctor_name=d.doctor_name,
            hospital_name=d.hospital_name,
            document_date=d.document_date,
            language=d.language,
            created_at=d.created_at,
            updated_at=d.updated_at
        ))

    return DocumentListResponse(documents=detail_list, total_count=len(detail_list))

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document_details(
    document_id: str,
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db)
):
    """
    Retrieve document metadata for a specific document owned by the user.
    Returns 404 if not found or if the document belongs to another user.
    """
    target_user_id = str(context["resolved_subject"]["id"])
    doc = db.query(RAGDocument).filter(
        RAGDocument.id == document_id,
        RAGDocument.user_id == target_user_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    c_count = db.query(RAGDocumentChunk).filter(RAGDocumentChunk.document_id == doc.id).count()

    return DocumentDetailResponse(
        id=doc.id,
        user_id=doc.user_id,
        title=doc.title,
        document_type=doc.document_type or "general_document",
        source=doc.source or "uploaded_file",
        page_count=doc.page_count or 1,
        file_size=doc.file_size or 0,
        processing_status=doc.processing_status or ProcessingStatus.READY,
        content_hash=doc.content_hash,
        chunk_count=c_count,
        extraction_method=doc.extraction_method,
        ocr_used=doc.ocr_used or False,
        error_message=doc.error_message,
        doctor_name=doc.doctor_name,
        hospital_name=doc.hospital_name,
        document_date=doc.document_date,
        language=doc.language,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db)
):
    """
    Deletes a user's document and all associated chunks.
    Returns 404 if not found or if the document belongs to another user.
    """
    target_user_id = str(context["resolved_subject"]["id"])
    doc = db.query(RAGDocument).filter(
        RAGDocument.id == document_id,
        RAGDocument.user_id == target_user_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete chunks
    db.query(RAGDocumentChunk).filter(
        RAGDocumentChunk.document_id == document_id,
        RAGDocumentChunk.user_id == target_user_id
    ).delete()

    # Delete document record
    db.delete(doc)
    db.commit()

    # Clean local file if exists
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Could not delete physical file {doc.file_path}: {e}")

    return {
        "success": True,
        "message": "Document and associated chunks deleted successfully.",
        "document_id": document_id
    }
