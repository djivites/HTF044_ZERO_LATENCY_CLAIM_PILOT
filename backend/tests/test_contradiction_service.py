import asyncio

from fastapi.testclient import TestClient

from backend.api.analysis import score_analysis_endpoint
from backend.main import app
from backend.models.schemas import CaseAnalysis, Claim, Evidence
from backend.services.contradiction_service import detect_contradictions


def test_detect_contradictions_preserves_unverified_source_status():
    claim = Claim(
        id="claim-1",
        source_doc_id="doc-company",
        page=1,
        speaker="company",
        kind="denial",
        text="The laptop screen has physical damage from a drop.",
        quote="The laptop screen has physical damage from a drop.",
    )
    evidence = Evidence(
        id="evidence-1",
        source_doc_id="doc-report",
        page=2,
        text="The laptop screen has no physical damage or drop marks.",
        quote="The laptop screen has no physical damage or drop marks.",
    )

    findings = detect_contradictions([claim], [evidence])

    assert len(findings) == 1
    assert findings[0].finding_type == "contradiction"
    assert findings[0].favors == "user"
    assert [quote.verified for quote in findings[0].quotes] == [False, False]


def test_score_endpoint_returns_score_findings_and_missing_evidence():
    case = CaseAnalysis(case_id="case-1", category="generic")

    result = asyncio.run(score_analysis_endpoint(case))

    assert 0 <= result["score"]["evidence_score"] <= 100
    assert isinstance(result["missing_evidence"], list)
    assert result["findings"] == []


def test_case_lifecycle_exposes_scoring_and_response():
    client = TestClient(app)
    created = client.post(
        "/api/v1/cases/",
        json={"title": "API audit smoke test", "description": "Test case", "category": "generic"},
    )
    assert created.status_code == 200
    case_id = created.json()["case_id"]

    try:
        uploaded = client.post(
            f"/api/v1/cases/{case_id}/documents",
            files={
                "files": (
                    "invoice.txt",
                    b"Purchase invoice dated 2025-01-01. The company denied the claim for damage. The inspection report states no physical damage.",
                    "text/plain",
                )
            },
        )
        assert uploaded.status_code == 200
        assert client.post(f"/api/v1/cases/{case_id}/analyze").status_code == 200

        scored = client.post(f"/api/v1/cases/{case_id}/score")
        assert scored.status_code == 200
        assert 0 <= scored.json()["score"]["evidence_score"] <= 100

        response = client.post(
            f"/api/v1/cases/{case_id}/response",
            json={"recipient_name": "Example Company", "sender_name": "Example Claimant"},
        )
        assert response.status_code == 200
        assert response.json()["full_text"]
    finally:
        client.delete(f"/api/v1/cases/{case_id}")