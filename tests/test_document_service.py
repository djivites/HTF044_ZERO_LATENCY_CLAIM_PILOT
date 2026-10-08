import pytest
import os
import tempfile
from backend.services.document_service import extract_document_text, process_document, register_extractor


def test_extract_document_text_valid_txt():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Inspection report: Device stopped working on 2026-08-02 due to power overload.")
        temp_path = f.name

    try:
        res = extract_document_text(temp_path)
        assert res["status"] == "success"
        assert "Inspection report" in res["text"]
        assert res["metadata"]["word_count"] > 0
    finally:
        os.remove(temp_path)


def test_extract_document_text_bytes():
    content = b"Sample text content in bytes format."
    res = extract_document_text(content, filename="test.txt")
    assert res["status"] == "success"
    assert res["text"] == "Sample text content in bytes format."
    assert res["filename"] == "test.txt"


def test_extract_document_text_empty():
    res = extract_document_text(b"", filename="empty.txt")
    assert res["status"] == "empty"
    assert res["text"] == ""
    assert res["error"] == "Document content is empty."


def test_extract_document_text_corrupted_pdf():
    # Invalid PDF bytes
    corrupted_bytes = b"%PDF-1.4 corrupted header data without valid PDF structure"
    res = extract_document_text(corrupted_bytes, filename="corrupted.pdf")
    assert res["status"] == "error"
    assert "Failed to extract text from PDF" in res["error"]


def test_process_document_structure():
    content = b"  Line 1  \n\n\n  Line 2  \n"
    res = process_document(content, filename="sample.txt", document_id="doc_123")
    assert res["document_id"] == "doc_123"
    assert res["filename"] == "sample.txt"
    assert res["source"] == "sample.txt"
    assert res["text"] == "Line 1\n\nLine 2"
    assert "metadata" in res


def test_modular_extractor_registration():
    def dummy_xml_extractor(content: bytes) -> str:
        return "extracted from xml"

    register_extractor(".xml", dummy_xml_extractor)
    res = extract_document_text(b"<root>test</root>", filename="data.xml")
    assert res["status"] == "success"
    assert res["text"] == "extracted from xml"
