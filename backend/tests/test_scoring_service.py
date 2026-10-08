from __future__ import annotations

import random
from decimal import Decimal

import pytest

from backend.config import SCORE_WEIGHTS
from backend.models.schemas import (
    CaseAnalysis,
    Claim,
    ComponentScore,
    Document,
    DocumentReference,
    Event,
    Evidence,
    Finding,
    MissingEvidence,
    QuoteRef,
    RuleResult,
    ScoreResult,
)
from backend.services.scoring_service import (
    CHECKLISTS,
    ChecklistResult,
    _min_reliability,
    _resolve_favors,
    calculate_case_score,
    calculate_evidence_strength,
    evaluate_checklist,
    find_missing_evidence,
    score_case,
)


def make_document(doc_id: str, doc_type: str, status: str = "done") -> Document:
    return Document(id=doc_id, filename=f"{doc_id}.pdf", doc_type=doc_type, status=status)


def make_finding(
    fid: str,
    finding_type: str,
    *,
    severity: str = "medium",
    source: str = "rule",
    favors: str | None = None,
    quotes: list[QuoteRef] | None = None,
    left_item_id: str | None = None,
    right_item_id: str | None = None,
) -> Finding:
    return Finding(
        id=fid,
        finding_type=finding_type,
        source=source,
        severity=severity,
        favors=favors,
        explanation="test",
        left_item_id=left_item_id,
        right_item_id=right_item_id,
        quotes=quotes or [],
    )


@pytest.mark.parametrize(
    "fid, finding, docs, expected",
    [
        ("T1", make_finding("T1", "contradiction", source="model_verified", quotes=[QuoteRef(doc_id="D1", page=1, quote="x", verified=True)]), [make_document("D1", "inspection_report")], "low"),
    ],
)
def test_evidence_strength_table(fid, finding, docs, expected):
    assert calculate_evidence_strength(finding, docs) == expected


def test_calculate_evidence_strength_examples():
    docs = [
        make_document("D1", "inspection_report"),
        make_document("D2", "warranty_terms"),
        make_document("D3", "company_response"),
        make_document("D4", "email_thread"),
    ]
    f1 = make_finding("K1", "contradiction", source="model_verified", quotes=[QuoteRef(doc_id="D3", page=1, quote="a", verified=True), QuoteRef(doc_id="D1", page=2, quote="b", verified=True)])
    assert calculate_evidence_strength(f1, docs) == "medium"
    f2 = make_finding("K2", "date_mismatch", source="rule", quotes=[QuoteRef(doc_id="D3", page=1, quote="a", verified=True), QuoteRef(doc_id="D4", page=1, quote="b", verified=True)])
    assert calculate_evidence_strength(f2, docs) == "high"
    f3 = make_finding("K3", "unsupported_claim", source="rule", quotes=[QuoteRef(doc_id="D3", page=1, quote="a", verified=True)])
    assert calculate_evidence_strength(f3, docs) == "medium"
    f4 = make_finding("K4", "contradiction", source="rule", quotes=[QuoteRef(doc_id="D1", page=1, quote="a", verified=False), QuoteRef(doc_id="D2", page=1, quote="b", verified=True)])
    assert calculate_evidence_strength(f4, docs) == "low"


def test_checklist_fallback_and_event_coverage():
    docs = [make_document("D1", "invoice", "done")]
    events = [Event(id="E1", source_doc_id="D1", page=1, event_type="purchase", date="2026-01-10", date_text="10 Jan 2026", quote="purchase", quote_verified=True)]
    result = evaluate_checklist("warranty", docs, events)
    assert "proof_of_purchase" in result.covered_keys
    assert "purchase_date_known" in result.covered_keys
    assert result.total == len(CHECKLISTS["warranty"])


