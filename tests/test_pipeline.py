"""End-to-end integration test suite for LogisticsUpdate AI."""
from fastapi.testclient import TestClient
from app.main import app
from database.db import init_db
from backend.services.data_processing import process_raw_records
from backend.services import data_processing
from backend.services.llm_service import LOCAL_REPORT_PROVIDER

client = TestClient(app)

def setup_module():
    """Ensure database is initialized for tests."""
    init_db()

def test_health_check():
    """Verify backend health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_source_crud():
    """Test creating and listing monitoring sources."""
    payload = {
        "name": "Integration Test Maritime Feed",
        "url": "https://maritime-test-feed.org/alerts",
        "category": "Port Disruption"
    }
    create_res = client.post("/api/sources", json=payload)
    assert create_res.status_code == 200
    source_id = create_res.json()["id"]

    list_res = client.get("/api/sources")
    assert list_res.status_code == 200
    assert any(s["id"] == source_id for s in list_res.json())

def test_disruption_and_similarity():
    """Test creating disruption and matching historical precedents."""
    payload = {
        "title": "Severe Port Dwell Bottleneck",
        "description": "Rail congestion causes severe dwell time backlog and container delays at maritime terminal in Los Angeles.",
        "category": "Port Disruption",
        "severity": "High",
        "status": "Active",
        "source_name": "Test Source",
        "source_url": "https://example.com/disruption"
    }
    create_res = client.post("/api/disruptions", json=payload)
    assert create_res.status_code == 200
    dis_data = create_res.json()
    assert "id" in dis_data

    history_res = client.post("/api/historical-events", json={
        "title": "Los Angeles port congestion and rail backlog",
        "description": "Terminal congestion and a rail car shortage caused container dwell delays.",
        "category": "Port Disruption",
        "location": "Los Angeles, CA, USA",
        "severity": "High",
        "source_name": "Port Authority Archive",
        "source_url": "https://archive.example/la-congestion",
        "response": "Rerouted priority cargo to a nearby terminal.",
        "outcome": "The backlog was reduced over the following week.",
    })
    assert history_res.status_code == 200

    # Test comparison endpoint
    comp_res = client.post(f"/api/compare/{dis_data['id']}")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "similar_events" in comp_data
    assert len(comp_data["similar_events"]) > 0

def test_report_generation_works_without_external_ai_provider():
    """Local reports require no external provider and remain downloadable."""
    payload = {
        "title": "Blizzard Rail Freeze Advisory",
        "description": "Sub-zero temperatures freeze tracks and halt freight rail corridors in Chicago.",
        "category": "Weather Disruption",
        "severity": "Critical",
        "status": "Active",
        "source_name": "Weather Bureau",
        "source_url": "https://example.com/weather"
    }
    create_res = client.post("/api/disruptions", json=payload)
    assert create_res.status_code == 200
    event_id = create_res.json()["id"]

    rep_res = client.post("/api/reports/generate", json={"event_id": event_id})
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "id" in rep_data
    assert "content" in rep_data
    assert rep_data["llm_provider"] == LOCAL_REPORT_PROVIDER
    assert "1. EXECUTIVE SUMMARY" in rep_data["content"]
    assert "12. SOURCE REFERENCES" in rep_data["content"]
    assert "This is not an AI-generated report." in rep_data["content"]

    # Test PDF generation endpoint
    pdf_res = client.get(f"/api/reports/{rep_data['id']}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 500


def test_report_integration_status_is_keyless():
    response = client.get("/api/integrations")

    assert response.status_code == 200
    assert response.json()["report_generator"] == "Local evidence-based template"
    assert response.json()["report_requires_api_key"] is False


def test_historical_event_requires_source_and_observed_outcome():
    response = client.post("/api/historical-events", json={
        "title": "Historical event without outcome",
        "description": "This request omits a real response and outcome.",
        "source_name": "Test archive",
        "source_url": "https://archive.example/event",
    })

    assert response.status_code == 422


def test_forecast_endpoint_returns_forecast_shape(monkeypatch):
    forecast = {
        "data_source": "Open-Meteo Forecast API",
        "forecast_window_hours": 24,
        "locations": [{"name": "Rotterdam", "risk_score": 0, "risk_level": "Low"}],
    }
    monkeypatch.setattr("backend.api.routes.get_24_hour_forecast", lambda: forecast)

    response = client.get("/api/forecast")

    assert response.status_code == 200
    assert response.json() == forecast

def test_data_processing(monkeypatch, tmp_path):
    """Test cleaning and severity extraction on raw data."""
    monkeypatch.setattr(data_processing, "PROCESSED_DATA_DIR", tmp_path)
    raw = [
        {
            "title": "Severe winter weather closes mountain pass",
            "content": "Heavy snowfall and blizzard conditions block road transport.",
            "category": "Road",
            "source_name": "Traffic Alert",
            "source_url": "https://example.com/road"
        }
    ]
    cleaned = process_raw_records(raw)
    assert len(cleaned) == 1
    assert cleaned[0]["severity"] in ["Critical", "High"]
