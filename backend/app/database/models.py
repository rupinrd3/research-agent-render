"""
Database Models

SQLAlchemy models for storing research sessions, traces, and evaluations.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ResearchSession(Base):
    """
    Research session model.

    Stores high-level information about a research query execution.
    """

    __tablename__ = "research_sessions"

    id = Column(String, primary_key=True)
    query = Column(Text, nullable=False)
    config = Column(JSON, nullable=False)
    status = Column(
        String, nullable=False, default="running"
    )  # 'running', 'completed', 'failed'

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Metrics
    total_duration_seconds = Column(Float, nullable=True)
    total_iterations = Column(Integer, nullable=True)
    total_cost_usd = Column(Float, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Results
    final_report = Column(Text, nullable=True)
    sources = Column(JSON, nullable=True)
    evaluation_summary = Column(JSON, nullable=True)

    # Relationships
    trace_events = relationship(
        "TraceEvent", back_populates="session", cascade="all, delete-orphan"
    )
    end_to_end_evaluation = relationship(
        "EndToEndEvaluation",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    performance_metrics = relationship(
        "PerformanceMetric",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class TraceEvent(Base):
    """
    Trace event model.

    Stores individual events during research execution (thoughts, actions,
    observations, tool executions, etc.).
    """

    __tablename__ = "trace_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String, ForeignKey("research_sessions.id"), nullable=False
    )
    type = Column(
        String, nullable=False
    )  # 'thought', 'action', 'tool_execution', 'observation', etc.
    iteration = Column(Integer, nullable=True)
    data = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship("ResearchSession", back_populates="trace_events")


class EndToEndEvaluation(Base):
    """
    End-to-end evaluation model.

    Stores 0-1 scale quality scores for the final research output.
    """

    __tablename__ = "end_to_end_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String, ForeignKey("research_sessions.id"), nullable=False, unique=True
    )

    # Quality scores (0-1 scale)
    relevance_score = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    source_quality_score = Column(Float, nullable=True)

    # Qualitative feedback
    strengths = Column(JSON, nullable=True)  # List of strings
    weaknesses = Column(JSON, nullable=True)  # List of strings
    recommendations = Column(JSON, nullable=True)  # List of strings

    # Evaluation cost
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship(
        "ResearchSession", back_populates="end_to_end_evaluation"
    )


class PerformanceMetric(Base):
    """
    Performance metric model.

    Stores individual performance metrics for tracking and analytics.
    """

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String, ForeignKey("research_sessions.id"), nullable=False
    )
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=True)  # e.g., 'seconds', 'tokens', 'usd'
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship(
        "ResearchSession", back_populates="performance_metrics"
    )
