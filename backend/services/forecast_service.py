"""Live 24-hour weather exposure forecasts for major logistics hubs."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_DOCS = "https://open-meteo.com/en/docs"
RISK_METHOD = (
    "Additive 0-100 index: weather code indicators add 12/25/35 points; "
    "maximum gust thresholds add 10/20/30; precipitation adds 8/15/25; "
    "snowfall adds 10/20. Scores are capped at 100; levels are Low (<20), "
    "Moderate (20-44), High (45-69), and Critical (70+). Not a trained or "
    "calibrated probability model."
)

LOGISTICS_HUBS = [
    {"name": "Rotterdam", "latitude": 51.9244, "longitude": 4.4777},
    {"name": "Singapore", "latitude": 1.3521, "longitude": 103.8198},
    {"name": "Los Angeles", "latitude": 33.7405, "longitude": -118.2720},
    {"name": "Shanghai", "latitude": 31.2304, "longitude": 121.4737},
    {"name": "Panama Canal", "latitude": 9.0800, "longitude": -79.6800},
    {"name": "Chicago", "latitude": 41.8781, "longitude": -87.6298},
]


def _values(hourly: dict[str, Any], field: str) -> list[float]:
    values = hourly.get(field)
    if not isinstance(values, list) or not values:
        raise ValueError(f"Open-Meteo response is missing hourly '{field}' data.")
    if any(value is None for value in values):
        raise ValueError(f"Open-Meteo returned incomplete hourly '{field}' data.")
    return [float(value) for value in values]


def _weather_risk(hourly: dict[str, Any]) -> tuple[int, list[str], dict[str, float]]:
    codes = _values(hourly, "weather_code")
    wind = _values(hourly, "wind_speed_10m")
    gusts = _values(hourly, "wind_gusts_10m")
    precipitation = _values(hourly, "precipitation")
    snowfall = _values(hourly, "snowfall")
    points = 0
    reasons = []

    if any(code in {95, 96, 99} for code in codes):
        points += 35
        reasons.append("Thunderstorm or hail indicated in the hourly forecast")
    elif any(code in {65, 66, 67, 75, 76, 77, 82, 86} for code in codes):
        points += 25
        reasons.append("Heavy rain, freezing rain, or heavy snow indicated")
    elif any(code in {51, 53, 55, 61, 63, 71, 73, 80, 81, 85} for code in codes):
        points += 12
        reasons.append("Rain or snow indicated in the hourly forecast")

    max_gust = max(gusts)
    if max_gust >= 90:
        points += 30
        reasons.append(f"Forecast wind gusts reach {max_gust:.0f} km/h")
    elif max_gust >= 65:
        points += 20
        reasons.append(f"Forecast wind gusts reach {max_gust:.0f} km/h")
    elif max_gust >= 45:
        points += 10
        reasons.append(f"Forecast wind gusts reach {max_gust:.0f} km/h")

    max_precipitation = max(precipitation)
    if max_precipitation >= 15:
        points += 25
        reasons.append(f"Hourly precipitation reaches {max_precipitation:.1f} mm")
    elif max_precipitation >= 8:
        points += 15
        reasons.append(f"Hourly precipitation reaches {max_precipitation:.1f} mm")
    elif max_precipitation >= 3:
        points += 8
        reasons.append(f"Hourly precipitation reaches {max_precipitation:.1f} mm")

    max_snowfall = max(snowfall)
    if max_snowfall >= 5:
        points += 20
        reasons.append(f"Hourly snowfall reaches {max_snowfall:.1f} cm")
    elif max_snowfall >= 1:
        points += 10
        reasons.append(f"Hourly snowfall reaches {max_snowfall:.1f} cm")

    return min(points, 100), reasons or ["No elevated weather indicators in the forecast"], {
        "wind_speed_max_kmh": max(wind),
        "wind_gust_max_kmh": max_gust,
        "precipitation_max_mm": max_precipitation,
        "snowfall_max_cm": max_snowfall,
    }


def _risk_level(score: int) -> str:
    if score >= 70:
        return "Critical"
    if score >= 45:
        return "High"
    if score >= 20:
        return "Moderate"
    return "Low"


def get_24_hour_forecast() -> dict[str, Any]:
    """Fetch and persist a live weather forecast and transparent risk index."""
    params = {
        "latitude": ",".join(str(hub["latitude"]) for hub in LOGISTICS_HUBS),
        "longitude": ",".join(str(hub["longitude"]) for hub in LOGISTICS_HUBS),
        "hourly": "weather_code,wind_speed_10m,wind_gusts_10m,precipitation,snowfall",
        "forecast_hours": 24,
        "timezone": "UTC",
    }
    response = requests.get(FORECAST_URL, params=params, timeout=20)
    response.raise_for_status()
    raw_data = response.json()
    forecasts = raw_data if isinstance(raw_data, list) else [raw_data]
    if len(forecasts) != len(LOGISTICS_HUBS):
        raise ValueError("Open-Meteo returned an unexpected number of location forecasts.")

    fetched_at = datetime.now(timezone.utc).isoformat()
    source_url = response.url
    locations = []
    for hub, forecast in zip(LOGISTICS_HUBS, forecasts):
        if not isinstance(forecast, dict):
            raise ValueError(f"Open-Meteo returned invalid forecast data for {hub['name']}.")
        hourly = forecast.get("hourly")
        if not isinstance(hourly, dict):
            raise ValueError(f"Open-Meteo returned no hourly forecast for {hub['name']}.")
        forecast_times = hourly.get("time")
        if not isinstance(forecast_times, list) or len(forecast_times) != 24:
            raise ValueError(f"Open-Meteo returned an incomplete 24-hour timeline for {hub['name']}.")
        score, reasons, metrics = _weather_risk(hourly)
        locations.append({
            **hub,
            "risk_score": score,
            "risk_level": _risk_level(score),
            "reasons": reasons,
            "metrics": metrics,
            "forecast_hours": len(forecast_times),
            "forecast_start": forecast_times[0],
            "forecast_end": forecast_times[-1],
        })

    snapshot_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_name = f"open_meteo_forecast_{snapshot_timestamp}.json"
    processed_name = f"24h_weather_risk_{snapshot_timestamp}"
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (RAW_DATA_DIR / raw_name).open("w", encoding="utf-8") as file:
        json.dump({"retrieved_at": fetched_at, "source_url": source_url, "data": raw_data}, file, indent=2)

    processed_data = {
        "forecast_window_hours": 24,
        "retrieved_at": fetched_at,
        "data_source": "Open-Meteo Forecast API",
        "source_url": source_url,
        "attribution_url": OPEN_METEO_DOCS,
        "risk_method": RISK_METHOD,
        "locations": locations,
        "raw_snapshot": f"data/raw/{raw_name}",
        "processed_snapshot": f"data/processed/{processed_name}.json",
    }
    json_path = PROCESSED_DATA_DIR / f"{processed_name}.json"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(processed_data, file, indent=2)
    with (PROCESSED_DATA_DIR / f"{processed_name}.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "name", "latitude", "longitude", "risk_score", "risk_level",
            "wind_speed_max_kmh", "wind_gust_max_kmh", "precipitation_max_mm",
            "snowfall_max_cm", "forecast_start", "forecast_end",
        ])
        writer.writeheader()
        for location in locations:
            writer.writerow({
                **{key: location[key] for key in ("name", "latitude", "longitude", "risk_score", "risk_level", "forecast_start", "forecast_end")},
                **location["metrics"],
            })

    return processed_data
