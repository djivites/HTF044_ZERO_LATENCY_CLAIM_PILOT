import os
import re
import json
import uuid
import logging
from typing import List, Dict, Any, Union, Optional

from backend.config import settings

logger = logging.getLogger(__name__)

# Prompts for Gemma
CLAIMS_PROMPT = """You are an AI evidence analysis assistant using gemma-4-31b-it. Extract all factual claims and assertions from the document text.
Do not hallucinate or infer information outside the text.

Return ONLY a valid JSON array of objects with the following schema for each claim:
[
  {
    "claim": "Direct factual claim or assertion made in text",
    "confidence": 0.95
  }
]

Document Text:
{text}
"""

EVIDENCE_PROMPT = """You are an AI evidence analysis assistant using gemma-4-31b-it. Extract all relevant physical evidence, facts, observations, and key evidence items from the document text.
Do not make legal conclusions. Do not hallucinate.

Return ONLY a valid JSON array of objects with the following schema for each evidence item:
[
  {
    "text": "Factual statement of evidence or observation",
    "confidence": 0.95
  }
]

Document Text:
{text}
"""

EVENTS_PROMPT = """You are an AI evidence analysis assistant using gemma-4-31b-it. Extract ONLY meaningful real-world events and their associated dates or ISO timestamps from the document text.

CRITICAL INSTRUCTIONS:
- Do NOT extract document headers, titles, metadata keys, or file identifiers (e.g. DO NOT extract "DOCUMENT: ...", "DOCUMENT ID: ...", "DATE: ...").
- Extract actual real-world actions, incidents, failures, inspections, diagnostic logs, and report filings.
- Include precise dates or timestamps if mentioned (e.g. "2026-08-02", "2026-08-02T14:30:00Z").
- Do not invent dates or events.

Return ONLY a valid JSON array of objects with the following schema for each real event:
[
  {
    "date": "2026-08-02",
    "event": "Clear description of real-world event",
    "confidence": 0.95
  }
]

Document Text:
{text}
"""


