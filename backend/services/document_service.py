import io
import os
import uuid
import logging
import json
from pathlib import Path
from typing import Union, Optional, Dict, Any, BinaryIO

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _extract_txt(content_bytes: bytes) -> str:
    """Extract text from plain text or markdown content."""
    try:
        return content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return content_bytes.decode("latin-1", errors="replace")


def _extract_pdf(content_bytes: bytes) -> str:
    """Extract text from PDF file content using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def _extract_docx(content_bytes: bytes) -> str:
    """Extract text from DOCX file content using python-docx."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(content_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {str(e)}")
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")


def _extract_json(content_bytes: bytes) -> str:
    """Extract text from JSON file content."""
    try:
        text_str = _extract_txt(content_bytes)
        parsed = json.loads(text_str)
        if isinstance(parsed, dict):
            # Format dictionary into structured text lines
            lines = [f"{k}: {v}" for k, v in parsed.items()]
            return "\n".join(lines)
        elif isinstance(parsed, list):
            return "\n".join(str(item) for item in parsed)
        return text_str
    except Exception as e:
        logger.error(f"Error parsing JSON text: {str(e)}")
        return _extract_txt(content_bytes)


# Modular Extractor Registry mapping file extensions to extractor functions
EXTRACTOR_REGISTRY = {
    ".txt": _extract_txt,
    ".md": _extract_txt,
    ".markdown": _extract_txt,
    ".pdf": _extract_pdf,
    ".docx": _extract_docx,
    ".json": _extract_json,
}


def register_extractor(extension: str, extractor_func):
    """Allow adding additional document format extractors modularly."""
    ext = extension.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    EXTRACTOR_REGISTRY[ext] = extractor_func


def extract_document_text(
    file_input: Union[str, Path, bytes, BinaryIO],
    filename: Optional[str] = None,
    document_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Accepts a document file path, bytes, or file-like object and extracts readable text.
    
    Returns clean extracted text along with document metadata.
    Does NOT perform AI analysis. Handles empty, corrupted, or unsupported documents gracefully.
    """
    doc_id = document_id or f"doc_{uuid.uuid4().hex[:8]}"
    
    content_bytes: bytes = b""
    resolved_filename = filename or "document.txt"

    try:
        if isinstance(file_input, (str, Path)):
            path = Path(file_input)
            resolved_filename = filename or path.name
            if not path.exists():
                logger.warning(f"File not found: {file_input}")
                return {
                    "document_id": doc_id,
                    "filename": resolved_filename,
                    "text": "",
                    "source": resolved_filename,
                    "status": "error",
                    "error": f"File path does not exist: {file_input}",
                    "metadata": {"size_bytes": 0, "extension": path.suffix.lower()}
                }
            with open(path, "rb") as f:
                content_bytes = f.read()
        elif isinstance(file_input, bytes):
            content_bytes = file_input
        elif hasattr(file_input, "read"):
            content_bytes = file_input.read()
            if hasattr(file_input, "name") and not filename:
                resolved_filename = file_input.name
        else:
            return {
                "document_id": doc_id,
                "filename": resolved_filename,
                "text": "",
                "source": resolved_filename,
                "status": "error",
                "error": "Unsupported file input type provided.",
                "metadata": {"size_bytes": 0}
            }

        if not content_bytes or len(content_bytes.strip()) == 0:
            logger.warning(f"Empty document provided for {resolved_filename}")
            return {
                "document_id": doc_id,
                "filename": resolved_filename,
                "text": "",
                "source": resolved_filename,
                "status": "empty",
                "error": "Document content is empty.",
                "metadata": {"size_bytes": 0, "extension": Path(resolved_filename).suffix.lower()}
            }

        ext = Path(resolved_filename).suffix.lower()
        if not ext:
            ext = ".txt"

        extractor = EXTRACTOR_REGISTRY.get(ext)
        if not extractor:
            # Fallback to plain text extraction for unknown formats
            logger.info(f"No specific extractor found for {ext}, falling back to plain text extractor.")
            extractor = _extract_txt

        extracted_text = extractor(content_bytes)
        
        return {
            "document_id": doc_id,
            "filename": resolved_filename,
            "text": extracted_text,
            "source": resolved_filename,
            "status": "success",
            "metadata": {
                "size_bytes": len(content_bytes),
                "extension": ext,
                "character_count": len(extracted_text),
                "word_count": len(extracted_text.split())
            }
        }

    except Exception as e:
        logger.error(f"Error processing document {resolved_filename}: {str(e)}")
        return {
            "document_id": doc_id,
            "filename": resolved_filename,
            "text": "",
            "source": resolved_filename,
            "status": "error",
            "error": str(e),
            "metadata": {
                "size_bytes": len(content_bytes) if content_bytes else 0,
                "extension": Path(resolved_filename).suffix.lower()
            }
        }


def _clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    if not text:
        return ""
    # Replace non-standard line breaks and control characters
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines]
    # Remove excessive blank lines
    result_lines = []
    prev_blank = False
    for line in cleaned_lines:
        if not line:
            if not prev_blank:
                result_lines.append("")
                prev_blank = True
        else:
            result_lines.append(line)
            prev_blank = False
    return "\n".join(result_lines).strip()


def process_document(
    file_input: Union[str, Path, bytes, BinaryIO],
    filename: Optional[str] = None,
    document_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Coordinates document processing: calls extract_document_text(), cleans/normalizes
    extracted text, and returns a structured object ready for Gemma extraction.
    """
    raw_result = extract_document_text(file_input=file_input, filename=filename, document_id=document_id)
    
    cleaned_text = _clean_text(raw_result.get("text", ""))
    
    processed_doc = {
        "document_id": raw_result.get("document_id"),
        "filename": raw_result.get("filename"),
        "text": cleaned_text,
        "source": raw_result.get("source", raw_result.get("filename")),
        "metadata": raw_result.get("metadata", {}),
        "status": raw_result.get("status", "success"),
        "error": raw_result.get("error")
    }
    
    return processed_doc
