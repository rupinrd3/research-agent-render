# Metrics & Evaluation Implementation Plan (Revised v2)

## 1. Goals & Scope

### ⚠️ IMPORTANT VERIFICATION BEFORE IMPLEMENTATION
Before starting implementation, verify the following:
1. **MetricsCollector structure**: Confirm that `metrics_collector.iterations` contains `duration` field
2. **WebSocket payload**: Verify `metrics_data` structure matches assumptions in frontend extraction
3. **Add Tailwind animation**: Ensure `animate-in fade-in duration-300` is available (or add to tailwind.config.js)
4. **LLMManager failover tracking**: Verify that `LLMManager` has `provider_failure_counts` attribute for tracking failovers
5. **Tool execution structure**: Confirm that `metrics_collector.tool_executions[tool]` items have `success` boolean field

### Core Objectives
- Implement **exact metrics** specified by user (no extras)
- Change evaluation scale from **0-10 to 0-1**
- Fix data loss issues (fields being dropped during save)
- Create simple JSON-based history for ≤200 sessions
- Build modern, polished UI matching existing dark theme
- **Delete** Enhanced Evaluator (not needed)

### User-Specified Metrics (Complete List)

**Current Run:**
1. **Latency Metrics**
   - Iteration Latency: Average time per ReAct cycle (ms)
   - Tool Execution Time: Per-tool average (ms)
   - End-to-End Duration: Total research time (seconds)

2. **Token & Cost Tracking**
   - Cumulative Token Usage: Total across all iterations
   - Cost per Research Session: Real-time USD tracking

3. **Agent Behavior Metrics**
   - Iterations to Completion: How many cycles needed
   - Tool Success Rate: % of successful vs. failed tool calls

4. **Quality Metrics (LLM-as-Judge, 0-1 scale)**
   - Relevance Score: Report addresses the query
   - Accuracy Score: Factual correctness
   - Completeness Score: Coverage of key aspects
   - Source Quality Score: Credibility of citations

5. **Reliability Metrics** (Inception only)
   - Success Rate: % of completed vs. failed research sessions
   - Provider Failover Events: Frequency of switching LLM providers

**Inception Till Date:**
- Latency: Median values
- Tokens/Cost: Average values
- Iterations: Average value
- Tool Success Rate: Ratio on total values (successes / total calls)
- Quality Scores: Average values
- Success Rate: Ratio on total values (completed / total sessions)
- Provider Failovers: Ratio on total values (failovers / total LLM calls)

### Metrics Being REMOVED
- ❌ Coherence score
- ❌ Recency score
- ❌ Overall score (can be computed client-side if needed)
- ❌ Per-phase token breakdown
- ❌ Per-step evaluation (tool appropriateness, execution quality, progress, information gain, efficiency)
- ❌ All Enhanced Evaluator metrics (hallucinations, contradictions, confidence, quality tiers)

---

## 2. Backend Implementation

### 2.1 Delete Enhanced Evaluator

**Action:** Complete removal of unused code

**Files to Delete:**
- `backend/app/agents/enhanced_evaluator.py`

**Files to Modify:**
- `backend/app/agents/__init__.py`
  - Remove: `from .enhanced_evaluator import (...)`
  - Remove: EnhancedEvaluator from `__all__`

**Database Cleanup:**
- No tables exist for EnhancedEvaluator, so no DB changes needed

---

### 2.2 Simplify EvaluatorAgent (0-1 Scale, 4 Metrics Only)

**File:** `backend/app/agents/evaluator_agent.py`

#### Changes Required:

**A. Remove Per-Step Evaluation Entirely**

Delete:
- `PER_STEP_PROMPT` constant
- `evaluate_step()` method
- All per-step logic from `evaluate_research()`

**B. Update End-to-End Prompt (0-1 Scale)**

```python
END_TO_END_PROMPT = """Evaluate this research comprehensively.

Query: {query}

Final Report:
{report}

Sources ({num_sources}):
{sources}

Rate each dimension on a 0-1 scale (0.0 = poor, 1.0 = excellent):

1. Relevance (0-1): How well does the report answer the query?
2. Accuracy (0-1): Is the information factually correct?
3. Completeness (0-1): Are all key aspects of the query covered?
4. Source Quality (0-1): Are sources authoritative and credible?

Also provide:
- Strengths (3-5 points)
- Weaknesses (3-5 points)
- Recommendations for improvement (3-5 points)

Format as JSON:
{{
    "relevance_score": 0.XX,
    "accuracy_score": 0.XX,
    "completeness_score": 0.XX,
    "source_quality_score": 0.XX,
    "strengths": ["...", "...", "..."],
    "weaknesses": ["...", "...", "..."],
    "recommendations": ["...", "...", "..."]
}}"""
```

**C. Update evaluate_end_to_end() Method**

