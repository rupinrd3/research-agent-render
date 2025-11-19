"""
Export API Routes

Endpoints for exporting research results in various formats.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, FileResponse
from typing import Optional

from ..exceptions import SessionNotFoundException
from ...database import get_session, get_session_trace, get_session_evaluations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research/{session_id}/export", tags=["export"])


@router.get("/markdown")
async def export_markdown(session_id: str):
    """
    Export report as Markdown.

    Returns the final research report in Markdown format.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    if not session.final_report:
        raise HTTPException(status_code=400, detail="Session not yet completed")

    # Return markdown content
    return Response(
        content=session.final_report,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="research_{session_id}.md"'
        },
    )


@router.get("/pdf")
async def export_pdf(session_id: str):
    """
    Export report as PDF.

    Generates a PDF document with the research report.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    if not session.final_report:
        raise HTTPException(status_code=400, detail="Session not yet completed")

    try:
        # Import PDF exporter
        from ...export.pdf import export_to_pdf

        # Generate PDF
        pdf_bytes = await export_to_pdf(
            report=session.final_report,
            query=session.query,
            sources=session.sources or [],
            metadata={
                "session_id": session.id,
                "created_at": session.created_at,
                "duration": session.total_duration_seconds,
                "cost": session.total_cost_usd,
            },
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="research_{session_id}.pdf"'
            },
        )

    except ImportError as e:
        logger.error(f"PDF export not available: {e}")
        raise HTTPException(
            status_code=501, detail="PDF export not implemented yet"
        )


@router.get("/word")
async def export_word(session_id: str):
    """
    Export report as Word document.

    Generates a .docx file with the research report.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    if not session.final_report:
        raise HTTPException(status_code=400, detail="Session not yet completed")

    try:
        # Import Word exporter
        from ...export.word import export_to_word

        # Generate Word document
        docx_bytes = await export_to_word(
            report=session.final_report,
            query=session.query,
            sources=session.sources or [],
            metadata={
                "session_id": session.id,
                "created_at": session.created_at,
                "duration": session.total_duration_seconds,
                "cost": session.total_cost_usd,
            },
        )

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="research_{session_id}.docx"'
            },
        )

    except ImportError as e:
        logger.error(f"Word export not available: {e}")
        raise HTTPException(
            status_code=501, detail="Word export not implemented yet"
        )


@router.get("/json")
async def export_json(session_id: str):
    """
    Export complete trace as JSON.

    Returns all session data, trace events, and evaluations as JSON.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    # Get trace events
    trace_events = await get_session_trace(session_id)

    # Get evaluations
    per_step_evals, end_to_end_eval = await get_session_evaluations(session_id)

    # Build JSON response
    data = {
        "session": {
            "id": session.id,
            "query": session.query,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "completed_at": (
                session.completed_at.isoformat() if session.completed_at else None
            ),
            "total_duration_seconds": session.total_duration_seconds,
            "total_iterations": session.total_iterations,
            "total_cost_usd": session.total_cost_usd,
            "final_report": session.final_report,
            "sources": session.sources,
        },
        "trace_events": [
            {
                "id": event.id,
                "type": event.type,
                "iteration": event.iteration,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
            }
            for event in trace_events
        ],
        "end_to_end_evaluation": (
            {
                "relevance_score": end_to_end_eval.relevance_score,
                "accuracy_score": end_to_end_eval.accuracy_score,
                "completeness_score": end_to_end_eval.completeness_score,
                "source_quality_score": end_to_end_eval.source_quality_score,
                "strengths": end_to_end_eval.strengths,
                "weaknesses": end_to_end_eval.weaknesses,
                "recommendations": end_to_end_eval.recommendations,
            }
            if end_to_end_eval
            else None
        ),
    }

    import json

    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="research_{session_id}.json"'
        },
    )


@router.get("/html")
async def export_html(session_id: str):
    """
    Export report as standalone HTML.

    Generates a self-contained HTML file with embedded CSS.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    if not session.final_report:
        raise HTTPException(status_code=400, detail="Session not yet completed")

    try:
        # Import HTML exporter
        from ...export.html import export_to_html

        # Generate HTML
        html_content = await export_to_html(
            report=session.final_report,
            query=session.query,
            sources=session.sources or [],
            metadata={
                "session_id": session.id,
                "created_at": session.created_at,
                "duration": session.total_duration_seconds,
                "cost": session.total_cost_usd,
            },
        )

        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="research_{session_id}.html"'
            },
        )

    except ImportError as e:
        logger.error(f"HTML export not available: {e}")
        raise HTTPException(
            status_code=501, detail="HTML export not implemented yet"
        )
