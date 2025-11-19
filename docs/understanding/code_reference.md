# Application Design & Architecture Overview

This document explains how the Agentic Research Lab application works end‑to‑end, with a focus on the **backend research workflow** and how it drives the **frontend workflow chart** and **ReAct Trace** views.

The target audience is people who are comfortable with generative AI concepts and basic code reading, but not necessarily experienced backend or frontend engineers. Throughout the document, you’ll see
references to specific files and function names so you can jump into the code for deeper understanding.

---

## 1. Introduction

### 1.1 Purpose

- Explain how the application performs deep research using LLMs and tools.
- Show how the **ReAct research agent**, **evaluator agent**, and **tools** work together.
- Describe how **backend stages** map to **frontend visualizations** (workflow chart and ReAct trace).
- Provide concrete references to files and functions for deeper inspection.

### 1.2 High‑Level System Overview

The system has two main parts:

- **Backend** (`backend/`):
- FastAPI app that orchestrates research sessions.
- ReAct‑style research agent, evaluator agent, tools, content pipeline, metrics, and WebSocket/SSE transport.
- **Frontend** (`frontend/`):
- Next.js app that shows the research process visually.
- Workflow chart, ReAct Trace timeline, metrics dashboard, configuration UI, and final report display.

### 1.3 End‑to‑End Research Flow (Happy Path)

1. User enters a research query and configuration in the frontend.
2. Frontend calls `POST /api/research/start`.
3. Backend creates a new **research session** in the database and starts a **background task**.
4. The **ReAct ResearcherAgent** runs multiple iterations:
    - Think → choose tools → execute tools → observe results, repeating until done.
5. When enough evidence is gathered, the agent calls a special `finish` tool to generate the final **Deep Research Report**.
6. The **EvaluatorAgent** runs an LLM‑as‑judge pass on the final report.
7. Throughout the process, the backend streams **trace events** and **completion data** via WebSocket/SSE.
8. The frontend:
    - Updates the **workflow chart** (stage‑level view).
    - Updates the **ReAct Trace** timeline (iteration‑level view).
    - Finally shows the report and evaluation metrics.

---

## 2. Backend Overview (FastAPI Orchestrator & Agents)

### 2.1 Core Responsibilities

- Orchestrate multi‑step research workflows.
- Manage:
- `ResearcherAgent` (ReAct agent).
- `EvaluatorAgent` (LLM‑as‑judge).
- Route prompts and tool calls through the `LLMManager`.
- Execute tools (web, arxiv, github, PDF, content pipeline).
- Persist sessions, traces, and evaluations.
- Stream live events to the frontend.

Key entry points:

- FastAPI app main: `backend/app/api/main.py`.
- Research routes: `backend/app/api/routes/research.py`.
- WebSocket/SSE manager: `backend/app/api/websocket.py`.

### 2.2 High‑Level Architecture

Main modules and their roles:

- **API Layer** (`backend/app/api`):
- HTTP + WebSocket endpoints (`main.py`, `routes/`, `websocket.py`).
- Dependency injection for settings and `LLMManager` (`dependencies.py`).
- **Agents** (`backend/app/agents`):
- `ResearcherAgent` (ReAct pattern) — `react_agent.py`.
- `EvaluatorAgent` — `evaluator_agent.py`.
- Data models: `AgentStep`, `ResearchResult`, `EndToEndEval`, `EvaluationResult` — `models.py`.
- **LLM Management** (`backend/app/llm`):
- `LLMManager` — `manager.py`.
- Providers: `openai_provider.py`, `gemini_provider.py`, `openrouter_provider.py`.
- **Tools** (`backend/app/tools`):
- Web / Arxiv / GitHub / PDF tools: `web_search.py`, `arxiv_search.py`, `github_search.py`, `pdf_parser.py`.
- OpenAI‑style tool definitions (including `finish`): `definitions.py`.
- **Content Pipeline** (`backend/app/content`):
- `ContentPipeline` orchestrates classification, extraction, summarization, ranking, caching — `pipeline.py`.
- **Database & Tracing** (`backend/app/database`, `backend/app/tracing`):
- Session, trace, evaluation persistence (async DB helpers).
- **Metrics** (`backend/app/metrics`):
- `MetricsCollector` and `MetricsData` for performance and quality metrics.

### 2.3 Research Session Lifecycle (Top‑Down)

Primary orchestration code:

- `start_research` endpoint — `backend/app/api/routes/research.py`, function `start_research`.
- Background worker — `_run_research_session` in the same file.

Flow:

1. **Start request:**
    - `POST /api/research/start` → `start_research(...)` (`research.py`).
    - Validates `StartResearchRequest` (`backend/app/api/models/requests.py`).
    - Normalizes configuration via `_normalize_request_config(...)`.
    - Resolves per‑session settings and LLM config via `_prepare_session_context(...)`.
2. **Session creation:**
    - `create_session(...)` — `backend/app/database` (called from `start_research`).
    - Returns `session_id`; status set to `"running"`.
3. **Background research task:**
    - `background_tasks.add_task(_run_research_session, ...)`.
    - `_run_research_session(...)` configures:
    - Optional `ContentPipeline` (if `settings.tools.use_content_pipeline`).
    - `MetricsCollector`.
    - An async `trace_callback` that writes trace events via `save_trace_event(...)`.
    - The `ResearcherAgent` instance.
    - Calls `await researcher.research(query, session_id=session_id)` to run the ReAct loop.
4. **Evaluation & completion:**
    - Creates `EvaluatorAgent` and calls `await evaluator.evaluate_research(result, ...)`.
    - Saves evaluation via `save_end_to_end_evaluation(...)`.
    - Builds a metrics snapshot with `MetricsCollector.finalize(...)` and history helpers.
    - Sends a final completion message over WebSocket:
    `websocket_manager.send_completion(...)` in `_run_research_session`.
    - Updates session status to `"completed"` via `update_session(...)`.

Error handling and cancellation:

- Errors: `_run_research_session` catches exceptions, calls `websocket_manager.send_error(...)`, and sets status `"failed"`.
- Cancellation: `cancel_session` endpoint in `research.py` sets an `_active_sessions[session_id]` flag and updates DB.