```python
async def evaluate_end_to_end(
    self, result: ResearchResult
) -> EndToEndEval:
    """
    Evaluate complete research output.

    Args:
        result: Research result to evaluate

    Returns:
        EndToEndEval with 4 quality scores (0-1 scale)
    """
    try:
        logger.info("Performing end-to-end evaluation")

        # Format sources
        sources_str = "\n".join(
            f"- {source}" for source in result.sources[:20]
        )

        prompt = self.END_TO_END_PROMPT.format(
            query=result.query,
            report=result.report[:5000],  # Limit size
            num_sources=len(result.sources),
            sources=sources_str,
        )

        response = await self.llm.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
            require_content=True,
        )

        # Parse JSON response
        eval_data = self._parse_json_response(response["content"])

        return EndToEndEval(
            relevance_score=self._clamp_score(eval_data.get("relevance_score", 0.5)),
            accuracy_score=self._clamp_score(eval_data.get("accuracy_score", 0.5)),
            completeness_score=self._clamp_score(eval_data.get("completeness_score", 0.5)),
            source_quality_score=self._clamp_score(eval_data.get("source_quality_score", 0.5)),
            strengths=eval_data.get("strengths", []),
            weaknesses=eval_data.get("weaknesses", []),
            recommendations=eval_data.get("recommendations", []),
            tokens_used=response["usage"]["total_tokens"],
            cost_usd=self.llm.estimate_cost(
                response["usage"]["input_tokens"],
                response["usage"]["output_tokens"],
            ),
        )

    except Exception as e:
        logger.error(f"End-to-end evaluation failed: {e}")
        # Return neutral scores on failure
        return EndToEndEval(
            relevance_score=0.5,
            accuracy_score=0.5,
            completeness_score=0.5,
            source_quality_score=0.5,
            strengths=[],
            weaknesses=[f"Evaluation failed: {str(e)}"],
            recommendations=[],
            tokens_used=0,
            cost_usd=0.0,
        )

def _clamp_score(self, score: float) -> float:
    """Ensure score is between 0 and 1."""
    return max(0.0, min(1.0, float(score)))
```

**D. Update evaluate_research() - Remove Per-Step**

```python
async def evaluate_research(
    self, result: ResearchResult, evaluate_steps: bool = False  # Ignored now
) -> EvaluationResult:
    """
    Perform end-to-end evaluation only.

    Args:
        result: Research result to evaluate
        evaluate_steps: Deprecated, ignored

    Returns:
        EvaluationResult with end-to-end evaluation
    """
    logger.info(f"Evaluating research session: {result.session_id}")

    # Only end-to-end evaluation now
    end_to_end_eval = await self.evaluate_end_to_end(result)

    return EvaluationResult(
        session_id=result.session_id,
        end_to_end_evaluation=end_to_end_eval,
    )
```

---

### 2.3 Update Data Models

**File:** `backend/app/agents/models.py`

#### Remove PerStepEval Dataclass

Delete entire `PerStepEval` class (lines 49-63)

#### Update EndToEndEval Dataclass

```python
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
```

#### Update EvaluationResult Dataclass

```python
@dataclass
class EvaluationResult:
    """
    Complete evaluation results for a research session.
    """

    session_id: str
    end_to_end_evaluation: EndToEndEval
```

---

### 2.4 Update Database Models

**File:** `backend/app/database/models.py`

#### Remove PerStepEvaluation Table

Delete entire `PerStepEvaluation` class (lines 104-139) and its relationship from `ResearchSession`

#### Update EndToEndEvaluation Table

```python
class EndToEndEvaluation(Base):
    """
    End-to-end evaluation model.

    Stores 0-1 scale quality scores for the final research output.
    """

    __tablename__ = "end_to_end_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String, ForeignKey("research_sessions.id"), nullable=False, unique=True
    )

    # Quality scores (0-1 scale)
    relevance_score = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    source_quality_score = Column(Float, nullable=True)

    # Qualitative feedback
    strengths = Column(JSON, nullable=True)  # List of strings
    weaknesses = Column(JSON, nullable=True)  # List of strings
    recommendations = Column(JSON, nullable=True)  # List of strings

    # Evaluation cost
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship(
        "ResearchSession", back_populates="end_to_end_evaluation"
    )
```

#### Update ResearchSession Relationships

```python
class ResearchSession(Base):
    # ... existing fields ...

    # Remove this relationship:
    # per_step_evaluations = relationship(...)

    # Keep only:
    end_to_end_evaluation = relationship(
        "EndToEndEvaluation",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
```

---

### 2.5 Metrics History Storage

**File:** `backend/app/metrics/history.py` (NEW)

Simple JSON file storage for up to 200 sessions.

```python
"""
Metrics History Storage

Simple JSON file-based storage for session metrics history.
Designed for small-scale usage (≤200 sessions).
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
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
```

**Dependencies:** Add `filelock` to `requirements.txt`

```
filelock==3.13.1
```

---

### 2.6 Update Research Workflow

**File:** `backend/app/api/routes/research.py`

#### Update _run_research_session()

