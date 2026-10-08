from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Mapping, Sequence

from rapidfuzz import fuzz

from backend.config import (
    CONTRADICTION_SATURATION,
    DOC_RELIABILITY,
    DEFAULT_RELIABILITY,
    SCORE_BANDS,
    SCORE_WEIGHTS,
    SEVERITY_RANK,
    SEVERITY_WEIGHT,
)
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
    Severity,
)

logger = logging.getLogger(__name__)

assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9

SCORING_FINDING_TYPES = {
    "contradiction",
    "unsupported_claim",
    "date_mismatch",
    "amount_mismatch",
    "sequence_anomaly",
    "window_check",
}
ABSENCE_FINDING_TYPES = {"unsupported_claim", "missing_reference"}


@dataclass(frozen=True)
class ChecklistItem:
    key: str
    label: str
    why_it_matters: str
    priority: Severity
    doc_types: frozenset[str] = frozenset()
    event_type: str | None = None


@dataclass(frozen=True)
class ChecklistResult:
    category: str
    total: int
    covered_keys: tuple[str, ...]
    missing_items: tuple[ChecklistItem, ...]
    basis: str


@dataclass(frozen=True)
class ScoringBundle:
    score: ScoreResult
    missing_evidence: list[MissingEvidence]
    findings: list[Finding]


