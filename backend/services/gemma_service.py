import os
import re
import json
import uuid
import logging
from typing import List, Dict, Any, Union, Optional

from backend.config import settings

logger = logging.getLogger(__name__)

# Prompts for Gemma
CLAIMS_PROMPT = """You are an AI evidence analysis assistant. Extract all factual claims and assertions from the document text.
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

EVIDENCE_PROMPT = """You are an AI evidence analysis assistant. Extract all relevant physical evidence, facts, observations, and key evidence items from the document text.
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

EVENTS_PROMPT = """You are an AI evidence analysis assistant. Extract all key events and their associated dates or timestamps from the document text.
If a date is mentioned or can be derived directly from the sentence, extract it in YYYY-MM-DD or standard date format. If no date is given, set date to null.
Do not invent dates or events.

Return ONLY a valid JSON array of objects with the following schema for each event:
[
  {
    "date": "2026-08-02",
    "event": "Description of the event",
    "confidence": 0.91
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
        # Match json block inside ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

    # Try direct json loads
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # If wrapped in a dictionary like {"claims": [...]} or {"items": [...]}
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


def _call_gemma_api(prompt: str) -> str:
    """
    Call Gemma LLM model configured in the project settings.
    Supports google-genai, google-generativeai, or custom HTTP endpoint.
    Returns raw string response.
    """
    api_key = settings.GEMMA_API_KEY
    model_name = settings.GEMMA_MODEL_NAME

    if not api_key:
        logger.info("GEMMA_API_KEY not configured. Falling back to local heuristic extraction.")
        return ""

    try:
        # Try google-genai client
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text or ""
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"google-genai call failed: {e}")

    try:
        # Try google-generativeai client
        import google.generativeai as gai
        gai.configure(api_key=api_key)
        model = gai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text or ""
    except Exception as e:
        logger.warning(f"google.generativeai call failed: {e}")

    return ""


def _rule_based_fallback_claims(text: str) -> List[Dict[str, Any]]:
    """Rule-based heuristic extraction of claims when API is offline or unconfigured."""
    claims = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        if len(line) > 10:
            # Look for statements containing assertion keywords
            if any(kw in line.lower() for kw in ["failed", "claimed", "states", "reported", "alleged", "occurred", "damaged", "broken"]):
                claims.append({
                    "claim": line,
                    "confidence": 0.85
                })
    if not claims and lines:
        # Use first non-empty line as baseline claim if no keyword matched
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


def _rule_based_fallback_events(text: str) -> List[Dict[str, Any]]:
    """Rule-based heuristic extraction of events and dates."""
    events = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    date_pattern = r"(\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:, \d{4})?\b)"
    
    for line in lines:
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


def extract_claims(processed_document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract factual claims/statements from the processed document using Gemma.
    Returns a list of structured claim dictionaries.
    """
    doc_id = processed_document.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
    source = processed_document.get("source") or processed_document.get("filename", "unknown_source")
    text = processed_document.get("text", "")

    if not text.strip():
        return []

    prompt = CLAIMS_PROMPT.replace("{text}", text)
    raw_response = _call_gemma_api(prompt)
    parsed_items = _clean_and_parse_json(raw_response)

    if not parsed_items:
        logger.info("Using rule-based fallback for claims extraction.")
        parsed_items = _rule_based_fallback_claims(text)

    results = []
    for idx, item in enumerate(parsed_items):
        claim_text = item.get("claim") or item.get("text") or item.get("statement") or ""
        if not claim_text:
            continue
            
        conf = item.get("confidence")
        try:
            confidence = float(conf) if conf is not None else 0.90
        except (ValueError, TypeError):
            confidence = 0.90

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
    Extract relevant evidence from the document using Gemma.
    Returns a list of structured evidence dictionaries.
    Does NOT make legal conclusions.
    """
    doc_id = processed_document.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
    source = processed_document.get("source") or processed_document.get("filename", "unknown_source")
    text = processed_document.get("text", "")

    if not text.strip():
        return []

    prompt = EVIDENCE_PROMPT.replace("{text}", text)
    raw_response = _call_gemma_api(prompt)
    parsed_items = _clean_and_parse_json(raw_response)

    if not parsed_items:
        logger.info("Using rule-based fallback for evidence extraction.")
        parsed_items = _rule_based_fallback_evidence(text)

    results = []
    for idx, item in enumerate(parsed_items):
        ev_text = item.get("text") or item.get("evidence") or item.get("observation") or ""
        if not ev_text:
            continue

        conf = item.get("confidence")
        try:
            confidence = float(conf) if conf is not None else 0.90
        except (ValueError, TypeError):
            confidence = 0.90

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
    Extract important events and dates from the document using Gemma.
    Returns a list of structured event dictionaries.
    """
    doc_id = processed_document.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
    source = processed_document.get("source") or processed_document.get("filename", "unknown_source")
    text = processed_document.get("text", "")

    if not text.strip():
        return []

    prompt = EVENTS_PROMPT.replace("{text}", text)
    raw_response = _call_gemma_api(prompt)
    parsed_items = _clean_and_parse_json(raw_response)

    if not parsed_items:
        logger.info("Using rule-based fallback for events extraction.")
        parsed_items = _rule_based_fallback_events(text)

    results = []
    for idx, item in enumerate(parsed_items):
        event_text = item.get("event") or item.get("description") or item.get("text") or ""
        if not event_text:
            continue

        event_date = item.get("date")
        if event_date is not None:
            event_date = str(event_date).strip()
            if event_date.lower() in ["null", "none", "n/a", ""]:
                event_date = None

        conf = item.get("confidence")
        try:
            confidence = float(conf) if conf is not None else 0.90
        except (ValueError, TypeError):
            confidence = 0.90

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