```python
async def _run_research_session(
    session_id: str,
    query: str,
    settings: Settings,
    llm_manager: LLMManager,
    llm_temperature: Optional[float] = None,
):
    """Background task to run research session."""
    try:
        logger.info(f"Starting research for session {session_id}")

        # ... existing setup code ...

        # Run research
        result = await researcher.research(query, session_id=session_id)

        # Create evaluator agent
        evaluator = EvaluatorAgent(llm_manager=llm_manager)

        # Run evaluation (no per-step anymore)
        logger.info("[Lifecycle] Quality Check - running EvaluatorAgent for session %s", session_id)
        eval_result = await evaluator.evaluate_research(result, evaluate_steps=False)

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

        # Finalize metrics collection
        metrics_collector.end_session(final_report=result.report)
        metrics_data = metrics_collector.finalize()

        # Create history snapshot
        from ..metrics.history import create_snapshot, append_run

        # Extract tool execution times from metrics_collector (not metrics_data)
        # Get actual individual execution times for accurate median calculation
        tool_times = {}
        for tool_name, executions in metrics_collector.tool_executions.items():
            # Extract individual durations in milliseconds
            tool_times[tool_name] = [exec_data["duration"] * 1000 for exec_data in executions]

        # Extract iteration latencies from metrics_collector
        # Note: Verify that iterations dict has "duration" field
        iteration_latencies = [
            iter_data["duration"] * 1000 for iter_data in metrics_collector.iterations if "duration" in iter_data
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
        # Note: LLMManager tracks failovers in provider_failure_counts dict
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
            end_to_end_seconds=result.total_duration_seconds,
            total_tokens=result.total_tokens,
            total_cost_usd=result.total_cost_usd,
            iterations_to_completion=result.total_iterations,
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
        # ... existing error handling ...
```

---

### 2.7 New Metrics API Endpoint

**File:** `backend/app/api/routes/metrics.py` (NEW)

```python
"""
Metrics API Routes

Provides endpoints for fetching current and historical metrics.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ...metrics.history import load_history, compute_aggregates
from ..models.responses import MetricsSummaryResponse

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary():
    """
    Get metrics summary including inception till date aggregates.

    Returns:
        Current session metrics (if available) and historical aggregates
    """
    try:
        # Load history
        history = load_history()

        # Compute aggregates
        inception = compute_aggregates(history)

        return MetricsSummaryResponse(
            inception=inception,
            total_sessions=len(history),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute metrics: {str(e)}"
        )
```

**File:** `backend/app/api/models/responses.py`

Add new response models:

```python
class MetricsSummaryResponse(BaseModel):
    """Metrics summary response."""

    inception: Dict[str, Any]  # Aggregated historical metrics
    total_sessions: int
```

**File:** `backend/app/api/main.py`

Register new router:

```python
from .routes import research, history, export, config, metrics

# ... existing code ...

app.include_router(metrics.router)
```

---

### 2.8 Update Database Operations

**File:** `backend/app/database/database.py`

Remove `save_per_step_evaluation()` function entirely.

Update `save_end_to_end_evaluation()` to handle new schema:

```python
async def save_end_to_end_evaluation(
    session_id: str,
    evaluation: Dict[str, Any],
) -> EndToEndEvaluation:
    """
    Save end-to-end evaluation.

    Args:
        session_id: Session ID
        evaluation: Evaluation data with 0-1 scale scores

    Returns:
        Created evaluation record
    """
    async with get_database() as db:
        # Check if evaluation already exists
        existing = await db.execute(
            select(EndToEndEvaluation).where(
                EndToEndEvaluation.session_id == session_id
            )
        )
        existing_eval = existing.scalar_one_or_none()

        if existing_eval:
            # Update existing
            for key, value in evaluation.items():
                setattr(existing_eval, key, value)
            await db.commit()
            await db.refresh(existing_eval)
            return existing_eval
        else:
            # Create new
            eval_record = EndToEndEvaluation(
                session_id=session_id,
                relevance_score=evaluation.get("relevance_score"),
                accuracy_score=evaluation.get("accuracy_score"),
                completeness_score=evaluation.get("completeness_score"),
                source_quality_score=evaluation.get("source_quality_score"),
                strengths=evaluation.get("strengths"),
                weaknesses=evaluation.get("weaknesses"),
                recommendations=evaluation.get("recommendations"),
                tokens_used=evaluation.get("tokens_used"),
                cost_usd=evaluation.get("cost_usd"),
            )
            db.add(eval_record)
            await db.commit()
            await db.refresh(eval_record)
            return eval_record
```

Update `get_session_evaluations()`:

```python
async def get_session_evaluations(session_id: str):
    """
    Get evaluations for a session.

    Args:
        session_id: Session ID

    Returns:
        Tuple of (empty list, end_to_end_evaluation)
        Note: per_step is always empty now
    """
    async with get_database() as db:
        # Get end-to-end evaluation
        result = await db.execute(
            select(EndToEndEvaluation).where(
                EndToEndEvaluation.session_id == session_id
            )
        )
        end_to_end_eval = result.scalar_one_or_none()

        return [], end_to_end_eval  # Per-step is always empty
```

---

## 3. Frontend Implementation

### 3.1 Update Types

**File:** `frontend/src/types/index.ts`

Remove or deprecate per-step types, update evaluation types:

```typescript
/**
 * End-to-end evaluation (0-1 scale)
 */
export interface EndToEndEvaluation {
  relevance: number; // 0-1
  accuracy: number; // 0-1
  completeness: number; // 0-1
  sourceQuality: number; // 0-1
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

/**
 * Current run metrics
 */
export interface CurrentRunMetrics {
  // Latency
  iterationLatencyAvg: number; // ms
  iterationLatencies: number[]; // ms array
  toolExecutionTimes: Record<string, number>; // tool -> avg ms
  endToEndSeconds: number;

  // Token & Cost
  totalTokens: number;
  totalCostUsd: number;

  // Agent Behavior
  iterationsToCompletion: number;
  toolSuccessRate: number; // 0-1

  // Evaluation
  evaluation: EndToEndEvaluation;
}

/**
 * Historical aggregate metrics
 */
export interface InceptionMetrics {
  totalSessions: number;
  completedSessions: number;

  // Latency (medians)
  iterationLatencyMedian: number; // ms
  endToEndMedian: number; // seconds
  tools: Record<string, number>; // tool -> median ms

  // Token & Cost (averages)
  avgTokens: number;
  avgCostUsd: number;

  // Agent Behavior
  avgIterations: number;
  toolSuccessRate: number; // 0-1

  // Reliability
  sessionSuccessRate: number; // 0-1
  providerFailoverRate: number; // 0-1

  // Quality (averages, 0-1)
  relevanceAvg: number;
  accuracyAvg: number;
  completenessAvg: number;
  sourceQualityAvg: number;
}

/**
 * Metrics state
 */
export interface MetricsState {
  current: CurrentRunMetrics | null;
  inception: InceptionMetrics | null;
}
```

---

### 3.2 Update Store

**File:** `frontend/src/store/research-store.ts`

Add metrics to state:

```typescript
interface ResearchState {
  // ... existing state ...

  // Metrics
  metrics: MetricsState;

  // Actions
  setMetrics: (metrics: MetricsState) => void;
  fetchMetricsSummary: () => Promise<void>;
}

// In create():
metrics: {
  current: null,
  inception: null,
},

setMetrics: (metrics) => {
  set({ metrics });
},

fetchMetricsSummary: async () => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/metrics/summary`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch metrics');
    }

    const data = await response.json();

    set((state) => ({
      metrics: {
        current: state.metrics.current, // Keep current
        inception: {
          totalSessions: data.inception.total_sessions,
          completedSessions: data.inception.completed_sessions,
          iterationLatencyMedian: data.inception.iteration_latency_median_ms,
          endToEndMedian: data.inception.end_to_end_median_seconds,
          tools: data.inception.tools,
          avgTokens: data.inception.avg_tokens,
          avgCostUsd: data.inception.avg_cost_usd,
          avgIterations: data.inception.avg_iterations,
          toolSuccessRate: data.inception.tool_success_rate,
          sessionSuccessRate: data.inception.session_success_rate,
          providerFailoverRate: data.inception.provider_failover_rate,
          relevanceAvg: data.inception.relevance_avg,
          accuracyAvg: data.inception.accuracy_avg,
          completenessAvg: data.inception.completeness_avg,
          sourceQualityAvg: data.inception.source_quality_avg,
        },
      },
    }));
  } catch (error) {
    console.error('Failed to fetch metrics summary:', error);
    // Set error state for UI to display
    set((state) => ({
      metrics: {
        current: state.metrics.current,
        inception: null, // Clear on error
      },
    }));
  }
},
```

---

### 3.3 Update WebSocket Handler

**File:** `frontend/src/hooks/use-websocket.ts`

Extract metrics and evaluation from completion event:

```typescript
case 'completion':
case 'session_complete': {
  const completionPayload = update.data?.session ?? update.data?.result;

  // Extract report
  if (completionPayload?.report) {
    const normalizedReport = normalizeReportPayload(
      completionPayload.report,
      completionPayload.sources,
    );
    if (normalizedReport) {
      store.setReport(normalizedReport);
    }
  }

  // Extract metrics
  if (completionPayload?.metrics) {
    const metricsData = completionPayload.metrics;

    // Calculate tool success rate
    let toolSuccesses = 0;
    let toolTotal = 0;
    if (metricsData.tool_metrics) {
      Object.values(metricsData.tool_metrics).forEach((metrics: any) => {
        toolSuccesses += metrics.success_count || 0;
        toolTotal += metrics.execution_count || 0;
      });
    }

    // Build current run metrics
    const currentMetrics: CurrentRunMetrics = {
      iterationLatencyAvg: metricsData.avg_iteration_duration * 1000, // s to ms
      iterationLatencies: metricsData.iterations?.map((i: any) => i.duration * 1000) || [],
      toolExecutionTimes: {},
      endToEndSeconds: metricsData.total_duration_seconds,
      totalTokens: metricsData.total_tokens_used,
      totalCostUsd: metricsData.total_cost_usd || 0,
      iterationsToCompletion: metricsData.total_iterations || 0,
      toolSuccessRate: toolTotal > 0 ? toolSuccesses / toolTotal : 0,
      evaluation: completionPayload.evaluation || {
        relevance: 0,
        accuracy: 0,
        completeness: 0,
        sourceQuality: 0,
        strengths: [],
        weaknesses: [],
        recommendations: [],
      },
    };

    // Extract tool times
    if (metricsData.tool_metrics) {
      Object.entries(metricsData.tool_metrics).forEach(([tool, metrics]: [string, any]) => {
        currentMetrics.toolExecutionTimes[tool] = metrics.avg_duration_seconds * 1000;
      });
    }

    // Set current metrics
    store.setMetrics({
      current: currentMetrics,
      inception: store.metrics.inception, // Keep existing
    });

    // Fetch historical metrics
    store.fetchMetricsSummary();
  }

  store.setResearching(false);
  // ... rest of completion logic ...
  break;
}
```

---

### 3.4 Modern UI Components

#### 3.4.1 Main Dashboard Component

**File:** `frontend/src/components/research/metrics-dashboard.tsx` (NEW)

```tsx
/**
 * Metrics Dashboard Component
 *
 * Displays current run and historical metrics in a modern, polished design.
 */