def _clean_and_parse_json(response_text: str) -> List[Dict[str, Any]]:
    """
    Cleans model response, handles markdown code blocks, extracts JSON arrays, and parses safely.
    """
    if not response_text or not response_text.strip():
        return []

    cleaned = response_text.strip()
    
    # Remove markdown code block fences if present
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

    # Direct JSON parsing
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    return val
            return [data]
    except json.JSONDecodeError as e:
        logger.warning(f"Direct JSON parsing failed ({e}), attempting regex fallback extraction.")

    # Fallback regex search for JSON array [...]
    array_match = re.search(r"\[\s*\{.*\}\s*\]", cleaned, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    return []


def _call_gemma_api(prompt: str, _retry: bool = True) -> str:
    """
    Call Gemma (gemma-4-31b-it) via Google GenAI SDK (google-genai).
    Retries once on transient 5xx errors. Raises RuntimeError on permanent failure
    so callers can distinguish a real API failure from an intentional fallback.
    """
    api_key = settings.GEMMA_API_KEY
    model_name = settings.GEMMA_MODEL_NAME

    logger.info(f"Gemma model: {model_name}")

    if not api_key:
        logger.warning("GEMMA_API_KEY not set — cannot call Gemma. Rule-based fallback will be used.")
        return ""

    try:
        from google import genai
    except ImportError:
        raise RuntimeError(
            "google-genai package is not installed. "
            "Run: pip install google-genai"
        )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        text = response.text or ""
        if not text.strip():
            logger.warning(f"Gemma returned an empty response for model {model_name}.")
        return text
    except Exception as e:
        err_str = str(e)
        # Retry once on transient 5xx server errors
        if _retry and ("500" in err_str or "503" in err_str or "502" in err_str):
            logger.warning(
                f"Gemma API transient error ({e}). Retrying once..."
            )
            return _call_gemma_api(prompt, _retry=False)
        raise RuntimeError(f"Gemma API call failed for model {model_name}: {e}") from e


def _rule_based_fallback_claims(text: str) -> List[Dict[str, Any]]:
    """Rule-based heuristic extraction of claims when API is offline or unconfigured."""
    claims = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        if len(line) > 10:
            if any(kw in line.lower() for kw in ["failed", "claimed", "states", "reported", "alleged", "occurred", "damaged", "broken"]):
                claims.append({
                    "claim": line,
                    "confidence": 0.85
                })
    if not claims and lines:
        claims.append({"claim": lines[0], "confidence": 0.75})
    return claims


def _rule_based_fallback_evidence(text: str) -> List[Dict[str, Any]]:
    """Rule-based heuristic extraction of evidence items."""
    evidence = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        if len(line) > 10:
            if any(kw in line.lower() for kw in ["observed", "no", "found", "inspected", "photo", "log", "record", "serial", "result", "test"]):
                evidence.append({
                    "text": line,
                    "confidence": 0.90
                })
    if not evidence and lines:
        evidence.append({"text": lines[-1], "confidence": 0.75})
    return evidence


def _is_metadata_line(text: str) -> bool:
    """Helper to detect and reject document metadata headers or keys."""
    t = text.strip().lower()
    if t.startswith(("document:", "document id:", "date:", "file:", "source:", "report id:")):
        return True
    if re.match(r"^date\s*:\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}$", t):
        return True
    if re.match(r"^document\s*id\s*:\s*[\w_]+$", t):
        return True
    return False


def _rule_based_fallback_events(text: str) -> List[Dict[str, Any]]:
    """Rule-based heuristic extraction of events and dates, ignoring metadata noise."""
    events = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    date_pattern = r"(\b\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:T\d{2}:\d{2}(?::\d{2})?Z?)?\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:, \d{4})?\b)"
    
    for line in lines:
        if _is_metadata_line(line):
            continue

        match = re.search(date_pattern, line, re.IGNORECASE)
        if match:
            date_str = match.group(0)
            events.append({
                "date": date_str,
                "event": line,
                "confidence": 0.88
            })
        elif any(kw in line.lower() for kw in ["stop", "start", "fail", "repair", "inspect", "complaint", "issue", "response"]):
            events.append({
                "date": None,
                "event": line,
                "confidence": 0.70
            })
            
    return events


def _deduplicate_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates events while preserving distinct events that occur on the same date.
    """
    unique_events = []
    seen_keys = set()

    for item in events:
        evt_text = str(item.get("event", "")).strip()
        evt_date = str(item.get("date", "")).strip() if item.get("date") else ""
        
        if not evt_text or _is_metadata_line(evt_text):
            continue

        # Create normalized deduplication key
        norm_text = re.sub(r"\W+", " ", evt_text.lower()).strip()
        key = (evt_date, norm_text)

        if key in seen_keys:
            continue
        
        seen_keys.add(key)
        unique_events.append(item)

    return unique_events


def extract_claims(processed_document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract factual claims/statements from the processed document using Gemma (gemma-4-31b-it).
    Returns a list of structured claim dictionaries.
    """
    doc_id = processed_document.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
    source = processed_document.get("source") or processed_document.get("filename", "unknown_source")
    text = processed_document.get("text", "")

    if not text.strip():
        return []

    prompt = CLAIMS_PROMPT.replace("{text}", text)
    try:
        raw_response = _call_gemma_api(prompt)
        parsed_items = _clean_and_parse_json(raw_response)
    except RuntimeError as e:
        logger.warning(f"Gemma claims extraction FAILED: {e}. Using rule-based fallback.")
        parsed_items = []

    if parsed_items:
        logger.info("Gemma claims extraction successful")
    else:
        logger.info("Using rule-based fallback for claims extraction.")
        parsed_items = _rule_based_fallback_claims(text)

    results = []
    for idx, item in enumerate(parsed_items):
        claim_text = item.get("claim") or item.get("text") or item.get("statement") or ""
        if not claim_text or _is_metadata_line(str(claim_text)):
            continue
            
        conf = item.get("confidence")
        try:
            confidence = float(conf) if conf is not None else 0.95
        except (ValueError, TypeError):
            confidence = 0.95

        claim_id = item.get("claim_id") or f"claim_{idx+1:03d}_{doc_id}"

        results.append({
            "claim_id": claim_id,
            "claim": str(claim_text).strip(),
            "document_id": doc_id,
            "source": source,
            "confidence": round(confidence, 2)
        })

    return results


def extract_evidence(processed_document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant evidence from the document using Gemma (gemma-4-31b-it).
    Returns a list of structured evidence dictionaries.
    Does NOT make legal conclusions.
    """
    doc_id = processed_document.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
    source = processed_document.get("source") or processed_document.get("filename", "unknown_source")
    text = processed_document.get("text", "")

    if not text.strip():
        return []

    prompt = EVIDENCE_PROMPT.replace("{text}", text)
    try:
        raw_response = _call_gemma_api(prompt)
        parsed_items = _clean_and_parse_json(raw_response)
    except RuntimeError as e:
        logger.warning(f"Gemma evidence extraction FAILED: {e}. Using rule-based fallback.")
        parsed_items = []

    if parsed_items:
        logger.info("Gemma evidence extraction successful")
    else:
        logger.info("Using rule-based fallback for evidence extraction.")
        parsed_items = _rule_based_fallback_evidence(text)

    results = []
    for idx, item in enumerate(parsed_items):
        ev_text = item.get("text") or item.get("evidence") or item.get("observation") or ""
        if not ev_text or _is_metadata_line(str(ev_text)):
            continue

        conf = item.get("confidence")
        try:
            confidence = float(conf) if conf is not None else 0.95
        except (ValueError, TypeError):
            confidence = 0.95

        evidence_id = item.get("evidence_id") or f"evidence_{idx+1:03d}_{doc_id}"

        results.append({
            "evidence_id": evidence_id,
            "text": str(ev_text).strip(),
            "document_id": doc_id,
            "source": source,
            "confidence": round(confidence, 2)
        })

    return results


def extract_events(processed_document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract important events and dates from the document using Gemma (gemma-4-31b-it).
    Returns a list of structured event dictionaries. Filtered and deduplicated.
    """
    doc_id = processed_document.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
    source = processed_document.get("source") or processed_document.get("filename", "unknown_source")
    text = processed_document.get("text", "")

    if not text.strip():
        return []

    prompt = EVENTS_PROMPT.replace("{text}", text)
    try:
        raw_response = _call_gemma_api(prompt)
        parsed_items = _clean_and_parse_json(raw_response)
    except RuntimeError as e:
        logger.warning(f"Gemma events extraction FAILED: {e}. Using rule-based fallback.")
        parsed_items = []

    if parsed_items:
        logger.info("Gemma events extraction successful")
    else:
        logger.info("Using rule-based fallback for events extraction.")
        parsed_items = _rule_based_fallback_events(text)

    # Deduplicate events while retaining distinct same-day events
    parsed_items = _deduplicate_events(parsed_items)

    results = []
    for idx, item in enumerate(parsed_items):
        event_text = item.get("event") or item.get("description") or item.get("text") or ""
        if not event_text or _is_metadata_line(str(event_text)):
            continue

        event_date = item.get("date")
        if event_date is not None:
            event_date = str(event_date).strip()
            if event_date.lower() in ["null", "none", "n/a", ""]:
                event_date = None

        conf = item.get("confidence")
        try:
            confidence = float(conf) if conf is not None else 0.95
        except (ValueError, TypeError):
            confidence = 0.95

        event_id = item.get("event_id") or f"event_{idx+1:03d}_{doc_id}"

        results.append({
            "event_id": event_id,
            "date": event_date,
            "event": str(event_text).strip(),
            "document_id": doc_id,
            "source": source,
            "confidence": round(confidence, 2)
        })

    return results
