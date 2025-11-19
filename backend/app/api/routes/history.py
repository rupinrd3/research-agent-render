"""
History & Stats API Routes

Endpoints for listing sessions and viewing aggregate statistics.
"""

import logging
from fastapi import APIRouter, Query
from typing import Optional
from sqlalchemy import select, func
from datetime import datetime

from ..models.responses import (
    HistoryResponse,
    SessionSummary,
    StatsResponse,
)
from ...database import get_database
from ...database.models import ResearchSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
):
    """
    List all research sessions with pagination.

    Supports filtering by status and sorting.
    """
    async with await get_database() as db:
        # Build query
        query = select(ResearchSession)

        # Apply filters
        if status:
            query = query.where(ResearchSession.status == status)

        # Count total
        count_query = select(func.count()).select_from(ResearchSession)
        if status:
            count_query = count_query.where(ResearchSession.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(ResearchSession, sort_by, ResearchSession.created_at)

        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        sessions = result.scalars().all()

        # Build response
        return HistoryResponse(
            sessions=[
                SessionSummary(
                    id=session.id,
                    query=session.query,
                    status=session.status,
                    created_at=session.created_at,
                    completed_at=session.completed_at,
                    total_duration_seconds=session.total_duration_seconds,
                    total_cost_usd=session.total_cost_usd,
                )
                for session in sessions
            ],
            total=total,
            page=page,
            page_size=page_size,
            has_more=offset + len(sessions) < total,
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get aggregate statistics.

    Returns total sessions, costs, and performance metrics.
    """
    async with await get_database() as db:
        # Count total sessions
        total_count = await db.execute(
            select(func.count()).select_from(ResearchSession)
        )
        total_sessions = total_count.scalar()

        # Count completed sessions
        completed_count = await db.execute(
            select(func.count())
            .select_from(ResearchSession)
            .where(ResearchSession.status == "completed")
        )
        completed_sessions = completed_count.scalar()

        # Count failed sessions
        failed_count = await db.execute(
            select(func.count())
            .select_from(ResearchSession)
            .where(ResearchSession.status == "failed")
        )
        failed_sessions = failed_count.scalar()

        # Calculate total cost
        cost_sum = await db.execute(
            select(func.sum(ResearchSession.total_cost_usd)).select_from(
                ResearchSession
            )
        )
        total_cost = cost_sum.scalar() or 0.0

        # Calculate average duration (for completed sessions)
        duration_avg = await db.execute(
            select(func.avg(ResearchSession.total_duration_seconds))
            .select_from(ResearchSession)
            .where(ResearchSession.status == "completed")
        )
        avg_duration = duration_avg.scalar() or 0.0

        # Calculate average cost (for completed sessions)
        cost_avg = await db.execute(
            select(func.avg(ResearchSession.total_cost_usd))
            .select_from(ResearchSession)
            .where(ResearchSession.status == "completed")
        )
        avg_cost = cost_avg.scalar() or 0.0

        return StatsResponse(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            failed_sessions=failed_sessions,
            total_cost_usd=total_cost,
            average_duration_seconds=avg_duration,
            average_cost_usd=avg_cost,
        )
