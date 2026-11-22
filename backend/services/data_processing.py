"""Data Processing & Validation Service (Member 2).
Uses Python and Pandas to clean, deduplicate, categorize, and extract attributes.
Persists processed datasets to `data/processed/` and adheres strictly to
transparent rule-based severity assignment without LLM hallucinations.
"""
import os
import re
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd

from utils.logger import logger
from utils.validators import (
    clean_text,
    is_valid_url,
    normalize_category,
    normalize_severity,
    VALID_CATEGORIES,
    VALID_SEVERITIES
)

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Curated lookup dictionary for common global ports, hubs, and regions
KNOWN_LOGISTICS_HUBS = [
    "Rotterdam", "Los Angeles", "Long Beach", "Singapore", "Shanghai", "Ningbo",
    "Shenzhen", "Busan", "Hamburg", "Antwerp", "Felixstowe", "Bremen",
    "Panama Canal", "Suez Canal", "Chicago", "Houston", "New York", "New Jersey",
    "Savannah", "Brenner Pass", "Red Sea", "Kaub", "Rhine River", "Baltimore"
]

# Transparent rule-based keyword mapping for Severity Assignment
# Critical: Complete stoppage, safety danger, extreme natural catastrophe, war/blockade
CRITICAL_KEYWORDS = [
    "closure", "closed", "halt", "halted", "suspended", "typhoon", "hurricane",
    "blizzard", "emergency", "force majeure", "strike", "blockade", "landslide",
    "collision", "ransomware", "cyberattack", "impassable"
]

# High: Severe delays (5+ days), major congestion, significant draft reduction
HIGH_KEYWORDS = [
    "severe", "congestion", "dwell", "rerout", "bottleneck", "backlog",
    "capacity reduction", "shortage", "surge", "restricted", "embargo", "gale"
]

# Medium: Moderate delays (1-3 days), maintenance, advisory, weather watch
MEDIUM_KEYWORDS = [
    "delay", "slowdown", "draft restriction", "maintenance", "fog",
    "surcharge", "interchange", "inspection", "conservation", "seasonal"
]

# Low: Informational notices, slight schedule updates, routine advisories
LOW_KEYWORDS = [
    "advisory", "notice", "schedule", "routine", "minor", "update", "tariff"
]

def extract_location(text: str) -> str:
    """Extract geographical location or port name using entity lookup and regex patterns."""
    if not text:
        return "Global / Unspecified"
    for hub in KNOWN_LOGISTICS_HUBS:
        if re.search(r"\b" + re.escape(hub) + r"\b", text, re.IGNORECASE):
            return hub
    # Secondary regex check for common patterns like 'Port of X'
    match = re.search(r"\bPort of ([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b", text)
    if match:
        return f"Port of {match.group(1)}"
    return "Global / Unspecified"

def assign_rule_based_severity(title: str, description: str) -> Tuple[str, str]:
    """Transparently assigns disruption severity using deterministic keyword evidence.
    Returns (severity_level, justification).
    """
    combined = f"{title} {description}".lower()

    for kw in CRITICAL_KEYWORDS:
        if kw in combined:
            return "Critical", f"Triggered by high-impact operational indicator: '{kw}'"

    for kw in HIGH_KEYWORDS:
        if kw in combined:
            return "High", f"Triggered by substantial operational disruption indicator: '{kw}'"

    for kw in MEDIUM_KEYWORDS:
        if kw in combined:
            return "Medium", f"Triggered by moderate operational delay indicator: '{kw}'"

    for kw in LOW_KEYWORDS:
        if kw in combined:
            return "Low", f"Identified as routine operational or scheduling update: '{kw}'"

    return "Unknown", "No specific severity keyword indicators matched; classified as Unknown."

