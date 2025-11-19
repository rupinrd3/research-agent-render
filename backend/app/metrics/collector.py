"""
Metrics Collector

Collects performance metrics during research execution.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict

from .models import MetricsData, ToolMetrics, ProviderMetrics
from ..utils.text import extract_keywords, count_words, extract_domain

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects metrics during research session execution.

    Usage:
        collector = MetricsCollector(session_id="abc123")
        collector.start_session()
        collector.record_tool_execution("web_search", duration=2.5, success=True)
        collector.record_llm_call("openai", input_tokens=100, output_tokens=50, cost=0.0015)
        metrics = collector.finalize()
    """

    def __init__(self, session_id: str):
        """
        Initialize metrics collector.

        Args:
            session_id: Research session ID
        """
        self.session_id = session_id
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Timing tracking
        self.phase_start_times: Dict[str, datetime] = {}
        self.phase_durations: Dict[str, float] = {}

        # Tool tracking
        self.tool_executions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # LLM tracking
        self.llm_calls: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Content tracking
        self.sources: List[Dict[str, Any]] = []

        # Query tracking
        self.query: str = ""
        self.query_keywords: List[str] = []

        # Output tracking
        self.final_report: str = ""

        # Iteration tracking
        self.iterations: List[Dict[str, Any]] = []

        logger.info(f"MetricsCollector initialized for session: {session_id}")

    def start_session(self, query: str = "") -> None:
        """
        Mark session start.

        Args:
            query: Research query
        """
        self.start_time = datetime.utcnow()
        self.query = query
        if query:
            self.query_keywords = extract_keywords(query, max_keywords=10)
        logger.info(f"Session started: {self.session_id}")

    def end_session(self, final_report: str = "") -> None:
        """
        Mark session end.

        Args:
            final_report: Final research report
        """
        self.end_time = datetime.utcnow()
        self.final_report = final_report
        logger.info(f"Session ended: {self.session_id}")

    def start_phase(self, phase: str) -> None:
        """
        Start timing a phase (planning, execution, evaluation).

        Args:
            phase: Phase name
        """
        self.phase_start_times[phase] = datetime.utcnow()

    def end_phase(self, phase: str) -> None:
        """
        End timing a phase.

        Args:
            phase: Phase name
        """
        if phase in self.phase_start_times:
            duration = (datetime.utcnow() - self.phase_start_times[phase]).total_seconds()
            self.phase_durations[phase] = duration
            logger.debug(f"Phase '{phase}' completed in {duration:.2f}s")

    def record_tool_execution(
        self,
        tool_name: str,
        duration: float,
        success: bool,
        results_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a tool execution.

        Args:
            tool_name: Name of the tool
            duration: Execution duration in seconds
            success: Whether execution succeeded
            results_count: Number of results returned
            metadata: Additional metadata
        """
        execution_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "duration": duration,
            "success": success,
            "results_count": results_count,
            "metadata": metadata or {},
        }
        self.tool_executions[tool_name].append(execution_data)
        logger.debug(f"Tool '{tool_name}' execution recorded: {success}, {duration:.2f}s")

    def record_llm_call(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        model: Optional[str] = None,
    ) -> None:
        """
        Record an LLM API call.

        Args:
            provider: Provider name ('openai', 'gemini', 'openrouter')
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
            cost: Cost in USD
            model: Model name
        """
        call_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "model": model,
        }
        self.llm_calls[provider].append(call_data)
        logger.debug(
            f"LLM call recorded: {provider}, "
            f"{input_tokens + output_tokens} tokens, ${cost:.4f}"
        )

    def add_sources(self, sources: List[Dict[str, Any]]) -> None:
        """
        Add sources found during research.

        Args:
            sources: List of source dictionaries with 'url', 'title', etc.
        """
        self.sources.extend(sources)

    def add_iteration(self, iteration_data: Dict[str, Any]) -> None:
        """
        Record an iteration.

        Args:
            iteration_data: Iteration metadata
        """
        self.iterations.append(iteration_data)

    def finalize(self, evaluation_result: Optional[Dict[str, Any]] = None) -> MetricsData:
        """
        Finalize collection and compute metrics.

        Args:
            evaluation_result: Optional evaluation results

        Returns:
            Complete metrics data
        """
        # Compute total duration
        total_duration = 0.0
        if self.start_time and self.end_time:
            total_duration = (self.end_time - self.start_time).total_seconds()

        # Compute tool metrics
        tool_metrics = {}
        total_tool_executions = 0
        total_tool_successes = 0

        for tool_name, executions in self.tool_executions.items():
            if not executions:
                continue

            durations = [e["duration"] for e in executions]
            successes = [e for e in executions if e["success"]]
            results = sum(e.get("results_count", 0) for e in executions)

            tool_metrics[tool_name] = ToolMetrics(
                tool_name=tool_name,
                execution_count=len(executions),
                success_count=len(successes),
                failure_count=len(executions) - len(successes),
                total_duration_seconds=sum(durations),
                avg_duration_seconds=sum(durations) / len(durations) if durations else 0,
                min_duration_seconds=min(durations) if durations else 0,
                max_duration_seconds=max(durations) if durations else 0,
                results_returned=results,
            )

            total_tool_executions += len(executions)
            total_tool_successes += len(successes)

        tool_success_rate = (
            total_tool_successes / total_tool_executions if total_tool_executions > 0 else 0
        )

        # Compute LLM provider metrics
        provider_metrics = {}
        total_llm_calls = 0
        total_tokens = 0
        total_cost = 0.0

        for provider, calls in self.llm_calls.items():
            if not calls:
                continue

            input_tokens = sum(c["input_tokens"] for c in calls)
            output_tokens = sum(c["output_tokens"] for c in calls)
            tokens = input_tokens + output_tokens
            cost = sum(c["cost"] for c in calls)

            provider_metrics[provider] = ProviderMetrics(
                provider=provider,
                call_count=len(calls),
                total_input_tokens=input_tokens,
                total_output_tokens=output_tokens,
                total_tokens=tokens,
                total_cost=cost,
                avg_tokens_per_call=tokens / len(calls) if calls else 0,
                avg_cost_per_call=cost / len(calls) if calls else 0,
            )

            total_llm_calls += len(calls)
            total_tokens += tokens
            total_cost += cost

        # Compute source metrics
        unique_urls = set(s.get("url") for s in self.sources if s.get("url"))
        unique_domains = set(extract_domain(s.get("url", "")) for s in self.sources if s.get("url"))
        pdf_count = sum(1 for s in self.sources if s.get("url", "").lower().endswith(".pdf"))

        source_diversity = len(unique_domains) / len(self.sources) if self.sources else 0

        # Compute output metrics
        word_count = count_words(self.final_report)
        char_count = len(self.final_report)
        citations = self.final_report.count("[") + self.final_report.count("(http")

        # Compute iteration metrics
        avg_iteration_duration = 0.0
        if self.iterations:
            durations = [i.get("duration", 0) for i in self.iterations]
            avg_iteration_duration = sum(durations) / len(durations) if durations else 0

        # Extract quality scores from evaluation (0-1 scale, only 4 metrics)
        quality_scores = {}
        if evaluation_result:
            quality_scores = {
                "relevance_score": evaluation_result.get("relevance_score"),
                "accuracy_score": evaluation_result.get("accuracy_score"),
                "completeness_score": evaluation_result.get("completeness_score"),
                "source_quality_score": evaluation_result.get("source_quality_score"),
            }

        # Build metrics data
        metrics = MetricsData(
            session_id=self.session_id,
            # Timing
            total_duration_seconds=total_duration,
            planning_duration_seconds=self.phase_durations.get("planning", 0),
            execution_duration_seconds=self.phase_durations.get("execution", 0),
            evaluation_duration_seconds=self.phase_durations.get("evaluation", 0),
            # Iterations
            total_iterations=len(self.iterations),
            avg_iteration_duration=avg_iteration_duration,
            # Tools
            tools_used=list(self.tool_executions.keys()),
            tool_metrics=tool_metrics,
            total_tool_executions=total_tool_executions,
            tool_success_rate=tool_success_rate,
            # LLM
            providers_used=list(self.llm_calls.keys()),
            provider_metrics=provider_metrics,
            total_llm_calls=total_llm_calls,
            total_tokens_used=total_tokens,
            total_cost=total_cost,
            # Sources
            total_sources_found=len(self.sources),
            unique_sources=len(unique_urls),
            source_diversity_score=source_diversity,
            pdf_sources_count=pdf_count,
            unique_domains=len(unique_domains),
            # Output
            report_word_count=word_count,
            report_char_count=char_count,
            citations_count=citations,
            # Query
            query_keywords=self.query_keywords,
            # Quality
            **quality_scores,
        )

        logger.info(
            f"Metrics finalized for {self.session_id}: "
            f"{total_duration:.1f}s, {total_tool_executions} tools, "
            f"{total_llm_calls} LLM calls, ${total_cost:.4f}"
        )

        return metrics
