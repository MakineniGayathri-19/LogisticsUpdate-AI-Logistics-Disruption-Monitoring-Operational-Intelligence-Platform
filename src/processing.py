"""Processing module – clean and structure raw HTML data.
Uses BeautifulSoup to extract relevant fields and pandas to build a clean DataFrame.
"""
import re
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

from .config import RAW_DATA_DIR, PROCESSED_DATA_DIR


def extract_fields(html: str, source_url: str) -> dict:
    """Very simple heuristic extraction – customize per source.
    Returns a dict with keys: date, location, type, description, source.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    # Basic pattern matching – placeholder implementation
    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    date = date_match.group(1) if date_match else ""
    # Assume first sentence as description
    description = text.split(".")[0] if text else ""
    return {
        "date": date,
        "location": "",  # could be parsed with NLP later
        "type": "",      # e.g., "weather", "port", "carrier"
        "description": description,
        "source": source_url,
    }


def clean() -> Path:
    """Read all raw HTML files, extract fields, and write a CSV.
    Returns path to the processed CSV.
    """
    records = []
    for file_path in RAW_DATA_DIR.glob("*.html"):
        html = file_path.read_text(encoding="utf-8")
        record = extract_fields(html, source_url=file_path.stem)
        records.append(record)
    df = pd.DataFrame(records)
    # Basic deduplication / cleaning
    df.drop_duplicates(subset=["date", "description"], inplace=True)
    out_path = PROCESSED_DATA_DIR / "disruptions.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Processed {len(records)} records → {out_path}")
    return out_path

if __name__ == "__main__":
    clean()
