"""Public-source collection using NOAA alerts and optional Firecrawl scraping."""
import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests

from utils.config import settings
from utils.logger import logger
from utils.validators import is_valid_url

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

NOAA_ALERTS_URL = "https://api.weather.gov/alerts/active"


def _collect_noaa_alerts(source: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Fetch actual severe and extreme alerts from the public NOAA/NWS API."""
    records = []
    seen_alerts = set()
    headers = {
        "User-Agent": "LogisticsUpdateAI/1.0 (public weather alerts)",
        "Accept": "application/geo+json",
    }
    try:
        for severity in ("Extreme", "Severe"):
            response = requests.get(
                NOAA_ALERTS_URL,
                params={
                    "status": "actual",
                    "message_type": "alert",
                    "severity": severity,
                },
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            for feature in payload.get("features", []):
                properties = feature.get("properties") or {}
                title = (properties.get("headline") or properties.get("event") or "").strip()
                description = " ".join(
                    str(properties.get(key) or "").strip()
                    for key in ("description", "instruction")
                    if properties.get(key)
                )
                alert_id = properties.get("id") or feature.get("id") or ""
                alert_url = properties.get("web") or ""
                if not is_valid_url(alert_url):
                    alert_url = alert_id if is_valid_url(alert_id) else NOAA_ALERTS_URL
                if (
                    not title
                    or len(description) < 5
                    or alert_id in seen_alerts
                ):
                    continue
                seen_alerts.add(alert_id)
                records.append({
                    "title": title,
                    "content": description,
                    "category": source.get("category", "Weather Disruption"),
                    "location": properties.get("areaDesc") or "Unspecified",
                    "source_name": "NOAA National Weather Service",
                    "source_url": alert_url,
                    "published_date": properties.get("sent") or properties.get("effective"),
                    "is_demo": False,
                })
    except (requests.RequestException, ValueError) as exc:
        return [], f"NOAA active alert feed failed: {exc}"

    return records, None

def collect_from_single_source(source: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Scrapes a real public source or returns a configuration/request error.
    Returns (records_list, error_message).
    """
    url = source.get("url", "").strip()
    name = source.get("name", "Unknown Source")
    category = source.get("category", "Other")

    if not is_valid_url(url):
        return [], f"Invalid URL provided: {url}"

    if url.rstrip("/") == NOAA_ALERTS_URL:
        return _collect_noaa_alerts(source)

    # Check if Firecrawl API is configured
    if not settings.is_firecrawl_active:
        message = f"FIRECRAWL_API_KEY is not configured; live scraping skipped for {url}."
        logger.warning(message)
        return [], message

    # Real Firecrawl SDK integration
    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=settings.firecrawl_api_key)
        logger.info(f"Invoking Firecrawl scrape on: {url}")
        result = app.scrape_url(url, params={"formats": ["markdown"], "onlyMainContent": True})

        if not result:
            return [], f"Firecrawl returned empty response for {url}"

        # Handle SDK structure
        metadata = result.get("metadata", {}) or {}
        markdown_content = result.get("markdown") or result.get("data") or ""
        title = metadata.get("title") or metadata.get("og:title") or f"Update from {name}"
        published_date = metadata.get("publishedDate") or metadata.get("og:article:published_time")

        if not markdown_content:
            return [], f"No substantive content extracted from {url}"

        record = {
            "title": title,
            "content": markdown_content,
            "category": category,
            "source_name": name,
            "source_url": url,
            "published_date": published_date,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
        return [record], None

    except (ImportError, requests.RequestException, ValueError, RuntimeError) as e:
        error_msg = f"Firecrawl exception on {url}: {str(e)}"
        logger.error(error_msg)
        return [], error_msg

def collect_updates(sources: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Collect updates across multiple configured sources.
    Saves raw collected payloads to `data/raw/raw_disruptions_<timestamp>.json`.
    Returns (collected_records, errors_list).
    """
    all_records = []
    errors = []

    for src in sources:
        recs, err = collect_from_single_source(src)
        if err:
            errors.append({"url": src.get("url"), "error": err})
        if recs:
            all_records.extend(recs)

    # Persist raw payload to data/raw/
    if all_records:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        raw_file = RAW_DATA_DIR / f"raw_disruptions_{ts}.json"
        try:
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(all_records, f, indent=2)
            logger.info(f"Persisted {len(all_records)} raw records to {raw_file}")
        except Exception as e:
            logger.error(f"Failed to persist raw records: {e}")

    return all_records, errors
