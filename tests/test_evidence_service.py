import pytest
from backend.services.evidence_service import create_evidence_graph


def test_create_evidence_graph_nodes_and_relationships():
    proc_doc = {
        "document_id": "doc_001",
        "filename": "inspection_report.pdf",
        "source": "inspection_report.pdf"
    }

    claims = [
        {
            "claim_id": "claim_001",
            "claim": "Device failed due to power surge.",
            "document_id": "doc_001",
            "source": "inspection_report.pdf"
        }
    ]

    evidence = [
        {
            "evidence_id": "evidence_001",
            "text": "Power board shows burn marks.",
            "document_id": "doc_001",
            "source": "inspection_report.pdf"
        }
    ]

    events = [
        {
            "event_id": "event_001",
            "date": "2026-08-02",
            "event": "Power failure occurred.",
            "document_id": "doc_001",
            "source": "inspection_report.pdf"
        }
    ]

    graph = create_evidence_graph(
        processed_document=proc_doc,
        claims=claims,
        evidence=evidence,
        events=events
    )

    assert "nodes" in graph
    assert "relationships" in graph

    node_types = {n["type"] for n in graph["nodes"]}
    assert "document" in node_types
    assert "claim" in node_types
    assert "evidence" in node_types
    assert "event" in node_types

    rel_types = {r["type"] for r in graph["relationships"]}
    assert "DOCUMENT_CONTAINS_CLAIM" in rel_types
    assert "DOCUMENT_CONTAINS_EVIDENCE" in rel_types
    assert "DOCUMENT_CONTAINS_EVENT" in rel_types
    assert "CLAIM_SUPPORTED_BY_EVIDENCE" in rel_types
    assert "CLAIM_ASSOCIATED_WITH_EVENT" in rel_types
    assert "EVIDENCE_ASSOCIATED_WITH_EVENT" in rel_types
