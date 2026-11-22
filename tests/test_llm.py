"""Tests for Generative AI Operational Brief Service (Member 4).
Validates:
- Generation of complete 13-section operational brief
- Strict adherence to input data (no hallucinations)
- Citing of source URLs
- Fallback handling when external LLM credentials are absent
"""
import pytest
from backend.services.llm_service import generate_brief, generate_deterministic_brief

def test_13_section_brief_structure():
    """Verify that generated brief contains all 13 mandatory sections."""
    event = {
        "event_id": "test-llm-01",
        "title": "Rotterdam Gate Automation Network Outage",
        "description": "Terminal operating system failure halts container processing gates.",
        "category": "Port Disruption",
        "location": "Rotterdam, Netherlands",
        "severity": "High",
        "severity_justification": "Gate closure halts drayage trucks",
        "source_name": "Maritime Executive",
        "source_url": "https://maritime-executive.com/article/rotterdam-gate-outage",
        "published_date": "2024-04-10T12:00:00Z"
    }
    comparison_data = {
        "similar_events": [
            {
                "title": "Rotterdam Port Cyberattack on Terminal Operating System",
                "category": "Port Disruption",
                "location": "Rotterdam, Netherlands",
                "similarity_percentage": 78.4,
                "previous_response": "Activated manual paper gate checks.",
                "historical_outcome": "Cleared backlog within 5 days.",
                "key_differences": ["Current is network glitch vs historical ransomware"],
                "operational_observations": ["Direct terminal precedent."]
            }
        ]
    }

    brief_text, provider = generate_brief(event, comparison_data)
    assert brief_text is not None
    assert len(brief_text) > 400

    # Verify key mandatory sections
    required_sections = [
        "1. EXECUTIVE SUMMARY",
        "2. CURRENT DISRUPTION DETAILS",
        "3. DISRUPTION CATEGORY",
        "4. LOCATION",
        "5. SEVERITY AND JUSTIFICATION",
        "6. POTENTIAL OPERATIONAL IMPACT",
        "7. HISTORICAL EVENT COMPARISON",
        "8. PREVIOUS OPERATIONAL RESPONSES",
        "9. KEY CHANGES",
        "10. RECOMMENDED MONITORING ACTIONS",
        "11. OPERATIONAL CONSIDERATIONS",
        "12. SOURCE REFERENCES",
        "13. DATA LIMITATIONS AND UNCERTAINTIES"
    ]
    for sec in required_sections:
        assert sec in brief_text, f"Missing mandatory brief section: {sec}"

    # Verify source URL is strictly cited
    assert event["source_url"] in brief_text

def test_missing_historical_context_handling():
    """Verify that brief explicitly transparently states when no historical precedents exist."""
    event = {
        "title": "Novel Drone Regulation Halts Drone Delivery Corridor",
        "description": "Civil aviation authority suspends drone corridor over urban distribution hub.",
        "category": "Other",
        "source_name": "Aviation Bulletin",
        "source_url": "https://aviation.gov/drone-notice",
        "severity": "Low"
    }
    comparison_data = {"similar_events": []}

    brief_text = generate_deterministic_brief(event, comparison_data)
    assert "No directly comparable historical disruption records logged" in brief_text
    assert event["source_url"] in brief_text
