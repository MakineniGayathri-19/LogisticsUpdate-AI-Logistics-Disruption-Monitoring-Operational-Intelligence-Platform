"""Report Service for LogisticsUpdate AI.
Orchestrates event fetching, historical comparison retrieval, LLM brief synthesis,
database persistence, and professional PDF brief generation via ReportLab.
"""
import io
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from backend.services.llm_service import generate_brief
from backend.services.event_comparison import compare_disruption_with_history
from database import repositories
from utils.logger import logger

def generate_report_for_event(event_id: str) -> Optional[Dict[str, Any]]:
    """Generate and store an operational intelligence brief for a disruption event."""
    event = repositories.get_disruption_by_id(event_id)
    if not event:
        logger.error(f"Cannot generate report: event '{event_id}' not found.")
        return None

    # 1. Retrieve similar historical events and comparison analysis
    comparison_data = compare_disruption_with_history(event, top_n=3)

    # 2. Generate brief using configured LLM or deterministic fallback
    brief_content, provider_name = generate_brief(event, comparison_data)

    # 3. Persist the report into SQLite database
    report = repositories.create_report(
        disruption_id=event_id,
        content=brief_content,
        provider=provider_name
    )
    return report

def generate_pdf_report(report_data: Dict[str, Any], event_data: Optional[Dict[str, Any]] = None) -> bytes:
    """Generate a clean, professional PDF document of the operational brief using ReportLab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#0B192C'),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#1E3E62'),
        spaceAfter=12
    )

    header_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#1E3E62'),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1A1A1A')
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#2C3E50')
    )

    story = []

    # Title Banner
    story.append(Paragraph("LogisticsUpdate AI", title_style))
    story.append(Paragraph("AI-Powered Logistics Disruption Monitoring & Operational Intelligence Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3E62'), spaceAfter=10))

    # Metadata Block
    meta_data = [
        [
            Paragraph(f"<b>Report ID:</b> {report_data.get('id', 'N/A')}", body_style),
            Paragraph(f"<b>Disruption Ref:</b> {report_data.get('disruption_id', 'N/A')}", body_style)
        ],
        [
            Paragraph(f"<b>Provider:</b> {report_data.get('llm_provider', 'LogisticsUpdate Engine')}", body_style),
            Paragraph(f"<b>Generated At:</b> {report_data.get('generated_at', datetime.now(timezone.utc).isoformat())}", body_style)
        ]
    ]
    t = Table(meta_data, colWidths=[260, 260])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F6F9')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D8E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Content breakdown
    content_raw = report_data.get("content", "")
    lines = content_raw.split("\n")

    in_header = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("===") or stripped.startswith("---"):
            continue

        # Check if line looks like a numbered section header: e.g. "1. EXECUTIVE SUMMARY"
        if stripped[0].isdigit() and ("." in stripped[:3] or ")" in stripped[:3]):
            story.append(Spacer(1, 6))
            story.append(Paragraph(stripped, header_style))
        elif stripped.startswith("•") or stripped.startswith("-"):
            bullet_text = stripped.lstrip("•- ")
            story.append(Paragraph(f"&bull; {bullet_text}", body_style))
        else:
            story.append(Paragraph(stripped, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
