import io
import logging
from typing import Dict, Any, Optional
from PIL import Image
import fitz  # PyMuPDF

from rag.processors.base_processor import BaseDocumentProcessor, ProcessedDocument
from rag.processors.normalizer import normalize_text
from ai.ocr_service import extract_text_from_image

logger = logging.getLogger(__name__)

class PDFDocumentProcessor(BaseDocumentProcessor):
    """
    High-performance PDF Processor using PyMuPDF (fitz).
    Preserves page boundaries and falls back to OCR for scanned/image-only pages.
    """

    def process_bytes(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        return self._process_fitz_doc(doc, filename)

    def process_file(self, file_path: str, filename: str) -> ProcessedDocument:
        doc = fitz.open(file_path)
        return self._process_fitz_doc(doc, filename)

    def _process_fitz_doc(self, doc: fitz.Document, filename: str) -> ProcessedDocument:
        text_by_page: Dict[int, str] = {}
        ocr_used = False
        page_count = len(doc)
        raw_meta = doc.metadata or {}

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]
            extracted_page_text = page.get_text("text").strip()

            # If page text is sparse/empty (scanned page), perform OCR on rendered page image
            if len(extracted_page_text) < 20:
                logger.info(f"[PDFProcessor] Page {page_num} in '{filename}' has sparse native text ({len(extracted_page_text)} chars). Triggering OCR fallback.")
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # Run OCR
                    import pytesseract
                    ocr_text = pytesseract.image_to_string(img).strip()
                    if ocr_text:
                        extracted_page_text = ocr_text
                        ocr_used = True
                except Exception as ocr_err:
                    logger.warning(f"[PDFProcessor] OCR fallback warning on page {page_num}: {ocr_err}")
                    # If Tesseract binary is not installed, use fallback mock
                    from ai.ocr_service import extract_text_from_image
                    # Save temp image for fallback handler
                    import tempfile, os
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                        tf.write(img_bytes)
                        tf_path = tf.name
                    try:
                        fallback_txt = extract_text_from_image(tf_path)
                        if fallback_txt:
                            extracted_page_text = fallback_txt
                            ocr_used = True
                    finally:
                        if os.path.exists(tf_path):
                            try: os.remove(tf_path)
                            except: pass

            normalized_page = normalize_text(extracted_page_text)
            text_by_page[page_num] = normalized_page

        doc.close()

        full_text = "\n\n".join([f"--- Page {p} ---\n{text}" for p, text in text_by_page.items() if text.strip()])
        extraction_method = "native_with_ocr_fallback" if ocr_used else "native_text"

        return ProcessedDocument(
            text_by_page=text_by_page,
            full_text=full_text,
            page_count=page_count,
            metadata=raw_meta,
            extraction_method=extraction_method,
            ocr_used=ocr_used,
            source_type="pdf",
            doctor_name=raw_meta.get("author") if raw_meta.get("author") else None,
            document_date=raw_meta.get("creationDate") if raw_meta.get("creationDate") else None
        )

pdf_processor = PDFDocumentProcessor()
