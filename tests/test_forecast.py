"""Tests for the live weather forecast score and persisted snapshots."""
import json
from types import SimpleNamespace

from backend.services import forecast_service


def _hourly(**overrides):
    values = {
        "weather_code": [0] * 24,
        "wind_speed_10m": [10] * 24,
        "wind_gusts_10m": [20] * 24,
        "precipitation": [0] * 24,
        "snowfall": [0] * 24,
        "time": [f"2025-01-01T{hour:02d}:00" for hour in range(24)],
    }
    values.update(overrides)
    return values


def test_weather_risk_score_uses_live_indicators():
    hourly = _hourly(
        weather_code=[95] + [0] * 23,
        wind_gusts_10m=[65] + [20] * 23,
        precipitation=[8] + [0] * 23,
        snowfall=[1] + [0] * 23,
    )

    score, reasons, metrics = forecast_service._weather_risk(hourly)

    assert score == 80
    assert len(reasons) == 4
    assert metrics["wind_gust_max_kmh"] == 65


def test_weather_risk_rejects_incomplete_api_values():
    hourly = _hourly(wind_speed_10m=[None] + [10] * 23)

    try:
        forecast_service._weather_risk(hourly)
    except ValueError as exc:
        assert "incomplete hourly 'wind_speed_10m'" in str(exc)
    else:
        raise AssertionError("Incomplete public forecast values must not be treated as zero.")


def test_forecast_saves_raw_processed_json_and_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(forecast_service, "RAW_DATA_DIR", tmp_path / "raw")
    monkeypatch.setattr(forecast_service, "PROCESSED_DATA_DIR", tmp_path / "processed")
    raw_payload = [{
        "hourly": _hourly(),
    } for _ in forecast_service.LOGISTICS_HUBS]
    monkeypatch.setattr(forecast_service.requests, "get", lambda *args, **kwargs: SimpleNamespace(
        url="https://api.open-meteo.com/v1/forecast?verified=true",
        raise_for_status=lambda: None,
        json=lambda: raw_payload,
    ))

    result = forecast_service.get_24_hour_forecast()

    assert result["forecast_window_hours"] == 24
    assert len(result["locations"]) == len(forecast_service.LOGISTICS_HUBS)
    raw_path = tmp_path / "raw" / result["raw_snapshot"].split("/")[-1]
    processed_path = tmp_path / "processed" / result["processed_snapshot"].split("/")[-1]
    csv_path = processed_path.with_suffix(".csv")
    assert json.loads(raw_path.read_text())["source_url"].startswith("https://api.open-meteo.com/")
    assert json.loads(processed_path.read_text())["risk_method"].startswith("Additive 0-100 index")
    assert csv_path.exists()
    assert result["raw_snapshot"].rsplit("_", 1)[-1].split(".")[0] == result["processed_snapshot"].rsplit("_", 1)[-1].split(".")[0]