---

## 3. Research Workflow Orchestration

### 3.1 Session Start & Configuration Resolution

**Request model:**

- `StartResearchRequest` — `backend/app/api/models/requests.py`.
- Fields: `query`, `config`, plus legacy overrides (`llm_provider`, `llm_model`, `temperature`, `max_iterations`).

**Configuration normalization:**

- `_normalize_request_config(request)` — `backend/app/api/routes/research.py`.
- Merges legacy top‑level fields into a structured `config` block:
    - `config["llm"]["provider"]`, `config["llm"]["model"]`, `config["llm"]["temperature"]`.
    - `config["research"]["max_iterations"]`.

**Session‑specific settings and LLM:**

- `_prepare_session_context(base_settings, base_llm_manager, session_config)` — `research.py`.
- Applies config overrides to `Settings` (from `backend/app/config/settings.py`).
- Constructs a per‑session `LLMManager` instance by calling `get_llm_config_dict(...)` and `LLMManager(...)`.

### 3.2 Background Research Task

**Orchestrator function:**

- `_run_research_session(session_id, query, settings, llm_manager, llm_temperature=None)` — `research.py`.

Inside this function:

1. **Content pipeline:**
    - If `settings.tools.use_content_pipeline` is true:
    - Creates `ContentPipeline` — `backend/app/content/pipeline.py`, class `ContentPipeline`.
    - Constructor invoked with `llm_manager`, `top_k=10`, `max_content_length=5000`, etc.
2. **Metrics collector:**
    - Creates `MetricsCollector(session_id=session_id)` — `backend/app/metrics/collector.py`.
    - Calls `metrics_collector.start_session(query)` to mark start.
3. **Trace callback:**
    - Defines an async `trace_callback(event_type, data, iteration)` in `_run_research_session`.
    - Persists trace events using `save_trace_event(...)` — `backend/app/database`.
4. **ResearcherAgent:**
    - Instantiated as:
    ```python
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
    ```
    (`backend/app/agents/react_agent.py`, class `ResearcherAgent.__init__`).
    - This wiring ensures:
    - LLM calls use the session’s `LLMManager`.
    - Tools and pipeline can be used inside the ReAct loop.
    - All trace events and WebSocket events are connected to this session.
5. **Research execution:**
    - `result = await researcher.research(query, session_id=session_id)` — `ResearcherAgent.research`.
    - Returns a `ResearchResult` (see `backend/app/agents/models.py`).

### 3.3 Session Completion Path

After `ResearcherAgent.research` returns:

1. **Evaluator agent:**
    - `evaluator = EvaluatorAgent(llm_manager=llm_manager)` — `backend/app/agents/evaluator_agent.py`.
    - Emits trace events for evaluator lifecycle using:
    - `save_trace_event(..., event_type="evaluator_start" | "evaluator_complete", ...)` in `_run_research_session`.
    - `websocket_manager.send_trace_event(...)` in the same places.
    - Runs evaluation:
    - `eval_result = await evaluator.evaluate_research(result, evaluate_steps=False)`.
2. **Persist evaluation:**
    - If `eval_result.end_to_end_evaluation` exists:
    - `save_end_to_end_evaluation(...)` — `backend/app/database`.
3. **Metrics and history:**
    - Calls `metrics_collector.end_session(final_report=result.report)` and `metrics_collector.finalize(evaluation_result=...)`.
    - Builds a snapshot via a helper (e.g., `create_snapshot(...)` and `append_run(...)` in `backend/app/metrics`).
4. **Completion WebSocket event:**
    - `_run_research_session` calls:
    ```python
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
            "strengths": ...,
            "weaknesses": ...,
            "recommendations": ...,
        },
        },
    )
    ```
    (`backend/app/api/websocket.py`, method `ConnectionManager.send_completion`).
5. **Session update:**
    - Final database update via `update_session(...)` in `_run_research_session`:
    - `status="completed"`, `completed_at`, `total_duration_seconds`, `total_iterations`, `total_cost_usd`, `final_report`, `sources`.

### 3.4 Error & Cancellation Handling

- **Errors in `_run_research_session`:**
- In `except Exception as e:` block:
    - Sends WebSocket error: `websocket_manager.send_error(session_id, error_message=str(e), ...)` — `websocket.py`, method `send_error`.
    - Updates session status to `"failed"` via `update_session(...)`.
- **Cancellation:**
- `cancel_session(session_id)` — `backend/app/api/routes/research.py`.
    - Validates session, checks `session.status == "running"`.
    - Sets `_active_sessions[session_id] = False` (used inside the research loop to stop).
    - Updates DB: `await update_session(session_id, status="cancelled")`.

---

## 4. ReAct Researcher Agent (Reasoning + Tools Loop)

> This section references **`backend/app/agents/react_agent.py`**, class **`ResearcherAgent`**.

### 4.1 Role of `ResearcherAgent`

- Class: `ResearcherAgent` in `backend/app/agents/react_agent.py`.
- Main public method: `async def research(self, query: str, session_id: Optional[str] = None) -> ResearchResult`.
- Implements the **ReAct pattern**:
- THOUGHT → ACTION → OBSERVATION → repeat.
- Produces a `ResearchResult` dataclass (`backend/app/agents/models.py`) that includes:
- `report`, `sources`, list of `AgentStep` (iterations), `total_iterations`, `total_duration_seconds`, `total_tokens`, `total_cost_usd`, `status`.

### 4.2 System Prompt, Tool Schema, and Policies

**System prompt:**

- Constant: `ResearcherAgent.SYSTEM_PROMPT` — `react_agent.py`.
- This prompt instructs the LLM on:
- ReAct loop discipline (THOUGHT, ACTION, OBSERVATION).
- Tool usage (web_search, arxiv_search, github_search, pdf_to_text, finish).
- Deep Research Report structure (title, TL;DR, methodology, findings, implementation/impact, risks, next steps, sources).
- Citation format `[ # ]`, recency handling (`CURRENT_YEAR`).

The prompt is injected at the start of `research`:

