"""Database repository functions for LogisticsUpdate AI.
Provides typed access to SQLite storage, duplicate prevention, and operational logs.
"""
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from .db import SessionLocal
from . import models
from utils.validators import normalize_category, normalize_severity, clean_text

def _gen_id() -> str:
    return uuid.uuid4().hex[:12]

def _model_to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    res = {}
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        res[column.name] = val
    return res

# ---------------------------------------------------------------------------
# Disruptions CRUD
# ---------------------------------------------------------------------------

def get_all_disruptions() -> List[Dict]:
    with SessionLocal() as db:
        stmt = select(models.Disruption).order_by(desc(models.Disruption.collected_at))
        results = db.execute(stmt).scalars().all()
        return [_model_to_dict(r) for r in results]

def get_disruption_by_id(event_id: str) -> Optional[Dict]:
    with SessionLocal() as db:
        obj = db.get(models.Disruption, event_id)
        return _model_to_dict(obj) if obj else None

def create_disruption(data: Dict) -> Dict:
    with SessionLocal() as db:
        # Check duplicate by URL + Title
        title = clean_text(data.get("title"))
        source_url = str(data.get("source_url", "")).strip()

        existing = db.execute(
            select(models.Disruption).where(
                models.Disruption.source_url == source_url,
                models.Disruption.title == title
            )
        ).scalar_one_or_none()
        if existing:
            if data.get("is_demo") and not existing.is_demo:
                existing.is_demo = True
                db.commit()
                db.refresh(existing)
            return _model_to_dict(existing)

        pub_date = data.get("published_date")
        if isinstance(pub_date, str):
            try:
                pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except Exception:
                pub_date = datetime.now(timezone.utc)
        elif not isinstance(pub_date, datetime):
            pub_date = datetime.now(timezone.utc)

        disruption = models.Disruption(
            id=data.get("event_id") or data.get("id") or _gen_id(),
            title=title,
            description=clean_text(data.get("description")),
            category=normalize_category(data.get("category")),
            location=clean_text(data.get("location")) or "Unspecified Location",
            severity=normalize_severity(data.get("severity")),
            status=data.get("status", "Active"),
            source_name=clean_text(data.get("source_name")) or "Logistics Feed",
            source_url=source_url,
            published_date=pub_date,
            collected_at=datetime.now(timezone.utc),
            is_demo=bool(data.get("is_demo", False)),
        )
        db.add(disruption)
        db.commit()
        db.refresh(disruption)
        return _model_to_dict(disruption)

# ---------------------------------------------------------------------------
# Historical Events & Operational Responses
# ---------------------------------------------------------------------------

def get_all_historical_events() -> List[Dict]:
    with SessionLocal() as db:
        stmt = select(models.HistoricalEvent).order_by(desc(models.HistoricalEvent.created_at))
        events = db.execute(stmt).scalars().all()
        result = []
        for ev in events:
            d = _model_to_dict(ev)
            # Fetch attached response if any
            resp_obj = db.execute(
                select(models.OperationalResponse).where(models.OperationalResponse.historical_event_id == ev.id)
            ).scalar_one_or_none()
            if resp_obj:
                d["response"] = resp_obj.response
                d["outcome"] = resp_obj.outcome
            else:
                d["response"] = "Standard rerouting protocols deployed."
                d["outcome"] = "Delays contained within 48-72 hours."
            result.append(d)
        return result

def get_historical_event_by_id(event_id: str) -> Optional[Dict]:
    with SessionLocal() as db:
        ev = db.get(models.HistoricalEvent, event_id)
        if not ev:
            # check by event_id string
            ev = db.execute(
                select(models.HistoricalEvent).where(models.HistoricalEvent.event_id == event_id)
            ).scalar_one_or_none()
        if not ev:
            return None
        d = _model_to_dict(ev)
        resp_obj = db.execute(
            select(models.OperationalResponse).where(models.OperationalResponse.historical_event_id == ev.id)
        ).scalar_one_or_none()
        if resp_obj:
            d["response"] = resp_obj.response
            d["outcome"] = resp_obj.outcome
        return d

