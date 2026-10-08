import pytest
from backend.services.timeline_service import build_timeline


def test_build_timeline_chronological_sorting():
    events = [
        {
            "event_id": "event_003",
            "date": "2026-08-09",
            "event": "Repair report created.",
            "source": "repair_report.pdf"
        },
        {
            "event_id": "event_001",
            "date": "2026-08-02",
            "event": "Device stopped working.",
            "source": "complaint.pdf"
        },
        {
            "event_id": "event_002",
            "date": "2026-08-07",
            "event": "Device inspected.",
            "source": "inspection.pdf"
        }
    ]

    timeline = build_timeline(events)
    assert len(timeline) == 3
    assert timeline[0]["event_id"] == "event_001"
    assert timeline[0]["date"] == "2026-08-02"
    assert timeline[1]["event_id"] == "event_002"
    assert timeline[1]["date"] == "2026-08-07"
    assert timeline[2]["event_id"] == "event_003"
    assert timeline[2]["date"] == "2026-08-09"


def test_build_timeline_handles_missing_or_invalid_dates():
    events = [
        {
            "event_id": "event_dated",
            "date": "2026-08-02",
            "event": "Dated event",
            "source": "doc1.pdf"
        },
        {
            "event_id": "event_no_date",
            "date": None,
            "event": "Undated event",
            "source": "doc2.pdf"
        },
        {
            "event_id": "event_invalid_date",
            "date": "Not a date at all",
            "event": "Invalid date event",
            "source": "doc3.pdf"
        }
    ]

    timeline = build_timeline(events)
    assert len(timeline) == 3
    assert timeline[0]["event_id"] == "event_dated"
    # Undated / invalid date events are appended without crashing
    event_ids = [t["event_id"] for t in timeline]
    assert "event_no_date" in event_ids
    assert "event_invalid_date" in event_ids


def test_build_timeline_empty():
    assert build_timeline([]) == []