```python
conversation_history: List[Dict[str, str]] = [
{
    "role": "system",
    "content": self.SYSTEM_PROMPT.format(
    max_iterations=self.max_iterations,
    query=query,
    current_year=self.current_year,
    ),
},
{
    "role": "user",
    "content": "You are about to start the research process described above. "
                f"Restate the plan and begin reasoning about the query:\n\n{query}",
},
]

Tool schema (OpenAI‑style tools):

- Defined in backend/app/tools/definitions.py, with:
    - WEB_SEARCH_DEFINITION
    - ARXIV_SEARCH_DEFINITION
    - GITHUB_SEARCH_DEFINITION
    - PDF_TO_TEXT_DEFINITION
    - FINISH_DEFINITION
- Combined by get_all_tool_definitions() — same file.
- ResearcherAgent.__init__ calls get_all_tool_definitions() and stores in self.tool_definitions.

The FINISH_DEFINITION contains the spec for the final report payload, including:

- The Markdown Deep Research Report structure.
- Requirements for TL;DR, methodology, findings, implementation/impact, risks, next steps, and sources.

This means: the LLM generates the report as the argument to the finish function call, following this schema.

Tool policies and heuristics:

- Initial policy: _derive_tool_policy(query) — react_agent.py.
    - Uses keyword sets GITHUB_KEYWORDS and ARXIV_KEYWORDS to decide:
        - allow_github, allow_arxiv.
        - default_tool ("arxiv_search" vs "web_search").
- Recency intent: _detect_recency_intent(query) and _preferred_date_filter(recency_intent).
- Extra guidance: _build_tool_policy_message(policy, recency_intent) injects a system message describing tool heuristics.
- Policy overrides (e.g., finish_guard_enabled, thresholds) are set in __init__ via policy_overrides.
```

### 4.3 ReAct Iteration Flow

Core method: ResearcherAgent.research.

Loop skeleton:

- Initializes:
    - iteration = 0, done = False, final_report = "", sources = [].
- While loop:

while not done and iteration < self.max_iterations:
    iteration += 1
    await self._emit_trace("iteration_start", {...}, iteration)
    # LLM call → tool calls → tool execution → observation → next iteration or finish

Stages within one iteration:

1. THOUGHT + ACTION planning:
    - Prepares conversation_history:
        - Ensures last message is a user message encouraging either progress or finish.
        - Calls _inject_domain_guidance(...) to optionally add coverage reminders.
    - Calls self.llm.complete(...):
        - Method: LLMManager.complete(...) — backend/app/llm/manager.py.
        - Parameters: messages=conversation_history, tools=self.tool_definitions, temperature=self.llm_temperature, max_tokens=6000.
        - May require tool calls (depending on context).
    - Extracts:
        - thought = response.get("content").
        - tool_calls = list of tool function calls.
    - Emits THOUGHT trace event:
        - await self._emit_trace("thought", {...}, iteration) — includes reasoning text, tokens, latency.
        - _emit_trace is defined in react_agent.py.
2. ACTION selection:
    - For each tool call in tool_calls:
        - Parses action_name and action_input (JSON arguments).
        - Validates against tool policy using _is_tool_allowed(tool_name, thought, action_input).
        - Emits ACTION trace via _emit_trace("action", {...}, iteration).
3. TOOL EXECUTION:
    - If the action_name is "finish":
        - Handled specially (see Section 4.5).
    - Else:
        - Determines timeout via _get_tool_timeout_seconds(action_name).
        - Executes tool via _execute_tool_with_timeout(action_name, action_input, timeout_seconds), which wraps _execute_tool.
        - _execute_tool dispatches to:
            - web_search(...) — backend/app/tools/web_search.py.
            - arxiv_search(...) — backend/app/tools/arxiv_search.py.
            - github_search(...) — backend/app/tools/github_search.py.
            - pdf_to_text(...) — backend/app/tools/pdf_parser.py.
            - Each tool may optionally use ContentPipeline (for example, web_search and github_search accept content_pipeline).
    - Records metrics:
        - _record_tool_usage(tool_name, success) — react_agent.py.
        - MetricsCollector.record_tool_execution(...) — backend/app/metrics/collector.py (tool execution data).
    - Emits TOOL EXECUTION trace:
        - _emit_trace("tool_execution", {...}, iteration) with duration_ms, success, result_summary, provider, result_count.
4. OBSERVATION:
    - Converts tool output into a concise observation string with _format_observation(tool_name, tool_output).
    - Updates conversation_history by adding a tool role message describing observations.
    - Emits OBSERVATION trace:
        - _emit_trace("observation", {"observation": ...}, iteration).
5. Deciding whether to continue:
    - The loop continues, and subsequent iterations follow the same THOUGHT → ACTION → TOOL → OBSERVATION pattern.
    - Domain coverage logic:
        - _missing_domain_tools() and _inject_domain_guidance(...) ensure web/arxiv/github are used when appropriate.
        - _handle_sparse_web_results(...) adds guidance if web search results are too sparse.
        - _maybe_mark_sufficient_evidence(...) marks when enough evidence has already been gathered.


### 4.4 Tool Selection Heuristics

Key functions:

- _derive_tool_policy(query) — see above.
- _is_tool_allowed(tool_name, thought, action_input) — react_agent.py:
    - For github_search, checks:
        - self.tool_policy["allow_github"] and GITHUB_KEYWORDS in the thought text.
    - For arxiv_search, checks:
        - self.tool_policy["allow_arxiv"] and ARXIV_KEYWORDS.
    - If a tool is blocked:
        - Emits a tool_blocked trace via _emit_trace("tool_blocked", {...}, iteration) and uses block_message to explain.
- _handle_sparse_web_results(...):
    - When a web search returns fewer than a threshold of results, it appends a system message to conversation_history with guidance on refining queries and using recency filters.
- _inject_domain_guidance(...):
    - Periodically injects a reminder system message listing missing tools (web/arxiv/github) that may enrich coverage.

These functions enforce a “tool routing policy” that balances coverage across web, academic, and code sources, while avoiding unnecessary specialized tools.

