"""
Research Session API Routes

Endpoints for starting, monitoring, and managing research sessions.
"""

import json
import logging
from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List, Set
import asyncio
import time

from ..models.requests import StartResearchRequest
from ..models.responses import (
    StartResearchResponse,
    SessionResponse,
    TraceResponse,
    TraceEventResponse,
    EvaluationResponse,
    EndToEndEvaluationResponse,
)
from ..exceptions import SessionNotFoundException
from ..dependencies import get_llm_manager, get_settings
from ..websocket import manager as websocket_manager
from ...database import (
    create_session,
    get_session,
    update_session,
    get_session_trace,
    get_session_evaluations,
    save_trace_event,
    save_per_step_evaluation,
    save_end_to_end_evaluation,
)
from ...agents import ResearcherAgent, EvaluatorAgent
from ...llm import LLMManager, LLMProvider
from ...config import Settings, get_llm_config_dict
from ...content import ContentPipeline
from ...metrics import MetricsCollector

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

VALID_MODEL_OVERRIDES: Dict[str, Set[str]] = {
    "openai": {
        "gpt-4.1-mini",
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "gpt-5-nano",
        "gpt-5-mini",
        "gpt-5.1",
    },
    "gemini": {
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-pro",
    },
}

router = APIRouter(prefix="/api/research", tags=["research"])

# Track active sessions
_active_sessions: Dict[str, bool] = {}