def add_historical_event(data: Dict) -> Dict:
    with SessionLocal() as db:
        he_id = data.get("id") or _gen_id()
        ev_id = data.get("event_id") or he_id

        # Check existing
        existing = db.execute(
            select(models.HistoricalEvent).where(
                (models.HistoricalEvent.id == he_id) | (models.HistoricalEvent.event_id == ev_id)
            )
        ).scalar_one_or_none()
        if existing:
            return _model_to_dict(existing)

        he = models.HistoricalEvent(
            id=he_id,
            event_id=ev_id,
            title=clean_text(data.get("title")),
            description=clean_text(data.get("description")),
            category=normalize_category(data.get("category")),
            location=clean_text(data.get("location")) or "Unspecified",
            severity=normalize_severity(data.get("severity")),
            status=data.get("status", "Resolved"),
            source_name=clean_text(data.get("source_name")) or "Historical Archive",
            source_url=str(data.get("source_url", "")),
            is_demo=bool(data.get("is_demo", True)),
            created_at=datetime.now(timezone.utc),
        )
        db.add(he)
        db.commit()

        # If operational response and outcome provided, attach them
        if data.get("response") or data.get("outcome"):
            op_resp = models.OperationalResponse(
                id=_gen_id(),
                historical_event_id=he.id,
                response=clean_text(data.get("response") or "Coordinated contingency rerouting."),
                outcome=clean_text(data.get("outcome") or "Resolved with mitigated dwell time."),
                created_at=datetime.now(timezone.utc),
            )
            db.add(op_resp)
            db.commit()

        db.refresh(he)
        res = _model_to_dict(he)
        res["response"] = data.get("response", "")
        res["outcome"] = data.get("outcome", "")
        return res

def add_operational_response(historical_event_id: Optional[str], disruption_id: Optional[str], response: str, outcome: str) -> Dict:
    with SessionLocal() as db:
        op = models.OperationalResponse(
            id=_gen_id(),
            historical_event_id=historical_event_id,
            disruption_id=disruption_id,
            response=clean_text(response),
            outcome=clean_text(outcome),
            created_at=datetime.now(timezone.utc)
        )
        db.add(op)
        db.commit()
        db.refresh(op)
        return _model_to_dict(op)

# ---------------------------------------------------------------------------
# Sources CRUD
# ---------------------------------------------------------------------------

def get_all_sources() -> List[Dict]:
    with SessionLocal() as db:
        stmt = select(models.Source).order_by(models.Source.name)
        results = db.execute(stmt).scalars().all()
        return [_model_to_dict(r) for r in results]

