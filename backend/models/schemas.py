from __future__ import annotations

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["high", "medium", "low"]
EvidenceStrength = Literal["high", "medium", "low"]
Favors = Literal["user", "company", "neutral"]
FindingType = Literal[
    "contradiction",
    "support",
    "unsupported_claim",
    "date_mismatch",
    "amount_mismatch",
    "sequence_anomaly",
    "window_check",
    "missing_reference",
]
FindingSource = Literal["rule", "model_verified"]
DocType = Literal[
    "invoice",
    "warranty_terms",
    "contract",
    "company_response",
    "inspection_report",
    "email_thread",
    "photo",
    "receipt",
    "other",
]
DocStatus = Literal["pending", "extracting", "done", "failed"]


class QuoteRef(BaseModel):
    doc_id: str
    page: int
    quote: str
    verified: bool = False


class Document(BaseModel):
    id: str
    filename: str
    doc_type: DocType
    status: DocStatus
    page_count: int = 0


class Claim(BaseModel):
    id: str
    source_doc_id: str
    page: int
    speaker: Literal["user", "company", "third_party"]
    kind: Literal["assertion", "promise", "denial", "exclusion_invoked", "request"]
    text: str
    quote: str
    quote_verified: bool = False


class Evidence(BaseModel):
    id: str
    source_doc_id: str
    page: int
    text: str
    quote: str
    quote_verified: bool = False


class Event(BaseModel):
    id: str
    source_doc_id: str
    page: int
    event_type: Literal[
        "purchase",
        "warranty_start",
        "warranty_end",
        "failure_reported",
        "ticket_created",
        "inspection",
        "report_issued",
        "claim_rejected",
        "response_received",
        "other",
    ]
    date: Date | None = None
    date_text: str = ""
    quote: str = ""
    quote_verified: bool = False


class DocumentReference(BaseModel):
    id: str
    source_doc_id: str
    page: int
    name: str
    quote: str
    quote_verified: bool = False


class Finding(BaseModel):
    id: str
    finding_type: FindingType
    source: FindingSource
    rule_id: str | None = None
    severity: Severity = "low"
    evidence_strength: EvidenceStrength | None = None
    favors: Favors | None = None
    explanation: str
    left_item_id: str | None = None
    right_item_id: str | None = None
    quotes: list[QuoteRef] = Field(default_factory=list)


class RuleResult(BaseModel):
    rule_id: str
    evaluated: bool
    passed: bool | None = None


class MissingEvidence(BaseModel):
    key: str
    label: str
    why_it_matters: str
    priority: Severity
    triggered_by: Literal["checklist", "referenced_but_not_uploaded"]
    referencing_quote: QuoteRef | None = None


class ComponentScore(BaseModel):
    value: float
    weight: float
    points: float
    explanation: str


class ScoreResult(BaseModel):
    evidence_score: int
    band: Literal["Weak", "Moderate", "Mixed", "Strong"]
    breakdown: dict[str, ComponentScore]
    inputs: dict[str, float | int | str | bool]
    notes: list[str] = Field(default_factory=list)
    perspective: Literal["user"] = "user"
    disclaimer: str = (
        "Evidence score based only on the submitted documents. "
        "It is not a probability of success and not legal advice."
    )


class GeneratedResponse(BaseModel):
    subject: str
    full_text: str
    paragraphs: list[str]
    requests: list[str]
    cited_finding_ids: list[str]
    used_model: bool
    model_name: str | None = None
    retries: int = 0
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Based only on the submitted documents. Not legal advice."


class CaseAnalysis(BaseModel):
    case_id: str
    category: str | None = None
    documents: list[Document] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    contradictions: list[Finding] = Field(default_factory=list)
    references: list[DocumentReference] = Field(default_factory=list)
    rule_results: list[RuleResult] = Field(default_factory=list)
    score: ScoreResult | None = None
    missing_evidence: list[MissingEvidence] = Field(default_factory=list)
