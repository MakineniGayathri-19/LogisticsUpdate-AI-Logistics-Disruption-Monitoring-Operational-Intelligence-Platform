"""Tests for the FastAPI-served operations dashboard."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_is_served_from_root():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LogisticsUpdate AI" in response.text


def test_dashboard_assets_are_served():
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "renderOverview" in response.text
