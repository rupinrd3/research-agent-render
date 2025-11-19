"""
Metrics Analyzer

Analyzes and summarizes metrics across research sessions.
"""

import logging
from typing import List, Dict, Any
from collections import Counter

from .models import MetricsData, MetricsSummary

logger = logging.getLogger(__name__)


class MetricsAnalyzer:
    """
    Analyzes metrics across multiple research sessions.

    Computes aggregate statistics, trends, and insights.
    """

    @staticmethod
    def compute_summary(metrics_list: List[MetricsData]) -> MetricsSummary:
        """
        Compute summary statistics across multiple sessions.

        Args:
            metrics_list: List of metrics from different sessions

        Returns:
            Summary statistics
        """
        if not metrics_list:
            return MetricsSummary(
                total_sessions=0,
                avg_duration_seconds=0,
                avg_iterations=0,
                avg_cost_per_session=0,
                total_cost=0,
                most_used_tools=[],
                most_used_providers=[],
                avg_quality_score=0,
                sessions_analyzed=0,
            )

        # Aggregate metrics
        total_sessions = len(metrics_list)
        total_duration = sum(m.total_duration_seconds for m in metrics_list)
        total_iterations = sum(m.total_iterations for m in metrics_list)
        total_cost = sum(m.total_cost for m in metrics_list)

        # Tool usage
        tool_counter = Counter()
        for m in metrics_list:
            for tool in m.tools_used:
                tool_counter[tool] += 1

        most_used_tools = [tool for tool, _ in tool_counter.most_common(5)]

        # Provider usage
        provider_counter = Counter()
        for m in metrics_list:
            for provider in m.providers_used:
                provider_counter[provider] += 1

        most_used_providers = [p for p, _ in provider_counter.most_common(3)]

        # Quality scores
        quality_scores = [
            m.overall_quality_score
            for m in metrics_list
            if m.overall_quality_score is not None
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        summary = MetricsSummary(
            total_sessions=total_sessions,
            avg_duration_seconds=total_duration / total_sessions,
            avg_iterations=total_iterations / total_sessions,
            avg_cost_per_session=total_cost / total_sessions,
            total_cost=total_cost,
            most_used_tools=most_used_tools,
            most_used_providers=most_used_providers,
            avg_quality_score=avg_quality,
            sessions_analyzed=total_sessions,
        )

        logger.info(
            f"Summary computed: {total_sessions} sessions, "
            f"avg ${summary.avg_cost_per_session:.4f}/session"
        )

        return summary

    @staticmethod
    def analyze_tool_performance(metrics_list: List[MetricsData]) -> Dict[str, Any]:
        """
        Analyze tool performance across sessions.

        Args:
            metrics_list: List of metrics from different sessions

        Returns:
            Dict with tool performance analysis
        """
        tool_stats: Dict[str, Dict[str, Any]] = {}

        for metrics in metrics_list:
            for tool_name, tool_metrics in metrics.tool_metrics.items():
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {
                        "total_executions": 0,
                        "total_successes": 0,
                        "total_failures": 0,
                        "total_duration": 0,
                        "total_results": 0,
                        "sessions_used": 0,
                    }

                stats = tool_stats[tool_name]
                stats["total_executions"] += tool_metrics.execution_count
                stats["total_successes"] += tool_metrics.success_count
                stats["total_failures"] += tool_metrics.failure_count
                stats["total_duration"] += tool_metrics.total_duration_seconds
                stats["total_results"] += tool_metrics.results_returned
                stats["sessions_used"] += 1

        # Compute averages
        for tool_name, stats in tool_stats.items():
            if stats["total_executions"] > 0:
                stats["success_rate"] = stats["total_successes"] / stats["total_executions"]
                stats["avg_duration"] = stats["total_duration"] / stats["total_executions"]
                stats["avg_results"] = stats["total_results"] / stats["total_executions"]
            else:
                stats["success_rate"] = 0
                stats["avg_duration"] = 0
                stats["avg_results"] = 0

        return tool_stats

    @staticmethod
    def analyze_cost_breakdown(metrics_list: List[MetricsData]) -> Dict[str, Any]:
        """
        Analyze cost breakdown by provider.

        Args:
            metrics_list: List of metrics from different sessions

        Returns:
            Dict with cost analysis by provider
        """
        provider_costs: Dict[str, Dict[str, Any]] = {}

        for metrics in metrics_list:
            for provider, provider_metrics in metrics.provider_metrics.items():
                if provider not in provider_costs:
                    provider_costs[provider] = {
                        "total_cost": 0,
                        "total_calls": 0,
                        "total_tokens": 0,
                        "sessions": 0,
                    }

                costs = provider_costs[provider]
                costs["total_cost"] += provider_metrics.total_cost
                costs["total_calls"] += provider_metrics.call_count
                costs["total_tokens"] += provider_metrics.total_tokens
                costs["sessions"] += 1

        # Compute averages
        for provider, costs in provider_costs.items():
            if costs["total_calls"] > 0:
                costs["avg_cost_per_call"] = costs["total_cost"] / costs["total_calls"]
                costs["avg_tokens_per_call"] = costs["total_tokens"] / costs["total_calls"]
            else:
                costs["avg_cost_per_call"] = 0
                costs["avg_tokens_per_call"] = 0

            if costs["sessions"] > 0:
                costs["avg_cost_per_session"] = costs["total_cost"] / costs["sessions"]
            else:
                costs["avg_cost_per_session"] = 0

        return provider_costs

    @staticmethod
    def get_top_sessions(
        metrics_list: List[MetricsData],
        criterion: str = "quality",
        limit: int = 5,
    ) -> List[MetricsData]:
        """
        Get top sessions by various criteria.

        Args:
            metrics_list: List of metrics from different sessions
            criterion: Sort criterion ('quality', 'cost', 'speed', 'completeness')
            limit: Number of top sessions to return

        Returns:
            List of top metrics sorted by criterion
        """
        if not metrics_list:
            return []

        if criterion == "quality":
            # Sort by overall quality score (descending)
            sorted_metrics = sorted(
                [m for m in metrics_list if m.overall_quality_score is not None],
                key=lambda m: m.overall_quality_score or 0,
                reverse=True,
            )
        elif criterion == "cost":
            # Sort by cost (ascending - cheaper is better)
            sorted_metrics = sorted(
                metrics_list,
                key=lambda m: m.total_cost,
            )
        elif criterion == "speed":
            # Sort by duration (ascending - faster is better)
            sorted_metrics = sorted(
                metrics_list,
                key=lambda m: m.total_duration_seconds,
            )
        elif criterion == "completeness":
            # Sort by completeness score (descending)
            sorted_metrics = sorted(
                [m for m in metrics_list if m.completeness_score is not None],
                key=lambda m: m.completeness_score or 0,
                reverse=True,
            )
        else:
            sorted_metrics = metrics_list

        return sorted_metrics[:limit]

    @staticmethod
    def analyze_quality_trends(
        metrics_list: List[MetricsData],
    ) -> Dict[str, Any]:
        """
        Analyze quality score trends and distributions.

        Args:
            metrics_list: List of metrics from different sessions

        Returns:
            Dict with quality trend analysis
        """
        # Extract quality scores
        relevance_scores = [
            m.relevance_score
            for m in metrics_list
            if m.relevance_score is not None
        ]
        accuracy_scores = [
            m.accuracy_score
            for m in metrics_list
            if m.accuracy_score is not None
        ]
        completeness_scores = [
            m.completeness_score
            for m in metrics_list
            if m.completeness_score is not None
        ]
        overall_scores = [
            m.overall_quality_score
            for m in metrics_list
            if m.overall_quality_score is not None
        ]

        def compute_stats(scores: List[float]) -> Dict[str, float]:
            if not scores:
                return {"avg": 0, "min": 0, "max": 0, "count": 0}
            return {
                "avg": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "count": len(scores),
            }

        return {
            "relevance": compute_stats(relevance_scores),
            "accuracy": compute_stats(accuracy_scores),
            "completeness": compute_stats(completeness_scores),
            "overall": compute_stats(overall_scores),
        }
