import io
import os
import tempfile
import logging
from typing import Dict, Any, Optional
from PIL import Image

from rag.processors.base_processor import BaseDocumentProcessor, ProcessedDocument
from rag.processors.normalizer import normalize_text
from ai.ocr_service import extract_text_from_image

logger = logging.getLogger(__name__)

class ImageDocumentProcessor(BaseDocumentProcessor):
    """
    Image Document Processor for PNG, JPG, JPEG, WEBP medical documents and prescriptions.
    Applies OCR to extract text from scanned images.
    """

    SUPPORTED_FORMATS = {'PNG', 'JPEG', 'JPG', 'WEBP'}

    def process_bytes(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()  # Validate image integrity
            # Reopen after verify
            img = Image.open(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image file '{filename}': {e}")

        # Save to temp file for OCR
        suffix = os.path.splitext(filename)[1].lower() or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(file_bytes)
            tf_path = tf.name

        try:
            return self._process_image_file(tf_path, filename, img)
        finally:
            if os.path.exists(tf_path):
                try:
                    os.remove(tf_path)
                except Exception:
                    pass

    def process_file(self, file_path: str, filename: str) -> ProcessedDocument:
        try:
            img = Image.open(file_path)
            img.verify()
            img = Image.open(file_path)
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image file '{filename}': {e}")

        return self._process_image_file(file_path, filename, img)

    def _process_image_file(self, file_path: str, filename: str, img: Image.Image) -> ProcessedDocument:
        raw_ocr_text = ""
        ocr_confidence: Optional[float] = None

        # Attempt direct pytesseract extraction
        try:
            import pytesseract
            raw_ocr_text = pytesseract.image_to_string(img).strip()
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confs = [float(c) for c in data.get('conf', []) if str(c).replace('.', '', 1).isdigit() and float(c) >= 0]
                if confs:
                    ocr_confidence = round(sum(confs) / len(confs), 2)
            except Exception:
                pass
        except Exception as ocr_err:
            logger.info(f"[ImageProcessor] pytesseract error ({ocr_err}). Using resilient ocr_service fallback.")
            raw_ocr_text = extract_text_from_image(file_path)

        cleaned_text = normalize_text(raw_ocr_text)

        metadata = {
            "image_format": img.format,
            "image_size": f"{img.width}x{img.height}",
            "image_mode": img.mode
        }

        return ProcessedDocument(
            text_by_page={1: cleaned_text},
            full_text=cleaned_text,
            page_count=1,
            metadata=metadata,
            extraction_method="ocr",
            ocr_used=True,
            ocr_confidence=ocr_confidence,
            source_type="image"
        )

image_processor = ImageDocumentProcessor()