### 4.5 Result Assembly & Final Report Generation

Normal finish path:

- When the LLM chooses to call the finish tool within the ReAct loop:
    - The code path is inside research(...) after parsing tool_calls.
    - The correlated logic:
        - Calls _run_finish_guard(...) if finish_guard_enabled (see next subsection).
        - If approved:
            - Extracts report and sources from action_input (i.e., the tool arguments).
            - Sets done = True.
            - Emits:
                - finish_guard trace: _emit_trace("finish_guard", {...}, iteration).
                - finish trace: _emit_trace("finish", {"report_length": ..., "num_sources": ..., "report": report, "sources": sources}, iteration).
            - Creates an AgentStep with:
                - action="finish", observation="Final report generated", tool_output={"report": ..., "sources": ...}, token and cost from response["usage"] and self.llm.estimate_cost(...).

Auto‑finish path:

- If the agent reaches max_iterations without calling finish, _force_finish_if_needed(...) is used:
    - Function: async def _force_finish_if_needed(...) -> tuple[bool, str, List[str], Optional[AgentStep]].
    - Adds an iteration_start event with mode="auto_finish".
    - Appends a user message instructing the model to use only existing observations and call finish.
    - Calls self.llm.complete(...) with tool_choice={"type": "function", "function": {"name": "finish"}}.
    - Optionally runs finish_guard again (see below).
    - Emits a finish trace with "auto_generated": True.
    - Returns (True, report, sources, AgentStep).

Finish guard (lightweight critic):

- Prompt: ResearcherAgent.FINISH_GUARD_PROMPT — react_agent.py.
- Function: async def _run_finish_guard(self, query, finish_args, iteration) -> tuple[bool, str, Optional[str]].
    - Builds a “guard” prompt with:
        - The query.
        - Truncated report and source list.
    - Calls self.llm.complete(...) as a separate LLM call.
    - Parses response with _parse_guard_response(content):
        - Expects JSON: { "allow_finish": bool, "feedback": "...", "next_action_hint": "..." }.
- If allow_finish is False and finish_guard_retry_on_auto_finish is true:
    - Injects system messages with guard feedback and hint.
    - Forces another finish tool call restricted to editing the report based on existing observations.

This ensures the final report meets a quality bar before being accepted.

### 4.6 Tracing Events from the ReAct Loop

Trace emitter:

- async def _emit_trace(self, event_type: str, data: Dict[str, Any], iteration: Optional[int] = None) — react_agent.py.

Responsibilities:

1. Augment data:
    - Adds iteration if provided.
    - Adds a default human‑readable message using _format_trace_message(event_type, iteration).
2. Logs stage transitions for animations via _log_animation_stage(...) (not shown here, but used to map internal events to frontend stages).
3. Calls the injected trace_callback (which saves events to DB via save_trace_event(...)).
4. Uses WebSocket manager for real‑time delivery:
    - await self.websocket_manager.send_trace_event(session_id, event_type, data) — backend/app/api/websocket.py, method ConnectionManager.send_trace_event.

Stage event mapping to workflow chart:

- Constant: STAGE_EVENT_MAP — at the end of react_agent.py:

STAGE_EVENT_MAP = {
    "iteration_start": "start->think",
    "thought": "think->act",
    "action": "act->execute",
    "tool_execution": "execute->evaluate",
    "observation": "execute->evaluate",
    "finish": "evaluate->finish",
}
- This mapping is used by _log_animation_stage to translate internal event types into higher‑level stages that the frontend workflow chart uses:
    - start, think, operate, reflect, evaluator, finish.

———

## 5. LLM Management & Providers

> This section references backend/app/llm/manager.py and provider files.

### 5.1 LLMManager Responsibilities

- Class: LLMManager — backend/app/llm/manager.py.
- Primary methods:
    - __init__(self, config: Dict[str, Any]).
    - async def complete(self, messages, tools=None, temperature=0.7, max_tokens=2048, require_content=False, require_tool_calls=False, tool_choice=None, retry_on_failure=True) -> Dict[str, Any].
    - def count_tokens(...).
    - def estimate_cost(...).

It provides a unified API for:

- Calling multiple providers (OpenAI, Gemini, OpenRouter).
- Automatically falling back to alternate providers on errors.
- Enforcing requirements:
    - require_content=True for prompts that must return text.
    - require_tool_calls=True when a tool call (e.g., finish) is required.
- Attaching provider metadata:
    - Each result includes provider_used, model, and usage (input_tokens, output_tokens, total_tokens).

### 5.2 Provider Adapters

Files:

- backend/app/llm/openai_provider.py — class OpenAIProvider.
- backend/app/llm/gemini_provider.py — class GeminiProvider.
- backend/app/llm/openrouter_provider.py — class OpenRouterProvider.

The manager configures them in LLMManager.__init__ using keys from the config dict (openai, gemini, openrouter).

### 5.3 Provider Selection, Fallback & Error Handling

Provider sequence:

- Determined in LLMManager.complete:
    - primary_provider from config (e.g., "openai").
    - fallback_order list (e.g., ["gemini", "openrouter"]).
- Builds provider_sequence = [self.primary_provider] + fallback_order.

Core loop:

- Inside complete(...):
    - For each provider_type in provider_sequence:
        - Skips if not configured or temporarily disabled (_is_disabled).
        - Calls _execute_provider_call(provider_type, messages, tools, temperature, max_tokens, tool_choice).
        - Validates:
            - If require_content and result["content"] is empty → error.
            - If require_tool_calls and tools provided but result["tool_calls"] is empty → error.
        - On success:
            - _reset_failure(provider_type).
            - Returns the result with result["provider_used"] set.
    - On failure:
        - Registers failure via _register_failure(provider_type, error).
        - Logs warning and continues to next provider.

Cost & tokens:

- Providers are responsible for computing cost per call.
- LLMManager.estimate_cost(input_tokens, output_tokens, provider_type=None) delegates to provider’s estimate_cost method if available.
- ResearcherAgent and EvaluatorAgent use estimate_cost to populate:
    - ResearchResult.total_cost_usd.
    - EndToEndEval.cost_usd.
