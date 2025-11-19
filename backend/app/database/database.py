"""
Database Utilities

Functions for database initialization and common operations.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import select

from .models import (
    Base,
    ResearchSession,
    TraceEvent,
    EndToEndEvaluation,
)

logger = logging.getLogger(__name__)

# Global database engine and session maker
_engine = None
_async_session_maker = None


async def init_database(database_url: str, echo: bool = False):
    """
    Initialize database connection and create tables.

    Args:
        database_url: SQLAlchemy database URL
        echo: If True, log all SQL statements
    """
    global _engine, _async_session_maker

    logger.info(f"Initializing database: {database_url}")

    # Create async engine
    _engine = create_async_engine(database_url, echo=echo)

    # Create session maker
    _async_session_maker = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create all tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def get_database() -> AsyncSession:
    """
    Get database session.

    Returns:
        Async database session

    Raises:
        RuntimeError: If database not initialized
    """
    if _async_session_maker is None:
        raise RuntimeError(
            "Database not initialized. Call init_database() first."
        )

    return _async_session_maker()


async def create_session(
    session_id: Optional[str], query: str, config: Dict[str, Any]
) -> ResearchSession:
    """
    Create a new research session.

    Args:
        session_id: Unique session identifier (will be generated if None)
        query: Research query
        config: Session configuration

    Returns:
        Created ResearchSession
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    async with await get_database() as db:
        session = ResearchSession(
            id=session_id, query=query, config=config, status="running"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info(f"Created research session: {session_id}")
        return session


async def get_session(session_id: str) -> Optional[ResearchSession]:
    """
    Get research session by ID.

    Args:
        session_id: Session identifier

    Returns:
        ResearchSession or None if not found
    """
    async with await get_database() as db:
        result = await db.execute(
            select(ResearchSession).where(ResearchSession.id == session_id)
        )
        return result.scalar_one_or_none()


async def update_session(
    session_id: str, **kwargs
) -> Optional[ResearchSession]:
    """
    Update research session.

    Args:
        session_id: Session identifier
        **kwargs: Fields to update

    Returns:
        Updated ResearchSession or None if not found
    """
    async with await get_database() as db:
        result = await db.execute(
            select(ResearchSession).where(ResearchSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            await db.commit()
            await db.refresh(session)
            logger.info(f"Updated session {session_id}")

        return session


async def save_trace_event(
    session_id: str,
    event_type: str,
    data: Dict[str, Any],
    iteration: Optional[int] = None,
) -> TraceEvent:
    """
    Save a trace event.

    Args:
        session_id: Session identifier
        event_type: Type of event
        data: Event data
        iteration: Iteration number (optional)

    Returns:
        Created TraceEvent
    """
    async with await get_database() as db:
        event = TraceEvent(
            session_id=session_id,
            type=event_type,
            iteration=iteration,
            data=data,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        return event


async def save_per_step_evaluation(
    session_id: str, iteration: int, evaluation: Dict[str, Any]
) -> None:
    """
    Save per-step evaluation.

    DEPRECATED: Per-step evaluation has been removed. This function is kept
    for backward compatibility but does nothing.

    Args:
        session_id: Session identifier
        iteration: Iteration number
        evaluation: Evaluation data

    Returns:
        None
    """
    # Per-step evaluation removed - function kept for backward compatibility
    logger.warning("save_per_step_evaluation called but per-step evaluation is deprecated")
    return None


async def save_end_to_end_evaluation(
    session_id: str, evaluation: Dict[str, Any]
) -> EndToEndEvaluation:
    """
    Save end-to-end evaluation.

    Args:
        session_id: Session identifier
        evaluation: Evaluation data

    Returns:
        Created EndToEndEvaluation
    """
    async with await get_database() as db:
        eval_record = EndToEndEvaluation(
            session_id=session_id, **evaluation
        )
        db.add(eval_record)
        await db.commit()
        await db.refresh(eval_record)

        return eval_record


async def get_session_trace(session_id: str) -> list[TraceEvent]:
    """
    Get all trace events for a session.

    Args:
        session_id: Session identifier

    Returns:
        List of TraceEvents ordered by timestamp
    """
    async with await get_database() as db:
        result = await db.execute(
            select(TraceEvent)
            .where(TraceEvent.session_id == session_id)
            .order_by(TraceEvent.timestamp)
        )
        return list(result.scalars().all())


async def get_session_evaluations(
    session_id: str,
) -> tuple[list, Optional[EndToEndEvaluation]]:
    """
    Get all evaluations for a session.

    Args:
        session_id: Session identifier

    Returns:
        Tuple of (per_step_evaluations, end_to_end_evaluation)
        Note: per_step_evaluations is always empty list (feature removed)
    """
    async with await get_database() as db:
        # Per-step evaluations removed - return empty list
        per_step_evals = []

        # Get end-to-end evaluation
        end_to_end_result = await db.execute(
            select(EndToEndEvaluation).where(
                EndToEndEvaluation.session_id == session_id
            )
        )
        end_to_end_eval = end_to_end_result.scalar_one_or_none()

        return per_step_evals, end_to_end_eval


async def close_database():
    """Close database connection."""
    global _engine

    if _engine:
        await _engine.dispose()
        logger.info("Database connection closed")
