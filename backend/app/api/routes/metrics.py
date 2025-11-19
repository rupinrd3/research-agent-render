"""
Metrics API Routes

Provides endpoints for fetching current and historical metrics.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

from ...metrics.history import load_history, compute_aggregates

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class MetricsSummaryResponse(BaseModel):
    """Metrics summary response."""
    inception: Dict[str, Any]  # Aggregated historical metrics
    total_sessions: int


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary():
    """
    Get metrics summary including inception till date aggregates.

    Returns:
        Current session metrics (if available) and historical aggregates
    """
    try:
        # Load history
        history = load_history()

        # Compute aggregates
        inception = compute_aggregates(history)

        return MetricsSummaryResponse(
            inception=inception,
            total_sessions=len(history),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute metrics: {str(e)}"
        )
