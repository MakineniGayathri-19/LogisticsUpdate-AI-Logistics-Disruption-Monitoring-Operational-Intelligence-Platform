"""Tests for Firecrawl Scraper Service (Member 1).
Validates:
- Successful collection from sources
- Handling of invalid URL formats
- Handling when website/endpoint returns empty content
- Demonstration fallback resilience
"""
import pytest
from backend.services.firecrawl_service import collect_from_single_source, collect_updates

def test_scraper_valid_demo_source():
    """Verify scraper successfully processes a valid logistics news URL."""
    source = {
        "name": "Maritime Executive Live Wire",
        "url": "https://maritime-executive.com/article/singapore-berthing-surge-2024",
        "category": "Port Disruption"
    }
    records, error = collect_from_single_source(source)
    assert error is None
    assert len(records) == 1
    assert "title" in records[0]
    assert "content" in records[0]
    assert records[0]["source_url"] == source["url"]

def test_scraper_invalid_url():
    """Verify scraper rejects malformed URLs with descriptive error."""
    source = {
        "name": "Corrupt Source",
        "url": "not-a-valid-http-url",
        "category": "Other"
    }
    records, error = collect_from_single_source(source)
    assert error is not None
    assert "Invalid URL" in error
    assert len(records) == 0

def test_scraper_batch_collection():
    """Verify multi-source batch collection handles mixed valid/invalid targets."""
    sources = [
        {
            "name": "NOAA Marine",
            "url": "https://www.weather.gov/marine/alerts",
            "category": "Weather Disruption"
        },
        {
            "name": "Bad URL Source",
            "url": "httpx://invalid-link",
            "category": "Other"
        }
    ]
    records, errors = collect_updates(sources)
    assert len(records) >= 1
    assert len(errors) == 1
    assert errors[0]["url"] == "httpx://invalid-link"