def add_source(data: Dict) -> Dict:
    with SessionLocal() as db:
        url = str(data.get("url", "")).strip()
        existing = db.execute(select(models.Source).where(models.Source.url == url)).scalar_one_or_none()
        if existing:
            return _model_to_dict(existing)

        source = models.Source(
            id=data.get("id") or _gen_id(),
            name=clean_text(data.get("name")),
            url=url,
            category=normalize_category(data.get("category")),
            active=bool(data.get("active", True)),
            created_at=datetime.now(timezone.utc)
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return _model_to_dict(source)

def delete_source(source_id: str) -> bool:
    with SessionLocal() as db:
        obj = db.get(models.Source, source_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

# ---------------------------------------------------------------------------
# Reports CRUD
# ---------------------------------------------------------------------------

def create_report(disruption_id: str, content: str, provider: str = "Deterministic Fallback") -> Dict:
    with SessionLocal() as db:
        rep = models.Report(
            id=_gen_id(),
            disruption_id=disruption_id,
            content=content,
            llm_provider=provider,
            generated_at=datetime.now(timezone.utc)
        )
        db.add(rep)
        db.commit()
        db.refresh(rep)
        return _model_to_dict(rep)

def get_all_reports() -> List[Dict]:
    with SessionLocal() as db:
        stmt = select(models.Report).order_by(desc(models.Report.generated_at))
        results = db.execute(stmt).scalars().all()
        return [_model_to_dict(r) for r in results]

def get_report_by_id(report_id: str) -> Optional[Dict]:
    with SessionLocal() as db:
        obj = db.get(models.Report, report_id)
        return _model_to_dict(obj) if obj else None

# ---------------------------------------------------------------------------
# Collection Logs
# ---------------------------------------------------------------------------

def log_collection(source_url: str, status: str, records_count: int = 0, error_message: Optional[str] = None) -> Dict:
    with SessionLocal() as db:
        cl = models.CollectionLog(
            id=_gen_id(),
            source_url=source_url,
            status=status,
            records_count=records_count,
            error_message=error_message,
            created_at=datetime.now(timezone.utc)
        )
        db.add(cl)
        db.commit()
        db.refresh(cl)
        return _model_to_dict(cl)

def get_collection_logs(limit: int = 20) -> List[Dict]:
    with SessionLocal() as db:
        stmt = select(models.CollectionLog).order_by(desc(models.CollectionLog.created_at)).limit(limit)
        results = db.execute(stmt).scalars().all()
        return [_model_to_dict(r) for r in results]

# ---------------------------------------------------------------------------
# Overview KPI & Stats
# ---------------------------------------------------------------------------

def get_overview_stats() -> Dict[str, Any]:
    with SessionLocal() as db:
        total_disruptions = db.query(models.Disruption).count()
        active_disruptions = db.query(models.Disruption).filter(models.Disruption.status == "Active").count()
        critical_disruptions = db.query(models.Disruption).filter(models.Disruption.severity == "Critical").count()
        high_disruptions = db.query(models.Disruption).filter(models.Disruption.severity == "High").count()
        historical_stored = db.query(models.HistoricalEvent).count()
        ai_reports_generated = db.query(models.Report).count()
        sources_count = db.query(models.Source).count()

        # Last successful collection
        last_log = db.execute(
            select(models.CollectionLog)
            .where(models.CollectionLog.status == "success")
            .order_by(desc(models.CollectionLog.created_at))
        ).scalars().first()

        last_collection_time = last_log.created_at.isoformat() if last_log else "Not recorded yet"

        return {
            "total_disruptions": total_disruptions,
            "active_disruptions": active_disruptions,
            "critical_disruptions": critical_disruptions,
            "high_disruptions": high_disruptions,
            "historical_stored": historical_stored,
            "ai_reports_generated": ai_reports_generated,
            "sources_count": sources_count,
            "last_collection_time": last_collection_time
        }

# ---------------------------------------------------------------------------
# Default Seeding for Clean Demo / Initial Start
# ---------------------------------------------------------------------------

DEFAULT_SOURCES = [
    {
        "name": "Maritime Executive Live Wire",
        "url": "https://maritime-executive.com/news",
        "category": "Port Disruption"
    },
    {
        "name": "FreightWaves Supply Chain Alerts",
        "url": "https://www.freightwaves.com/news/category/supply-chain",
        "category": "Supply Chain Disruption"
    },
    {
        "name": "Panama Canal Authority Notices",
        "url": "https://pancanal.com/en/notices-to-shipping/",
        "category": "Shipping Delay"
    },
    {
        "name": "NOAA National Marine Weather Center",
        "url": "https://www.weather.gov/marine/",
        "category": "Weather Disruption"
    },
    {
        "name": "Federal Railroad Administration Bulletins",
        "url": "https://railroads.dot.gov/newsroom",
        "category": "Railway Disruption"
    }
]

DEFAULT_DISRUPTIONS = [
    {
        "event_id": "demo-dis-001",
        "title": "Port of Rotterdam Terminal Gate Automation Outage",
        "description": "Terminal operating system connectivity failure causes 12-hour container gate closures and heavy arterial drayage truck congestion.",
        "category": "Port Disruption",
        "location": "Rotterdam, Netherlands",
        "severity": "High",
        "status": "Active",
        "source_name": "Maritime Executive Live Wire",
        "source_url": "https://maritime-executive.com/article/rotterdam-gate-system-outage",
        "is_demo": True
    },
    {
        "event_id": "demo-dis-002",
        "title": "Typhoon Malakas Severe Swells Halt Shanghai & Ningbo Port Operations",
        "description": "Category 3 typhoon brings 8-meter storm surges, forcing Port of Shanghai and Ningbo-Zhoushan to suspend all container vessel berthing for 48 hours.",
        "category": "Weather Disruption",
        "location": "Shanghai / Ningbo, China",
        "severity": "Critical",
        "status": "Active",
        "source_name": "NOAA National Marine Weather Center",
        "source_url": "https://www.weather.gov/marine/typhoon-east-asia-advisory",
        "is_demo": True
    },
    {
        "event_id": "demo-dis-003",
        "title": "Red Sea Shipping Rerouting via Cape of Good Hope Extends Transit Times",
        "description": "Major ocean carriers continue routing container fleets around Africa due to maritime security risks in Bab-el-Mandeb Strait, adding 10-14 days transit.",
        "category": "Shipping Delay",
        "location": "Red Sea / Suez Canal Corridor",
        "severity": "High",
        "status": "Active",
        "source_name": "FreightWaves Supply Chain Alerts",
        "source_url": "https://www.freightwaves.com/news/red-sea-carrier-rerouting-update",
        "is_demo": True
    },
    {
        "event_id": "demo-dis-004",
        "title": "Class 1 Midwest Freight Rail Winter Freeze Corridor Restrictions",
        "description": "Sub-zero temperatures across Chicago interchange hub require train length reductions and reduce diesel locomotive brake efficiency.",
        "category": "Railway Disruption",
        "location": "Chicago, IL, USA",
        "severity": "Medium",
        "status": "Active",
        "source_name": "Federal Railroad Administration Bulletins",
        "source_url": "https://railroads.dot.gov/newsroom/midwest-winter-speed-restrictions",
        "is_demo": True
    },
    {
        "event_id": "demo-dis-005",
        "title": "Panama Canal Transit Slot Conservation Advisory",
        "description": "Water levels at Gatun Lake require daily transit slots capped at 32 vessels, increasing auction slot premiums for neo-Panamax vessels.",
        "category": "Shipping Delay",
        "location": "Panama Canal, Panama",
        "severity": "Medium",
        "status": "Active",
        "source_name": "Panama Canal Authority Notices",
        "source_url": "https://pancanal.com/en/notices/advisory-a-08-2024",
        "is_demo": True
    }
]

def seed_default_data_if_empty():
    """Seed initial sources, disruptions, and historical database records if empty."""
    with SessionLocal() as db:
        # 1. Seed sources
        if db.query(models.Source).count() == 0:
            for s in DEFAULT_SOURCES:
                db.add(models.Source(
                    id=_gen_id(),
                    name=s["name"],
                    url=s["url"],
                    category=s["category"],
                    active=True,
                    created_at=datetime.now(timezone.utc)
                ))
            db.commit()

        # 2. Seed disruptions
        if db.query(models.Disruption).count() == 0:
            for d in DEFAULT_DISRUPTIONS:
                db.add(models.Disruption(
                    id=d["event_id"],
                    title=d["title"],
                    description=d["description"],
                    category=d["category"],
                    location=d["location"],
                    severity=d["severity"],
                    status=d["status"],
                    source_name=d["source_name"],
                    source_url=d["source_url"],
                    published_date=datetime.now(timezone.utc),
                    collected_at=datetime.now(timezone.utc),
                    is_demo=True
                ))
            db.commit()
