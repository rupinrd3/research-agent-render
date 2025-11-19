"""
Metrics Data Models

Pydantic models for performance metrics.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ToolMetrics(BaseModel):
    """Metrics for a single tool execution."""

    tool_name: str
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration_seconds: float = 0.0
    avg_duration_seconds: float = 0.0
    min_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    results_returned: int = 0


class ProviderMetrics(BaseModel):
    """Metrics for LLM provider usage."""

    provider: str  # 'openai', 'gemini', 'openrouter'
    call_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_tokens_per_call: float = 0.0
    avg_cost_per_call: float = 0.0


class MetricsData(BaseModel):
    """
    Comprehensive metrics for a research session.

    Captures performance, usage, and quality metrics.
    """

    session_id: str

    # Timing metrics
    total_duration_seconds: float = 0.0
    planning_duration_seconds: float = 0.0
    execution_duration_seconds: float = 0.0
    evaluation_duration_seconds: float = 0.0

    # Iteration metrics
    total_iterations: int = 0
    avg_iteration_duration: float = 0.0

    # Tool usage metrics
    tools_used: List[str] = Field(default_factory=list)
    tool_metrics: Dict[str, ToolMetrics] = Field(default_factory=dict)
    total_tool_executions: int = 0
    tool_success_rate: float = 0.0

    # LLM usage metrics
    providers_used: List[str] = Field(default_factory=list)
    provider_metrics: Dict[str, ProviderMetrics] = Field(default_factory=dict)
    total_llm_calls: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0

    # Content metrics
    total_sources_found: int = 0
    unique_sources: int = 0
    source_diversity_score: float = 0.0  # 0-1 score
    avg_source_recency_days: Optional[float] = None
    pdf_sources_count: int = 0

    # Output metrics
    report_word_count: int = 0
    report_char_count: int = 0
    citations_count: int = 0
    unique_domains: int = 0

    # Query analysis
    query_keywords: List[str] = Field(default_factory=list)
    query_keyword_coverage: float = 0.0  # % of keywords addressed

    # Quality metrics (from evaluation, 0-1 scale)
    relevance_score: Optional[float] = None
    accuracy_score: Optional[float] = None
    completeness_score: Optional[float] = None
    source_quality_score: Optional[float] = None

    # Timestamp
    collected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricsSummary(BaseModel):
    """Summary statistics across multiple sessions."""

    total_sessions: int
    avg_duration_seconds: float
    avg_iterations: int
    avg_cost_per_session: float
    total_cost: float
    most_used_tools: List[str]
    most_used_providers: List[str]
    avg_quality_score: float
    sessions_analyzed: int
