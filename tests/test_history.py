"""Tests for Memento Historical Context Manager (Member 3).
Validates:
- Storing historical event records
- Retrieving historical events
- Retrieving previous operational responses
- Transparent adapter fallback status
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
    """Verify Memento status clearly reports local adapter vs cloud connection."""
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
        "is_demo": True
    }
    stored = store_event(test_event)
    assert stored is True

    all_events = get_all_stored_events()
    matched = [e for e in all_events if e.get("title") == test_event["title"]]
    assert len(matched) >= 1
    assert matched[0]["location"] == "Antwerp, Belgium"

def test_retrieve_previous_responses_by_category():
    """Verify querying previous operational responses filtered by disruption category."""
    responses = retrieve_previous_responses(category="Port Disruption")
    assert isinstance(responses, list)
    assert len(responses) > 0
    assert "response" in responses[0]
    assert "outcome" in responses[0]