- MetricsCollector.record_llm_call(...) collects per‑provider token and cost metrics.

———

## 6. Research Tools & Content Pipeline

> Main references: backend/app/tools/*.py and backend/app/content/pipeline.py.

### 6.1 Tool Catalog and Definitions

Tool definitions (schema):

- backend/app/tools/definitions.py:
    - WEB_SEARCH_DEFINITION
    - ARXIV_SEARCH_DEFINITION
    - GITHUB_SEARCH_DEFINITION
    - PDF_TO_TEXT_DEFINITION
    - FINISH_DEFINITION
    - get_all_tool_definitions() returns the list used by ResearcherAgent.

These definitions are OpenAI function‑call compatible and describe:

- Each tool’s name, description, and parameters schema.
- The finish tool’s expected report, sources, and optional confidence.

Tool implementations:

- Web search:
    - backend/app/tools/web_search.py, function async def web_search(...).
- Arxiv search:
    - backend/app/tools/arxiv_search.py, function async def arxiv_search(...).
- GitHub search:
    - backend/app/tools/github_search.py, function async def github_search(...).
- PDF parsing:
    - backend/app/tools/pdf_parser.py, function async def pdf_to_text(...).

ResearcherAgent._execute_tool routes to these functions.

### 6.2 Tool Execution Pattern

Inside ResearcherAgent:

- _execute_tool(tool_name, tool_input) — react_agent.py.
    - Matches tool_name to the appropriate async function:
        - web_search(content_pipeline=self.content_pipeline, **tool_input).
        - arxiv_search(content_pipeline=self.content_pipeline, **tool_input).
        - github_search(content_pipeline=self.content_pipeline, **tool_input).
        - pdf_to_text(**tool_input).
- _execute_tool_with_timeout(tool_name, tool_input, timeout_seconds):
    - Wraps _execute_tool inside asyncio.wait_for when a timeout is configured.
- _get_tool_timeout_seconds(tool_name):
    - Uses self.tool_settings (from ToolsSettings in backend/app/config/settings.py) to choose:
        - web_search_timeout_seconds or default tool_execution_timeout_seconds.

Tool output shape:

- Typically a dict containing:
    - Structured results (results, papers, repositories, or extracted text).
    - notes: additional comments from tools or content pipeline.
    - pipeline_stats: details about classification, extraction, summarization, ranking.
- ResearcherAgent._summarize_tool_output(tool_name, tool_output):
    - Returns a one‑line summary stored in trace events and shown in the UI.

### 6.3 Content Pipeline

Class:

- ContentPipeline — backend/app/content/pipeline.py.

Constructor:

- Created in _run_research_session(...) with:
    - llm_manager, top_k=10, max_content_length=5000, cache_ttl_minutes=15, enable_cache=True.

Method:

- async def process(self, items: List[Dict[str, Any]], query: str) -> Dict[str, Any].

Pipeline stages:

1. Classification:
    - ContentClassifier.classify_batch(...) — classifier.py.
2. Cache check:
    - ContentCache — cache.py.
3. Extraction:
    - ContentExtractor.extract_batch(...) — extractor.py.
4. Summarization:
    - ContentSummarizer.summarize_batch(...) — summarizer.py, uses llm_manager to generate short summaries conditioned on the query.
5. Ranking:
    - ContentRanker.rank(...) — ranker.py, selects top‑K items.
6. Output:
    - Returns dict with:
        - top_items, all_summaries, stats, notes.

For tools like web_search and github_search, when content_pipeline is passed, their implementations call pipeline.process(...) to:

- Normalize heterogeneous tool outputs into structured, ranked evidence.
- Provide the agent with richer, pre‑summarized context for the final report.

———

## 7. Evaluator Agent (LLM‑as‑Judge)

> Main references: backend/app/agents/evaluator_agent.py and backend/app/agents/models.py.

### 7.1 Role of EvaluatorAgent

- Class: EvaluatorAgent — evaluator_agent.py.
- Constructor: __init__(self, llm_manager: LLMManager).
- Main method:
    - async def evaluate_end_to_end(self, result: ResearchResult) -> EndToEndEval.
    - async def evaluate_research(self, result: ResearchResult, evaluate_steps: bool = False) -> EvaluationResult.

Goal:

- Provide an LLM‑as‑judge evaluation of the final research report, not per‑step right now.
- Score the report across four dimensions:
    - Relevance, Accuracy, Completeness, Source Quality (each 0–1).
- Generate qualitative feedback (strengths, weaknesses, recommendations).

### 7.2 End‑to‑End Evaluation Flow

Prompt:

- Constant: EvaluatorAgent.END_TO_END_PROMPT — evaluator_agent.py.
- Template includes:
    - Query.
    - Final report (truncated).
    - Source list (up to 20).
    - Instructions to rate:
        - relevance_score, accuracy_score, completeness_score, source_quality_score (0–1 each).
    - Instructions to produce:
        - Arrays: strengths, weaknesses, recommendations.

Evaluation logic:

- Function: async def evaluate_end_to_end(self, result: ResearchResult) -> EndToEndEval.
    - Builds sources_str from result.sources[:20].
    - Fills the prompt template with:
        - query=result.query
        - report=result.report[:5000] (size‑limited)
        - num_sources=len(result.sources)
        - sources=sources_str.
    - Calls:

    response = await self.llm.complete(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
        require_content=True,
    )
    - Parses JSON with _parse_json_response(response["content"]).
        - Handles plain JSON, json fenced blocks, or simple ``` blocks.
    - Creates an EndToEndEval dataclass (backend/app/agents/models.py) with:
        - Scores (clamped to [0,1] using _clamp_score).
        - strengths, weaknesses, recommendations.
        - tokens_used=response["usage"]["total_tokens"].
        - cost_usd=self.llm.estimate_cost(...).

Public wrapper:

- async def evaluate_research(self, result: ResearchResult, evaluate_steps: bool = False) -> EvaluationResult:
    - Currently calls only evaluate_end_to_end.
    - Wraps in EvaluationResult(session_id=result.session_id, end_to_end_evaluation=end_to_end_eval).

### 7.3 Output Models and Persistence

Data models:

- EndToEndEval and EvaluationResult are defined in backend/app/agents/models.py.
- Fields:
    - EndToEndEval: scores, qualitative lists, tokens_used, cost_usd.
    - EvaluationResult: session_id, end_to_end_evaluation: EndToEndEval.

Persistence:

- In _run_research_session (research route), after evaluation:
    - save_end_to_end_evaluation(session_id=session_id, evaluation={...}) — DB helper (backend/app/database).
- API exposure:
    - Endpoint: GET /api/research/{session_id}/evaluation — backend/app/api/routes/research.py, function get_evaluation.
    - Response model: EvaluationResponse / EndToEndEvaluationResponse — backend/app/api/models/responses.py.

Metrics integration:

- When metrics are finalized:
    - The evaluation scores feed into MetricsData (backend/app/metrics/models.py), fields:
        - relevance_score, accuracy_score, completeness_score, source_quality_score.
    - This enables:
        - Historical analysis via MetricsAnalyzer.
        - Reporting in the frontend metrics dashboard.

———

## 8. Persistence, Tracing & Metrics

### 8.1 Session & Trace Storage

Database helpers (async functions in backend/app/database) manage:

- create_session(...) — insert new session with query and config.
- get_session(session_id) — retrieve session metadata and results.
- update_session(...) — set status, timestamps, totals, report, sources.
- save_trace_event(...) — persist each trace event from _emit_trace.
- get_session_trace(session_id) — returns ordered trace events.
- save_end_to_end_evaluation(...), get_session_evaluations(...) — handle evaluation persistence.

### 8.2 Trace API

Endpoints in backend/app/api/routes/research.py:

- GET /api/research/{session_id}/trace — get_trace(session_id).
    - Uses get_session_trace to load events.
    - Maps DB records to TraceEventResponse objects (type, iteration, data, timestamp).
    - Response model: TraceResponse (list of events + count).

These events are consumed by the frontend to:

- Build the ReAct Trace timeline.
- Update the workflow chart for session replay.

### 8.3 Metrics Collection

Collector:

- MetricsCollector — backend/app/metrics/collector.py.

Key methods:

- start_session(query) and end_session(final_report) — mark session times.
- record_tool_execution(tool_name, duration, success, results_count, metadata) — called by ResearcherAgent.
- record_llm_call(provider, input_tokens, output_tokens, cost, model) — should be called by providers or the agent; aggregated per provider.
- add_sources(...), add_iteration(...).
- finalize(evaluation_result):
    - Computes MetricsData:
        - Duration, iterations, tool metrics, provider metrics, source metrics, report metrics, and quality scores.

MetricsData is then:

- Stored via a metrics history helper (e.g., append_run(snapshot)).
- Partially included in the WebSocket completion message (as metrics).

———

## 9. Real‑Time Transport Layer (WebSocket & SSE)

> File: backend/app/api/websocket.py, class ConnectionManager.

### 9.1 Connection Manager

Responsibilities:

- Track WebSocket connections per session:
    - self.active_connections: Dict[str, Set[WebSocket]].
- Maintain message queues for offline clients:
    - self.message_queues: Dict[str, list].
- Manage SSE subscribers:
    - self.sse_subscribers: Dict[str, List[asyncio.Queue]].

Key methods:

- async def connect(websocket, session_id).
- def disconnect(websocket, session_id).
- async def broadcast_to_session(session_id, message) — sends to all WebSocket and SSE subscribers, or queues if none connected.
- async def send_trace_event(session_id, event_type, data):
    - Wraps trace event into a standardized message:
        - {"id", "type", "session_id", "data", "message", "timestamp", "iteration"}.
- async def send_completion(session_id, result) — sends final completion event.
- async def send_error(session_id, error_message, error_type) — sends error event.
- async def send_progress_update(...) — status/progress events.

### 9.2 Transport Endpoints

Router: router = APIRouter(prefix="/ws", tags=["WebSocket"]) in websocket.py.

- WebSocket endpoint:
    - @router.websocket("/{session_id}") → websocket_endpoint(websocket, session_id).
    - Uses manager.connect and manager.disconnect.
    - Receives messages (e.g., ping, subscribe) and responds appropriately.
- SSE endpoint:
    - @router.get("/{session_id}/stream") → sse_endpoint(session_id).
    - Registers an asyncio.Queue via manager.register_sse(session_id).
    - Returns a StreamingResponse that emits data: lines for each queued message.

———

## 10. Frontend Overview (Next.js Research UI)

> Main folders: frontend/src/app, frontend/src/components, frontend/src/stores, frontend/src/types.

### 10.1 High‑Level Responsibilities

- Provide a UI to:
    - Input query and settings.
    - Visualize the ReAct agent’s internal loop.
    - Display metrics, evaluation, and final report.
- Maintain synchronized views:
    - WorkflowChart — stage‑level, horizontal pipeline view.
    - ReactTraceTimeline — iteration‑level, detailed ReAct view.

### 10.2 Key Frontend Modules

- Research components: frontend/src/components/research/:
    - query-input.tsx
    - current-activity-panel.tsx
    - react-trace-timeline.tsx
    - metrics-dashboard.tsx
    - research-output-panel.tsx
    - settings-modal.tsx
- Workflow visualization: frontend/src/components/workflow/:
    - WorkflowChart.tsx
    - WorkflowNode.tsx
    - ConnectionLine.tsx
    - LoopArc.tsx
    - constants.ts
- State management:
    - frontend/src/stores/workflowStore.ts — workflow visualization state.
    - Additional stores under frontend/src/store / frontend/src/stores.
- Shared types:
    - frontend/src/types/index.ts.

———

## 11. Frontend Data Flow & State Management

### 11.1 WebSocket Client & Event Handling

The frontend subscribes to the backend’s WebSocket endpoint /ws/{sessionId} using the URL provided by StartResearchResponse (websocket_url).

Events coming over the socket:

- Conform to ResearchUpdate and WebSocketEventType defined in frontend/src/types/index.ts.
    - Types include:
        - 'session_start', 'iteration_start', 'thought', 'action', 'tool_execution', 'observation', 'finish', 'session_complete', 'completion', 'session_failed', 'error', etc.

Client code:

- Parses incoming JSON messages into ResearchUpdate objects.
- Dispatches events to:
    - workflowStore.handleEvent(...).
    - Other stores for metrics, report, and activity panels.

### 11.2 Global Stores

Workflow store:

- File: frontend/src/stores/workflowStore.ts.
- Uses Zustand: export const useWorkflowStore = create<WorkflowStore>((set) => ({ ... })).

WorkflowState includes:

- sessionId, query.
- iteration info: current, max, totalCompleted.
- nodes for each stage (start, think, operate, reflect, evaluator, finish), with NodeState.
- edges for each connection (start->think, think->operate, operate->reflect, reflect->evaluator, evaluator->finish, reflect->think), with EdgeState.
- stats and eventHistory.

WorkflowStore adds:

- handleEvent(event: WorkflowEvent) — main reducer entrypoint.
- reset().

### 11.3 Event → Store Mapping

Event types:

- WorkflowEvent union in workflowStore.ts:
    - SessionStartEvent, IterationStartEvent, ThoughtEvent, ActionEvent, ToolExecutionEvent, ObservationEvent, FinishGuardEvent, FinishEvent, EvaluatorStartEvent, EvaluatorCompleteEvent, ToolBlockedEvent,
    ErrorEvent, SessionCompleteEvent, SessionFailedEvent.

Reducer:

- workflowReducer(state: WorkflowState, event: WorkflowEvent): WorkflowState.

Core patterns:

- On 'session_start':
    - Resets state; sets sessionId, query, iteration.max from the event.
    - Resets all nodes and edges to idle.
- On 'iteration_start':
    - Updates iteration.current.
    - Marks think node as active, resets downstream nodes.
    - Activates edge start->think or reflect->think depending on whether this is first iteration or a loop.
- On 'thought':
    - Marks think as completed; operate as active.
    - Activates think->operate edge, deactivates start->think / reflect->think.
    - Stores thought text in nodes.think.metadata.thought.
- On 'action':
    - Updates nodes.operate.metadata.selectedTool and startTime.
- On 'tool_execution':
    - Marks operate completed or error.
    - If success:
        - Activates reflect node.
        - Updates nodes.operate.metadata.provider, duration, resultCount.
- On 'observation':
    - Stores observation text in nodes.reflect.metadata.observation.
- On 'finish':
    - Marks think, operate, reflect completed; sets reflect decision to 'finish'.
    - Activates edge reflect->evaluator.
    - Stores report and source counts in pendingFinish.
- On 'evaluator_start' / 'evaluator_complete':
    - Moves activity to evaluator node.
    - On completion, marks finish node completed and sets report metadata.
- On 'session_complete' / 'session_failed':
    - Updates stats and eventHistory.

This reducer is the single source of truth for how backend trace events affect the workflow chart’s state.

———

## 12. Workflow Chart: Backend–Frontend Stage Mapping

> Main files: frontend/src/components/workflow/WorkflowChart.tsx, frontend/src/stores/workflowStore.ts, frontend/src/components/workflow/constants.ts.

### 12.1 Workflow Nodes and Edges

Node IDs (NodeId in workflowStore.ts):

- 'start' | 'think' | 'operate' | 'reflect' | 'evaluator' | 'finish'.

Edge IDs (EdgeId):

- 'start->think'
- 'think->operate'
- 'operate->reflect'
- 'reflect->evaluator'
- 'evaluator->finish'
- 'reflect->think' (loopback edge).

Each node has a NodeState:

- status: 'idle' | 'active' | 'completed' | 'error' | 'skipped'.
- visitCount, currentVisitIteration, lastCompletedAt.
- Visual flags: showPulse, showGlow.
- metadata with thought, tool, provider, durations, evaluation scores, etc.

Each edge has an EdgeState:

- status: 'idle' | 'active' | 'completed' | 'disabled'.
- showFlowAnimation, transitionCount.
- Style attributes, e.g., strokeWidth, opacity.

### 12.2 From Backend Events to Workflow Stages

Mapping between backend event types and the chart:

- iteration_start:
    - Triggers 'start' → 'think' movement.
    - In workflowReducer, case 'iteration_start':
        - Sets nodes.think.status = 'active'.
        - Activates start->think or reflect->think edge.
- thought:
    - Maps to 'think' → 'operate':
        - Marks think completed, operate active.
        - Activates think->operate edge.
- action:
    - Keeps operate active and sets selectedTool, startTime.
- tool_execution:
    - Maps 'operate' → 'reflect':
        - On success, marks operate completed, reflect active.
        - Activates operate->reflect edge.
- observation:
    - Adds observation text to reflect metadata.
- finish:
    - Maps 'reflect' → 'evaluator':
        - Marks earlier nodes completed.
        - Activates reflect->evaluator edge and sets pendingFinish.
- evaluator_start / evaluator_complete:
    - Drive 'evaluator' → 'finish':
        - On complete, evaluator and finish nodes become completed.
        - Activates evaluator->finish edge.

The STAGE_EVENT_MAP in ResearcherAgent guides this relationship, and workflowReducer reflects it in the UI state.

### 12.3 Looping & Progress Calculation

Loop arc:

- Component: LoopArc — frontend/src/components/workflow/LoopArc.tsx.
- Visibility logic in WorkflowChart (loopVisibility):
    - Uses edges['reflect->think'] and nodes.reflect, nodes.finish.
    - Shows arc as:
        - 'hidden' before first loop.
        - 'active' when loop edge is active.
        - 'pulsing' when reflect is active.
        - 'dormant' after at least one loop.

Progress bar:

- In WorkflowChart.tsx, workflowProgress is computed with:
    - 90% of progress from iterations, 10% from finish.
    - progressPerIteration = 90 / maxIterations.
    - baseProgress = completed iterations × progressPerIteration.
    - Within current iteration, stage weights:
        - think: 0.25, operate: 0.65, reflect: 0.9.
    - Total progress capped at 90% until finish node is completed (then 100%).

This ensures progress never goes backwards, even when loops occur.

### 12.4 Visual Behavior & Metadata

Nodes display:

- Iteration badges (visitCount, currentVisitIteration).
- Pulse/glow for active stages.
- Metadata such as:
    - thought text for think.
    - selectedTool, provider, duration, resultCount for operate.
    - observation for reflect.
    - Evaluation scores and durations for evaluator.
    - reportLength and sourceCount for finish.

All of this metadata is derived from backend event data fields passed through workflowReducer.

———

## 13. React Trace Timeline: Iteration‑Level View

> File: frontend/src/components/research/react-trace-timeline.tsx. Types: Iteration in frontend/src/types/index.ts.

### 13.1 Iteration Model

Type definition:

- interface Iteration — frontend/src/types/index.ts:
    - id, index, status: IterationStatus.
    - thought: Thought, action: Action, observation: Observation.
    - evaluation?: PerStepEvaluation (currently unused as per‑step evaluation is disabled).
    - duration, timestamp.

These are derived by combining multiple backend events (thought, action, tool_execution, observation, and completion markers) into a single logical “iteration” object managed in frontend state.

### 13.2 Rendering the ReAct Trace

Component: ReactTraceTimeline — react-trace-timeline.tsx.

Props:

- iterations: Iteration[].

Behavior:

- Shows:
    - Total number of iterations.
    - Total duration (sum of iteration.duration).
- For each iteration:
    - Renders IterationCard with:
        - Status badges (active, complete, failed).
        - Duration.
    - Inside an expanded card:
        - THOUGHT phase:
            - PhaseCard with iteration.thought.content, tokens, latency.
        - ACTION phase:
            - Shows iteration.action.toolName and serialized toolParams.
        - EXECUTION phase:
            - Summary from iteration.action.result?.summary or error text.
            - Duration and result count.
        - OBSERVATION phase:
            - iteration.observation.content.
        - EVALUATION phase (if present):
            - toolSelectionScore, toolExecutionScore, progressScore, informationGain.

### 13.3 Synchronization with Workflow Chart

Both the ReactTraceTimeline and WorkflowChart:

- Consume the same stream of backend events:
    - WebSocket messages of types:
        - 'iteration_start', 'thought', 'action', 'tool_execution', 'observation', 'finish', 'evaluator_start', 'evaluator_complete', 'session_complete', 'session_failed', etc.
- Use shared timestamps and iteration numbers to correlate events.

Conceptually:

- WorkflowChart: aggregated stage‑level view per iteration.
- ReactTraceTimeline: detailed per‑iteration view of the underlying ReAct phases (THOUGHT, ACTION, EXECUTION, OBSERVATION, optional EVALUATION).

———

## 14. Putting It Together: Example End‑to‑End Walkthrough

1. User submits query via UI:
    - Frontend sends POST /api/research/start with StartResearchRequest.
2. Backend creates session:
    - start_research → create_session → returns session_id and websocket_url.
3. Frontend opens WebSocket to /ws/{session_id}:
    - Receives session_start and iteration_start events.
    - workflowStore.handleEvent('session_start') sets up nodes.
    - Workflow chart shows the first iteration starting.
4. First ReAct iteration:
    - Backend:
        - Calls LLMManager.complete with SYSTEM_PROMPT and initial user query.
        - Gets THOUGHT + tool_calls.
        - Emits thought trace → WebSocket.
    - Frontend:
        - Updates think node as completed, operate active.
        - ReactTraceTimeline displays the THOUGHT text.
5. Tool call (e.g., web_search):
    - Backend:
        - Executes web_search, possibly via ContentPipeline.
        - Emits action and then tool_execution trace with result_summary.
        - Formats observation and emits observation trace.
    - Frontend:
        - Workflow chart moves through operate → reflect.
        - ReActTrace shows ACTION parameters, EXECUTION summary, OBSERVATION narrative.
6. Subsequent iterations:
    - Same pattern until:
        - Either finish is called explicitly by the LLM.
        - Or _force_finish_if_needed triggers auto‑finish.
7. Finish & evaluation:
    - Backend:
        - Emits finish trace with report_length and num_sources.
        - Runs EvaluatorAgent.evaluate_research.
        - Emits evaluator_start and evaluator_complete events.
        - Sends completion WebSocket message with report, sources, metrics, evaluation.
    - Frontend:
        - Workflow chart moves through evaluator to finish, progress hits 100%.
        - ReactTrace shows the final iteration’s THOUGHT/ACTION/OBSERVATION.
        - Output panel displays the report and evaluation scores.

———

## 15. Extensibility & Customization

### 15.1 Adding New Tools or Agents

- Add a new tool implementation under backend/app/tools/.
- Register its schema in backend/app/tools/definitions.py and extend get_all_tool_definitions().
- Add routing logic in ResearcherAgent._execute_tool.
- Optionally update _derive_tool_policy, _is_tool_allowed, and STAGE_EVENT_MAP if the tool introduces a new stage or domain.

### 15.2 Changing LLM Providers or Models

- Update .env and config.yaml / config.example.yaml to configure LLMManager:
    - primary provider.
    - Provider‑specific model, temperature, max_tokens.
- LLMManager.__init__ will wire providers accordingly.
- You can override provider/model per session via StartResearchRequest.config or legacy fields.

### 15.3 Adapting the Workflow Visualization

- To add or adjust stages:
    - Update NodeId and EdgeId in workflowStore.ts.
    - Adjust NODE_POSITIONS and NODE_LABELS in frontend/src/components/workflow/constants.ts.
    - Update workflowReducer to handle new WorkflowEvent types.
- To add new trace events:
    - Emit them in _emit_trace or inside _run_research_session.
    - Extend WorkflowEvent union and corresponding reducer cases.

———

This document should give you both a conceptual understanding of the research workflow and concrete pointers into the code. You can use the file and function references to explore specific behaviors more
deeply—for example, reading ResearcherAgent.research alongside WorkflowChart.tsx and workflowStore.ts to see exactly how backend ReAct iterations drive the frontend’s visual stages.