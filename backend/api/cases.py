"""
Cases Router — /api/v1/cases
Manages case lifecycle: create, list, retrieve, and run full pipeline on a case.
Cases are kept in memory for the hackathon demo; swap for a DB in production.
"""
import uuid
import logging
import re
from datetime import date
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, Field

from backend.services.document_service import process_document
from backend.services.gemma_service import extract_claims, extract_evidence, extract_events
from backend.services.evidence_service import create_evidence_graph
from backend.services.timeline_service import build_timeline
from backend.models.schemas import CaseAnalysis, Claim, Document, Event, Evidence
from backend.services.contradiction_service import detect_contradictions
from backend.services.response_service import generate_response
from backend.services.scoring_service import score_case

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── In-memory store (demo only) ─────────────────────────────────────────────
_cases: Dict[str, Dict[str, Any]] = {}


# ─── Schemas ─────────────────────────────────────────────────────────────────
class CreateCaseRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Short case title")
    description: str = Field(default="", description="What happened — user's own words")
    category: Optional[str] = Field(
        default="generic",
        description="warranty | rental | insurance | service | generic",
    )


class CaseSummary(BaseModel):
    case_id: str
    title: str
    description: str
    category: str
    document_count: int
    status: str


class CaseResponseRequest(BaseModel):
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    tone: str = "formal"
    finding_ids: Optional[List[str]] = None


def _case_analysis_from_stored(case: Dict[str, Any]) -> CaseAnalysis:
    documents = []
    document_types = {
        "invoice": "invoice",
        "receipt": "receipt",
        "warranty": "warranty_terms",
        "contract": "contract",
        "agreement": "contract",
        "response": "company_response",
        "rejection": "company_response",
        "denial": "company_response",
        "inspection": "inspection_report",
        "report": "inspection_report",
        "email": "email_thread",
        "photo": "photo",
    }
    documents_by_id = {}
    for source in case.get("documents", []):
        filename = str(source.get("filename", "document"))
        normalized_name = filename.lower()
        doc_type = next(
            (value for word, value in document_types.items() if word in normalized_name),
            "other",
        )
        document = Document(
            id=str(source.get("document_id", "unknown")),
            filename=filename,
            doc_type=doc_type,
            status="done" if source.get("status") == "success" else "failed",
        )
        documents.append(document)
        documents_by_id[document.id] = document

    claims = []
    for source in case.get("claims", []):
        text = str(source.get("claim", "")).strip()
        if not text:
            continue
        doc_id = str(source.get("document_id", "unknown"))
        filename = documents_by_id.get(doc_id).filename.lower() if doc_id in documents_by_id else ""
        speaker = "company" if re.search(r"response|rejection|denial|decision", filename) else "user"
        kind = "denial" if re.search(r"den(y|ied|ial)|reject", text, re.IGNORECASE) else "assertion"
        claims.append(
            Claim(
                id=str(source.get("claim_id", f"claim_{len(claims) + 1}")),
                source_doc_id=doc_id,
                page=1,
                speaker=speaker,
                kind=kind,
                text=text,
                quote=text,
                quote_verified=False,
            )
        )

    evidence = [
        Evidence(
            id=str(source.get("evidence_id", f"evidence_{index + 1}")),
            source_doc_id=str(source.get("document_id", "unknown")),
            page=1,
            text=str(source.get("text", "")),
            quote=str(source.get("text", "")),
            quote_verified=False,
        )
        for index, source in enumerate(case.get("evidence", []))
        if str(source.get("text", "")).strip()
    ]

    event_types = {
        "purchas": "purchase",
        "warranty": "warranty_start",
        "fail": "failure_reported",
        "report": "report_issued",
        "inspect": "inspection",
        "reject": "claim_rejected",
        "response": "response_received",
        "ticket": "ticket_created",
    }
    events = []
    for index, source in enumerate(case.get("events", [])):
        text = str(source.get("event", "")).strip()
        if not text:
            continue
        raw_date = source.get("date")
        try:
            event_date = date.fromisoformat(str(raw_date)) if raw_date else None
        except ValueError:
            event_date = None
        event_type = next(
            (value for word, value in event_types.items() if word in text.lower()),
            "other",
        )
        events.append(
            Event(
                id=str(source.get("event_id", f"event_{index + 1}")),
                source_doc_id=str(source.get("document_id", "unknown")),
                page=1,
                event_type=event_type,
                date=event_date,
                date_text=str(raw_date or ""),
                quote=text,
                quote_verified=False,
            )
        )

    analysis = CaseAnalysis(
        case_id=case["case_id"],
        category=case.get("category"),
        documents=documents,
        claims=claims,
        evidence=evidence,
        events=events,
    )
    analysis.contradictions = detect_contradictions(claims, evidence)
    return analysis


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post("/", summary="Create a new case", response_model=CaseSummary)
async def create_case(body: CreateCaseRequest):
    """Creates an empty case with a unique ID, ready for document uploads."""
    case_id = f"case_{uuid.uuid4().hex[:10]}"
    _cases[case_id] = {
        "case_id": case_id,
        "title": body.title,
        "description": body.description,
        "category": body.category or "generic",
        "documents": [],
        "claims": [],
        "evidence": [],
        "events": [],
        "graph": {},
        "timeline": [],
        "status": "created",
    }
    logger.info(f"Case created: {case_id} — '{body.title}'")
    return CaseSummary(
        case_id=case_id,
        title=body.title,
        description=body.description,
        category=body.category or "generic",
        document_count=0,
        status="created",
    )


