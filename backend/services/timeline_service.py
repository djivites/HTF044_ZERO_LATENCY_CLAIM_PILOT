import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def _parse_and_normalize_date(date_str: Optional[str]) -> Tuple[Optional[str], Optional[datetime]]:
    """
    Attempts to parse date strings into ISO YYYY-MM-DD format and datetime object.
    Returns (normalized_date_str, datetime_obj) or (None, None) if missing/invalid.
    """
    if not date_str or not isinstance(date_str, str):
        return None, None

    cleaned_str = date_str.strip()
    if cleaned_str.lower() in ["null", "none", "n/a", "unknown", ""]:
        return None, None

    # Try python-dateutil parser if available
    try:
        from dateutil import parser
        dt = parser.parse(cleaned_str, fuzzy=True)
        return dt.strftime("%Y-%m-%d"), dt
    except Exception:
        pass

    # Standard strftime format fallbacks
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            dt = datetime.strptime(cleaned_str, fmt)
            return dt.strftime("%Y-%m-%d"), dt
        except ValueError:
            continue

    return None, None


def build_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Responsibilities:
    - Accept events from extract_events().
    - Normalize event dates where possible into YYYY-MM-DD format.
    - Sort events chronologically.
    - Preserve event IDs, document/source references.
    - Handle missing or invalid dates safely without crashing (place them at the end).
    - Do not invent dates.
    """
    if not events:
        return []

    dated_events = []
    undated_events = []

    for item in events:
        event_id = item.get("event_id", "")
        raw_date = item.get("date")
        event_desc = item.get("event") or item.get("text", "")
        source = item.get("source") or item.get("document_id", "unknown_source")
        doc_id = item.get("document_id")

        normalized_date, dt_obj = _parse_and_normalize_date(raw_date)

        timeline_item = {
            "event_id": event_id,
            "date": normalized_date if normalized_date else (raw_date if raw_date else None),
            "event": event_desc,
            "source": source,
        }
        if doc_id:
            timeline_item["document_id"] = doc_id
        if "confidence" in item:
            timeline_item["confidence"] = item["confidence"]

        if dt_obj is not None:
            dated_events.append((dt_obj, timeline_item))
        else:
            undated_events.append(timeline_item)

    # Sort dated events chronologically
    dated_events.sort(key=lambda x: x[0])
    sorted_dated = [item[1] for item in dated_events]

    # Combine sorted dated events followed by undated/invalid-date events
    final_timeline = sorted_dated + undated_events
    return final_timeline