def test_find_missing_evidence_basic_and_reference_matching():
    docs = [
        Document(id="D1", filename="invoice.pdf", doc_type="invoice", status="done"),
        Document(id="D2", filename="warranty.pdf", doc_type="warranty_terms", status="done"),
        Document(id="D3", filename="company_reply.pdf", doc_type="company_response", status="done"),
        Document(id="D4", filename="repair_report.pdf", doc_type="inspection_report", status="done"),
        Document(id="D5", filename="emails.txt", doc_type="email_thread", status="done"),
        Document(id="D6", filename="laptop_damage.jpg", doc_type="photo", status="done"),
    ]
    events = [
        Event(id="E1", source_doc_id="D1", page=1, event_type="purchase", date="2026-01-10", date_text="10 Jan 2026", quote="purchase", quote_verified=True),
        Event(id="E2", source_doc_id="D4", page=1, event_type="failure_reported", date="2026-08-02", date_text="2 Aug 2026", quote="reported", quote_verified=True),
    ]
    refs = [DocumentReference(id="R1", source_doc_id="D4", page=2, name="Annex A photographs", quote="Annex A", quote_verified=True)]
    missing = find_missing_evidence("warranty", docs, events, refs)
    assert any(item.key == "ref:annex a" for item in missing)
    assert all(item.triggered_by == "referenced_but_not_uploaded" for item in missing if item.key.startswith("ref:"))


def test_score_case_example_a_exact_numbers():
    docs = [
        make_document("D1", "invoice"),
        make_document("D2", "warranty_terms"),
        make_document("D3", "company_response"),
        make_document("D4", "inspection_report"),
        make_document("D5", "email_thread"),
        make_document("D6", "photo"),
    ]
    claims = [
        Claim(id="C1", source_doc_id="D3", page=1, speaker="company", kind="denial", text="not covered", quote="not covered", quote_verified=True),
        Claim(id="C2", source_doc_id="D1", page=1, speaker="user", kind="assertion", text="purchase", quote="purchase", quote_verified=True),
    ]
    findings = [
        make_finding("K1", "contradiction", severity="high", source="model_verified", favors="user", quotes=[QuoteRef(doc_id="D3", page=1, quote="x", verified=True), QuoteRef(doc_id="D4", page=2, quote="y", verified=True)], left_item_id="C1"),
        make_finding("K2", "date_mismatch", severity="medium", source="rule", favors="user", quotes=[QuoteRef(doc_id="D3", page=1, quote="x", verified=True), QuoteRef(doc_id="D5", page=1, quote="y", verified=True)]),
        make_finding("K3", "unsupported_claim", severity="medium", source="rule", favors="user", quotes=[QuoteRef(doc_id="D3", page=1, quote="x", verified=True)]),
        make_finding("K4", "support", severity="medium", source="model_verified", favors="user", quotes=[QuoteRef(doc_id="D1", page=1, quote="x", verified=True), QuoteRef(doc_id="D2", page=1, quote="y", verified=True)]),
        make_finding("K5", "support", severity="medium", source="model_verified", favors="company", quotes=[QuoteRef(doc_id="D2", page=1, quote="x", verified=True), QuoteRef(doc_id="D3", page=1, quote="y", verified=True)]),
    ]
    checklist = evaluate_checklist("warranty", docs, [])
    # Force 6 covered of 8
    checklist = ChecklistResult(category="warranty", total=8, covered_keys=("proof_of_purchase", "warranty_terms", "company_rejection", "inspection_report", "condition_photos", "support_correspondence"), missing_items=tuple(), basis="checklist")
    result = calculate_case_score(claims, [], findings, checklist, [RuleResult(rule_id="R1", evaluated=True, passed=True), RuleResult(rule_id="R2", evaluated=True, passed=False), RuleResult(rule_id="R3", evaluated=True, passed=True), RuleResult(rule_id="R4", evaluated=True, passed=False), RuleResult(rule_id="R5", evaluated=False, passed=None)], docs)
    assert result.evidence_score == 74
    assert result.band == "Moderate"


