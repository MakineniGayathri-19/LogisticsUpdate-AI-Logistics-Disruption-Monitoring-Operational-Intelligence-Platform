"""Collection Pipeline Orchestration Service.
Coordinates:
1. Querying active source targets from SQLite.
2. Web scraping via Firecrawl service (with rate-limit handling & raw logging).
3. Pandas-based text cleaning, deduplication, categorization, and rule-based severity.
4. Database persistence and Memento historical memory synchronization.
5. Audit logging in CollectionLog table.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone

from backend.services.firecrawl_service import collect_updates
from backend.services.data_processing import process_raw_records
from backend.services.memento_manager import store_event
from database import repositories
from utils.logger import logger

def run_collection() -> Dict[str, Any]:
    """Run an end-to-end data ingestion and processing cycle."""
    # 1. Fetch configured monitoring feeds
    sources = repositories.get_all_sources()
    if not sources:
        logger.warning("No monitoring feeds registered in database.")
        repositories.log_collection(
            source_url="ALL_SOURCES",
            status="skipped",
            records_count=0,
            error_message="No active monitoring sources configured."
        )
        return {
            "status": "warning",
            "message": "No monitoring sources configured. Please add feeds in Data Collection.",
            "fetched": 0,
            "processed": 0,
            "stored": 0
        }

    # 2. Scrape raw data via Firecrawl service
    raw_records, errors = collect_updates(sources)

    # Log errors per source if any
    for err_item in errors:
        repositories.log_collection(
            source_url=err_item.get("url", "unknown"),
            status="failed",
            records_count=0,
            error_message=err_item.get("error")
        )

    if not raw_records:
        repositories.log_collection(
            source_url="BATCH_CYCLE",
            status="failed",
            records_count=0,
            error_message="Firecrawl collection returned 0 raw records."
        )
        return {
            "status": "no_data",
            "message": "Firecrawl collection returned no records. Check feed URLs or API credentials.",
            "errors": errors,
            "fetched": 0,
            "processed": 0,
            "stored": 0
        }

    # 3. Clean and categorize using Pandas data processing engine
    cleaned_records = process_raw_records(raw_records)

    # 4. Store cleaned disruptions and sync to Memento
    stored_count = 0
    for rec in cleaned_records:
        try:
            persisted = repositories.create_disruption(rec)
            # Push to Memento memory
            store_event(persisted)
            stored_count += 1
        except Exception as e:
            logger.error(f"Error persisting disruption '{rec.get('title')}': {e}")

    # 5. Record successful collection audit log
    repositories.log_collection(
        source_url=f"BATCH ({len(sources)} sources)",
        status="success",
        records_count=stored_count,
        error_message=None if not errors else f"{len(errors)} sources encountered scrape errors"
    )

    return {
        "status": "success",
        "sources_scraped": len(sources),
        "fetched": len(raw_records),
        "processed": len(cleaned_records),
        "stored": stored_count,
        "errors_count": len(errors)
    }
