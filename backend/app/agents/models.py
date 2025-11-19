"""
Agent Data Models

Pydantic models for agent inputs, outputs, and intermediate states.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class AgentStep:
    """
    Represents a single step in the ReAct loop.
    """

    iteration: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str
    tool_output: Any
    timestamp: datetime
    tokens_used: int
    cost_usd: float
    latency_seconds: float


@dataclass
class ResearchResult:
    """
    Final result of research execution.
    """

    session_id: str
    query: str
    report: str
    sources: List[str]
    steps: List[AgentStep]
    total_iterations: int
    total_duration_seconds: float
    total_tokens: int
    total_cost_usd: float
    status: str  # 'completed', 'failed', 'timeout'
    error: Optional[str] = None


@dataclass
class EndToEndEval:
    """
    Comprehensive evaluation of final research output.
    Uses 0-1 scale for all scores.
    """

    # Quality dimensions (0-1 scale)
    relevance_score: float  # 0-1
    accuracy_score: float  # 0-1
    completeness_score: float  # 0-1
    source_quality_score: float  # 0-1

    # Qualitative feedback
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

    # Evaluation cost tracking
    tokens_used: int
    cost_usd: float


@dataclass
class EvaluationResult:
    """
    Complete evaluation results for a research session.
    """

    session_id: str
    end_to_end_evaluation: EndToEndEval