def test_score_case_example_b_and_c():
    docs = [make_document("D1", "invoice")]
    empty_checklist = evaluate_checklist("warranty", docs, [])
    score_b = calculate_case_score([], [], [], empty_checklist, [], docs)
    assert score_b.evidence_score == 48
    assert score_b.band == "Mixed"
    assert any("Not enough verified material" in note for note in score_b.notes)
    no_items = ChecklistResult(category="generic", total=0, covered_keys=(), missing_items=tuple(), basis="none")
    score_c = calculate_case_score([], [], [], no_items, [], docs)
    assert score_c.evidence_score == 58
    assert score_c.band == "Mixed"


def test_property_determinism_and_range():
    random.seed(1234)
    docs = [make_document("D1", "invoice"), make_document("D2", "warranty_terms")]
    findings = [
        make_finding("K1", "contradiction", severity="high", source="model_verified", favors="user", quotes=[QuoteRef(doc_id="D1", page=1, quote="a", verified=True), QuoteRef(doc_id="D2", page=1, quote="b", verified=True)]),
        make_finding("K2", "support", severity="medium", source="model_verified", favors="company", quotes=[QuoteRef(doc_id="D1", page=1, quote="a", verified=True), QuoteRef(doc_id="D2", page=1, quote="b", verified=True)]),
    ]
    checklist = evaluate_checklist("warranty", docs, [])
    s1 = calculate_case_score([], [], findings, checklist, [], docs)
    s2 = calculate_case_score([], [], list(reversed(findings)), checklist, [], docs)
    assert s1.model_dump() == s2.model_dump()
    for _ in range(200):
        score = calculate_case_score([], [], findings, checklist, [], docs)
        assert 0 <= score.evidence_score <= 100


def test_resolve_favors_table():
    claims = {
        "C1": Claim(id="C1", source_doc_id="D1", page=1, speaker="company", kind="denial", text="", quote="", quote_verified=True),
        "C2": Claim(id="C2", source_doc_id="D1", page=1, speaker="user", kind="assertion", text="", quote="", quote_verified=True),
    }
    assert _resolve_favors(make_finding("F1", "contradiction", favors=None, left_item_id="C1"), claims) == "user"
    assert _resolve_favors(make_finding("F2", "contradiction", favors=None, left_item_id="C2"), claims) == "company"
    assert _resolve_favors(make_finding("F3", "support", favors=None, left_item_id="C1"), claims) == "company"
    assert _resolve_favors(make_finding("F4", "support", favors=None, left_item_id="C2"), claims) == "user"
    assert _resolve_favors(make_finding("F5", "unsupported_claim", favors=None, left_item_id="C1"), claims) == "user"
    assert _resolve_favors(make_finding("F6", "unsupported_claim", favors=None, left_item_id="C2"), claims) == "company"
    assert _resolve_favors(make_finding("F7", "date_mismatch", favors=None), claims) == "neutral"
    assert _resolve_favors(make_finding("F8", "amount_mismatch", favors=None), claims) == "neutral"
    assert _resolve_favors(make_finding("F9", "window_check", favors=None), claims) == "neutral"


def test_weights_sum_to_one_and_score_case_bundle():
    assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9
    case = CaseAnalysis(case_id="CASE-1", category="warranty", documents=[make_document("D1", "invoice")], claims=[], evidence=[], events=[], contradictions=[], references=[])
    bundle = score_case(case)
    assert isinstance(bundle.score, ScoreResult)
    assert isinstance(bundle.missing_evidence, list)
    assert isinstance(bundle.findings, list)


def test_missing_evidence_no_documents_and_failed_document():
    missing = find_missing_evidence("warranty", [], [], [])
    assert len(missing) == 8
    docs = [make_document("D1", "invoice", "failed")]
    checklist = evaluate_checklist("warranty", docs, [])
    assert "proof_of_purchase" not in checklist.covered_keys


if __name__ == "__main__":
    pytest.main(["-q", __file__])