@router.post("/start", response_model=StartResearchResponse)
async def start_research(
    request: StartResearchRequest,
    background_tasks: BackgroundTasks,
    llm_manager: LLMManager = Depends(get_llm_manager),
    settings: Settings = Depends(get_settings),
):
    """
    Start a new research session.

    Creates a new session and starts research in the background.
    Returns session ID and WebSocket URL for real-time updates.
    """
    try:
        session_config = _normalize_request_config(request)
        session_settings, session_llm_manager, llm_temperature = _prepare_session_context(
            settings, llm_manager, session_config
        )
        _log_research_start(request.query, session_config, session_settings)

        # Create session in database
        session = await create_session(
            session_id=None,
            query=request.query,
            config=deepcopy(session_config) if session_config else {},
        )

        session_id = session.id
        logger.info("[Lifecycle] Create Session in DB: %s", session_id)

        # Mark session as active
        _active_sessions[session_id] = True

        # Start research in background
        background_tasks.add_task(
            _run_research_session,
            session_id,
            request.query,
            session_settings,
            session_llm_manager,
            llm_temperature,
        )

        # Return response
        return StartResearchResponse(
            session_id=session_id,
            websocket_url=f"/ws/{session_id}",
            status="running",
        )

    except Exception as e:
        logger.error(f"Failed to start research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_status(session_id: str):
    """
    Get session status and results.

    Returns session metadata, current status, and results if complete.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    return SessionResponse(
        id=session.id,
        query=session.query,
        status=session.status,
        created_at=session.created_at,
        completed_at=session.completed_at,
        total_duration_seconds=session.total_duration_seconds,
        total_iterations=session.total_iterations,
        total_cost_usd=session.total_cost_usd,
        final_report=session.final_report,
        sources=session.sources,
    )


@router.get("/{session_id}/trace", response_model=TraceResponse)
async def get_trace(session_id: str):
    """
    Get complete trace for a session.

    Returns all trace events ordered by timestamp.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    events = await get_session_trace(session_id)

    return TraceResponse(
        session_id=session_id,
        events=[
            TraceEventResponse(
                id=event.id,
                session_id=event.session_id,
                type=event.type,
                iteration=event.iteration,
                data=event.data,
                timestamp=event.timestamp,
            )
            for event in events
        ],
        total_events=len(events),
    )


@router.get("/{session_id}/evaluation", response_model=EvaluationResponse)
async def get_evaluation(session_id: str):
    """
    Get evaluation results for a session.

    Returns per-step evaluations and end-to-end evaluation.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    per_step_evals, end_to_end_eval = await get_session_evaluations(session_id)

    return EvaluationResponse(
        session_id=session_id,
        end_to_end_evaluation=(
            EndToEndEvaluationResponse(
                relevance_score=end_to_end_eval.relevance_score,
                accuracy_score=end_to_end_eval.accuracy_score,
                completeness_score=end_to_end_eval.completeness_score,
                source_quality_score=end_to_end_eval.source_quality_score,
                strengths=end_to_end_eval.strengths,
                weaknesses=end_to_end_eval.weaknesses,
                recommendations=end_to_end_eval.recommendations,
            )
            if end_to_end_eval
            else None
        ),
    )


@router.post("/{session_id}/cancel")
async def cancel_session(session_id: str):
    """
    Cancel a running research session.

    Stops the research process and marks session as cancelled.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    if session.status != "running":
        raise HTTPException(
            status_code=400, detail=f"Session is not running: {session.status}"
        )

    # Mark as inactive to stop background task
    _active_sessions[session_id] = False

    # Update session status
    await update_session(session_id, status="cancelled")

    return {"status": "cancelled", "session_id": session_id}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a research session and all associated data.

    WARNING: This permanently deletes all session data.
    """
    session = await get_session(session_id)

    if not session:
        raise SessionNotFoundException(session_id)

    # TODO: Implement cascade delete of trace events and evaluations
    # For now, just update status
    await update_session(session_id, status="deleted")

    return {"status": "deleted", "session_id": session_id}


async def _run_research_session(
    session_id: str,
    query: str,
    settings: Settings,
    llm_manager: LLMManager,
    llm_temperature: Optional[float] = None,
):
    """
    Background task to run research session.

    Args:
        session_id: Session identifier
        query: Research query
        settings: Session-resolved application settings
        llm_manager: LLM manager instance for this session
        llm_temperature: Optional override for agent reasoning temperature
    """
    try:
        logger.info(f"Starting research for session {session_id}")

        # Create content pipeline (if enabled)
        content_pipeline = None
        if settings.tools.use_content_pipeline:
            content_pipeline = ContentPipeline(
                llm_manager=llm_manager,
                top_k=10,
                max_content_length=5000,
                cache_ttl_minutes=15,
                enable_cache=True,
            )
            logger.info("Content pipeline enabled")

        # Create metrics collector
        metrics_collector = MetricsCollector(session_id=session_id)
        metrics_collector.start_session(query)

        # Create trace callback
        async def trace_callback(event_type: str, data: dict, iteration: int = None):
            try:
                await save_trace_event(
                    session_id=session_id,
                    event_type=event_type,
                    data=data,
                    iteration=iteration,
                )
            except Exception as e:
                logger.error(f"Failed to save trace event: {e}")

        # Create researcher agent
        researcher = ResearcherAgent(
            llm_manager=llm_manager,
            max_iterations=settings.research.max_iterations,
            timeout_minutes=settings.research.timeout_minutes,
            trace_callback=trace_callback,
            content_pipeline=content_pipeline,
            websocket_manager=websocket_manager,
            metrics_collector=metrics_collector,
            tool_settings=settings.tools,
            llm_temperature=llm_temperature,
        )

        # Run research (propagate persistent session_id so sockets/SSE align)
        result = await researcher.research(query, session_id=session_id)

        # Create evaluator agent
        evaluator = EvaluatorAgent(llm_manager=llm_manager)

        # Emit evaluator start event
        evaluator_trace = {"message": "Evaluator agent started"}
        evaluator_started_at = time.time()
        await save_trace_event(
            session_id=session_id,
            event_type="evaluator_start",
            data=evaluator_trace,
            iteration=None,
        )
        await websocket_manager.send_trace_event(
            session_id=session_id,
            event_type="evaluator_start",
            data=evaluator_trace,
        )

        # Run evaluation (no per-step anymore)
        logger.info("[Lifecycle] Quality Check - running EvaluatorAgent for session %s", session_id)
        eval_result = await evaluator.evaluate_research(result, evaluate_steps=False)

        evaluator_duration = time.time() - evaluator_started_at
        evaluator_complete_data = {
            "message": "Evaluator agent completed quality review",
            "duration_seconds": evaluator_duration,
            "scores": {
                "relevance": eval_result.end_to_end_evaluation.relevance_score,
                "accuracy": eval_result.end_to_end_evaluation.accuracy_score,
                "completeness": eval_result.end_to_end_evaluation.completeness_score,
                "source_quality": eval_result.end_to_end_evaluation.source_quality_score,
            },
        }
        await save_trace_event(
            session_id=session_id,
            event_type="evaluator_complete",
            data=evaluator_complete_data,
            iteration=None,
        )
        await websocket_manager.send_trace_event(
            session_id=session_id,
            event_type="evaluator_complete",
            data=evaluator_complete_data,
        )

        # Save end-to-end evaluation ONLY
        if eval_result.end_to_end_evaluation:
            await save_end_to_end_evaluation(
                session_id=session_id,
                evaluation={
                    "relevance_score": eval_result.end_to_end_evaluation.relevance_score,
                    "accuracy_score": eval_result.end_to_end_evaluation.accuracy_score,
                    "completeness_score": eval_result.end_to_end_evaluation.completeness_score,
                    "source_quality_score": eval_result.end_to_end_evaluation.source_quality_score,
                    "strengths": eval_result.end_to_end_evaluation.strengths,
                    "weaknesses": eval_result.end_to_end_evaluation.weaknesses,
                    "recommendations": eval_result.end_to_end_evaluation.recommendations,
                    "tokens_used": eval_result.end_to_end_evaluation.tokens_used,
                    "cost_usd": eval_result.end_to_end_evaluation.cost_usd,
                },
            )

        # Finalize metrics collection with evaluation data
        metrics_collector.end_session(final_report=result.report)
        evaluation_dict = {
            "relevance_score": eval_result.end_to_end_evaluation.relevance_score,
            "accuracy_score": eval_result.end_to_end_evaluation.accuracy_score,
            "completeness_score": eval_result.end_to_end_evaluation.completeness_score,
            "source_quality_score": eval_result.end_to_end_evaluation.source_quality_score,
        }
        metrics_data = metrics_collector.finalize(evaluation_result=evaluation_dict)

        # Create history snapshot
        from ...metrics.history import create_snapshot, append_run

        # Extract tool execution times from metrics_collector (not metrics_data)
        # Get actual individual execution times for accurate median calculation
        tool_times = {}
        for tool_name, executions in metrics_collector.tool_executions.items():
            # Extract individual durations in milliseconds
            tool_times[tool_name] = [exec_data["duration"] * 1000 for exec_data in executions]

        # Extract iteration latencies from metrics_collector
        iteration_latencies = [
            iter_data.get("duration", 0) * 1000 for iter_data in metrics_collector.iterations if "duration" in iter_data
        ]

        # Calculate tool success/failure counts
        tool_success_count = sum(
            len([e for e in executions if e.get("success", False)])
            for executions in metrics_collector.tool_executions.values()
        )
        tool_failure_count = sum(
            len([e for e in executions if not e.get("success", False)])
            for executions in metrics_collector.tool_executions.values()
        )

        # Get provider failover count from LLMManager
        provider_failover_count = sum(llm_manager.provider_failure_counts.values()) if hasattr(llm_manager, 'provider_failure_counts') else 0

        # Count total LLM calls
        total_llm_calls = sum(
            len(calls) for calls in metrics_collector.llm_calls.values()
        )

        snapshot = create_snapshot(
            session_id=session_id,
            status=result.status,
            iteration_latencies_ms=iteration_latencies,
            tool_execution_times=tool_times,
            end_to_end_seconds=metrics_data.total_duration_seconds,
            total_tokens=metrics_data.total_tokens_used,
            total_cost_usd=metrics_data.total_cost,
            iterations_to_completion=metrics_data.total_iterations,
            tool_success_count=tool_success_count,
            tool_failure_count=tool_failure_count,
            provider_failover_count=provider_failover_count,
            total_llm_calls=total_llm_calls,
            relevance=eval_result.end_to_end_evaluation.relevance_score,
            accuracy=eval_result.end_to_end_evaluation.accuracy_score,
            completeness=eval_result.end_to_end_evaluation.completeness_score,
            source_quality=eval_result.end_to_end_evaluation.source_quality_score,
        )

        append_run(snapshot)
        logger.info(f"Appended metrics snapshot to history for session {session_id}")
        logger.info(f"Metrics collected: ${metrics_data.total_cost:.4f}, {metrics_data.total_tokens_used} tokens")

        # Send completion via WebSocket
        await websocket_manager.send_completion(
            session_id,
            {
                "report": result.report,
                "sources": result.sources,
                "iterations": result.total_iterations,
                "duration": result.total_duration_seconds,
                "cost": result.total_cost_usd,
                "metrics": metrics_data.dict(),
                "evaluation": {
                    "relevance": eval_result.end_to_end_evaluation.relevance_score,
                    "accuracy": eval_result.end_to_end_evaluation.accuracy_score,
                    "completeness": eval_result.end_to_end_evaluation.completeness_score,
                    "sourceQuality": eval_result.end_to_end_evaluation.source_quality_score,
                    "strengths": eval_result.end_to_end_evaluation.strengths,
                    "weaknesses": eval_result.end_to_end_evaluation.weaknesses,
                    "recommendations": eval_result.end_to_end_evaluation.recommendations,
                }
            }
        )

        # Update session with results
        from datetime import datetime

        await update_session(
            session_id=session_id,
            status="completed",
            completed_at=datetime.utcnow(),
            total_duration_seconds=result.total_duration_seconds,
            total_iterations=result.total_iterations,
            total_cost_usd=result.total_cost_usd,
            final_report=result.report,
            sources=result.sources,
        )

        logger.info(f"Research completed for session {session_id}")

    except Exception as e:
        logger.error(f"Research failed for session {session_id}: {e}")

        # Send error via WebSocket
        await websocket_manager.send_error(
            session_id,
            error_message=str(e),
            error_type=type(e).__name__,
        )

        # Update session status to failed
        from datetime import datetime

        await update_session(
            session_id=session_id,
            status="failed",
            completed_at=datetime.utcnow(),
        )

    finally:
        # Remove from active sessions
        _active_sessions.pop(session_id, None)


def _normalize_request_config(request: StartResearchRequest) -> Optional[Dict[str, Any]]:
    """
    Merge legacy override fields into the structured config block.
    """
    base_config = deepcopy(request.config) if isinstance(request.config, dict) else {}

    if request.llm_provider or request.llm_model or request.temperature is not None:
        llm_cfg = base_config.setdefault("llm", {})
        if request.llm_provider:
            llm_cfg["provider"] = request.llm_provider
        if request.llm_model:
            llm_cfg["model"] = request.llm_model
        if request.temperature is not None:
            llm_cfg["temperature"] = request.temperature

    if request.max_iterations is not None:
        research_cfg = base_config.setdefault("research", {})
        research_cfg["max_iterations"] = request.max_iterations

    return base_config if base_config else None


def _prepare_session_context(
    base_settings: Settings,
    base_llm_manager: LLMManager,
    session_config: Optional[Dict[str, Any]],
) -> tuple[Settings, LLMManager, Optional[float]]:
    """
    Apply per-session overrides and build the appropriate LLM manager.
    """
    if not session_config:
        return base_settings, base_llm_manager, None

    session_settings = base_settings.copy(deep=True)

    llm_overrides = session_config.get("llm") or {}
    research_overrides = session_config.get("research") or {}

    provider_override = llm_overrides.get("provider")
    model_override = llm_overrides.get("model")
    fallback_override = llm_overrides.get("fallback_order")
    llm_temperature = llm_overrides.get("temperature")

    if provider_override:
        session_settings.llm.primary = provider_override
        # Ensure fallback order does not include the primary twice
        session_settings.llm.fallback_order = [
            name
            for name in (session_settings.llm.fallback_order or [])
            if name != provider_override
        ]

    if fallback_override:
        session_settings.llm.fallback_order = fallback_override

    target_provider = provider_override or session_settings.llm.primary
    if model_override and target_provider:
        _apply_model_override(session_settings, target_provider, model_override)

    if "max_iterations" in research_overrides:
        session_settings.research.max_iterations = research_overrides["max_iterations"]
    if "timeout_minutes" in research_overrides:
        session_settings.research.timeout_minutes = research_overrides["timeout_minutes"]

    new_manager_required = any(
        key in llm_overrides for key in ("provider", "model", "fallback_order")
    )
    session_settings.llm.fallback_order = _normalize_fallback_order(
        session_settings, session_settings.llm.primary
    )

    session_llm_manager = (
        LLMManager(get_llm_config_dict(session_settings))
        if new_manager_required
        else base_llm_manager
    )

    return session_settings, session_llm_manager, llm_temperature


def _normalize_fallback_order(
    session_settings: Settings, primary: str
) -> List[str]:
    """
    Ensure fallback order has no duplicates and prioritizes OpenRouter/OpenAI.
    """
    preferred_sequence = ["openrouter", "openai", "gemini"]
    configured = session_settings.llm.fallback_order or []
    candidate_order = configured + preferred_sequence
    final_order: List[str] = []

    for name in candidate_order:
        if name == primary:
            continue
        try:
            provider_enum = LLMProvider(name)
        except ValueError:
            continue

        provider_cfg = getattr(session_settings.llm, name, None)
        if not provider_cfg or not provider_cfg.api_key:
            continue

        if provider_enum.value not in final_order:
            final_order.append(provider_enum.value)

    return final_order


def _apply_model_override(
    session_settings: Settings, provider_name: str, requested_model: str
) -> None:
    provider_cfg = getattr(session_settings.llm, provider_name, None)
    if not provider_cfg:
        logger.warning(
            "Model override for %s ignored: provider not configured",
            provider_name,
        )
        return

    allowed = VALID_MODEL_OVERRIDES.get(provider_name)
    if allowed and requested_model not in allowed:
        logger.warning(
            "Model '%s' is not supported for provider '%s'. "
            "Allowed models: %s. Using configured default '%s' instead.",
            requested_model,
            provider_name,
            ", ".join(sorted(allowed)),
            provider_cfg.model,
        )
        return

    provider_cfg.model = requested_model


def _log_research_start(
    query: str,
    requested_config: Optional[Dict[str, Any]],
    session_settings: Settings,
) -> None:
    """
    Emit a structured log entry for each research start request.
    """
    resolved_models = {
        "openai": session_settings.llm.openai.model
        if session_settings.llm.openai
        else None,
        "gemini": session_settings.llm.gemini.model
        if session_settings.llm.gemini
        else None,
        "openrouter": session_settings.llm.openrouter.model
        if session_settings.llm.openrouter
        else None,
    }

    payload = {
        "query": query,
        "requested_overrides": requested_config or {},
        "resolved_llm": {
            "primary": session_settings.llm.primary,
            "fallback_order": session_settings.llm.fallback_order,
            "models": resolved_models,
        },
        "research": {
            "max_iterations": session_settings.research.max_iterations,
            "timeout_minutes": session_settings.research.timeout_minutes,
        },
    }

    log_block = json.dumps(payload, indent=2)
    logger.info("[Research] Start request details:\n%s", log_block)
    print(f"[Research] Start request details:\n{log_block}")
