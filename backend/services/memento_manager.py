"""Historical incident and operational-response memory."""

import json
from typing import Any, Dict, List, Optional

import requests

from utils.config import settings
from utils.logger import logger
from utils.validators import clean_text, normalize_category


def get_memento_status() -> Dict[str, Any]:
    """Report where historical events are stored without claiming a live connection."""
    if settings.is_memento_active:
        return {
            "status": "configured",
            "adapter": "Memento Cloud API (configured; not health-checked)",
            "endpoint": settings.memento_api_url,
            "is_live": False,
            "message": "Cloud sync is configured; the local database remains authoritative.",
        }
    return {
        "status": "local_database",
        "adapter": "SQLite Historical Event Store",
        "endpoint": "database/app.db",
        "is_live": False,
        "message": "Historical events and documented responses are stored in the application database.",
    }


def store_event(event: Dict[str, Any]) -> bool:
    """Persist a verified historical event and optionally sync it to Memento."""
    from database import repositories

    repositories.add_historical_event(event)
    if not settings.is_memento_active:
        return True

    try:
        response = requests.post(
            f"{settings.memento_api_url}/memories",
            headers={
                "Authorization": f"Bearer {settings.memento_api_key}",
                "Content-Type": "application/json",
            },
            json={"content": json.dumps(event), "category": "logistics_disruption"},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error(f"Memento Cloud API sync failed: {exc}")
        return False
    return True


def get_all_stored_events() -> List[Dict[str, Any]]:
    """Return non-demo historical events persisted in the application database."""
    from database import repositories

    return repositories.get_all_historical_events()


def retrieve_similar_events(event: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
    """Retrieve historical matches using the event comparison service."""
    from backend.services.event_comparison import compare_disruption_with_history

    comparison = compare_disruption_with_history(event, top_n=top_n)
    return comparison.get("similar_events", [])


def retrieve_previous_responses(
    category: Optional[str] = None,
    location: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve only operational responses and outcomes actually recorded."""
    results = []
    for event in get_all_stored_events():
        if category and normalize_category(category) != normalize_category(event.get("category")):
            continue
        if location and location.lower() not in str(event.get("location", "")).lower():
            continue
        if event.get("response") or event.get("outcome"):
            results.append({
                "title": event.get("title"),
                "category": event.get("category"),
                "location": event.get("location"),
                "response": event.get("response", ""),
                "outcome": event.get("outcome", ""),
                "is_demo": False,
            })
    return results


def store_operational_response(event_id: str, response: str, outcome: str) -> Dict[str, Any]:
    """Store an operational mitigation and its observed outcome for an event."""
    from database import repositories

    historical_event = repositories.get_historical_event_by_id(event_id)
    historical_event_id = historical_event.get("id") if historical_event else None
    disruption = repositories.get_disruption_by_id(event_id)
    disruption_id = disruption.get("id") if disruption else None
    if not historical_event_id and not disruption_id:
        raise ValueError(f"No historical event or disruption found for id '{event_id}'")
    return repositories.add_operational_response(
        historical_event_id=historical_event_id,
        disruption_id=disruption_id,
        response=clean_text(response),
        outcome=clean_text(outcome),
    )