'use client';

import React from 'react';
import {
  Clock,
  Zap,
  Timer,
  Hash,
  Award,
  TrendingUp,
  BarChart3,
} from 'lucide-react';
import type { CurrentRunMetrics, InceptionMetrics } from '@/types';
import { MetricCard } from './metric-card';
import { ScoreBar } from './score-bar';
import { ToolBreakdown } from './tool-breakdown';

interface MetricsDashboardProps {
  current: CurrentRunMetrics | null;
  inception: InceptionMetrics | null;
}

export function MetricsDashboard({ current, inception }: MetricsDashboardProps) {
  if (!current && !inception) {
    return null; // Don't show until data available
  }

  return (
    <div className="mt-6 animate-in fade-in duration-300">
      {/* Section Header */}
      <div className="mb-6 p-6 rounded-lg border-t-2 border-indigo-500/50 bg-gradient-to-r from-slate-900/80 to-slate-800/60 backdrop-blur">
        <h2 className="text-xl font-bold gradient-text flex items-center gap-2">
          <BarChart3 className="w-6 h-6" />
          Research Metrics & Evaluation
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Performance metrics and quality scores for current run and historical trends
        </p>
      </div>

      {/* Two-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Run */}
        {current && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-400" />
              Current Run
            </h3>
            <CurrentRunPanel metrics={current} />
          </div>
        )}

        {/* Inception Till Date */}
        {inception && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-400" />
              Inception Till Date
              <span className="text-xs text-slate-500 font-normal">
                ({inception.totalSessions} sessions)
              </span>
            </h3>
            <InceptionPanel metrics={inception} />
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Current Run Panel
 */
function CurrentRunPanel({ metrics }: { metrics: CurrentRunMetrics }) {
  return (
    <div className="space-y-4">
      {/* Performance Metrics */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          Performance Metrics
        </h4>
        <div className="grid grid-cols-1 gap-3">
          <MetricCard
            label="Iteration Latency"
            value={Math.round(metrics.iterationLatencyAvg)}
            unit="ms"
            icon={<Zap className="w-4 h-4" />}
            subtitle="Average per cycle"
          />
          <MetricCard
            label="End-to-End Duration"
            value={metrics.endToEndSeconds.toFixed(1)}
            unit="seconds"
            icon={<Timer className="w-4 h-4" />}
            subtitle="Total research time"
          />
        </div>

        {/* Tool Breakdown */}
        {Object.keys(metrics.toolExecutionTimes).length > 0 && (
          <ToolBreakdown tools={metrics.toolExecutionTimes} />
        )}
      </div>

      {/* Token & Cost */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Hash className="w-4 h-4 text-indigo-400" />
          Token & Cost Tracking
        </h4>
        <div className="grid grid-cols-1 gap-3">
          <MetricCard
            label="Total Tokens"
            value={metrics.totalTokens.toLocaleString()}
            icon={<Hash className="w-4 h-4" />}
            subtitle="Across all iterations"
          />
          <MetricCard
            label="Cost"
            value={`$${metrics.totalCostUsd.toFixed(4)}`}
            subtitle="Real-time USD tracking"
          />
        </div>
      </div>

      {/* Agent Behavior */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Zap className="w-4 h-4 text-indigo-400" />
          Agent Behavior
        </h4>
        <div className="grid grid-cols-1 gap-3">
          <MetricCard
            label="Iterations to Completion"
            value={metrics.iterationsToCompletion}
            subtitle="ReAct cycles needed"
          />
          <MetricCard
            label="Tool Success Rate"
            value={`${(metrics.toolSuccessRate * 100).toFixed(1)}%`}
            subtitle="Successful vs failed calls"
          />
        </div>
      </div>

      {/* Quality Evaluation */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Award className="w-4 h-4 text-indigo-400" />
          Quality Evaluation
        </h4>
        <div className="space-y-2">
          <ScoreBar label="Relevance" score={metrics.evaluation.relevance} />
          <ScoreBar label="Accuracy" score={metrics.evaluation.accuracy} />
          <ScoreBar label="Completeness" score={metrics.evaluation.completeness} />
          <ScoreBar label="Source Quality" score={metrics.evaluation.sourceQuality} />
        </div>

        {/* Strengths & Weaknesses */}
        {(metrics.evaluation.strengths.length > 0 || metrics.evaluation.weaknesses.length > 0) && (
          <div className="mt-4 p-4 rounded-lg bg-slate-900/50 border border-slate-700/30 space-y-3">
            {metrics.evaluation.strengths.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-green-400 mb-2">✓ Strengths</p>
                <ul className="text-xs text-slate-300 space-y-1">
                  {metrics.evaluation.strengths.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-green-400">•</span>
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {metrics.evaluation.weaknesses.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-yellow-400 mb-2">⚠ Areas for Improvement</p>
                <ul className="text-xs text-slate-300 space-y-1">
                  {metrics.evaluation.weaknesses.map((weakness, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-yellow-400">•</span>
                      <span>{weakness}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Inception Panel
 */
function InceptionPanel({ metrics }: { metrics: InceptionMetrics }) {
  if (metrics.totalSessions === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-slate-700/50 rounded-lg">
        <BarChart3 className="w-12 h-12 text-slate-600 mb-3" />
        <p className="text-sm text-slate-400 mb-1">No historical data yet</p>
        <p className="text-xs text-slate-500">
          Complete more research sessions to see trends
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Performance Metrics */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          Performance Metrics
        </h4>
        <div className="grid grid-cols-1 gap-3">
          <MetricCard
            label="Iteration Latency"
            value={Math.round(metrics.iterationLatencyMedian)}
            unit="ms"
            icon={<Zap className="w-4 h-4" />}
            subtitle="Median per cycle"
          />
          <MetricCard
            label="End-to-End Duration"
            value={metrics.endToEndMedian.toFixed(1)}
            unit="seconds"
            icon={<Timer className="w-4 h-4" />}
            subtitle="Median research time"
          />
        </div>

        {/* Tool Breakdown */}
        {Object.keys(metrics.tools).length > 0 && (
          <ToolBreakdown tools={metrics.tools} isMedian />
        )}
      </div>

      {/* Token & Cost */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Hash className="w-4 h-4 text-indigo-400" />
          Token & Cost Tracking
        </h4>
        <div className="grid grid-cols-1 gap-3">
          <MetricCard
            label="Avg Tokens"
            value={Math.round(metrics.avgTokens).toLocaleString()}
            icon={<Hash className="w-4 h-4" />}
            subtitle="Average per session"
          />
          <MetricCard
            label="Avg Cost"
            value={`$${metrics.avgCostUsd.toFixed(4)}`}
            subtitle="Average per session"
          />
        </div>
      </div>

      {/* Agent Behavior */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Zap className="w-4 h-4 text-indigo-400" />
          Agent Behavior
        </h4>
        <div className="grid grid-cols-1 gap-3">
          <MetricCard
            label="Avg Iterations"
            value={metrics.avgIterations.toFixed(1)}
            subtitle="Average cycles to completion"
          />
          <MetricCard
            label="Tool Success Rate"
            value={`${(metrics.toolSuccessRate * 100).toFixed(1)}%`}
            subtitle="Successful vs failed (total)"
          />
        </div>
      </div>

      {/* Reliability */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Award className="w-4 h-4 text-indigo-400" />
          Reliability Metrics
        </h4>
        <div className="grid grid-cols-1 gap-3">
          <MetricCard
            label="Session Success Rate"
            value={`${(metrics.sessionSuccessRate * 100).toFixed(1)}%`}
            subtitle={`${metrics.completedSessions} / ${metrics.totalSessions} completed`}
          />
          <MetricCard
            label="Provider Failover Rate"
            value={`${(metrics.providerFailoverRate * 100).toFixed(1)}%`}
            subtitle="LLM provider switches"
          />
        </div>
      </div>

      {/* Quality Evaluation */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Award className="w-4 h-4 text-indigo-400" />
          Quality Evaluation
        </h4>
        <div className="space-y-2">
          <ScoreBar label="Relevance" score={metrics.relevanceAvg} />
          <ScoreBar label="Accuracy" score={metrics.accuracyAvg} />
          <ScoreBar label="Completeness" score={metrics.completenessAvg} />
          <ScoreBar label="Source Quality" score={metrics.sourceQualityAvg} />
        </div>
      </div>
    </div>
  );
}
```

#### 3.4.2 Metric Card Component

**File:** `frontend/src/components/research/metric-card.tsx` (NEW)

```tsx
/**
 * Metric Card Component
 *
 * Modern glass-morphism card for displaying individual metrics.
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  subtitle?: string;
  className?: string;
}

export function MetricCard({
  label,
  value,
  unit,
  icon,
  subtitle,
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-lg bg-gradient-to-br from-slate-800/40 to-slate-900/60',
        'border border-slate-700/30 p-4 backdrop-blur-sm',
        'hover:border-indigo-500/50 transition-all duration-300 group',
        className
      )}
    >
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            {icon && <div className="text-indigo-400">{icon}</div>}
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">
              {label}
            </span>
          </div>
        </div>

        {/* Value */}
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-3xl font-bold text-slate-100 font-mono">
            {value}
          </span>
          {unit && (
            <span className="text-sm text-slate-500 font-medium">{unit}</span>
          )}
        </div>

        {/* Subtitle */}
        {subtitle && (
          <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
```

#### 3.4.3 Score Bar Component

**File:** `frontend/src/components/research/score-bar.tsx` (NEW)

```tsx
/**
 * Score Bar Component
 *
 * Animated progress bar for displaying 0-1 evaluation scores.
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ScoreBarProps {
  label: string;
  score: number; // 0-1
}

export function ScoreBar({ label, score }: ScoreBarProps) {
  const percentage = score * 100;

  // Color based on score
  const getColor = () => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-blue-400';
    if (score >= 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono font-semibold text-slate-200">
          {score.toFixed(2)}
        </span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-700 ease-out',
            getColor()
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
```

#### 3.4.4 Tool Breakdown Component

**File:** `frontend/src/components/research/tool-breakdown.tsx` (NEW)

```tsx
/**
 * Tool Breakdown Component
 *
 * Expandable section showing execution times per tool.
 */

'use client';

import React from 'react';
import { ChevronRight, Wrench } from 'lucide-react';

interface ToolBreakdownProps {
  tools: Record<string, number>; // tool name -> time in ms
  isMedian?: boolean;
}

export function ToolBreakdown({ tools, isMedian = false }: ToolBreakdownProps) {
  const toolEntries = Object.entries(tools).sort((a, b) => b[1] - a[1]);

  if (toolEntries.length === 0) {
    return null;
  }

  return (
    <details className="group mt-3">
      <summary className="cursor-pointer text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 select-none">
        <ChevronRight className="w-3 h-3 group-open:rotate-90 transition-transform" />
        <Wrench className="w-3 h-3" />
        View tool breakdown ({toolEntries.length} tools)
      </summary>
      <div className="mt-3 space-y-2 pl-5">
        {toolEntries.map(([tool, time]) => (
          <div
            key={tool}
            className="flex justify-between items-center text-xs p-2 rounded bg-slate-900/30 hover:bg-slate-900/50 transition-colors"
          >
            <span className="text-slate-300">{tool}</span>
            <span className="text-slate-200 font-mono font-semibold">
              {Math.round(time)}ms
              {isMedian && (
                <span className="text-slate-500 ml-1 text-[10px]">median</span>
              )}
            </span>
          </div>
        ))}
      </div>
    </details>
  );
}
```

#### 3.4.5 Integrate in Main Page

**File:** `frontend/src/app/page.tsx`

```tsx
import { MetricsDashboard } from '@/components/research/metrics-dashboard';
import { useResearchStore } from '@/store/research-store';

export default function ResearchPage() {
  const { metrics } = useResearchStore();

  // ... existing code ...

  return (
    <div className="min-h-screen bg-slate-950">
      <Header />

      <main className="pt-20 px-6 pb-6">
        <div className="container mx-auto max-w-[1920px]">
          <QueryInput />

          {/* Existing 3-panel grid */}
          <div className="grid grid-cols-1 lg:grid-cols-[30%_40%_30%] gap-6 h-[calc(100vh-280px)]">
            <ReactTraceTimeline iterations={iterations} />
            <CurrentActivityPanel />
            <ResearchOutputPanel />
          </div>

          {/* NEW: Metrics Dashboard */}
          <MetricsDashboard
            current={metrics.current}
            inception={metrics.inception}
          />
        </div>
      </main>
    </div>
  );
}
```

---

## 4. Testing

### 4.1 Backend Tests

**File:** `backend/tests/test_metrics_history.py` (NEW)

```python
"""Tests for metrics history storage."""

import pytest
from pathlib import Path
from backend.app.metrics.history import (
    append_run,
    load_history,
    compute_aggregates,
    create_snapshot,
    HISTORY_FILE,
)


@pytest.fixture
def clean_history(tmp_path, monkeypatch):
    """Use temporary directory for history file."""
    test_file = tmp_path / "test_history.json"
    monkeypatch.setattr('backend.app.metrics.history.HISTORY_FILE', test_file)
    yield
    if test_file.exists():
        test_file.unlink()


def test_create_snapshot():
    """Test snapshot creation."""
    snapshot = create_snapshot(
        session_id="test-123",
        status="completed",
        iteration_latencies_ms=[800, 900, 850],
        tool_execution_times={"web_search": [1200, 1100]},
        end_to_end_seconds=45.5,
        total_tokens=10000,
        relevance=0.9,
        accuracy=0.85,
        completeness=0.88,
        source_quality=0.8,
    )

    assert snapshot["session_id"] == "test-123"
    assert snapshot["status"] == "completed"
    assert snapshot["relevance"] == 0.9
    assert len(snapshot["iteration_latencies_ms"]) == 3


def test_append_and_load(clean_history):
    """Test appending and loading history."""
    snapshot = create_snapshot(
        session_id="test-1",
        status="completed",
        iteration_latencies_ms=[800],
        tool_execution_times={},
        end_to_end_seconds=30,
        total_tokens=5000,
        relevance=0.8,
        accuracy=0.75,
        completeness=0.7,
        source_quality=0.65,
    )

    append_run(snapshot)
    history = load_history()

    assert len(history) == 1
    assert history[0]["session_id"] == "test-1"


def test_compute_aggregates_empty():
    """Test aggregates with empty history."""
    agg = compute_aggregates([])
    assert agg["total_sessions"] == 0
    assert agg["relevance_avg"] == 0


def test_compute_aggregates_with_data():
    """Test aggregates with actual data."""
    history = [
        create_snapshot(
            session_id=f"test-{i}",
            status="completed",
            iteration_latencies_ms=[800 + i * 10, 900 + i * 10],
            tool_execution_times={"web_search": [1200]},
            end_to_end_seconds=40 + i,
            total_tokens=10000,
            relevance=0.8 + i * 0.01,
            accuracy=0.75,
            completeness=0.7,
            source_quality=0.65,
        )
        for i in range(5)
    ]

    agg = compute_aggregates(history)

    assert agg["total_sessions"] == 5
    assert agg["relevance_avg"] > 0.8
    assert "web_search" in agg["tools"]
```

**File:** `backend/tests/test_evaluator_scale.py` (NEW)

```python
"""Tests for 0-1 scale evaluation."""

import pytest
from backend.app.agents.evaluator_agent import EvaluatorAgent


def test_score_clamping():
    """Test that scores are clamped to 0-1 range."""
    evaluator = EvaluatorAgent(llm_manager=mock_llm)

    # Test clamping
    assert evaluator._clamp_score(1.5) == 1.0
    assert evaluator._clamp_score(-0.5) == 0.0
    assert evaluator._clamp_score(0.75) == 0.75
```

---

### 4.2 Frontend Tests

Create tests for new components ensuring they handle null/empty states correctly.

---

## 5. Migration Steps

### 5.1 Database Migration

Since we're removing the `per_step_evaluations` table:

1. **Create migration script:** `backend/migrations/remove_per_step_evals.py`
2. **Backup existing data** (if needed)
3. **Drop table:** `DROP TABLE IF EXISTS per_step_evaluations;`
4. **Update constraints** on `research_sessions` table

### 5.2 Update .gitignore

Add runtime directory to gitignore:

```
backend/runtime/
!backend/runtime/.gitkeep
```

Create `.gitkeep` file in `backend/runtime/`

---

## 6. Documentation Updates

Update the following files:

1. **README.md** - Update architecture section
2. **GETTING_STARTED.md** - Update evaluation section
3. **CLAUDE.md** - Update evaluation system description
4. Remove references to EnhancedEvaluator
5. Update API documentation

---

## 7. Summary of Changes

### Deleted:
- ✅ `backend/app/agents/enhanced_evaluator.py`
- ✅ `PerStepEvaluation` dataclass and table
- ✅ `evaluate_step()` method and all per-step logic
- ✅ Coherence, recency scores
- ✅ Deprecated fields from `EvaluationResult`: `per_step_evaluations`, `average_per_step_score`, `overall_quality_score`
- ✅ Provider failover tracking
- ✅ Tool success rate
- ✅ Framer-motion dependency (replaced with CSS)

### Modified (0-10 → 0-1):
- ✅ Evaluation prompts
- ✅ `EndToEndEval` dataclass
- ✅ Database columns
- ✅ API responses
- ✅ UI display

### Added:
- ✅ Simple JSON history storage
- ✅ Metrics aggregation logic
- ✅ New API endpoint `/api/metrics/summary`
- ✅ Modern metrics dashboard UI
- ✅ Metric card, score bar, tool breakdown components

### Implemented (Complete Metrics Set):

**Latency Metrics:**
- ✅ Iteration latency (avg for current, median for inception)
- ✅ Tool execution time (per-tool, median for inception)
- ✅ End-to-end duration (total for current, median for inception)

**Token & Cost:**
- ✅ Cumulative token usage (total for current, avg for inception)
- ✅ Cost per session (real-time USD, avg for inception)

**Agent Behavior:**
- ✅ Iterations to completion (count for current, avg for inception)
- ✅ Tool success rate (% successful calls, ratio for inception)

**Quality Metrics (0-1 scale):**
- ✅ Relevance, accuracy, completeness, source quality
- ✅ Qualitative feedback (strengths, weaknesses, recommendations)

**Reliability (Inception only):**
- ✅ Session success rate (% completed vs failed)
- ✅ Provider failover rate (% of LLM calls that switched providers)

---

## 8. Implementation Checklist

**Phase 1: Backend Cleanup**
- [ ] Delete `enhanced_evaluator.py`
- [ ] Remove EnhancedEvaluator imports
- [ ] Remove PerStepEval from models
- [ ] Remove deprecated fields from `EvaluationResult`
- [ ] Update database models (remove PerStepEvaluation table)
- [ ] Update EvaluatorAgent (0-1 scale, remove per-step logic)

**Phase 2: History Storage**
- [ ] Create `metrics/history.py`
- [ ] Add filelock dependency
- [ ] Create runtime directory
- [ ] Update .gitignore

**Phase 3: Integration**
- [ ] Update `_run_research_session`
- [ ] Create metrics API endpoint
- [ ] Update database operations

**Phase 4: Frontend**
- [ ] Update types
- [ ] Update store
- [ ] Update WebSocket handler
- [ ] Create UI components
- [ ] Integrate in main page

**Phase 5: Testing**
- [ ] Add backend tests
- [ ] Add frontend tests
- [ ] Manual testing

**Phase 6: Documentation**
- [ ] Update README
- [ ] Update GETTING_STARTED
- [ ] Update CLAUDE.md
- [ ] Update API docs

---

**End of Plan**
