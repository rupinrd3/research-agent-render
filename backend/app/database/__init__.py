"""
Database Layer

SQLite database with async support for storing research sessions,
traces, and evaluation results.
"""

from .models import (
    Base,
    ResearchSession,
    TraceEvent,
    EndToEndEvaluation,
    PerformanceMetric,
)
from .database import (
    get_database,
    init_database,
    create_session,
    get_session,
    update_session,
    save_trace_event,
    save_per_step_evaluation,
    save_end_to_end_evaluation,
    get_session_trace,
    get_session_evaluations,
    close_database,
)

__all__ = [
    "Base",
    "ResearchSession",
    "TraceEvent",
    "EndToEndEvaluation",
    "PerformanceMetric",
    "get_database",
    "init_database",
    "create_session",
    "get_session",
    "update_session",
    "save_trace_event",
    "save_end_to_end_evaluation",
    "get_session_trace",
    "get_session_evaluations",
    "close_database",
]
