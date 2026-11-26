"""SQLAlchemy database models for LogisticsUpdate AI.
Defines tables for:
1. Disruptions (Live/Collected updates)
2. Historical Events (Curated historical incidents)
3. Operational Responses (Past actions and operational outcomes)
4. Sources (Configured monitoring feeds)
5. AI Reports (Generated operational intelligence briefs)
6. Collection Logs (Auditable run logs of scraping operations)
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

def utcnow():
    return datetime.now(timezone.utc)

class Disruption(Base):
    """Live collected logistics disruptions."""
    __tablename__ = "disruptions"

    id = Column(String(36), primary_key=True)  # event_id
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    location = Column(String(200), nullable=True)
    severity = Column(String(50), nullable=False, default="Unknown")
    status = Column(String(50), default="Active")
    source_name = Column(String(150), nullable=False)
    source_url = Column(String(500), nullable=False)
    published_date = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=utcnow)
    is_demo = Column(Boolean, default=False)

    reports = relationship("Report", back_populates="disruption", cascade="all, delete-orphan")


class HistoricalEvent(Base):
    """Archival / precedent disruption incidents."""
    __tablename__ = "historical_events"

    id = Column(String(36), primary_key=True)
    event_id = Column(String(50), unique=True, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    location = Column(String(200), nullable=True)
    severity = Column(String(50), nullable=False, default="High")
    status = Column(String(50), default="Resolved")
    source_name = Column(String(150), nullable=True)
    source_url = Column(String(500), nullable=True)
    published_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    is_demo = Column(Boolean, default=False)

    responses = relationship("OperationalResponse", back_populates="historical_event", cascade="all, delete-orphan")


class OperationalResponse(Base):
    """Documented mitigation responses and real-world outcomes for incidents."""
    __tablename__ = "operational_responses"

    id = Column(String(36), primary_key=True)
    historical_event_id = Column(String(36), ForeignKey("historical_events.id"), nullable=True)
    disruption_id = Column(String(36), ForeignKey("disruptions.id"), nullable=True)
    response = Column(Text, nullable=False)
    outcome = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    historical_event = relationship("HistoricalEvent", back_populates="responses")


class Source(Base):
    """Configured public monitoring feeds for web scraping."""
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True)
    name = Column(String(150), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class Report(Base):
    """Generative AI operational intelligence briefs."""
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True)
    disruption_id = Column(String(36), ForeignKey("disruptions.id"), nullable=False)
    content = Column(Text, nullable=False)
    llm_provider = Column(String(50), nullable=False)
    generated_at = Column(DateTime, default=utcnow)

    disruption = relationship("Disruption", back_populates="reports")


class CollectionLog(Base):
    """Audit logs for data collection and web scraping operations."""
    __tablename__ = "collection_logs"

    id = Column(String(36), primary_key=True)
    source_url = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False)  # success, failed, skipped
    records_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
