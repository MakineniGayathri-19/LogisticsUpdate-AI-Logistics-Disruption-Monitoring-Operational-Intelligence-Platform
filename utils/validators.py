"""Data validation utilities for LogisticsUpdate AI.
Provides rigorous URL validation, text hygiene, and schema validation.
"""
import re
from urllib.parse import urlparse
from typing import Dict, Any, Tuple, Optional

# Valid standard disruption categories
VALID_CATEGORIES = [
    "Port Disruption",
    "Weather Disruption",
    "Shipping Delay",
    "Road Transportation Disruption",
    "Railway Disruption",
    "Carrier Announcement",
    "Supply Chain Disruption",
    "Other"
]

# Valid standard severities
VALID_SEVERITIES = [
    "Critical",
    "High",
    "Medium",
    "Low",
    "Unknown"
]

def is_valid_url(url: str) -> bool:
    """Validate if string is a valid HTTP/HTTPS URL."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

def clean_text(text: Optional[str]) -> str:
    """Sanitize and clean raw text, removing excessive whitespace and html residues."""
    if not text:
        return ""
    # Strip basic html tags
    cleaned = re.sub(r"<[^>]+>", " ", str(text))
    # Replace multiple whitespaces/newlines with single space
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def validate_disruption_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a disruption record payload against standard schema."""
    if not isinstance(data, dict):
        return False, "Payload must be a dictionary"

    title = clean_text(data.get("title"))
    if not title or len(title) < 3:
        return False, "Title is required and must be at least 3 characters"

    description = clean_text(data.get("description"))
    if not description or len(description) < 5:
        return False, "Description is required and must be at least 5 characters"

    source_name = clean_text(data.get("source_name"))
    if not source_name:
        return False, "source_name is required"

    source_url = str(data.get("source_url", "")).strip()
    if not is_valid_url(source_url):
        return False, f"source_url is invalid or missing: '{source_url}'"

    return True, None

def normalize_category(cat: Optional[str]) -> str:
    """Map arbitrary category strings to canonical categories."""
    if not cat:
        return "Other"
    c = cat.strip().lower()
    if "port" in c or "harbor" in c or "terminal" in c or "berth" in c:
        return "Port Disruption"
    elif "weather" in c or "storm" in c or "hurricane" in c or "typhoon" in c or "flood" in c or "snow" in c or "freeze" in c:
        return "Weather Disruption"
    elif "ship" in c or "vessel" in c or "maritime" in c or "canal" in c:
        return "Shipping Delay"
    elif "road" in c or "highway" in c or "truck" in c:
        return "Road Transportation Disruption"
    elif "rail" in c or "train" in c or "freight rail" in c:
        return "Railway Disruption"
    elif "carrier" in c or "notice" in c or "announcement" in c or "advisory" in c:
        return "Carrier Announcement"
    elif "supply" in c or "inventory" in c or "warehouse" in c:
        return "Supply Chain Disruption"
    return "Other"

def normalize_severity(sev: Optional[str]) -> str:
    """Normalize severity level to canonical set."""
    if not sev:
        return "Unknown"
    s = sev.strip().capitalize()
    if s in VALID_SEVERITIES:
        return s
    return "Unknown"
