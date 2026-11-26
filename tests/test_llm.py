"""Tests for local evidence-based operational report generation."""

from backend.services.llm_service import LOCAL_REPORT_PROVIDER, generate_brief


def _event():
    return {
        "event_id": "test-report-01",
        "title": "Rotterdam Gate Automation Network Outage",
        "description": "Terminal operating system failure halts container processing gates.",
        "category": "Port Disruption",
        "location": "Rotterdam, Netherlands",
        "severity": "High",
        "severity_justification": "Source reports stopped gate processing.",
        "status": "Active",
        "published_date": "2025-03-10",
        "source_name": "Maritime Executive",
        "source_url": "https://maritime.example/rotterdam-gate-outage",
    }


def test_local_report_uses_recorded_event_and_historical_facts():
    brief, provider = generate_brief(_event(), {
        "similar_events": [{
            "title": "Recorded Rotterdam terminal outage",
            "category": "Port Disruption",
            "location": "Rotterdam",
            "similarity_percentage": 78.4,
            "previous_response": "Activated manual gate checks.",
            "historical_outcome": "Backlog cleared within five days.",
        }]
    })

    assert provider == LOCAL_REPORT_PROVIDER
    assert "This is not an AI-generated report." in brief
    assert "Rotterdam Gate Automation Network Outage" in brief
    assert "Source reports stopped gate processing." in brief
    assert "https://maritime.example/rotterdam-gate-outage" in brief
    assert "78.4%" in brief
    assert "Activated manual gate checks." in brief
    assert "Backlog cleared within five days." in brief
    assert "1. EXECUTIVE SUMMARY" in brief
    assert "13. DATA LIMITATIONS AND UNCERTAINTIES" in brief
    assert "Similarity scores are text-matching results, not probabilities or forecasts." in brief


def test_local_report_handles_missing_fields_and_empty_history():
    brief, provider = generate_brief(
        {"title": "Record with missing evidence"},
        {"similar_events": []},
    )

    assert provider == LOCAL_REPORT_PROVIDER
    assert "No stored historical precedents matched this event." in brief
    assert "No operational responses or outcomes are recorded" in brief
    assert "No severity justification is recorded." in brief
    assert "Not recorded" in brief
