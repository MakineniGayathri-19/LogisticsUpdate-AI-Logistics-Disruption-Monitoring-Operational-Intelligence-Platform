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
        stmt = (
            select(models.Disruption)
            .where(models.Disruption.is_demo.is_(False))
            .order_by(desc(models.Disruption.collected_at))
        )
        results = db.execute(stmt).scalars().all()
        return [_model_to_dict(r) for r in results]

def get_disruption_by_id(event_id: str) -> Optional[Dict]:
    with SessionLocal() as db:
        obj = db.get(models.Disruption, event_id)
        return _model_to_dict(obj) if obj and not obj.is_demo else None

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
                pub_date = None
        elif not isinstance(pub_date, datetime):
            pub_date = None

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
        stmt = (
            select(models.HistoricalEvent)
            .where(models.HistoricalEvent.is_demo.is_(False))
            .order_by(desc(models.HistoricalEvent.created_at))
        )
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
                d["response"] = ""
                d["outcome"] = ""
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
        if not ev or ev.is_demo:
            return None
        d = _model_to_dict(ev)
        resp_obj = db.execute(
            select(models.OperationalResponse).where(models.OperationalResponse.historical_event_id == ev.id)
        ).scalar_one_or_none()
        if resp_obj:
            d["response"] = resp_obj.response
            d["outcome"] = resp_obj.outcome
        else:
            d["response"] = ""
            d["outcome"] = ""
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

        published_date = data.get("published_date")
        if isinstance(published_date, str):
            try:
                published_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            except ValueError:
                published_date = None
        elif not isinstance(published_date, datetime):
            published_date = None

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
            published_date=published_date,
            is_demo=bool(data.get("is_demo", False)),
            created_at=datetime.now(timezone.utc),
        )
        db.add(he)
        db.commit()

        # If operational response and outcome provided, attach them
        if data.get("response") and data.get("outcome"):
            op_resp = models.OperationalResponse(
                id=_gen_id(),
                historical_event_id=he.id,
                response=clean_text(data["response"]),
                outcome=clean_text(data["outcome"]),
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

def create_report(disruption_id: str, content: str, provider: str) -> Dict:
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
        stmt = (
            select(models.Report)
            .join(models.Disruption)
            .where(models.Disruption.is_demo.is_(False))
            .order_by(desc(models.Report.generated_at))
        )
        results = db.execute(stmt).scalars().all()
        return [_model_to_dict(r) for r in results]

def get_report_by_id(report_id: str) -> Optional[Dict]:
    with SessionLocal() as db:
        obj = db.get(models.Report, report_id)
        if not obj:
            return None
        disruption = db.get(models.Disruption, obj.disruption_id)
        return _model_to_dict(obj) if disruption and not disruption.is_demo else None

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
        real_disruptions = models.Disruption.is_demo.is_(False)
        total_disruptions = db.query(models.Disruption).filter(real_disruptions).count()
        active_disruptions = db.query(models.Disruption).filter(real_disruptions, models.Disruption.status == "Active").count()
        critical_disruptions = db.query(models.Disruption).filter(real_disruptions, models.Disruption.severity == "Critical").count()
        high_disruptions = db.query(models.Disruption).filter(real_disruptions, models.Disruption.severity == "High").count()
        historical_stored = db.query(models.HistoricalEvent).filter(models.HistoricalEvent.is_demo.is_(False)).count()
        ai_reports_generated = (
            db.query(models.Report)
            .join(models.Disruption)
            .filter(real_disruptions)
            .count()
        )
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
# Default public monitoring sources
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
        "name": "NOAA National Weather Service Active Alerts",
        "url": "https://api.weather.gov/alerts/active",
        "category": "Weather Disruption"
    },
    {
        "name": "Federal Railroad Administration Bulletins",
        "url": "https://railroads.dot.gov/newsroom",
        "category": "Railway Disruption"
    }
]

def seed_default_data_if_empty():
    """Register real public sources without seeding synthetic disruption records."""
    with SessionLocal() as db:
        existing_urls = set(db.execute(select(models.Source.url)).scalars())
        for source in DEFAULT_SOURCES:
            if source["url"] not in existing_urls:
                db.add(models.Source(
                    id=_gen_id(),
                    name=source["name"],
                    url=source["url"],
                    category=source["category"],
                    active=True,
                    created_at=datetime.now(timezone.utc)
                ))
        db.commit()
