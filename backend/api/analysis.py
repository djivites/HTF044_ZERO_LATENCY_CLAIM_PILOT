"""
Analysis Router — /api/v1/analysis
Handles AI extraction: claims, evidence, events, evidence graph, and timeline.
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.gemma_service import extract_claims, extract_evidence, extract_events
from backend.services.evidence_service import create_evidence_graph
from backend.services.timeline_service import build_timeline
from backend.models.schemas import CaseAnalysis
from backend.services.contradiction_service import detect_contradictions
from backend.services.response_service import generate_response
from backend.services.scoring_service import score_case

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Request/Response schemas ────────────────────────────────────────────────
class ProcessedDocumentIn(BaseModel):
    document_id: str
    filename: str
    text: str
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyzeDocumentRequest(BaseModel):
    documents: List[ProcessedDocumentIn] = Field(
        ..., description="List of processed documents (text already extracted)"
    )
    case_category: Optional[str] = Field(
        default=None,
        description="Case category: warranty, rental, insurance, service, or generic",
    )


class FullAnalysisResponse(BaseModel):
    claims: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    graph: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    summary: Dict[str, Any]


class ResponseRequest(CaseAnalysis):
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    tone: str = "formal"
    finding_ids: Optional[List[str]] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post("/score", summary="Score a typed case and list missing evidence")
async def score_analysis_endpoint(case: CaseAnalysis):
    if not case.contradictions:
        case = case.model_copy(
            update={"contradictions": detect_contradictions(case.claims, case.evidence)}
        )
    bundle = score_case(case)
    return {
        "score": bundle.score.model_dump(mode="json"),
        "missing_evidence": [item.model_dump(mode="json") for item in bundle.missing_evidence],
        "findings": [item.model_dump(mode="json") for item in bundle.findings],
    }


@router.post("/contradictions", summary="Find cautious claim/evidence conflicts")
async def contradictions_endpoint(case: CaseAnalysis):
    findings = detect_contradictions(case.claims, case.evidence)
    return {
        "contradictions": [finding.model_dump(mode="json") for finding in findings],
        "total": len(findings),
    }


@router.post("/response", summary="Generate an evidence-backed dispute response")
async def response_endpoint(request: ResponseRequest):
    case_data = request.model_dump(
        exclude={"recipient_name", "sender_name", "tone", "finding_ids"}
    )
    case = CaseAnalysis.model_validate(case_data)
    if not case.contradictions:
        case.contradictions = detect_contradictions(case.claims, case.evidence)
    if request.tone not in {"formal", "firm_polite"}:
        raise HTTPException(status_code=422, detail="tone must be 'formal' or 'firm_polite'.")
    response = await generate_response(
        case,
        tone=request.tone,
        recipient_name=request.recipient_name,
        sender_name=request.sender_name,
        finding_ids=request.finding_ids,
    )
    return response.model_dump(mode="json")


@router.post(
    "/claims",
    summary="Extract factual claims from one or more processed documents",
)
async def extract_claims_endpoint(request: AnalyzeDocumentRequest):
    """
    Runs Gemma claim extraction (with rule-based fallback) on every document.
    Returns a flat list of claim objects.
    """
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided.")

    all_claims: List[Dict[str, Any]] = []
    for doc in request.documents:
        try:
            claims = extract_claims(doc.model_dump())
            all_claims.extend(claims)
        except Exception as e:
            logger.error(f"Claims extraction failed for {doc.filename}: {e}")

    return {"claims": all_claims, "total": len(all_claims)}


@router.post(
    "/evidence",
    summary="Extract evidence items from one or more processed documents",
)
async def extract_evidence_endpoint(request: AnalyzeDocumentRequest):
    """
    Runs Gemma evidence extraction (with rule-based fallback) on every document.
    Returns a flat list of evidence items.
    """
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided.")

    all_evidence: List[Dict[str, Any]] = []
    for doc in request.documents:
        try:
            evidence = extract_evidence(doc.model_dump())
            all_evidence.extend(evidence)
        except Exception as e:
            logger.error(f"Evidence extraction failed for {doc.filename}: {e}")

    return {"evidence": all_evidence, "total": len(all_evidence)}


@router.post(
    "/events",
    summary="Extract events and dates from one or more processed documents",
)
async def extract_events_endpoint(request: AnalyzeDocumentRequest):
    """
    Runs Gemma event/date extraction (with rule-based fallback) on every document.
    Returns a flat list of event objects.
    """
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided.")

    all_events: List[Dict[str, Any]] = []
    for doc in request.documents:
        try:
            events = extract_events(doc.model_dump())
            all_events.extend(events)
        except Exception as e:
            logger.error(f"Events extraction failed for {doc.filename}: {e}")

    return {"events": all_events, "total": len(all_events)}


@router.post(
    "/graph",
    summary="Build evidence graph from claims, evidence, and events",
)
async def build_graph_endpoint(request: AnalyzeDocumentRequest):
    """
    Constructs a node/relationship evidence graph.
    First runs all extractions, then links them.
    """
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided.")

    docs_dicts = [d.model_dump() for d in request.documents]
    all_claims, all_evidence, all_events = [], [], []

    for doc in docs_dicts:
        try:
            all_claims.extend(extract_claims(doc))
            all_evidence.extend(extract_evidence(doc))
            all_events.extend(extract_events(doc))
        except Exception as e:
            logger.error(f"Extraction error for {doc.get('filename')}: {e}")

    graph = create_evidence_graph(
        processed_document=docs_dicts,
        claims=all_claims,
        evidence=all_evidence,
        events=all_events,
    )
    return {
        "graph": graph,
        "nodes_count": len(graph.get("nodes", [])),
        "relationships_count": len(graph.get("relationships", [])),
    }


@router.post(
    "/timeline",
    summary="Build a sorted timeline from extracted events",
)
async def build_timeline_endpoint(request: AnalyzeDocumentRequest):
    """
    Extracts events from all documents and returns them sorted chronologically.
    """
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided.")

    all_events: List[Dict[str, Any]] = []
    for doc in request.documents:
        try:
            all_events.extend(extract_events(doc.model_dump()))
        except Exception as e:
            logger.error(f"Events extraction failed for {doc.filename}: {e}")

    timeline = build_timeline(all_events)
    return {"timeline": timeline, "total": len(timeline)}


@router.post(
    "/full",
    summary="Full pipeline: extract claims, evidence, events, graph, and timeline",
    response_model=FullAnalysisResponse,
)
async def full_analysis(request: AnalyzeDocumentRequest):
    """
    Runs the complete analysis pipeline on the provided documents.
    Returns claims, evidence, events, evidence graph, timeline, and a summary.
    """
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided.")

    docs_dicts = [d.model_dump() for d in request.documents]
    all_claims, all_evidence, all_events = [], [], []

    for doc in docs_dicts:
        try:
            all_claims.extend(extract_claims(doc))
            all_evidence.extend(extract_evidence(doc))
            all_events.extend(extract_events(doc))
        except Exception as e:
            logger.error(f"Pipeline error for {doc.get('filename')}: {e}")

    graph = create_evidence_graph(
        processed_document=docs_dicts,
        claims=all_claims,
        evidence=all_evidence,
        events=all_events,
    )
    timeline = build_timeline(all_events)

    return FullAnalysisResponse(
        claims=all_claims,
        evidence=all_evidence,
        events=all_events,
        graph=graph,
        timeline=timeline,
        summary={
            "documents_analyzed": len(docs_dicts),
            "total_claims": len(all_claims),
            "total_evidence": len(all_evidence),
            "total_events": len(all_events),
            "graph_nodes": len(graph.get("nodes", [])),
            "graph_relationships": len(graph.get("relationships", [])),
            "timeline_entries": len(timeline),
            "case_category": request.case_category or "generic",
        },
    )
