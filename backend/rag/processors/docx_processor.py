import io
import zipfile
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, Optional, List

from rag.processors.base_processor import BaseDocumentProcessor, ProcessedDocument
from rag.processors.normalizer import normalize_text

logger = logging.getLogger(__name__)

# XML Namespaces in standard Office Open XML (.docx)
WORD_NAMESPACE = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
CORE_NAMESPACE = 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'
DC_NAMESPACE = 'http://purl.org/dc/elements/1.1/'
CP_NAMESPACE = 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'
APP_NAMESPACE = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'

NAMESPACES = {
    'w': WORD_NAMESPACE,
    'cp': CP_NAMESPACE,
    'dc': DC_NAMESPACE,
    'ep': APP_NAMESPACE
}

class DOCXDocumentProcessor(BaseDocumentProcessor):
    """
    Zero-dependency, high-speed DOCX processor.
    Extracts structured paragraphs, headings, and tables from Office Open XML.
    """

    def process_bytes(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        bio = io.BytesIO(file_bytes)
        return self._extract_docx(bio, filename)

    def process_file(self, file_path: str, filename: str) -> ProcessedDocument:
        with open(file_path, 'rb') as f:
            bio = io.BytesIO(f.read())
        return self._extract_docx(bio, filename)

    def _extract_docx(self, zip_source: io.BytesIO, filename: str) -> ProcessedDocument:
        metadata: Dict[str, Any] = {}
        page_count = 1
        doctor_name = None
        doc_date = None

        try:
            with zipfile.ZipFile(zip_source, 'r') as zf:
                # 1. Extract Core Properties (author, title, creation date)
                if 'docProps/core.xml' in zf.namelist():
                    try:
                        core_xml = zf.read('docProps/core.xml')
                        core_root = ET.fromstring(core_xml)
                        creator_elem = core_root.find('dc:creator', NAMESPACES)
                        if creator_elem is not None and creator_elem.text:
                            metadata['creator'] = creator_elem.text
                            doctor_name = creator_elem.text

                        date_elem = core_root.find('cp:created', NAMESPACES) or core_root.find('dc:date', NAMESPACES)
                        if date_elem is not None and date_elem.text:
                            metadata['date'] = date_elem.text
                            doc_date = date_elem.text

                        title_elem = core_root.find('dc:title', NAMESPACES)
                        if title_elem is not None and title_elem.text:
                            metadata['title'] = title_elem.text
                    except Exception as e:
                        logger.warning(f"[DOCXProcessor] Error parsing core metadata: {e}")

                # 2. Extract App Properties (page count estimation)
                if 'docProps/app.xml' in zf.namelist():
                    try:
                        app_xml = zf.read('docProps/app.xml')
                        app_root = ET.fromstring(app_xml)
                        pages_elem = app_root.find('ep:Pages', NAMESPACES)
                        if pages_elem is not None and pages_elem.text and pages_elem.text.isdigit():
                            page_count = max(1, int(pages_elem.text))
                    except Exception as e:
                        logger.warning(f"[DOCXProcessor] Error parsing app properties: {e}")

                # 3. Extract Document Body (paragraphs, headings, tables)
                if 'word/document.xml' not in zf.namelist():
                    raise ValueError(f"Invalid DOCX file: 'word/document.xml' missing in {filename}")

                doc_xml = zf.read('word/document.xml')
                doc_root = ET.fromstring(doc_xml)
                body = doc_root.find('w:body', NAMESPACES)

                if body is None:
                    raise ValueError(f"Invalid DOCX file: body element missing in {filename}")

                extracted_blocks: List[str] = []

                for child in body:
                    tag = child.tag
                    if tag == f"{{{WORD_NAMESPACE}}}p":
                        # Paragraph
                        p_text = self._extract_paragraph_text(child)
                        if p_text.strip():
                            extracted_blocks.append(p_text.strip())
                    elif tag == f"{{{WORD_NAMESPACE}}}tbl":
                        # Table
                        tbl_text = self._extract_table_text(child)
                        if tbl_text.strip():
                            extracted_blocks.append(tbl_text.strip())

                raw_full_text = "\n\n".join(extracted_blocks)
                cleaned_text = normalize_text(raw_full_text)

                text_by_page = {1: cleaned_text}

                return ProcessedDocument(
                    text_by_page=text_by_page,
                    full_text=cleaned_text,
                    page_count=page_count,
                    metadata=metadata,
                    extraction_method="docx_parser",
                    ocr_used=False,
                    source_type="docx",
                    doctor_name=doctor_name,
                    document_date=doc_date
                )

        except zipfile.BadZipFile:
            raise ValueError(f"File '{filename}' is not a valid DOCX zip archive.")

    def _extract_paragraph_text(self, p_elem: ET.Element) -> str:
        # Check if heading
        pStyle = p_elem.find('.//w:pStyle', NAMESPACES)
        style_val = pStyle.attrib.get(f"{{{WORD_NAMESPACE}}}val", "") if pStyle is not None else ""
        
        runs_text = []
        for t in p_elem.findall('.//w:t', NAMESPACES):
            if t.text:
                runs_text.append(t.text)

        p_str = "".join(runs_text).strip()
        if not p_str:
            return ""

        if "heading" in style_val.lower():
            return f"## {p_str}"
        return p_str

    def _extract_table_text(self, tbl_elem: ET.Element) -> str:
        rows_text = []
        for tr in tbl_elem.findall('.//w:tr', NAMESPACES):
            cell_texts = []
            for tc in tr.findall('.//w:tc', NAMESPACES):
                tc_runs = []
                for t in tc.findall('.//w:t', NAMESPACES):
                    if t.text:
                        tc_runs.append(t.text)
                cell_str = "".join(tc_runs).strip()
                cell_texts.append(cell_str if cell_str else "-")
            if any(c != "-" for c in cell_texts):
                rows_text.append(" | ".join(cell_texts))

        if not rows_text:
            return ""
        return "\n".join(rows_text)

docx_processor = DOCXDocumentProcessor()
