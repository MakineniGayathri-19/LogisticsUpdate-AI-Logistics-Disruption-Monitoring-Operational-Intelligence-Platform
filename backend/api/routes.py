"""FastAPI API routes for LogisticsUpdate AI.
Exposes endpoints for collection, disruptions, historical context, comparison,
LLM operational briefs, and system health.
"""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from database import repositories
from backend.services.collect_service import run_collection
from backend.services.report_service import generate_report_for_event, generate_pdf_report
from backend.services.event_comparison import compare_disruption_with_history
from backend.services.memento_manager import get_memento_status, store_operational_response

router = APIRouter()

# ---------------------------------------------------------------------------
# Request & Response Pydantic Schemas
# ---------------------------------------------------------------------------

class DisruptionCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    category: str = Field(default="Other")
    location: Optional[str] = "Unspecified Location"
    severity: str = Field(default="Unknown")
    status: str = Field(default="Active")
    source_name: str = Field(..., min_length=2)
    source_url: str = Field(..., min_length=5)
    published_date: Optional[str] = None

class HistoricalEventCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    category: str = Field(default="Other")
    location: Optional[str] = "Unspecified Location"
    severity: str = Field(default="High")
    response: Optional[str] = None
    outcome: Optional[str] = None
    source_name: Optional[str] = "Manual Entry"
    source_url: Optional[str] = ""

class SourceCreate(BaseModel):
    name: str = Field(..., min_length=2)
    url: str = Field(..., min_length=7)
    category: str = Field(default="Other")

class ReportGenerateRequest(BaseModel):
    event_id: str

class OperationalResponseCreate(BaseModel):
    event_id: str
    response: str
    outcome: str

# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check():
    """Verify backend and database operational health."""
    return {"status": "ok", "service": "LogisticsUpdate AI Backend", "version": "1.0.0"}

@router.get("/stats")
async def get_stats():
    """Returns aggregated KPI metrics for the overview dashboard."""
    return repositories.get_overview_stats()

@router.get("/memento/status")
async def memento_status():
    """Returns Memento adapter connection status."""
    return get_memento_status()

# ---------------------------------------------------------------------------
# Data Collection
# ---------------------------------------------------------------------------

@router.post("/collect")
async def trigger_collection():
    """Triggers the full scraping, cleaning, categorization, and persistence pipeline."""
    return run_collection()

@router.get("/logs")
async def list_collection_logs(limit: int = 25):
    """Retrieves auditable collection run logs."""
    return repositories.get_collection_logs(limit=limit)

# ---------------------------------------------------------------------------
# Disruptions
# ---------------------------------------------------------------------------

@router.get("/disruptions", response_model=List[Dict[str, Any]])
async def list_disruptions():
    """Retrieve all logged disruptions ordered by latest arrival."""
    return repositories.get_all_disruptions()

@router.get("/disruptions/{event_id}")
async def get_disruption(event_id: str):
    """Retrieve single disruption details by event_id."""
    item = repositories.get_disruption_by_id(event_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Disruption '{event_id}' not found")
    return item

@router.post("/disruptions")
async def create_disruption(payload: DisruptionCreate):
    """Manually insert a disruption record."""
    return repositories.create_disruption(payload.model_dump())

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

@router.get("/sources", response_model=List[Dict[str, Any]])
async def list_sources():
    """Retrieve configured web scraping sources."""
    return repositories.get_all_sources()

@router.post("/sources")
async def add_source(payload: SourceCreate):
    """Register a new public monitoring feed URL."""
    return repositories.add_source(payload.model_dump())

@router.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    """Remove a monitoring source."""
    success = repositories.delete_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"deleted": True, "source_id": source_id}

# ---------------------------------------------------------------------------
# Historical Precedents & Comparison
# ---------------------------------------------------------------------------

@router.get("/historical-events", response_model=List[Dict[str, Any]])
async def list_historical():
    """Retrieve archived historical events with past responses and outcomes."""
    return repositories.get_all_historical_events()

@router.post("/historical-events")
async def add_historical(payload: HistoricalEventCreate):
    """Add a historical incident record to memory store."""
    return repositories.add_historical_event(payload.model_dump())

@router.post("/historical-events/response")
async def record_operational_response(payload: OperationalResponseCreate):
    """Store mitigation response and observed outcome for an event."""
    return store_operational_response(
        event_id=payload.event_id,
        response=payload.response,
        outcome=payload.outcome
    )

@router.post("/compare/{event_id}")
async def compare(event_id: str):
    """Compare an active disruption against historical memory using TF-IDF and cosine similarity."""
    disruption = repositories.get_disruption_by_id(event_id)
    if not disruption:
        raise HTTPException(status_code=404, detail=f"Disruption '{event_id}' not found")
    comparison = compare_disruption_with_history(disruption, top_n=3)
    return comparison

# ---------------------------------------------------------------------------
# AI Reports
# ---------------------------------------------------------------------------

@router.post("/reports/generate")
async def generate_report(request: ReportGenerateRequest):
    """Synthesizes a 13-section Operational Intelligence Brief using GenAI/LLM."""
    report = generate_report_for_event(request.event_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Failed to generate brief for event '{request.event_id}'")
    return report

@router.get("/reports", response_model=List[Dict[str, Any]])
async def list_reports():
    """Retrieve all previously generated operational intelligence reports."""
    return repositories.get_all_reports()

@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Retrieve a single report by report_id."""
    r = repositories.get_report_by_id(report_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return r

@router.get("/reports/{report_id}/pdf")
async def export_report_pdf(report_id: str):
    """Exports an operational brief as a downloadable PDF."""
    r = repositories.get_report_by_id(report_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

    pdf_bytes = generate_pdf_report(r)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=logistics_brief_{report_id}.pdf"}
    )