CHECKLISTS: dict[str, tuple[ChecklistItem, ...]] = {
    "warranty": (
        ChecklistItem(
            "proof_of_purchase",
            "Proof of purchase (invoice or receipt)",
            "Shows what was bought, when, and for how much, which anchors the warranty period.",
            "high",
            frozenset({"invoice", "receipt"}),
        ),
        ChecklistItem(
            "warranty_terms",
            "Warranty terms and conditions",
            "Defines what is covered, what is excluded, and any evidence the company must provide.",
            "high",
            frozenset({"warranty_terms", "contract"}),
        ),
        ChecklistItem(
            "company_rejection",
            "Written rejection from the company",
            "States the exact reason given, which every other document is compared against.",
            "high",
            frozenset({"company_response"}),
        ),
        ChecklistItem(
            "inspection_report",
            "Inspection or repair report",
            "Independent findings about the cause of the fault are the strongest evidence for or against the stated reason.",
            "high",
            frozenset({"inspection_report"}),
        ),
        ChecklistItem(
            "condition_photos",
            "Photographs of the product's condition",
            "Dated photos help show the condition of the product before and after the fault.",
            "medium",
            frozenset({"photo"}),
        ),
        ChecklistItem(
            "support_correspondence",
            "Support emails or ticket history",
            "Shows when the fault was reported and how the company responded.",
            "medium",
            frozenset({"email_thread"}),
        ),
        ChecklistItem(
            "purchase_date_known",
            "A clearly stated purchase date",
            "Needed to check the claim falls inside the warranty period.",
            "medium",
            event_type="purchase",
        ),
        ChecklistItem(
            "failure_date_known",
            "A clearly stated date the fault was reported",
            "Needed to check the fault was reported in time and to build the timeline.",
            "medium",
            event_type="failure_reported",
        ),
    ),
    "rental": (
        ChecklistItem(
            "rental_agreement",
            "Rental agreement",
            "Defines the deposit, the condition obligations and the deduction terms.",
            "high",
            frozenset({"contract"}),
        ),
        ChecklistItem(
            "deposit_receipt",
            "Proof of deposit payment",
            "Proves how much deposit was paid and when.",
            "high",
            frozenset({"receipt", "invoice"}),
        ),
        ChecklistItem(
            "move_in_inspection",
            "Move-in inspection report",
            "Records the condition of the property at the start, which deductions are compared against.",
            "high",
            frozenset({"inspection_report"}),
        ),
        ChecklistItem(
            "move_in_photos",
            "Move-in photographs",
            "Dated photos show the condition before the tenancy started.",
            "medium",
            frozenset({"photo"}),
        ),
        ChecklistItem(
            "deduction_notice",
            "Deduction notice from the landlord",
            "States exactly what was deducted and why.",
            "high",
            frozenset({"company_response"}),
        ),
        ChecklistItem(
            "correspondence",
            "Emails or messages with the landlord",
            "Shows what was agreed or disputed during and after the tenancy.",
            "medium",
            frozenset({"email_thread"}),
        ),
    ),
    "insurance": (
        ChecklistItem(
            "policy_document",
            "Insurance policy document",
            "Defines the coverage, exclusions and the policy period.",
            "high",
            frozenset({"contract", "warranty_terms"}),
        ),
        ChecklistItem(
            "incident_report",
            "Incident or assessment report",
            "Independent description of what happened and the damage.",
            "high",
            frozenset({"inspection_report"}),
        ),
        ChecklistItem(
            "incident_photos",
            "Photographs of the incident or damage",
            "Dated photos support what the incident report says.",
            "medium",
            frozenset({"photo"}),
        ),
        ChecklistItem(
            "insurer_decision",
            "Insurer's written decision",
            "States the exact reason the claim was rejected or reduced.",
            "high",
            frozenset({"company_response"}),
        ),
        ChecklistItem(
            "supporting_invoices",
            "Invoices or receipts for the loss",
            "Show the value of what was lost or the cost of repair.",
            "medium",
            frozenset({"invoice", "receipt"}),
        ),
        ChecklistItem(
            "correspondence",
            "Emails or letters with the insurer",
            "Shows what was reported and how the insurer responded.",
            "medium",
            frozenset({"email_thread"}),
        ),
    ),
    "service": (
        ChecklistItem(
            "service_agreement",
            "Service agreement or terms",
            "Defines what was promised, the price and the cancellation or refund terms.",
            "high",
            frozenset({"contract", "warranty_terms"}),
        ),
        ChecklistItem(
            "payment_proof",
            "Proof of payment",
            "Proves what was paid and when.",
            "high",
            frozenset({"invoice", "receipt"}),
        ),
        ChecklistItem(
            "provider_response",
            "Provider's written response",
            "States the provider's reason for refusing the refund or remedy.",
            "high",
            frozenset({"company_response"}),
        ),
        ChecklistItem(
            "correspondence",
            "Emails or messages with the provider",
            "Shows when requests were made and how the provider responded.",
            "medium",
            frozenset({"email_thread"}),
        ),
        ChecklistItem(
            "work_evidence",
            "Evidence of the work or service delivered",
            "Shows the quality or completion of the work or service.",
            "medium",
            frozenset({"photo", "inspection_report"}),
        ),
    ),
    "generic": (
        ChecklistItem(
            "transaction_record",
            "Record of the transaction",
            "Shows what was agreed or purchased and for how much.",
            "high",
            frozenset({"invoice", "receipt", "contract"}),
        ),
        ChecklistItem(
            "company_response",
            "Written response from the other party",
            "States the exact reason given for the decision.",
            "high",
            frozenset({"company_response"}),
        ),
        ChecklistItem(
            "correspondence",
            "Emails or messages between the parties",
            "Shows the sequence of requests and replies.",
            "medium",
            frozenset({"email_thread"}),
        ),
    ),
}


def _required_quotes(f: Finding) -> int:
    return 1 if f.finding_type in ABSENCE_FINDING_TYPES else 2


def _is_verified(f: Finding) -> bool:
    return len(f.quotes) >= _required_quotes(f) and all(q.verified for q in f.quotes)


def _reliability_of(doc_id: str, docs_by_id: Mapping[str, Document], table) -> float:
    d = docs_by_id.get(doc_id)
    if d is None:
        return DEFAULT_RELIABILITY
    return table.get(d.doc_type, DEFAULT_RELIABILITY)


def _min_reliability(f: Finding, docs_by_id: Mapping[str, Document], table) -> float:
    if not f.quotes:
        return DEFAULT_RELIABILITY
    reliabilities = [_reliability_of(q.doc_id, docs_by_id, table) for q in f.quotes]
    return min(reliabilities) if reliabilities else DEFAULT_RELIABILITY


