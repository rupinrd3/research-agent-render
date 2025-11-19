"""
Agent System

Implements the two-agent architecture:
1. Researcher Agent (ReAct pattern)
2. Evaluator Agent (Multi-level assessment)
"""

from .react_agent import ResearcherAgent
from .evaluator_agent import EvaluatorAgent
from .models import (
    AgentStep,
    ResearchResult,
    EvaluationResult,
)

__all__ = [
    "ResearcherAgent",
    "EvaluatorAgent",
    "AgentStep",
    "ResearchResult",
    "EvaluationResult",
]
