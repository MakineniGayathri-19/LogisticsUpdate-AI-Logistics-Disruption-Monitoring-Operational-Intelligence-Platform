"""Data collection module using Firecrawl.
It iterates over the URLs defined in config.SOURCES, fetches the page content,
and stores the raw HTML/text under data/raw/ with a timestamped filename.
"""
import os
import time
from pathlib import Path

from firecrawl import FirecrawlApp
from .config import FIRECRAWL_API_KEY, RAW_DATA_DIR, SOURCES


def init_app():
    if not FIRECRAWL_API_KEY:
        raise ValueError("FIRECRAWL_API_KEY not set in environment")
    return FirecrawlApp(api_key=FIRECRAWL_API_KEY)


def fetch_and_store(app: "FirecrawlApp", url: str) -> Path:
    """Fetch a URL and store the raw HTML.
    Returns the path to the saved file.
    """
    # Scrape markdown for a stable, text-focused raw payload.
    result = app.scrape_url(
        url,
        params={"formats": ["markdown"], "onlyMainContent": True},
    )
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    if isinstance(result, dict):
        html = result.get("markdown") or (result.get("data") or {}).get("markdown") or ""
    else:
        html = str(result or "")
    if not html:
        raise ValueError(f"Firecrawl returned no content for {url}")
    timestamp = int(time.time())
    safe_name = url.replace("https://", "").replace("http://", "").replace("/", "_")
    filename = f"{safe_name}_{timestamp}.html"
    out_path = RAW_DATA_DIR / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path


def run():
    """Run the collection pipeline for all sources."""
    app = init_app()
    for url in SOURCES:
        try:
            path = fetch_and_store(app, url)
            print(f"Fetched {url} → {path}")
        except Exception as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")

if __name__ == "__main__":
    run()
