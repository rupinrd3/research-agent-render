"""
API Response Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class StartResearchResponse(BaseModel):
    """Response after starting a research session."""

    session_id: str = Field(..., description="Unique session identifier")
    websocket_url: str = Field(..., description="WebSocket URL for real-time updates")
    status: str = Field(default="running", description="Session status")


class SessionResponse(BaseModel):
    """Research session details."""

    id: str
    query: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    total_iterations: Optional[int] = None
    total_cost_usd: Optional[float] = None
    final_report: Optional[str] = None
    sources: Optional[List[str]] = None


class TraceEventResponse(BaseModel):
    """Single trace event."""

    id: int
    session_id: str
    type: str
    iteration: Optional[int] = None
    data: Dict[str, Any]
    timestamp: datetime


class TraceResponse(BaseModel):
    """Complete trace for a session."""

    session_id: str
    events: List[TraceEventResponse]
    total_events: int


class EndToEndEvaluationResponse(BaseModel):
    """End-to-end evaluation details (0-1 scale, 4 metrics only)."""

    relevance_score: float  # 0-1
    accuracy_score: float  # 0-1
    completeness_score: float  # 0-1
    source_quality_score: float  # 0-1
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class EvaluationResponse(BaseModel):
    """Complete evaluation for a session (end-to-end only)."""

    session_id: str
    end_to_end_evaluation: Optional[EndToEndEvaluationResponse] = None


class SessionSummary(BaseModel):
    """Summary of a research session."""

    id: str
    query: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    total_cost_usd: Optional[float] = None


class HistoryResponse(BaseModel):
    """List of research sessions with pagination."""

    sessions: List[SessionSummary]
    total: int
    page: int
    page_size: int
    has_more: bool


class StatsResponse(BaseModel):
    """Aggregate statistics."""

    total_sessions: int
    completed_sessions: int
    failed_sessions: int
    total_cost_usd: float
    average_duration_seconds: float
    average_cost_usd: float


class ConfigResponse(BaseModel):
    """System configuration."""

    llm: Dict[str, Any]
    research: Dict[str, Any]
    tools: Dict[str, Any]
    evaluation: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
    session_id: Optional[str] = None
