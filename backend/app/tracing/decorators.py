"""
Tracing Decorators

Provides decorators for automatic function tracing with LangSmith.
"""

import functools
import logging
from typing import Callable, Any, Optional, Dict
import inspect

from .langsmith import get_tracer

logger = logging.getLogger(__name__)


def traceable(
    name: Optional[str] = None,
    run_type: str = "chain",
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Decorator to trace a function execution with LangSmith.

    Args:
        name: Custom run name (default: function name)
        run_type: Type of run ('chain', 'llm', 'tool', 'retriever')
        tags: List of tags
        metadata: Additional metadata

    Example:
        @traceable(name="my_function", run_type="chain", tags=["custom"])
        def my_function(x, y):
            return x + y
    """

    def decorator(func: Callable) -> Callable:
        func_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()

            # If tracer not initialized or disabled, just call function
            if not tracer or not tracer.enabled:
                return func(*args, **kwargs)

            # Extract inputs
            try:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                inputs = dict(bound_args.arguments)
            except Exception:
                inputs = {"args": args, "kwargs": kwargs}

            # Start trace run
            run_id = tracer.start_run(
                name=func_name,
                run_type=run_type,
                inputs=inputs,
                tags=tags,
                metadata=metadata,
            )

            try:
                # Execute function
                result = func(*args, **kwargs)

                # End trace run with outputs
                if run_id:
                    tracer.end_run(run_id, outputs={"result": result})

                return result

            except Exception as e:
                # End trace run with error
                if run_id:
                    tracer.end_run(run_id, error=str(e))
                raise

        return wrapper

    return decorator


def trace_async(
    name: Optional[str] = None,
    run_type: str = "chain",
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Decorator to trace an async function execution with LangSmith.

    Args:
        name: Custom run name (default: function name)
        run_type: Type of run ('chain', 'llm', 'tool', 'retriever')
        tags: List of tags
        metadata: Additional metadata

    Example:
        @trace_async(name="async_function", run_type="chain")
        async def async_function(x, y):
            return x + y
    """

    def decorator(func: Callable) -> Callable:
        func_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()

            # If tracer not initialized or disabled, just call function
            if not tracer or not tracer.enabled:
                return await func(*args, **kwargs)

            # Extract inputs
            try:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                inputs = dict(bound_args.arguments)
            except Exception:
                inputs = {"args": args, "kwargs": kwargs}

            # Start trace run
            run_id = tracer.start_run(
                name=func_name,
                run_type=run_type,
                inputs=inputs,
                tags=tags,
                metadata=metadata,
            )

            try:
                # Execute async function
                result = await func(*args, **kwargs)

                # End trace run with outputs
                if run_id:
                    tracer.end_run(run_id, outputs={"result": result})

                return result

            except Exception as e:
                # End trace run with error
                if run_id:
                    tracer.end_run(run_id, error=str(e))
                raise

        return wrapper

    return decorator


def trace_llm_call(name: Optional[str] = None):
    """
    Decorator specifically for LLM API calls.

    Args:
        name: Custom run name

    Example:
        @trace_llm_call(name="research_completion")
        async def call_llm(messages):
            return await llm.complete(messages)
    """
    return trace_async(name=name, run_type="llm", tags=["llm"])


def trace_tool_call(tool_name: str):
    """
    Decorator specifically for tool executions.

    Args:
        tool_name: Name of the tool

    Example:
        @trace_tool_call("web_search")
        async def web_search(query):
            # Search implementation
            pass
    """
    return trace_async(name=tool_name, run_type="tool", tags=["tool", tool_name])
