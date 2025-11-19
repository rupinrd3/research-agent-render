"""
LangSmith Tracing Integration

Provides integration with LangSmith for comprehensive tracing and observability.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Try to import LangSmith (optional dependency)
try:
    from langsmith import Client
    from langsmith.run_helpers import traceable as langsmith_traceable
    from langsmith.run_trees import RunTree

    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logger.warning(
        "LangSmith not installed. Tracing features will be disabled. "
        "Install with: pip install langsmith"
    )


class LangSmithTracer:
    """
    LangSmith tracing integration.

    Provides hierarchical tracing of research sessions with automatic
    upload to LangSmith platform.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_name: str = "agentic-research",
        enabled: bool = True,
    ):
        """
        Initialize LangSmith tracer.

        Args:
            api_key: LangSmith API key (or use LANGSMITH_API_KEY env var)
            project_name: Project name in LangSmith
            enabled: Enable/disable tracing
        """
        self.enabled = enabled and LANGSMITH_AVAILABLE
        self.project_name = project_name
        self.client: Optional[Any] = None
        self.active_runs: Dict[str, Any] = {}

        if not self.enabled:
            if not LANGSMITH_AVAILABLE:
                logger.info("LangSmith tracing disabled (library not installed)")
            else:
                logger.info("LangSmith tracing disabled by configuration")
            return

        # Get API key
        self.api_key = api_key or os.getenv("LANGSMITH_API_KEY")

        if not self.api_key:
            logger.warning(
                "LangSmith API key not provided. Tracing disabled. "
                "Set LANGSMITH_API_KEY environment variable."
            )
            self.enabled = False
            return

        try:
            # Initialize LangSmith client
            self.client = Client(api_key=self.api_key)

            # Set environment variables for langsmith decorator
            os.environ["LANGSMITH_API_KEY"] = self.api_key
            os.environ["LANGSMITH_PROJECT"] = self.project_name

            logger.info(f"LangSmith tracing enabled (project: {project_name})")

        except Exception as e:
            logger.error(f"Failed to initialize LangSmith client: {e}")
            self.enabled = False

    def start_run(
        self,
        name: str,
        run_type: str = "chain",
        inputs: Optional[Dict[str, Any]] = None,
        parent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Start a new trace run.

        Args:
            name: Run name
            run_type: Type of run ('chain', 'llm', 'tool', 'retriever')
            inputs: Input data
            parent_run_id: Parent run ID for hierarchical tracing
            tags: List of tags
            metadata: Additional metadata

        Returns:
            Run ID if successful, None otherwise
        """
        if not self.enabled or not self.client:
            return None

        try:
            run = RunTree(
                name=name,
                run_type=run_type,
                inputs=inputs or {},
                project_name=self.project_name,
                tags=tags or [],
                extra=metadata or {},
                parent_run=self.active_runs.get(parent_run_id) if parent_run_id else None,
            )

            run.post()  # Upload to LangSmith
            run_id = str(run.id)

            self.active_runs[run_id] = run

            logger.debug(f"Started LangSmith run: {name} (ID: {run_id})")
            return run_id

        except Exception as e:
            logger.error(f"Failed to start LangSmith run: {e}")
            return None

    def end_run(
        self,
        run_id: str,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        End a trace run.

        Args:
            run_id: Run ID to end
            outputs: Output data
            error: Error message if run failed
        """
        if not self.enabled or run_id not in self.active_runs:
            return

        try:
            run = self.active_runs[run_id]

            if error:
                run.end(error=error)
            else:
                run.end(outputs=outputs or {})

            run.patch()  # Update in LangSmith

            # Remove from active runs
            del self.active_runs[run_id]

            logger.debug(f"Ended LangSmith run: {run_id}")

        except Exception as e:
            logger.error(f"Failed to end LangSmith run: {e}")

    def log_event(
        self,
        run_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Log an event within a run.

        Args:
            run_id: Run ID
            event_type: Event type
            data: Event data
        """
        if not self.enabled or run_id not in self.active_runs:
            return

        try:
            run = self.active_runs[run_id]

            # Add event to run metadata
            if not hasattr(run, "extra"):
                run.extra = {}

            if "events" not in run.extra:
                run.extra["events"] = []

            run.extra["events"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": event_type,
                "data": data,
            })

            run.patch()  # Update in LangSmith

        except Exception as e:
            logger.error(f"Failed to log event to LangSmith: {e}")

    @contextmanager
    def trace_context(
        self,
        name: str,
        run_type: str = "chain",
        inputs: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Context manager for tracing a block of code.

        Args:
            name: Run name
            run_type: Type of run
            inputs: Input data
            tags: List of tags

        Example:
            with tracer.trace_context("research_session", inputs={"query": "..."}):
                # Your code here
                pass
        """
        run_id = self.start_run(name, run_type, inputs, tags=tags)

        try:
            yield run_id
        except Exception as e:
            if run_id:
                self.end_run(run_id, error=str(e))
            raise
        else:
            if run_id:
                self.end_run(run_id, outputs={"status": "success"})

    def trace_research_session(
        self,
        session_id: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Start tracing a research session.

        Args:
            session_id: Research session ID
            query: Research query
            metadata: Additional metadata

        Returns:
            Run ID for the session
        """
        return self.start_run(
            name=f"research_session_{session_id}",
            run_type="chain",
            inputs={"query": query, "session_id": session_id},
            tags=["research", "session"],
            metadata=metadata,
        )

    def trace_iteration(
        self,
        session_run_id: str,
        iteration: int,
        thought: str,
        action: str,
        action_input: Dict[str, Any],
    ) -> Optional[str]:
        """
        Trace a ReAct iteration.

        Args:
            session_run_id: Parent session run ID
            iteration: Iteration number
            thought: Agent's thought
            action: Action taken
            action_input: Action parameters

        Returns:
            Run ID for the iteration
        """
        return self.start_run(
            name=f"iteration_{iteration}",
            run_type="chain",
            inputs={
                "thought": thought,
                "action": action,
                "action_input": action_input,
            },
            parent_run_id=session_run_id,
            tags=["iteration", f"iteration_{iteration}"],
        )

    def trace_tool_execution(
        self,
        iteration_run_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
    ) -> Optional[str]:
        """
        Trace a tool execution.

        Args:
            iteration_run_id: Parent iteration run ID
            tool_name: Tool name
            tool_input: Tool parameters

        Returns:
            Run ID for the tool execution
        """
        return self.start_run(
            name=tool_name,
            run_type="tool",
            inputs=tool_input,
            parent_run_id=iteration_run_id,
            tags=["tool", tool_name],
        )

    def get_run_url(self, run_id: str) -> Optional[str]:
        """
        Get LangSmith UI URL for a run.

        Args:
            run_id: Run ID

        Returns:
            URL to view run in LangSmith UI
        """
        if not self.enabled or not self.client:
            return None

        try:
            return f"https://smith.langchain.com/o/default/projects/{self.project_name}/r/{run_id}"
        except Exception:
            return None


# Global tracer instance
_global_tracer: Optional[LangSmithTracer] = None


def init_langsmith(
    api_key: Optional[str] = None,
    project_name: str = "agentic-research",
    enabled: bool = True,
) -> LangSmithTracer:
    """
    Initialize global LangSmith tracer.

    Args:
        api_key: LangSmith API key
        project_name: Project name
        enabled: Enable/disable tracing

    Returns:
        LangSmithTracer instance
    """
    global _global_tracer
    _global_tracer = LangSmithTracer(
        api_key=api_key,
        project_name=project_name,
        enabled=enabled,
    )
    return _global_tracer


def get_tracer() -> Optional[LangSmithTracer]:
    """
    Get global LangSmith tracer instance.

    Returns:
        LangSmithTracer instance or None if not initialized
    """
    return _global_tracer
