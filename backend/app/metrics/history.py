"""
Metrics History Storage

Simple JSON file-based storage for session metrics history.
Designed for small-scale usage (≤200 sessions).
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import statistics
from filelock import FileLock

logger = logging.getLogger(__name__)

HISTORY_FILE = Path("backend/runtime/metrics_history.json")
LOCK_FILE = Path("backend/runtime/metrics_history.lock")


def _ensure_runtime_dir():
    """Ensure runtime directory exists."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def append_run(snapshot: Dict[str, Any]) -> None:
    """
    Append a session snapshot to history.

    Args:
        snapshot: Session metrics snapshot
    """
    _ensure_runtime_dir()

    with FileLock(str(LOCK_FILE)):
        # Load existing history
        history = load_history()

        # Append new snapshot
        history.append(snapshot)

        # Keep only last 200 sessions
        if len(history) > 200:
            history = history[-200:]

        # Write back
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)

    logger.info(f"Appended session {snapshot.get('session_id')} to history")


def load_history() -> List[Dict[str, Any]]:
    """
    Load all session history.

    Returns:
        List of session snapshots
    """
    _ensure_runtime_dir()

    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load history: {e}")
        return []


def compute_aggregates(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate metrics from history.

    Args:
        history: List of session snapshots

    Returns:
        Aggregated metrics with medians and averages
    """
    if not history:
        return {
            "total_sessions": 0,
            "completed_sessions": 0,
            "iteration_latency_median_ms": 0,
            "end_to_end_median_seconds": 0,
            "tools": {},
            "avg_tokens": 0,
            "avg_cost_usd": 0,
            "avg_iterations": 0,
            "tool_success_rate": 0,
            "session_success_rate": 0,
            "provider_failover_rate": 0,
            "relevance_avg": 0,
            "accuracy_avg": 0,
            "completeness_avg": 0,
            "source_quality_avg": 0,
        }

    # All sessions (for success rate)
    total_sessions = len(history)
    completed_sessions = [s for s in history if s.get("status") == "completed"]

    if not completed_sessions:
        return compute_aggregates([])  # Return zeros

    # Collect iteration latencies
    all_iteration_latencies = []
    for session in completed_sessions:
        latencies = session.get("iteration_latencies_ms", [])
        all_iteration_latencies.extend(latencies)

    # Collect end-to-end durations
    end_to_end_durations = [
        s.get("end_to_end_seconds", 0) for s in completed_sessions if s.get("end_to_end_seconds")
    ]

    # Collect tool execution times
    tools_aggregated = {}
    for session in completed_sessions:
        tool_times = session.get("tool_execution_times", {})
        for tool, times in tool_times.items():
            if tool not in tools_aggregated:
                tools_aggregated[tool] = []
            tools_aggregated[tool].extend(times)

    # Compute tool medians
    tools_median = {
        tool: statistics.median(times) if times else 0
        for tool, times in tools_aggregated.items()
    }

    # Collect tokens and cost
    all_tokens = [s.get("total_tokens", 0) for s in completed_sessions if s.get("total_tokens")]
    all_costs = [s.get("total_cost_usd", 0) for s in completed_sessions if s.get("total_cost_usd")]

    # Collect iterations
    all_iterations = [s.get("iterations_to_completion", 0) for s in completed_sessions if s.get("iterations_to_completion")]

    # Collect tool success/failure counts
    total_tool_successes = sum(s.get("tool_success_count", 0) for s in completed_sessions)
    total_tool_failures = sum(s.get("tool_failure_count", 0) for s in completed_sessions)
    total_tool_calls = total_tool_successes + total_tool_failures

    # Collect provider failovers
    total_failovers = sum(s.get("provider_failover_count", 0) for s in completed_sessions)
    total_llm_calls = sum(s.get("total_llm_calls", 0) for s in completed_sessions)

    # Collect evaluation scores
    relevance_scores = [s.get("relevance", 0) for s in completed_sessions if "relevance" in s]
    accuracy_scores = [s.get("accuracy", 0) for s in completed_sessions if "accuracy" in s]
    completeness_scores = [s.get("completeness", 0) for s in completed_sessions if "completeness" in s]
    source_quality_scores = [s.get("source_quality", 0) for s in completed_sessions if "source_quality" in s]

    return {
        "total_sessions": total_sessions,
        "completed_sessions": len(completed_sessions),

        # Latency Metrics (medians)
        "iteration_latency_median_ms": statistics.median(all_iteration_latencies) if all_iteration_latencies else 0,
        "end_to_end_median_seconds": statistics.median(end_to_end_durations) if end_to_end_durations else 0,
        "tools": tools_median,

        # Token & Cost (averages)
        "avg_tokens": statistics.mean(all_tokens) if all_tokens else 0,
        "avg_cost_usd": statistics.mean(all_costs) if all_costs else 0,

        # Agent Behavior (average iterations, ratio for success rate)
        "avg_iterations": statistics.mean(all_iterations) if all_iterations else 0,
        "tool_success_rate": (total_tool_successes / total_tool_calls) if total_tool_calls > 0 else 0,

        # Reliability (ratios)
        "session_success_rate": (len(completed_sessions) / total_sessions) if total_sessions > 0 else 0,
        "provider_failover_rate": (total_failovers / total_llm_calls) if total_llm_calls > 0 else 0,

        # Quality Evaluation (averages)
        "relevance_avg": statistics.mean(relevance_scores) if relevance_scores else 0,
        "accuracy_avg": statistics.mean(accuracy_scores) if accuracy_scores else 0,
        "completeness_avg": statistics.mean(completeness_scores) if completeness_scores else 0,
        "source_quality_avg": statistics.mean(source_quality_scores) if source_quality_scores else 0,
    }


def create_snapshot(
    session_id: str,
    status: str,
    iteration_latencies_ms: List[float],
    tool_execution_times: Dict[str, List[float]],
    end_to_end_seconds: float,
    total_tokens: int,
    total_cost_usd: float,
    iterations_to_completion: int,
    tool_success_count: int,
    tool_failure_count: int,
    provider_failover_count: int,
    total_llm_calls: int,
    relevance: float,
    accuracy: float,
    completeness: float,
    source_quality: float,
) -> Dict[str, Any]:
    """
    Create a metrics snapshot for a session.

    Args:
        session_id: Session identifier
        status: completed/failed/cancelled
        iteration_latencies_ms: List of iteration durations
        tool_execution_times: Dict of tool -> list of execution times
        end_to_end_seconds: Total duration
        total_tokens: Total tokens used
        total_cost_usd: Total cost in USD
        iterations_to_completion: Number of ReAct cycles
        tool_success_count: Number of successful tool calls
        tool_failure_count: Number of failed tool calls
        provider_failover_count: Number of LLM provider switches
        total_llm_calls: Total LLM API calls made
        relevance: Relevance score (0-1)
        accuracy: Accuracy score (0-1)
        completeness: Completeness score (0-1)
        source_quality: Source quality score (0-1)

    Returns:
        Snapshot dictionary ready for storage
    """
    return {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": status,

        # Latency Metrics
        "iteration_latency_avg_ms": statistics.mean(iteration_latencies_ms) if iteration_latencies_ms else 0,
        "iteration_latencies_ms": iteration_latencies_ms,
        "tool_execution_times": tool_execution_times,
        "end_to_end_seconds": end_to_end_seconds,

        # Token & Cost
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,

        # Agent Behavior
        "iterations_to_completion": iterations_to_completion,
        "tool_success_count": tool_success_count,
        "tool_failure_count": tool_failure_count,
        "tool_total_calls": tool_success_count + tool_failure_count,

        # Reliability (for inception aggregation)
        "provider_failover_count": provider_failover_count,
        "total_llm_calls": total_llm_calls,

        # Quality Evaluation (0-1 scale)
        "relevance": relevance,
        "accuracy": accuracy,
        "completeness": completeness,
        "source_quality": source_quality,
    }
