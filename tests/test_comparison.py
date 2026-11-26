"""Tests for Event Comparison Service (TF-IDF & Cosine Similarity).
Validates:
- Identifying similar historical incidents
- Distinguishing different incidents
- Handling events with no matching text
- Extracting key differences and operational observations
"""
import pytest
from database.db import init_db
from database import repositories
from backend.services.event_comparison import compare_disruption_with_history

def setup_module():
    init_db()
    repositories.add_historical_event({
        "event_id": "test-port-precedent",
        "title": "Los Angeles port berth congestion and container dwell backlog",
        "description": "Rail car shortage and terminal congestion caused container dwell delays.",
        "category": "Port Disruption",
        "location": "Los Angeles, CA, USA",
        "severity": "High",
        "source_name": "Port authority archive",
        "source_url": "https://archive.example/los-angeles-congestion",
        "response": "Rerouted priority cargo to a nearby terminal.",
        "outcome": "Backlog reduced over the following week.",
    })
    repositories.add_historical_event({
        "event_id": "test-winter-precedent",
        "title": "Chicago winter blizzard freezes freight rail switches",
        "description": "Freezing temperatures and snow halted freight trains across the Midwest.",
        "category": "Weather Disruption",
        "location": "Chicago, IL, USA",
        "severity": "Critical",
        "source_name": "Rail operator archive",
        "source_url": "https://archive.example/chicago-winter",
        "response": "Deployed crews to clear switches and reroute freight.",
        "outcome": "Rail service resumed after the storm passed.",
    })

def test_compare_similar_port_incident():
    """Verify that a port dwell disruption matches historical port incidents with high score."""
    current = {
        "title": "Severe Berth Congestion and Container Dwell Backlog",
        "description": "Port of Los Angeles faces rail car shortage and container dwell times exceeding 6 days.",
        "category": "Port Disruption",
        "location": "Los Angeles, CA, USA",
        "severity": "High"
    }
    result = compare_disruption_with_history(current, top_n=2)
    assert "similar_events" in result
    matches = result["similar_events"]
    assert len(matches) > 0
    assert matches[0]["similarity"] > 0.15
    assert "previous_response" in matches[0]
    assert "historical_outcome" in matches[0]
    assert len(matches[0]["key_differences"]) > 0

def test_compare_weather_blizzard_incident():
    """Verify that a rail freeze disruption matches winter storm historical precedent."""
    current = {
        "title": "Midwest Sub-Zero Rail Freeze Stoppage",
        "description": "Blizzard temperatures freeze Chicago interchange rail switches and halt freight trains.",
        "category": "Weather Disruption",
        "location": "Chicago, IL, USA",
        "severity": "Critical"
    }
    result = compare_disruption_with_history(current, top_n=1)
    matches = result["similar_events"]
    assert len(matches) > 0
    top_match = matches[0]
    assert "winter" in top_match["title"].lower() or "rail" in top_match["title"].lower() or "chicago" in top_match["location"].lower()

def test_compare_empty_or_no_text():
    """Verify graceful handling when query text is minimal."""
    empty_event = {"title": "", "description": ""}
    result = compare_disruption_with_history(empty_event)
    assert result["similar_events"] == []
    assert "message" in result
