import re
import logging
from typing import List, Dict, Any, Optional, Union, Set

logger = logging.getLogger(__name__)

STOP_WORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in",
    "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will", "with",
    "there", "no", "or", "been", "this", "during", "which", "official", "reported"
}
KEYWORD_NORMALIZATIONS = {
    "failed": "fail",
    "failing": "fail",
    "fails": "fail",
    "failure": "fail",
    "failures": "fail",
}


def _extract_keywords(text: str) -> Set[str]:
    """Extract significant keywords from text for semantic matching."""
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    return {KEYWORD_NORMALIZATIONS.get(word, word) for word in words if word not in STOP_WORDS}


def _are_texts_related(text1: str, text2: str, min_shared: int = 1) -> bool:
    """
    Determines if two text items are semantically related based on keyword overlap.
    """
    kw1 = _extract_keywords(text1)
    kw2 = _extract_keywords(text2)
    if not kw1 or not kw2:
        return False
    shared = kw1.intersection(kw2)
    return len(shared) >= min_shared


def create_evidence_graph(
    processed_document: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    claims: Optional[List[Dict[str, Any]]] = None,
    evidence: Optional[List[Dict[str, Any]]] = None,
    events: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Accepts structured data produced by document_service and gemma_service.
    Constructs a precise, non-redundant evidence graph representing Nodes and Relationships.

    Nodes:
      - Document
      - Claim
      - Evidence
      - Event

    Relationships:
      - DOCUMENT_CONTAINS_CLAIM
      - DOCUMENT_CONTAINS_EVIDENCE
      - DOCUMENT_CONTAINS_EVENT
      - CLAIM_SUPPORTED_BY_EVIDENCE (only when evidence relates to claim)
      - CLAIM_ASSOCIATED_WITH_EVENT (only when claim relates to event)
      - EVIDENCE_ASSOCIATED_WITH_EVENT (only when evidence relates to event)
    """
    nodes_map: Dict[str, Dict[str, Any]] = {}
    relationships: List[Dict[str, Any]] = []
    seen_rel_keys = set()

    # Normalize processed_document input
    doc_list: List[Dict[str, Any]] = []
    if processed_document:
        if isinstance(processed_document, dict):
            doc_list = [processed_document]
        elif isinstance(processed_document, list):
            doc_list = processed_document

    claims_list = claims or []
    evidence_list = evidence or []
    events_list = events or []

    # 1. Add Document Nodes
    for doc in doc_list:
        doc_id = doc.get("document_id")
        if doc_id:
            nodes_map[doc_id] = {
                "id": doc_id,
                "type": "document",
                "filename": doc.get("filename"),
                "source": doc.get("source")
            }

    # 2. Add Claim Nodes & DOCUMENT_CONTAINS_CLAIM Relationships
    for claim in claims_list:
        claim_id = claim.get("claim_id")
        doc_id = claim.get("document_id")
        
        if claim_id:
            nodes_map[claim_id] = {
                "id": claim_id,
                "type": "claim",
                "text": claim.get("claim"),
                "confidence": claim.get("confidence"),
                "source": claim.get("source")
            }

            if doc_id and doc_id not in nodes_map:
                nodes_map[doc_id] = {
                    "id": doc_id,
                    "type": "document",
                    "filename": claim.get("source", doc_id),
                    "source": claim.get("source", doc_id)
                }

            if doc_id:
                rel_key = (doc_id, claim_id, "DOCUMENT_CONTAINS_CLAIM")
                if rel_key not in seen_rel_keys:
                    seen_rel_keys.add(rel_key)
                    relationships.append({
                        "source": doc_id,
                        "target": claim_id,
                        "type": "DOCUMENT_CONTAINS_CLAIM"
                    })

    # 3. Add Evidence Nodes & DOCUMENT_CONTAINS_EVIDENCE Relationships
    for ev in evidence_list:
        ev_id = ev.get("evidence_id")
        doc_id = ev.get("document_id")

        if ev_id:
            nodes_map[ev_id] = {
                "id": ev_id,
                "type": "evidence",
                "text": ev.get("text"),
                "confidence": ev.get("confidence"),
                "source": ev.get("source")
            }

            if doc_id and doc_id not in nodes_map:
                nodes_map[doc_id] = {
                    "id": doc_id,
                    "type": "document",
                    "filename": ev.get("source", doc_id),
                    "source": ev.get("source", doc_id)
                }

            if doc_id:
                rel_key = (doc_id, ev_id, "DOCUMENT_CONTAINS_EVIDENCE")
                if rel_key not in seen_rel_keys:
                    seen_rel_keys.add(rel_key)
                    relationships.append({
                        "source": doc_id,
                        "target": ev_id,
                        "type": "DOCUMENT_CONTAINS_EVIDENCE"
                    })

    # 4. Add Event Nodes & DOCUMENT_CONTAINS_EVENT Relationships
    for event in events_list:
        event_id = event.get("event_id")
        doc_id = event.get("document_id")

        if event_id:
            nodes_map[event_id] = {
                "id": event_id,
                "type": "event",
                "date": event.get("date"),
                "text": event.get("event"),
                "confidence": event.get("confidence"),
                "source": event.get("source")
            }

            if doc_id and doc_id not in nodes_map:
                nodes_map[doc_id] = {
                    "id": doc_id,
                    "type": "document",
                    "filename": event.get("source", doc_id),
                    "source": event.get("source", doc_id)
                }

            if doc_id:
                rel_key = (doc_id, event_id, "DOCUMENT_CONTAINS_EVENT")
                if rel_key not in seen_rel_keys:
                    seen_rel_keys.add(rel_key)
                    relationships.append({
                        "source": doc_id,
                        "target": event_id,
                        "type": "DOCUMENT_CONTAINS_EVENT"
                    })

    # 5. Connect CLAIM_SUPPORTED_BY_EVIDENCE (only when evidence relates to claim)
    for claim in claims_list:
        claim_id = claim.get("claim_id")
        c_doc = claim.get("document_id")
        c_text = str(claim.get("claim", ""))

        for ev in evidence_list:
            ev_id = ev.get("evidence_id")
            e_doc = ev.get("document_id")
            e_text = str(ev.get("text", ""))

            if claim_id and ev_id and c_doc and e_doc and c_doc == e_doc:
                if _are_texts_related(c_text, e_text, min_shared=1):
                    rel_key = (claim_id, ev_id, "CLAIM_SUPPORTED_BY_EVIDENCE")
                    if rel_key not in seen_rel_keys:
                        seen_rel_keys.add(rel_key)
                        relationships.append({
                            "source": claim_id,
                            "target": ev_id,
                            "type": "CLAIM_SUPPORTED_BY_EVIDENCE"
                        })

    # 6. Connect CLAIM_ASSOCIATED_WITH_EVENT (only when claim relates to event)
    for claim in claims_list:
        claim_id = claim.get("claim_id")
        c_doc = claim.get("document_id")
        c_text = str(claim.get("claim", ""))

        for event in events_list:
            event_id = event.get("event_id")
            ev_doc = event.get("document_id")
            evt_text = str(event.get("event", ""))

            if claim_id and event_id and c_doc and ev_doc and c_doc == ev_doc:
                if _are_texts_related(c_text, evt_text, min_shared=2):
                    rel_key = (claim_id, event_id, "CLAIM_ASSOCIATED_WITH_EVENT")
                    if rel_key not in seen_rel_keys:
                        seen_rel_keys.add(rel_key)
                        relationships.append({
                            "source": claim_id,
                            "target": event_id,
                            "type": "CLAIM_ASSOCIATED_WITH_EVENT"
                        })

    # 7. Connect EVIDENCE_ASSOCIATED_WITH_EVENT (only when evidence relates to event)
    for ev in evidence_list:
        ev_id = ev.get("evidence_id")
        e_doc = ev.get("document_id")
        e_text = str(ev.get("text", ""))

        for event in events_list:
            event_id = event.get("event_id")
            ev_doc = event.get("document_id")
            evt_text = str(event.get("event", ""))

            if ev_id and event_id and e_doc and ev_doc and e_doc == ev_doc:
                if _are_texts_related(e_text, evt_text, min_shared=1):
                    rel_key = (ev_id, event_id, "EVIDENCE_ASSOCIATED_WITH_EVENT")
                    if rel_key not in seen_rel_keys:
                        seen_rel_keys.add(rel_key)
                        relationships.append({
                            "source": ev_id,
                            "target": event_id,
                            "type": "EVIDENCE_ASSOCIATED_WITH_EVENT"
                        })

    return {
        "nodes": list(nodes_map.values()),
        "relationships": relationships
    }