def clean_and_normalize_date(date_val: Any) -> str:
    """Normalize various date formats into standard ISO 8601 UTC timestamp."""
    if not date_val:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(date_val, datetime):
        if date_val.tzinfo is None:
            return date_val.replace(tzinfo=timezone.utc).isoformat()
        return date_val.isoformat()
    if isinstance(date_val, str):
        val = date_val.strip()
        try:
            val_clean = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(val_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    dt = datetime.strptime(val, fmt).replace(tzinfo=timezone.utc)
                    return dt.isoformat()
                except Exception:
                    continue
    return datetime.now(timezone.utc).isoformat()

def process_raw_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean, filter, deduplicate, and validate raw scraped records using Pandas.
    Produces structured records conforming to the unified disruption schema:
    {
        "event_id": str,
        "title": str,
        "description": str,
        "category": str,
        "location": str,
        "severity": str,
        "status": str,
        "source_name": str,
        "source_url": str,
        "published_date": str,
        "collected_at": str
    }
    """
    if not records:
        return []

    # Load into Pandas DataFrame for tabular data processing
    df = pd.DataFrame(records)

    # 1. Remove empty or corrupt records
    if "title" not in df.columns:
        df["title"] = ""
    if "content" not in df.columns:
        df["content"] = ""

    df["title"] = df["title"].fillna("").astype(str).apply(clean_text)
    df["content"] = df["content"].fillna("").astype(str).apply(clean_text)
    df = df[(df["title"].str.len() >= 3) & (df["content"].str.len() >= 5)]

    if df.empty:
        logger.warning("All records dropped after empty check.")
        return []

    # 2. Duplicate Detection (by source_url and normalized title)
    df["source_url"] = df["source_url"].fillna("").astype(str).str.strip()
    df["title_clean_lower"] = df["title"].str.lower()
    df = df.drop_duplicates(subset=["source_url", "title_clean_lower"])

    # 3. Clean Text, Validate URLs
    valid_mask = df["source_url"].apply(is_valid_url)
    df = df[valid_mask]
    if df.empty:
        return []

    # 4. Normalize categories and severities
    if "category" not in df.columns:
        df["category"] = "Other"
    df["category"] = df["category"].fillna("Other").astype(str).apply(normalize_category)

    # 5. Extract Location
    if "location" not in df.columns or df["location"].isnull().all():
        df["location"] = (df["title"] + " " + df["content"]).apply(extract_location)
    else:
        df["location"] = df["location"].fillna("").astype(str).apply(clean_text)
        df["location"] = df.apply(
            lambda r: r["location"] if r["location"] and r["location"] != "Unspecified"
            else extract_location(f"{r['title']} {r['content']}"),
            axis=1
        )

    # 6. Transparent Rule-Based Severity
    severity_results = df.apply(lambda r: assign_rule_based_severity(r["title"], r["content"]), axis=1)
    df["severity"] = [s[0] for s in severity_results]
    df["severity_justification"] = [s[1] for s in severity_results]

    # 7. Normalize Dates, IDs & Sources
    if "source_name" not in df.columns:
        df["source_name"] = "Logistics Feed"
    else:
        df["source_name"] = df["source_name"].fillna("Logistics Feed").astype(str).str.strip()
        df["source_name"] = df["source_name"].replace("", "Logistics Feed")

    if "published_date" not in df.columns:
        df["published_date"] = None

    df["published_date"] = df["published_date"].apply(clean_and_normalize_date)
    if "is_demo" not in df.columns:
        df["is_demo"] = False
    else:
        df["is_demo"] = df["is_demo"].fillna(False).astype(bool)
    df["collected_at"] = datetime.now(timezone.utc).isoformat()
    df["status"] = "Active"
    df["event_id"] = [uuid.uuid4().hex[:12] for _ in range(len(df))]
    df["description"] = df["content"]

    # Select standard output columns
    output_cols = [
        "event_id", "title", "description", "category", "location",
        "severity", "status", "source_name", "source_url", "published_date", "collected_at", "is_demo"
    ]
    cleaned_df = df[output_cols]

    # 8. Export to data/processed/ for auditability
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    processed_json = PROCESSED_DATA_DIR / f"disruptions_{ts}.json"
    processed_csv = PROCESSED_DATA_DIR / f"disruptions_{ts}.csv"
    try:
        cleaned_df.to_json(processed_json, orient="records", indent=2)
        cleaned_df.to_csv(processed_csv, index=False)
        logger.info(f"Processed dataset saved to {processed_json} and {processed_csv}")
    except Exception as e:
        logger.error(f"Failed to export processed files: {e}")

    return cleaned_df.to_dict(orient="records")