def _resolve_favors(f: Finding, claims_by_id: Mapping[str, Claim]) -> str:
    if f.favors is not None:
        return f.favors
    for item_id in (f.left_item_id, f.right_item_id):
        if item_id and item_id in claims_by_id:
            claim = claims_by_id[item_id]
            if f.finding_type == "contradiction":
                return "user" if claim.speaker == "company" else "company" if claim.speaker == "user" else "neutral"
            if f.finding_type == "support":
                return "company" if claim.speaker == "company" else "user" if claim.speaker == "user" else "neutral"
            if f.finding_type == "unsupported_claim":
                return "user" if claim.speaker == "company" else "company" if claim.speaker == "user" else "neutral"
    if f.finding_type in {"date_mismatch", "amount_mismatch", "sequence_anomaly", "window_check"}:
        return "neutral"
    return "neutral"


def _normalise_category(category: str | None) -> str:
    value = str(category or "").strip().lower()
    return value if value in CHECKLISTS else "generic"


def evaluate_checklist(category: str, documents: Sequence[Document], events: Sequence[Event]) -> ChecklistResult:
    """Evaluate a category checklist against uploaded documents and dated events.

    Inputs: category name, uploaded documents, and event records.
    Outputs: the checklist result containing the total count, covered keys and the missing items.
    Edge cases: missing/empty category falls back to generic; failed or pending documents never count.
    """
    key = _normalise_category(category)
    items = CHECKLISTS.get(key, CHECKLISTS["generic"])
    covered: list[str] = []
    missing: list[ChecklistItem] = []
    doc_map = {d.id: d for d in documents}
    for item in items:
        is_covered = False
        for document in documents:
            if document.status != "done":
                continue
            if item.doc_types and document.doc_type in item.doc_types:
                is_covered = True
                break
        if not is_covered and item.event_type:
            is_covered = any(
                event.event_type == item.event_type and event.date is not None and event.quote_verified is True
                for event in events
            )
        if is_covered:
            covered.append(item.key)
        else:
            missing.append(item)
    return ChecklistResult(
        category=key,
        total=len(items),
        covered_keys=tuple(covered),
        missing_items=tuple(missing),
        basis="checklist" if items else "none",
    )


def find_missing_evidence(
    category: str,
    documents: Sequence[Document],
    events: Sequence[Event],
    references: Sequence[DocumentReference],
) -> list[MissingEvidence]:
    """Return missing checklist items and references that were mentioned but not uploaded.

    Inputs: category, uploaded documents, events, and referenced documents.
    Outputs: a list of MissingEvidence entries sorted by priority and order.
    Edge cases: no documents, unknown source document ids, duplicate invalid references and empty inputs are handled safely.
    """
    checklist = evaluate_checklist(category, documents, events)
    results: list[MissingEvidence] = []
    order = 0
    for item in checklist.missing_items:
        results.append(
            MissingEvidence(
                key=item.key,
                label=item.label,
                why_it_matters=item.why_it_matters,
                priority=item.priority,
                triggered_by="checklist",
                referencing_quote=None,
            )
        )
        order += 1

    seen_keys: set[str] = set()
    for ref in references:
        if not ref.quote_verified:
            continue
        norm_name = re.sub(r"[^a-z0-9]+", " ", str(ref.name).lower().replace("_", " ")).strip()
        match = re.search(r"\b(annex|annexure|appendix|attachment|enclosure|exhibit|schedule)\s+([a-z0-9]+)\b", norm_name)
        designator = f"{match.group(1)} {match.group(2)}" if match else None
        key = f"ref:{designator or norm_name or 'reference'}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        local_name = next((d.filename for d in documents if d.id == ref.source_doc_id), "an uploaded document")
        matched = False
        if designator:
            designator_norm = re.sub(r"[^a-z0-9]+", " ", designator).strip()
            for document in documents:
                doc_norm = re.sub(r"[^a-z0-9]+", " ", document.filename.lower().replace("_", " ")).strip()
                if designator_norm in doc_norm:
                    matched = True
                    break
        if not matched:
            for document in documents:
                doc_norm = re.sub(r"[^a-z0-9]+", " ", document.filename.lower().replace("_", " ")).strip()
                if doc_norm and fuzz.token_set_ratio(norm_name, doc_norm) >= 85:
                    matched = True
                    break
        if matched:
            continue
        source_filename = local_name if local_name != "an uploaded document" else "an uploaded document"
        results.append(
            MissingEvidence(
                key=key,
                label=ref.name.strip(),
                why_it_matters=f"Referenced in {source_filename}, page {ref.page}, but no matching file was uploaded.",
                priority="high",
                triggered_by="referenced_but_not_uploaded",
                referencing_quote=QuoteRef(doc_id=ref.source_doc_id, page=ref.page, quote=ref.quote, verified=True),
            )
        )

    def sort_key(item: MissingEvidence):
        priority_sort = SEVERITY_RANK.get(item.priority, 2)
        triggered_order = 0 if item.triggered_by == "checklist" else 1
        return (priority_sort, triggered_order, results.index(item))

    results = sorted(results, key=lambda item: sort_key(item))
    return results


