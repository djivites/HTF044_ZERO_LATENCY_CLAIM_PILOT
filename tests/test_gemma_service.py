import pytest
from unittest.mock import patch
from backend.services.gemma_service import extract_claims, extract_evidence, extract_events, _clean_and_parse_json


def test_clean_and_parse_json_valid_markdown():
    raw = """Here is the extracted data:
```json
[
  {"claim": "The screen broke after impact.", "confidence": 0.95}
]
```
"""
    res = _clean_and_parse_json(raw)
    assert len(res) == 1
    assert res[0]["claim"] == "The screen broke after impact."


def test_clean_and_parse_json_malformed():
    raw = "Invalid json response without structure"
    res = _clean_and_parse_json(raw)
    assert res == []


def test_extract_claims_returns_structured_data():
    proc_doc = {
        "document_id": "doc_001",
        "filename": "inspection_report.pdf",
        "source": "inspection_report.pdf",
        "text": "The device failed due to physical damage. Company response claims water damage."
    }
    claims = extract_claims(proc_doc)
    assert isinstance(claims, list)
    assert len(claims) > 0
    first = claims[0]
    assert "claim_id" in first
    assert "claim" in first
    assert first["document_id"] == "doc_001"
    assert first["source"] == "inspection_report.pdf"
    assert "confidence" in first


def test_extract_evidence_returns_structured_data():
    proc_doc = {
        "document_id": "doc_001",
        "filename": "inspection_report.pdf",
        "source": "inspection_report.pdf",
        "text": "No external physical damage was observed during inspection."
    }
    evidence = extract_evidence(proc_doc)
    assert isinstance(evidence, list)
    assert len(evidence) > 0
    first = evidence[0]
    assert "evidence_id" in first
    assert "text" in first
    assert first["document_id"] == "doc_001"
    assert first["source"] == "inspection_report.pdf"


def test_extract_events_returns_structured_data():
    proc_doc = {
        "document_id": "doc_001",
        "filename": "complaint.pdf",
        "source": "complaint.pdf",
        "text": "Device stopped working on 2026-08-02. Repair technician visited on 2026-08-05."
    }
    events = extract_events(proc_doc)
    assert isinstance(events, list)
    assert len(events) > 0
    first = events[0]
    assert "event_id" in first
    assert "event" in first
    assert first["document_id"] == "doc_001"
    assert first["source"] == "complaint.pdf"


def test_extract_with_mocked_gemma_response():
    proc_doc = {
        "document_id": "doc_999",
        "source": "mock.pdf",
        "text": "Mock text content for test."
    }
    mock_response = '[{"claim": "Mock claim", "confidence": 0.99}]'
    with patch("backend.services.gemma_service._call_gemma_api", return_value=mock_response):
        claims = extract_claims(proc_doc)
        assert len(claims) == 1
        assert claims[0]["claim"] == "Mock claim"
        assert claims[0]["confidence"] == 0.99
