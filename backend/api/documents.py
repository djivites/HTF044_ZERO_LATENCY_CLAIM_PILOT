"""
Documents Router — /api/v1/documents
Handles file uploads and text extraction.
"""
import uuid
import logging
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse

from backend.services.document_service import process_document

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", summary="Upload one or more documents for text extraction")
async def upload_documents(
    files: List[UploadFile] = File(..., description="PDF, DOCX, TXT, MD or JSON files"),
    case_id: str = Form(default="", description="Optional case ID to associate documents with"),
):
    """
    Accepts one or more files, extracts their text, and returns structured
    document objects ready for evidence analysis.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    results = []
    for upload in files:
        content = await upload.read()
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        result = process_document(
            file_input=content,
            filename=upload.filename,
            document_id=doc_id,
        )
        result["case_id"] = case_id or None
        results.append(result)
        logger.info(
            f"Processed document: {upload.filename} → status={result.get('status')} "
            f"chars={result.get('metadata', {}).get('character_count', 0)}"
        )

    return JSONResponse(
        status_code=200,
        content={
            "message": f"{len(results)} document(s) processed.",
            "documents": results,
        },
    )


@router.post("/extract-text", summary="Extract text from a single document")
async def extract_text(file: UploadFile = File(...)):
    """Extract raw text from a single uploaded file."""
    content = await file.read()
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    result = process_document(file_input=content, filename=file.filename, document_id=doc_id)

    if result.get("status") == "error":
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "Failed to extract text from document."),
        )

    return {
        "document_id": result["document_id"],
        "filename": result["filename"],
        "status": result["status"],
        "text": result["text"],
        "metadata": result["metadata"],
    }
