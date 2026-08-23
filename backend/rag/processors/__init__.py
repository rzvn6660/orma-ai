import os
from typing import Optional

from rag.processors.base_processor import BaseDocumentProcessor, ProcessedDocument
from rag.processors.pdf_processor import PDFDocumentProcessor, pdf_processor
from rag.processors.docx_processor import DOCXDocumentProcessor, docx_processor
from rag.processors.image_processor import ImageDocumentProcessor, image_processor
from rag.processors.normalizer import normalize_text

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.png', '.jpg', '.jpeg', '.webp'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/png',
    'image/jpeg',
    'image/jpg',
    'image/webp'
}

def get_document_processor(filename: str, mime_type: Optional[str] = None) -> BaseDocumentProcessor:
    """
    Factory function returning the appropriate format processor.
    Validates file extension against allowed whitelist.
    """
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        # Fallback to mime type check
        if mime_type == 'application/pdf':
            return pdf_processor
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return docx_processor
        elif mime_type in {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}:
            return image_processor
        raise ValueError(f"File '{filename}' has no extension and unrecognized MIME type.")

    if ext == '.pdf':
        return pdf_processor
    elif ext == '.docx':
        return docx_processor
    elif ext in {'.png', '.jpg', '.jpeg', '.webp'}:
        return image_processor
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Supported formats: PDF, DOCX, PNG, JPG, JPEG, WEBP.")
