"""Tests for source-backed NOAA and Firecrawl collection."""
import sys
from types import SimpleNamespace

from backend.services import firecrawl_service
from utils.config import settings


NOAA_SOURCE = {
    "name": "NOAA Active Alerts",
    "url": firecrawl_service.NOAA_ALERTS_URL,
    "category": "Weather Disruption",
}


def _noaa_response():
    return SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {
            "features": [{
                "id": "https://api.weather.gov/alerts/urn:alert:123",
                "properties": {
                    "headline": "Severe wind warning",
                    "description": "High winds threaten transportation operations.",
                    "instruction": "Secure equipment and monitor official updates.",
                    "areaDesc": "Coastal Washington",
                    "sent": "2025-01-02T03:00:00Z",
                },
            }]
        },
    )


def test_firecrawl_scrape_uses_provider_result(monkeypatch):
    class FakeFirecrawlApp:
        def __init__(self, api_key):
            assert api_key == "configured-test-key"

        def scrape_url(self, url, params):
            assert url == "https://maritime.example/news"
            assert params["formats"] == ["markdown"]
            return {
                "metadata": {"title": "Verified port notice"},
                "markdown": "The port authority reported an operational delay.",
            }

    monkeypatch.setattr(settings, "firecrawl_api_key", "configured-test-key")
    monkeypatch.setitem(sys.modules, "firecrawl", SimpleNamespace(FirecrawlApp=FakeFirecrawlApp))
    records, error = firecrawl_service.collect_from_single_source({
        "name": "Port Authority",
        "url": "https://maritime.example/news",
        "category": "Port Disruption",
    })

    assert error is None
    assert len(records) == 1
    assert records[0]["title"] == "Verified port notice"
    assert records[0]["content"] == "The port authority reported an operational delay."
    assert records[0]["source_url"] == "https://maritime.example/news"
    assert records[0]["published_date"] is None
    assert records[0]["collected_at"]


def test_website_scraping_without_firecrawl_key_returns_error(monkeypatch):
    monkeypatch.setattr(settings, "firecrawl_api_key", "")
    records, error = firecrawl_service.collect_from_single_source({
        "name": "Port Authority",
        "url": "https://maritime.example/news",
        "category": "Port Disruption",
    })

    assert records == []
    assert error and "FIRECRAWL_API_KEY is not configured" in error


def test_scraper_rejects_invalid_url():
    records, error = firecrawl_service.collect_from_single_source({
        "name": "Corrupt Source",
        "url": "not-a-valid-http-url",
        "category": "Other",
    })

    assert records == []
    assert error and "Invalid URL" in error


def test_noaa_collection_uses_actual_alert_payload(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return _noaa_response()

    monkeypatch.setattr(firecrawl_service.requests, "get", fake_get)
    records, error = firecrawl_service.collect_from_single_source(NOAA_SOURCE)

    assert error is None
    assert len(calls) == 2
    assert records[0]["title"] == "Severe wind warning"
    assert records[0]["source_url"] == "https://api.weather.gov/alerts/urn:alert:123"
    assert records[0]["is_demo"] is False


def test_batch_collection_keeps_real_records_and_logs_invalid_sources(monkeypatch, tmp_path):
    monkeypatch.setattr(firecrawl_service.requests, "get", lambda *args, **kwargs: _noaa_response())
    monkeypatch.setattr(firecrawl_service, "RAW_DATA_DIR", tmp_path)
    records, errors = firecrawl_service.collect_updates([
        NOAA_SOURCE,
        {"name": "Bad URL Source", "url": "httpx://invalid-link", "category": "Other"},
    ])

    assert len(records) == 1
    assert len(errors) == 1
    assert errors[0]["url"] == "httpx://invalid-link"
    assert list(tmp_path.glob("raw_disruptions_*.json"))
