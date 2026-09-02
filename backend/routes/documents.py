import os
import io
import re
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse, RedirectResponse
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
from infrastructure.storage_service import storage_service

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
    Enforces strict ownership or approved caregiver authorization first.
    Deletes object from storage provider and database.
    """
    target_user_id = str(context["resolved_subject"]["id"])
    doc = db.query(RAGDocument).filter(
        RAGDocument.id == document_id,
        RAGDocument.user_id == target_user_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete storage object via storage abstraction
    if doc.file_path:
        bucket = getattr(storage_service, "default_bucket", "medical-documents")
        try:
            storage_service.delete_file(bucket=bucket, object_path=doc.file_path)
        except Exception as e:
            logger.warning(f"Could not delete storage object {doc.file_path}: {e}")
        # Legacy local file cleanup if path exists on disk
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception:
                pass

    # Delete chunks
    db.query(RAGDocumentChunk).filter(
        RAGDocumentChunk.document_id == document_id,
        RAGDocumentChunk.user_id == target_user_id
    ).delete()

    # Delete document record
    db.delete(doc)
    db.commit()

    return {
        "success": True,
        "message": "Document and associated chunks deleted successfully.",
        "document_id": document_id
    }

@router.get("/{document_id}/url")
def get_document_signed_url(
    document_id: str,
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db)
):
    """
    Generates a secure, temporary signed download URL for an authorized document.
    Enforces strict ownership/caregiver authorization.
    Signed URL expiration is strictly <= 300 seconds. Never returns public URLs.
    """
    target_user_id = str(context["resolved_subject"]["id"])
    doc = db.query(RAGDocument).filter(
        RAGDocument.id == document_id,
        RAGDocument.user_id == target_user_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not doc.file_path:
        raise HTTPException(status_code=404, detail="Document raw file is not available.")

    bucket = getattr(storage_service, "default_bucket", "medical-documents")
    try:
        signed_url = storage_service.create_signed_download_url(
            bucket=bucket,
            object_path=doc.file_path,
            expires_in=300
        )
    except Exception as e:
        logger.error(f"Failed to generate signed download URL for {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate document download URL.")

    return {
        "document_id": doc.id,
        "title": doc.title,
        "download_url": signed_url,
        "expires_in": 300,
        "provider": storage_service.provider_name
    }

@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db)
):
    """
    Direct authenticated download endpoint.
    - If provider is Supabase: Redirects (HTTP 307) to the temporary signed URL (expiry <= 300s).
    - If provider is Local: Streams raw bytes with appropriate content headers.
    """
    target_user_id = str(context["resolved_subject"]["id"])
    doc = db.query(RAGDocument).filter(
        RAGDocument.id == document_id,
        RAGDocument.user_id == target_user_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not doc.file_path:
        raise HTTPException(status_code=404, detail="Document raw file is not available.")

    bucket = getattr(storage_service, "default_bucket", "medical-documents")
    if storage_service.provider_name == "supabase":
        signed_url = storage_service.create_signed_download_url(
            bucket=bucket,
            object_path=doc.file_path,
            expires_in=300
        )
        return RedirectResponse(url=signed_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # Local storage streaming
    try:
        file_bytes = storage_service.get_file_bytes(bucket, doc.file_path)
    except Exception:
        # Fallback for legacy absolute local paths
        if os.path.exists(doc.file_path):
            with open(doc.file_path, "rb") as f:
                file_bytes = f.read()
        else:
            raise HTTPException(status_code=404, detail="Physical file not found.")

    ext = os.path.splitext(doc.file_path)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = mime_map.get(ext, "application/octet-stream")
    safe_title = re.sub(r'[^a-zA-Z0-9._\- ]', '_', doc.title or "document")
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_title}{ext}"'}
    )

@router.get("/local-download")
def local_signed_download(
    bucket: str,
    key: str,
    expires: int,
    sig: str
):
    """
    Internal authenticated streaming endpoint for LocalStorageProvider HMAC-signed URLs.
    Validates HMAC signature and timestamp before releasing file bytes.
    """
    if storage_service.provider_name != "local":
        raise HTTPException(status_code=403, detail="Local download endpoint is not available.")

    local_provider = storage_service
    if not hasattr(local_provider, "verify_local_signed_url") or not local_provider.verify_local_signed_url(bucket, key, expires, sig):
        raise HTTPException(status_code=403, detail="Invalid or expired download signature.")

    try:
        file_bytes = local_provider.get_file_bytes(bucket, key)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found.")

    ext = os.path.splitext(key)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = mime_map.get(ext, "application/octet-stream")
    fname = os.path.basename(key)
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{fname}"'}
    )

