"""Tests for source-backed historical event storage.
Validates:
- Storing historical event records
- Retrieving historical events
- Retrieving previous operational responses
- Accurate local storage status and demo exclusion
"""
import pytest
from database.db import init_db
from backend.services.memento_manager import (
    store_event,
    get_all_stored_events,
    retrieve_previous_responses,
    get_memento_status,
    store_operational_response
)

def setup_module():
    init_db()

def test_memento_status_reporting():
    """Verify historical storage status clearly reports the SQLite database."""
    status = get_memento_status()
    assert "status" in status
    assert "adapter" in status
    assert "is_live" in status

def test_store_and_retrieve_historical_event():
    """Verify saving a historical precedent and retrieving it."""
    test_event = {
        "event_id": "test-hist-999",
        "title": "Historical Antwerp Berth Congestion",
        "description": "Vessel queue at Antwerp due to feeder ship bunching.",
        "category": "Port Disruption",
        "location": "Antwerp, Belgium",
        "severity": "High",
        "response": "Rerouted non-urgent feeder traffic to Zeebrugge.",
        "outcome": "Congestion cleared within 4 business days.",
        "source_name": "Port Authority Archive",
        "source_url": "https://archive.example/antwerp-berth-congestion",
        "is_demo": False
    }
    stored = store_event(test_event)
    assert stored is True

    all_events = get_all_stored_events()
    matched = [e for e in all_events if e.get("title") == test_event["title"]]
    assert len(matched) >= 1
    assert matched[0]["location"] == "Antwerp, Belgium"
    assert matched[0]["source_url"] == test_event["source_url"]


def test_demo_history_is_not_returned():
    """Exclude old simulated precedents from historical retrieval."""
    test_event = {
        "event_id": "test-demo-hist-999",
        "title": "Simulated port closure",
        "description": "A test-only simulated closure record.",
        "category": "Port Disruption",
        "severity": "High",
        "source_name": "Test fixture",
        "source_url": "https://example.test/simulated",
        "response": "Test response action.",
        "outcome": "Test outcome recorded.",
        "is_demo": True,
    }

    store_event(test_event)
    assert all(event.get("event_id") != test_event["event_id"] for event in get_all_stored_events())

def test_retrieve_previous_responses_by_category():
    """Verify querying previous operational responses filtered by disruption category."""
    responses = retrieve_previous_responses(category="Port Disruption")
    assert isinstance(responses, list)
    assert len(responses) > 0
    assert "response" in responses[0]
    assert "outcome" in responses[0]
