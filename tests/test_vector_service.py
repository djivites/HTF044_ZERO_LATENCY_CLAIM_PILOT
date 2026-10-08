import pytest
from backend.services.vector_service import store_document_embeddings, store_evidence_embeddings


def test_store_document_embeddings():
    doc = {
        "document_id": "doc_vec_001",
        "filename": "inspection.pdf",
        "source": "inspection.pdf",
        "text": "This is a long document text. " * 30
    }
    res = store_document_embeddings(doc)
    assert res["status"] == "success"
    assert res["stored_count"] > 0
    assert res["document_id"] == "doc_vec_001"


def test_store_evidence_embeddings():
    evidence_list = [
        {
            "evidence_id": "ev_001",
            "text": "No physical damage observed.",
            "document_id": "doc_vec_001",
            "source": "inspection.pdf",
            "confidence": 0.95
        },
        {
            "evidence_id": "ev_002",
            "text": "Internal circuit burned.",
            "document_id": "doc_vec_001",
            "source": "inspection.pdf",
            "confidence": 0.90
        }
    ]
    res = store_evidence_embeddings(evidence_list)
    assert res["status"] == "success"
    assert res["stored_count"] == 2
    assert "evidence_ids" in res


def test_store_embeddings_empty_inputs():
    doc_res = store_document_embeddings({"document_id": "doc_empty", "text": ""})
    assert doc_res["status"] == "skipped"

    ev_res = store_evidence_embeddings([])
    assert ev_res["status"] == "skipped"


def test_pinecone_storage_mock(monkeypatch):
    from unittest.mock import MagicMock
    from backend.config import settings
    from backend.services.vector_service import store_document_embeddings

    monkeypatch.setattr(settings, "PINECONE_API_KEY", "pcsk_test_key_123")
    monkeypatch.setattr(settings, "PINECONE_INDEX_NAME", "test-index")
    monkeypatch.setattr(settings, "VECTOR_DB_TYPE", "pinecone")

    mock_index = MagicMock()
    mock_pinecone = MagicMock()
    mock_pinecone.Index.return_value = mock_index

    with monkeypatch.context() as m:
        m.setattr("pinecone.Pinecone", lambda api_key: mock_pinecone)
        doc = {
            "document_id": "doc_pc_001",
            "filename": "pc_report.pdf",
            "source": "pc_report.pdf",
            "text": "Pinecone test content"
        }
        res = store_document_embeddings(doc)
        assert res["status"] == "success"
        assert res["store"] == "pinecone"
        assert mock_index.upsert.called


def test_huggingface_api_embedding_mock(monkeypatch):
    from unittest.mock import MagicMock
    from backend.config import settings
    from backend.services.vector_service import _get_embedding

    monkeypatch.setattr(settings, "HUGGINGFACE_API_KEY", "hf_test_key_123")

    mock_response = MagicMock()
    mock_response.status_code = 200
    expected_embedding = [0.1] * settings.PINECONE_DIMENSION
    mock_response.json.return_value = [expected_embedding]

    with monkeypatch.context() as m:
        m.setattr("requests.post", lambda *args, **kwargs: mock_response)
        embedding = _get_embedding("Sample text for HF embedding")
        assert embedding == expected_embedding