def calculate_evidence_strength(
    finding: Finding,
    documents: Sequence[Document],
    reliability: Mapping[str, float] | None = None,
) -> str:
    """Calculate the evidence strength for a single finding.

    Inputs: a Finding and the document set from which its quotes are sourced.
    Outputs: a deterministic EvidenceStrength value between high/medium/low.
    Edge cases: unverified or missing quotes return low; absence findings are capped at medium.
    """
    if not _is_verified(finding):
        return "low"
    docs_by_id = {d.id: d for d in documents}
    table = reliability or DOC_RELIABILITY
    level = "high" if finding.source == "rule" and _min_reliability(finding, docs_by_id, table) >= 0.6 else "high" if _min_reliability(finding, docs_by_id, table) >= 0.9 else "medium"
    if finding.finding_type in ABSENCE_FINDING_TYPES and level == "high":
        level = "medium"
    return level


def calculate_case_score(
    claims: Sequence[Claim],
    evidence: Sequence[Evidence],
    findings: Sequence[Finding],
    checklist: ChecklistResult,
    rule_results: Sequence[RuleResult],
    documents: Sequence[Document],
    *,
    reliability: Mapping[str, float] | None = None,
) -> ScoreResult:
    """Compute a deterministic evidence score for the user's perspective.

    Inputs: claims, evidence, findings, checklist coverage, rule results and documents.
    Outputs: a ScoreResult with breakdown, raw inputs and notes.
    Edge cases: no verified material, empty checklist and missing document ids are handled with neutral defaults.
    """
    docs_by_id = {d.id: d for d in documents}
    table = reliability or DOC_RELIABILITY
    verified = [f for f in findings if _is_verified(f)]
    excluded = len(findings) - len(verified)

    claims_by_id = {c.id: c for c in claims}
    U = 0.0
    C = 0.0
    for finding in verified:
        if finding.finding_type not in {"contradiction", "support"}:
            continue
        resolved = _resolve_favors(finding, claims_by_id)
        weight = _min_reliability(finding, docs_by_id, table)
        if resolved == "user":
            U += weight
        elif resolved == "company":
            C += weight

    support_ratio = U / (U + C) if U + C > 0 else 0.5

    favor_w = 0.0
    against_w = 0.0
    for finding in verified:
        if finding.finding_type not in SCORING_FINDING_TYPES:
            continue
        resolved = _resolve_favors(finding, claims_by_id)
        weight = SEVERITY_WEIGHT.get(finding.severity, 0.3)
        if resolved == "user":
            favor_w += weight
        elif resolved == "company":
            against_w += weight
    net = favor_w - against_w
    contradiction_score = max(0.0, min(1.0, 0.5 + net / (2 * CONTRADICTION_SATURATION)))
    if not verified:
        support_ratio = 0.5
        contradiction_score = 0.5 if checklist.total == 0 else 0.45
    else:
        contradiction_score = round(contradiction_score, 1)

    completeness = len(checklist.covered_keys) / checklist.total if checklist.total > 0 else 0.5
    evaluated = [r for r in rule_results if r.evaluated]
    passed = [r for r in evaluated if r.passed is True]
    timeline_consistency = len(passed) / len(evaluated) if evaluated else 1.0

    raw = Decimal("100") * (
        Decimal(str(SCORE_WEIGHTS["support"])) * Decimal(str(support_ratio))
        + Decimal(str(SCORE_WEIGHTS["contradiction"])) * Decimal(str(contradiction_score))
        + Decimal(str(SCORE_WEIGHTS["completeness"])) * Decimal(str(completeness))
        + Decimal(str(SCORE_WEIGHTS["timeline"])) * Decimal(str(timeline_consistency))
    )
    evidence_score = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    evidence_score = max(0, min(100, evidence_score))

    band = "Weak"
    for threshold, name in SCORE_BANDS:
        if evidence_score >= threshold:
            band = name
            break

    breakdown = {
        "support_ratio": ComponentScore(
            value=round(float(support_ratio), 6),
            weight=SCORE_WEIGHTS["support"],
            points=round(100 * SCORE_WEIGHTS["support"] * float(support_ratio), 2),
            explanation=f"Reliability-weighted evidence for your position {U:.2f} vs against {C:.2f}.",
        ),
        "contradiction_score": ComponentScore(
            value=round(float(contradiction_score), 6),
            weight=SCORE_WEIGHTS["contradiction"],
            points=round(100 * SCORE_WEIGHTS["contradiction"] * float(contradiction_score), 2),
            explanation=f"Net severity-weighted findings in your favour: {favor_w:.2f} (saturates at {CONTRADICTION_SATURATION:.2f}).",
        ),
        "completeness": ComponentScore(
            value=round(float(completeness), 6),
            weight=SCORE_WEIGHTS["completeness"],
            points=round(100 * SCORE_WEIGHTS["completeness"] * float(completeness), 2),
            explanation=f"{len(checklist.covered_keys)} of {checklist.total} checklist items covered.",
        ),
        "timeline_consistency": ComponentScore(
            value=round(float(timeline_consistency), 6),
            weight=SCORE_WEIGHTS["timeline"],
            points=round(100 * SCORE_WEIGHTS["timeline"] * float(timeline_consistency), 2),
            explanation=f"{len(passed)} of {len(evaluated)} evaluated rule checks passed.",
        ),
    }

    inputs = {
        "U": round(U, 6),
        "C": round(C, 6),
        "favor_w": round(favor_w, 6),
        "against_w": round(against_w, 6),
        "net": round(net, 6),
        "verified_findings": len(verified),
        "excluded_unverified_findings": excluded,
        "checklist_total": checklist.total,
        "checklist_covered": len(checklist.covered_keys),
        "rules_evaluated": len(evaluated),
        "rules_passed": len(passed),
        "verified_claims": sum(1 for c in claims if c.quote_verified),
        "verified_evidence": sum(1 for e in evidence if e.quote_verified),
        "category": checklist.category,
    }

    notes: list[str] = []
    if excluded > 0:
        notes.append(f"{excluded} unverified finding(s) were excluded from the score.")
    if inputs["verified_claims"] == 0 or inputs["verified_evidence"] == 0:
        notes.append("Not enough verified material to judge; the score reflects neutral defaults.")
    if checklist.total == 0:
        notes.append("No checklist applied; completeness set to a neutral 0.5.")

    return ScoreResult(
        evidence_score=evidence_score,
        band=band,
        breakdown=breakdown,
        inputs=inputs,
        notes=notes,
        perspective="user",
        disclaimer="Evidence score based only on the submitted documents. It is not a probability of success and not legal advice.",
    )


def score_case(case: CaseAnalysis) -> ScoringBundle:
    """Compute the final score and missing-evidence set for a case.

    Inputs: a CaseAnalysis object.
    Outputs: a ScoringBundle containing the score, missing evidence and findings with evidence_strength updated.
    Edge cases: missing rule results are treated as neutral and no model calls are made.
    """
    findings = [
        f.model_copy(update={"evidence_strength": calculate_evidence_strength(f, case.documents)})
        for f in getattr(case, "contradictions", [])
    ]
    checklist = evaluate_checklist(case.category or "", case.documents, case.events)
    missing_evidence = find_missing_evidence(case.category or "", case.documents, case.events, case.references)
    rule_results = list(getattr(case, "rule_results", []))
    if not rule_results:
        missing_note = "No rule results available; timeline consistency set to 1.0."
    else:
        missing_note = None
    score = calculate_case_score(
        claims=case.claims,
        evidence=case.evidence,
        findings=findings,
        checklist=checklist,
        rule_results=rule_results,
        documents=case.documents,
    )
    if missing_note and missing_note not in score.notes:
        score.notes.append(missing_note)
    return ScoringBundle(score=score, missing_evidence=missing_evidence, findings=findings)
