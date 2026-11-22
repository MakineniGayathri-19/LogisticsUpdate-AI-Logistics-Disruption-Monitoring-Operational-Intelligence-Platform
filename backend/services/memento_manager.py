"""Memento Historical Context Manager (Member 3).
Dedicated adapter for Memento memory service.
Supports real Memento API interactions when `MEMENTO_API_KEY` is provided,
and seamlessly switches to a clearly labeled Local Development Adapter
utilizing `data/sample/memento_fallback.json` and the SQLite database when credentials are unset.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from utils.config import settings
from utils.logger import logger
from utils.validators import clean_text, normalize_category

BASE_DIR = Path(__file__).resolve().parents[2]
SAMPLE_DIR = BASE_DIR / "data" / "sample"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
FALLBACK_FILE = SAMPLE_DIR / "memento_fallback.json"

DEFAULT_HISTORICAL_PRECEDENTS = [
    {
        "event_id": "hist-001",
        "title": "Port of Los Angeles Container Congestion",
        "description": "Severe container backlog and dwell time at Port of Los Angeles due to rail carrier labor shortages and peak season volume.",
        "category": "Port Disruption",
        "location": "Los Angeles, CA, USA",
        "severity": "High",
        "status": "Resolved",
        "source_name": "Maritime Executive",
        "source_url": "https://maritime-executive.com/article/la-congestion",
        "published_date": "2024-03-15T08:00:00Z",
        "response": "Rerouted priority cargo via Oakland and Pacific Northwest ports; extended gate appointment hours to 24/7.",
        "outcome": "Terminal dwell time reduced by 35% within 10 days; average delay mitigated from 7 days to 2 days.",
        "is_demo": True
    },
    {
        "event_id": "hist-002",
        "title": "Winter Storm Elliott Class 1 Rail Freeze",
        "description": "Sub-zero temperatures and blizzard conditions halt Class 1 rail operations across Midwest and Northeast corridors.",
        "category": "Weather Disruption",
        "location": "Chicago, IL, USA",
        "severity": "Critical",
        "status": "Resolved",
        "source_name": "FreightWaves",
        "source_url": "https://freightwaves.com/news/winter-storm-rail-delays",
        "published_date": "2023-12-22T14:30:00Z",
        "response": "Shifted time-sensitive freight to team long-haul truck drivers; staged heated warehouse storage for temperature-controlled cargo.",
        "outcome": "Critical cold-chain goods preserved without spoilage; freight delivery delayed by 48 hours rather than 6 days.",
        "is_demo": True
    },
    {
        "event_id": "hist-003",
        "title": "Panama Canal Drought Draft Restrictions",
        "description": "Historic low water levels at Gatun Lake force Panama Canal Authority to reduce daily vessel transit slots and maximum draft.",
        "category": "Shipping Delay",
        "location": "Panama Canal",
        "severity": "High",
        "status": "Resolved",
        "source_name": "Journal of Commerce",
        "source_url": "https://joc.com/article/panama-canal-drought-restrictions",
        "published_date": "2024-01-10T11:00:00Z",
        "response": "Booked neo-Panamax transits 30 days in advance and shifted non-urgent container cargo to Cape of Good Hope routes.",
        "outcome": "Increased transit time by 10-14 days but avoided unpredictable anchorage waiting times exceeding 21 days.",
        "is_demo": True
    },
    {
        "event_id": "hist-004",
        "title": "Rotterdam Port Cyberattack on Terminal Operating System",
        "description": "Ransomware outage disabled automated crane dispatch and gate appointment system at major container terminal.",
        "category": "Port Disruption",
        "location": "Rotterdam, Netherlands",
        "severity": "Critical",
        "status": "Resolved",
        "source_name": "Lloyds List",
        "source_url": "https://lloydslist.maritimeintelligence.informa.com/rotterdam-incident",
        "published_date": "2023-09-05T09:15:00Z",
        "response": "Activated manual paper gate checks and diverted incoming feeder vessels to Port of Antwerp.",
        "outcome": "Terminal operating system restored within 72 hours; clearance backlogs eliminated within 5 business days.",
        "is_demo": True
    },
    {
        "event_id": "hist-005",
        "title": "Brenner Pass Rail Freight Rockfall Closure",
        "description": "Severe Alpine landslides shut down trans-European rail freight corridor between Innsbruck and Verona.",
        "category": "Railway Disruption",
        "location": "Brenner Pass, Austria / Italy",
        "severity": "High",
        "status": "Resolved",
        "source_name": "RailFreight Bulletin",
        "source_url": "https://railfreight.com/rail-rockfall-brenner",
        "published_date": "2023-08-14T10:00:00Z",
        "response": "Enacted intermodal freight trucking transfer via Tarvisio and Tauern alternative routes.",
        "outcome": "Maintained 70% freight volume continuity with an average transit premium of 18%.",
        "is_demo": True
    }
]

def _load_fallback_store() -> List[Dict[str, Any]]:
    """Loads historical precedents from local fallback file."""
    if not FALLBACK_FILE.exists():
        try:
            with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_HISTORICAL_PRECEDENTS, f, indent=2)
            return list(DEFAULT_HISTORICAL_PRECEDENTS)
        except Exception as e:
            logger.error(f"Error initializing Memento fallback file: {e}")
            return list(DEFAULT_HISTORICAL_PRECEDENTS)
    try:
        with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading Memento fallback file: {e}")
        return list(DEFAULT_HISTORICAL_PRECEDENTS)

def _save_fallback_store(events: List[Dict[str, Any]]) -> bool:
    try:
        with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving to Memento fallback store: {e}")
        return False

# ---------------------------------------------------------------------------
# Memento Adapter Status
# ---------------------------------------------------------------------------

def get_memento_status() -> Dict[str, Any]:
    """Returns the live connection status of Memento."""
    if settings.is_memento_active:
        return {
            "status": "connected",
            "adapter": "Memento Cloud API",
            "endpoint": settings.memento_api_url,
            "is_live": True,
            "message": "Connected to Memento Cloud Memory Service"
        }
    return {
        "status": "local_fallback",
        "adapter": "Local Memento Adapter [Demo/Dev Mode]",
        "endpoint": str(FALLBACK_FILE),
        "is_live": False,
        "message": "Running on Local Precedent Repository (No Memento API key configured)"
    }

# ---------------------------------------------------------------------------
# Application-level Memento Functions
# ---------------------------------------------------------------------------

def store_event(event: Dict[str, Any]) -> bool:
    """Stores an event into historical memory via Memento API or Local Adapter."""
    from database import repositories

    # Always persist into DB historical tables
    try:
        repositories.add_historical_event(event)
    except Exception as e:
        logger.warning(f"Could not persist to DB historical_events: {e}")

    # If real Memento credentials configured, send HTTP request
    if settings.is_memento_active:
        try:
            headers = {
                "Authorization": f"Bearer {settings.memento_api_key}",
                "Content-Type": "application/json"
            }
            res = requests.post(
                f"{settings.memento_api_url}/memories",
                headers=headers,
                json={"content": json.dumps(event), "category": "logistics_disruption"},
                timeout=5
            )
            if res.status_code in (200, 201):
                logger.info(f"Stored event {event.get('title')} to Memento Cloud API.")
                return True
        except Exception as e:
            logger.error(f"Memento Cloud API call failed: {e}. Falling back to local store.")

    # Local Adapter storage
    events = _load_fallback_store()
    ev_id = event.get("event_id") or event.get("id")
    for ex in events:
        if (ev_id and ex.get("event_id") == ev_id) or (ex.get("title") == event.get("title")):
            return True
    events.append(event)
    return _save_fallback_store(events)

def get_all_stored_events() -> List[Dict[str, Any]]:
    """Retrieve all historical events stored in the memory repository."""
    from database import repositories
    db_events = repositories.get_all_historical_events()
    fallback_events = _load_fallback_store()

    # Combine ensuring no duplicates
    combined = list(fallback_events)
    existing_ids = {e.get("event_id") or e.get("id") for e in combined}
    for dbe in db_events:
        dbe_id = dbe.get("event_id") or dbe.get("id")
        if dbe_id not in existing_ids:
            combined.append(dbe)
            existing_ids.add(dbe_id)
    return combined

def retrieve_similar_events(event: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
    """Retrieves top N similar historical events using the Event Comparison Service."""
    from backend.services.event_comparison import compare_disruption_with_history
    comparison = compare_disruption_with_history(event, top_n=top_n)
    return comparison.get("similar_events", [])

def retrieve_previous_responses(category: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve documented historical responses and outcomes filtered by category or location."""
    events = get_all_stored_events()
    results = []
    for ev in events:
        if category and normalize_category(category) != normalize_category(ev.get("category")):
            continue
        if location and location.lower() not in str(ev.get("location", "")).lower():
            continue
        if ev.get("response") or ev.get("outcome"):
            results.append({
                "title": ev.get("title"),
                "category": ev.get("category"),
                "location": ev.get("location"),
                "response": ev.get("response", "Standard rerouting protocol."),
                "outcome": ev.get("outcome", "Delay mitigated within 48-72 hours."),
                "is_demo": ev.get("is_demo", True)
            })
    return results

def store_operational_response(event_id: str, response: str, outcome: str) -> Dict[str, Any]:
    """Store an operational mitigation response and observed outcome for an event."""
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
        outcome=clean_text(outcome)
    )