@router.get("/", summary="List all cases")
async def list_cases():
    """Returns a summary list of all cases."""
    return {
        "cases": [
            {
                "case_id": c["case_id"],
                "title": c["title"],
                "category": c["category"],
                "document_count": len(c.get("documents", [])),
                "status": c.get("status", "created"),
            }
            for c in _cases.values()
        ],
        "total": len(_cases),
    }


@router.get("/{case_id}", summary="Retrieve a single case by ID")
async def get_case(case_id: str):
    """Returns full case data including all extracted artefacts."""
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case


@router.post("/{case_id}/documents", summary="Upload documents to an existing case")
async def upload_to_case(
    case_id: str,
    files: List[UploadFile] = File(...),
):
    """
    Upload one or more files to an existing case.
    Text is extracted immediately and stored on the case object.
    """
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    added = []
    for upload in files:
        content = await upload.read()
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        result = process_document(file_input=content, filename=upload.filename, document_id=doc_id)
        result["case_id"] = case_id
        case["documents"].append(result)
        added.append({"document_id": doc_id, "filename": upload.filename, "status": result.get("status")})
        logger.info(f"Uploaded to {case_id}: {upload.filename} → {result.get('status')}")

    case["status"] = "documents_uploaded"
    return {"case_id": case_id, "added": added, "total_documents": len(case["documents"])}


@router.post("/{case_id}/analyze", summary="Run full analysis pipeline on a case")
async def analyze_case(case_id: str):
    """
    Runs the full pipeline (claims → evidence → events → graph → timeline)
    on all documents already uploaded to the case.
    Updates and returns the complete case object.
    """
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    docs = [d for d in case.get("documents", []) if d.get("status") == "success" and d.get("text")]
    if not docs:
        raise HTTPException(
            status_code=422,
            detail="No successfully processed documents found in this case. Upload documents first.",
        )

    case["status"] = "analyzing"
    all_claims, all_evidence, all_events = [], [], []

    for doc in docs:
        try:
            all_claims.extend(extract_claims(doc))
            all_evidence.extend(extract_evidence(doc))
            all_events.extend(extract_events(doc))
        except Exception as e:
            logger.error(f"Pipeline error for {doc.get('filename')} in case {case_id}: {e}")

    graph = create_evidence_graph(
        processed_document=docs,
        claims=all_claims,
        evidence=all_evidence,
        events=all_events,
    )
    timeline = build_timeline(all_events)

    case["claims"] = all_claims
    case["evidence"] = all_evidence
    case["events"] = all_events
    case["graph"] = graph
    case["timeline"] = timeline
    case["status"] = "analyzed"

    logger.info(
        f"Case {case_id} analyzed — "
        f"claims={len(all_claims)}, evidence={len(all_evidence)}, "
        f"events={len(all_events)}, graph_nodes={len(graph.get('nodes', []))}"
    )

    return {
        "case_id": case_id,
        "status": "analyzed",
        "summary": {
            "documents_analyzed": len(docs),
            "total_claims": len(all_claims),
            "total_evidence": len(all_evidence),
            "total_events": len(all_events),
            "graph_nodes": len(graph.get("nodes", [])),
            "graph_relationships": len(graph.get("relationships", [])),
            "timeline_entries": len(timeline),
        },
        "data": case,
    }


@router.post("/{case_id}/score", summary="Score an analyzed case and list missing evidence")
async def score_stored_case(case_id: str):
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    analysis = _case_analysis_from_stored(case)
    bundle = score_case(analysis)
    case["score"] = bundle.score.model_dump(mode="json")
    case["missing_evidence"] = [item.model_dump(mode="json") for item in bundle.missing_evidence]
    case["contradictions"] = [item.model_dump(mode="json") for item in bundle.findings]
    return {
        "case_id": case_id,
        "score": case["score"],
        "missing_evidence": case["missing_evidence"],
        "contradictions": case["contradictions"],
    }


@router.post("/{case_id}/response", summary="Generate a response from a stored case")
async def generate_case_response(case_id: str, request: CaseResponseRequest):
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    if request.tone not in {"formal", "firm_polite"}:
        raise HTTPException(status_code=422, detail="tone must be 'formal' or 'firm_polite'.")
    analysis = _case_analysis_from_stored(case)
    response = await generate_response(
        analysis,
        tone=request.tone,
        recipient_name=request.recipient_name,
        sender_name=request.sender_name,
        finding_ids=request.finding_ids,
    )
    return response.model_dump(mode="json")


@router.delete("/{case_id}", summary="Delete a case")
async def delete_case(case_id: str):
    """Removes a case from the in-memory store."""
    if case_id not in _cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    del _cases[case_id]
    return {"message": f"Case '{case_id}' deleted successfully."}
