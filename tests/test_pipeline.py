"""End-to-end integration test suite for LogisticsUpdate AI."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from database.db import init_db
from backend.services.data_processing import process_raw_records
from backend.services.memento_manager import retrieve_similar_events
from backend.services.report_service import generate_report_for_event

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

    # Test comparison endpoint
    comp_res = client.post(f"/api/compare/{dis_data['id']}")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "similar_events" in comp_data
    assert len(comp_data["similar_events"]) > 0

def test_report_generation():
    """Test generating, retrieving, and exporting an operational intelligence brief."""
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

    # Generate brief
    rep_res = client.post("/api/reports/generate", json={"event_id": event_id})
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "id" in rep_data
    assert "content" in rep_data
    assert "1. EXECUTIVE SUMMARY" in rep_data["content"]
    assert "12. SOURCE REFERENCES" in rep_data["content"]

    # Test PDF generation endpoint
    pdf_res = client.get(f"/api/reports/{rep_data['id']}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 500

def test_data_processing():
    """Test cleaning and severity extraction on raw data."""
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
