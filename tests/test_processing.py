"""Tests for Data Processing Service (Member 2).
Validates:
- Missing value dropping
- Duplicate detection & removal
- Date normalization to ISO 8601 UTC
- Category classification mapping
- Rule-based severity assignment (no hallucinations)
"""
import pytest
from backend.services.data_processing import (
    process_raw_records,
    assign_rule_based_severity,
    extract_location,
    clean_and_normalize_date
)

def test_missing_and_empty_records_dropped():
    """Verify records with empty or corrupt titles/content are dropped."""
    raw = [
        {"title": "", "content": "", "source_url": "https://valid.com/1"},
        {"title": "Valid Incident", "content": "", "source_url": "https://valid.com/2"},
        {"title": "Valid Incident", "content": "Substantive description of port stoppage", "source_url": "https://valid.com/3"}
    ]
    cleaned = process_raw_records(raw)
    assert len(cleaned) == 1
    assert cleaned[0]["title"] == "Valid Incident"

def test_duplicate_record_removal():
    """Verify identical URL + Title combinations are deduplicated."""
    raw = [
        {"title": "Red Sea Divergence", "content": "Vessels detour around Africa", "source_url": "https://freight.com/red-sea"},
        {"title": "Red Sea Divergence", "content": "Vessels detour around Africa duplicate", "source_url": "https://freight.com/red-sea"}
    ]
    cleaned = process_raw_records(raw)
    assert len(cleaned) == 1

def test_demo_provenance_is_preserved():
    """Keep the demo marker when raw records are cleaned and normalized."""
    raw = [{
        "title": "Simulated Port Closure",
        "content": "Example content describing an operational port closure.",
        "source_url": "https://example.com/demo",
        "is_demo": True
    }]
    cleaned = process_raw_records(raw)
    assert len(cleaned) == 1
    assert cleaned[0]["is_demo"] is True

def test_rule_based_severity_assignment():
    """Verify evidence-based severity keywords."""
    sev1, just1 = assign_rule_based_severity("Terminal Closure Notice", "Port suspended operations due to hurricane")
    assert sev1 == "Critical"
    assert "closure" in just1.lower() or "hurricane" in just1.lower()

    sev2, just2 = assign_rule_based_severity("Minor delay in clearance", "Slight equipment inspection slowdown")
    assert sev2 in ("Medium", "Low")

def test_location_extraction():
    """Verify extraction of known hubs."""
    loc = extract_location("Severe container backlog observed at Rotterdam container terminal")
    assert loc == "Rotterdam"

    loc2 = extract_location("Dense fog causes anchor hold at Port of Savannah")
    assert "Savannah" in loc2

def test_date_normalization():
    """Verify ISO normalization of diverse dates."""
    res1 = clean_and_normalize_date("2024-05-12T10:00:00Z")
    assert "2024-05-12" in res1
    res2 = clean_and_normalize_date(None)
    assert isinstance(res2, str)
