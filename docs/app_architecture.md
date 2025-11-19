# Agentic Research Lab – Application Architecture and Design

This document explains how the Agentic Research Lab works end‑to‑end, with a strong focus on the backend agent system and how it drives the frontend workflow chart and ReAct trace views. It assumes high‑level familiarity with LLMs, tools, and the ReAct pattern, but only basic coding knowledge.

---

## 1. Purpose and High‑Level Overview

- **Goal**: Turn a natural‑language research query into a structured, well‑sourced report.
- **Core idea**: A **Researcher agent** (ReAct pattern) iteratively reasons and uses tools, then an **Evaluator agent** performs a quality review on the final report.
- **User experience**:
  - User submits a query from the web UI.
  - Backend starts a **research session** and runs the agents in the background.
  - The frontend receives **live events** over WebSockets/SSE and visualizes:
    - A **horizontal workflow chart** (THINK → OPERATE → REFLECT → EVALUATOR → FINISH).
    - A **ReAct trace timeline** showing Thought → Action → Observation per iteration.
  - When finished, the user sees a report, metrics, and evaluation scores.

Key concepts:

- **Session**: One complete run from query to final report.
- **Iteration**: One ReAct loop of thought → tool action → observation.
- **Trace event**: A structured record of something that happened (e.g. "thought", "tool_execution").
- **Evaluation**: End‑to‑end quality assessment of the final report.

---

## 2. End‑to‑End Research Session Flow

### 2.1 High‑Level Journey

1. **User submits a query**
   - Frontend sends `POST /api/research/start` with the query and optional overrides (e.g. preferred provider, model, max iterations).
2. **Backend creates a research session**
   - Session is stored in the DB with status `running`.
   - A background task is launched to run the research logic.
   - Backend returns:
     - `session_id`
     - `websocket_url` (`/ws/{session_id}`) for live updates.
3. **Frontend connects for live updates**
   - The React app uses a `useWebSocket` hook to connect to `/ws/{session_id}` (or SSE `/ws/{session_id}/stream`).
   - All real‑time messages are normalized into a `ResearchUpdate` structure.
4. **Researcher agent runs the ReAct loop**
   - For each iteration:
     - THINK: Reason about what to do next.
     - ACT: Call tools (web search, arxiv, github, PDF, content pipeline).
     - OBSERVE: Interpret tool outputs.
     - Decide whether to **loop** or **finish**.
   - Each stage produces **trace events** that the frontend visualizes.
5. **Evaluator agent runs the quality review**
   - Once the Researcher calls `finish`, the Evaluator reviews the final report.
   - It outputs scalar scores (relevance, accuracy, completeness, source quality) and qualitative feedback.
6. **Session completes**
   - Backend emits a `completion`/`session_complete` event with the final report and metrics.
   - DB is updated with report, sources, cost, and iteration counts.
7. **User reviews results**
   - ReAct trace timeline shows how the answer was built.
   - Workflow chart shows how many iterations were needed and where the evaluator stepped in.
   - Metrics dashboard aggregates latency, tool usage, and evaluation scores.

---

## 3. Backend Architecture Overview

The backend is a FastAPI application (`backend/app`) with the following key modules:

- **API Layer (`app/api`)**
  - `routes/research.py` – session lifecycle (start, status, trace, evaluation).
  - `websocket.py` – real‑time transport (WebSockets + SSE).
  - `models/requests.py` and `models/responses.py` – typed API contracts.
- **Agent Layer (`app/agents`)**
  - `react_agent.py` – **ResearcherAgent**, the main ReAct loop.
  - `evaluator_agent.py` – **EvaluatorAgent**, end‑to‑end quality assessment.
  - `models.py` – data structures for steps, results, and evaluations.
- **LLM Layer (`app/llm`)**
  - `manager.py` – **LLMManager**, orchestrates OpenAI, Gemini, and OpenRouter with fallback.
  - `openai_provider.py`, `gemini_provider.py`, `openrouter_provider.py` – provider integrations.
- **Tools Layer (`app/tools`)**
  - `web_search.py`, `arxiv_search.py`, `github_search.py`, `pdf_parser.py` – domain tools.
  - `definitions.py` – tool schemas for function‑calling.
- **Supporting Modules**
  - `app/content` – optional content pipeline for pre‑retrieval/aggregation.
  - `app/metrics` – metrics collection and history snapshots.
  - `app/database` – session, trace, and evaluation persistence.
  - `app/config/settings.py` – structured application settings.

Key design choice: the **ResearcherAgent** is a pure orchestrator of tools + LLM, while the **API** and **WebSocket manager** focus on IO, transport, and persistence.

---

## 4. Research Session Lifecycle in the Backend

### 4.1 Starting a Session (`POST /api/research/start`)

**Endpoint**: `backend/app/api/routes/research.py: start_research`

Inputs (via `StartResearchRequest`):
- `query` – the user’s research question.
- Optional overrides:
  - `config.llm` – provider, model, temperature, fallback order.
  - `config.research` – max_iterations, timeout_minutes.
  - Legacy shortcuts: `llm_provider`, `llm_model`, `temperature`, `max_iterations`.

Main steps:

1. **Normalize configuration**
   - `_normalize_request_config` merges legacy fields into a structured `config` block.
2. **Prepare session context**
   - `_prepare_session_context`:
     - Clones base `Settings`.
     - Applies per‑session overrides for LLM provider/model and research parameters.
     - Creates a **session‑specific LLMManager** if provider/model changed.
3. **Create session record**
   - `create_session` stores the session in the DB:
     - `id`, `query`, `status="running"`, `config`, timestamps.
4. **Mark as active**
   - An in‑memory `_active_sessions` dict is updated: `session_id → True`.
5. **Launch background research task**
   - FastAPI `BackgroundTasks` schedules `_run_research_session(session_id, query, session_settings, session_llm_manager, llm_temperature)`.
6. **Return handle to client**
   - `StartResearchResponse`:
     - `session_id`
     - `websocket_url` (e.g. `/ws/{session_id}`)
     - `status="running"`

From this point on, the frontend uses the `session_id` and WebSocket URL to subscribe to live events.

### 4.2 Monitoring and Managing Sessions

- **Status** – `GET /api/research/{session_id}` returns `SessionResponse` with query, status, timestamps, totals, and final report.
- **Trace** – `GET /api/research/{session_id}/trace` returns a `TraceResponse` with all persisted trace events.
- **Evaluation** – `GET /api/research/{session_id}/evaluation` returns `EvaluationResponse` with end‑to‑end scores and feedback.
- **Cancel** – `POST /api/research/{session_id}/cancel` marks the session inactive and sets status `cancelled`.
- **Delete** – `DELETE /api/research/{session_id}` marks the session as `deleted` (trace/eval cleanup is TODO).

---

## 5. ResearcherAgent: ReAct Loop and Tool Use

The **ResearcherAgent** (`backend/app/agents/react_agent.py`) implements the ReAct pattern:

> Think → Act (tool calls) → Observe → Repeat or Finish.

This is the core of the backend logic and the main driver of both the ReAct trace and the workflow chart.

### 5.1 Inputs and Configuration

The ResearcherAgent is constructed with:

- **LLMManager** – decides which LLM provider/model to call, with fallback.
- **Research settings** – `max_iterations`, `timeout_minutes` (from `Settings.research`).
- **Tool settings** – which tools are enabled, timeouts, safety rules.
- **Trace callback** – async function that persists trace events to the DB.
- **WebSocket manager** – broadcasts live events to the frontend.
- **Content pipeline** (optional) – pre‑retrieval and caching layer across tools.
- **LLM temperature override** – per‑session reasoning temperature.

Session‑specific overrides (provider, model, max iterations, temperature) are injected from `_run_research_session` using `_prepare_session_context`.

### 5.2 Conversation Setup and System Prompt

For each session, the agent:

1. Associates the persistent `session_id` with itself.
2. Initializes `conversation_history` with:
   - A **system message** containing the `SYSTEM_PROMPT`:
     - Explains the ReAct loop discipline.
     - Describes available tools and their intended use.
     - Specifies citation format and report structure.
   - A **user message** that contains the query and asks the agent to restate the plan and begin reasoning.
3. Optionally injects more system messages:
   - Domain guidance (e.g., when to use GitHub vs arXiv).
   - Recency hints and date filters.

This provides the LLM with an explicit "operating manual" for how to research.

### 5.3 Core ReAct Loop (Per Iteration)

The main method `research(query, session_id=...)` executes a loop until either:

- The final report is produced and approved, or
- Max iterations or timeout is reached, or
- The session is externally cancelled.

Within the loop:

1. **Session and iteration start**
   - At the very beginning:
     - Emit `session_start` trace with `{ session_id, query, timestamp }`.
     - This seeds the DB trace and wakes up the workflow chart (start → think).
   - For each iteration:
     - Increment `iteration` counter.
     - Emit `iteration_start` trace with `{ iteration, mode, message }`.
     - Frontend interprets this as "THINK phase starting" for that iteration.

2. **Reasoning step (THOUGHT)**
   - Clean up any dangling tool calls in `conversation_history`.
   - Optionally add a user "continue" prompt and domain guidance.
   - Call `LLMManager.complete(...)` with:
     - Current conversation history.
     - Tool definitions for function‑calling.
     - `require_tool_calls=True`, `require_content=True`.
   - Receive:
     - A **thought** (LLM content text).
     - One or more **tool calls** (functions with JSON arguments).
     - Usage stats (tokens, provider, model).
   - Emit `thought` trace event:
     - Data includes `thought`, `tokens_used`, `provider`, `latency_ms`.
   - Frontend effects:
     - ReAct trace: THOUGHT block for the current iteration.
     - Workflow chart: THINK node is completed, OPERATE node becomes active.

3. **Tool selection and ACTION/EXECUTION**
   - For each suggested tool call:
     - Apply safety and policy checks (e.g., "tool blocked" for disallowed calls).
     - Emit `action` trace with `{ tool, parameters }`.
     - Execute the tool with a per‑tool timeout via `_execute_tool_with_timeout`:
       - `web_search`, `arxiv_search`, `github_search`, `pdf_to_text`, or content pipeline calls.
     - On completion or timeout, emit `tool_execution` trace with:
       - `tool`, `duration_ms`, `success`, `result_summary`, `provider`, `result_count`.
   - Frontend effects:
     - ReAct trace: ACTION block (tool selection) and EXECUTION block (result summary).
     - Workflow chart:
       - OPERATE node transitions from active → completed (or error).
       - `think->operate` and `operate->reflect` edges animate and update status.

4. **Observation and REFLECT**
   - The agent synthesizes tool outputs into an "observation" describing:
     - What was learned.
     - What remains unclear.
   - Emit `observation` trace with `{ observation }`.
   - Frontend effects:
     - ReAct trace: OBSERVATION block for the iteration.
     - Workflow chart: REFLECT node obtains `metadata.observation` and becomes active.

5. **Finish guard and loop decision**
   - When the LLM proposes the `finish` tool:
     - A "finish guard" checks whether it is actually safe to stop:
       - Are key aspects covered?
       - Are sources sufficient and diverse?
     - Emit `finish_guard` trace with `{ approved, feedback, hint? }`.
   - If `approved = false`:
     - Decision: **loop again**.
     - Workflow chart:
       - REFLECT node metadata records decision `"iterate"`.
       - `reflect->think` edge becomes active, loops back to THINK.
       - `iteration.current` is incremented.
   - If `approved = true`:
     - Decision: **proceed to finish and evaluation**.
     - Workflow chart:
       - REFLECT node metadata records decision `"finish"`.
       - `reflect->evaluator` edge becomes active, pushing flow toward the evaluator node.

6. **Final report construction (FINISH)**
   - When finishing is approved, the agent:
     - Collates evidence and internal notes into a final **report**.
     - Produces a list of **sources**.
   - Emit `finish` trace with:
     - `report`, `sources`, `report_length`, `num_sources`.
   - Frontend effects:
     - ReAct trace: the last iteration includes an ACTION/EXECUTION pair for `finish` and a final OBSERVATION.
     - Workflow chart:
       - THINK/OPERATE/REFLECT nodes are set to completed for the final iteration.
       - `reflect->evaluator` edge is activated if not already.

7. **Aggregating results**
   - All iterations are materialized as a list of `AgentStep` objects.
   - A `ResearchResult` is returned, containing:
     - Final `report` and `sources`.
     - `steps`, `total_iterations`, `total_duration_seconds`.
     - Aggregated `total_tokens` and `total_cost_usd`.
     - Final `status` (completed/failed/timeout).

### 5.4 What the ReAct Trace and Workflow Chart Are Really Showing

- The **ReAct trace timeline** is a per‑iteration lens on the loop:
  - Each `THOUGHT`/`ACTION`/`EXECUTION`/`OBSERVATION` block corresponds to `thought`, `action`, `tool_execution`, `observation` events emitted by the ResearcherAgent.
- The **workflow chart** is a high‑level state machine:
  - Nodes (THINK/OPERATE/REFLECT/EVALUATOR/FINISH) light up and complete based on those same events.
  - Looping behaviour (reflect → think) is driven by `iteration_start` + `finish_guard` events.

---

## 6. EvaluatorAgent: End‑to‑End Quality Review

The **EvaluatorAgent** (`backend/app/agents/evaluator_agent.py`) performs a holistic evaluation of the final report after the ReAct loop finishes.

### 6.1 When and How the Evaluator Runs

Within `_run_research_session` (in `routes/research.py`):

1. After the ResearcherAgent returns a successful `ResearchResult`, an EvaluatorAgent is created using the same `LLMManager`.
2. Before evaluation starts:
   - Emit `evaluator_start` trace with `{ message: "Evaluator agent started" }`.
   - Immediately broadcast via WebSocket.
   - Workflow chart response:
     - REFLECT node’s pulse stops.
     - EVALUATOR node becomes active.
     - `reflect->evaluator` edge animates.
3. Call `evaluate_research(result, evaluate_steps=False)`:
   - The evaluator reads the **final report** (and optionally structured metadata) and produces an end‑to‑end assessment.
   - Per‑step evaluation is intentionally disabled in this configuration to keep evaluation cost bounded.

### 6.2 Evaluation Dimensions and Output

The evaluator returns an `EvaluationResult` with an `EndToEndEval`:

- **Quantitative scores (0–1)**:
  - `relevance_score` – does the report stay focused on the query?
  - `accuracy_score` – how factually correct and faithful to sources is it?
  - `completeness_score` – are major angles and sub‑questions covered?
  - `source_quality_score` – are the sources credible, varied, and appropriate?
- **Qualitative feedback**:
  - `strengths` – what the report does particularly well (e.g., strong structure, clear comparisons).
  - `weaknesses` – gaps, missing perspectives, or potential inaccuracies.
  - `recommendations` – how a human researcher could deepen or refine the work.
- **Cost metadata**:
  - `tokens_used`, `cost_usd` for the evaluation itself.

This output is small but expressive: ideal for dashboards and as a quick quality signal to users.

### 6.3 Persisting and Broadcasting Evaluation

After evaluation completes:

1. The backend measures evaluation duration.
2. It constructs an `evaluator_complete` payload containing:
   - `message` – human‑readable summary.
   - `duration_seconds`.
   - `scores` – with keys `relevance`, `accuracy`, `completeness`, `source_quality` derived from the 0–1 scores.
3. Two things happen:
   - **Trace persistence**:
     - `save_trace_event` stores an `evaluator_complete` event for the session.
   - **Real‑time broadcast**:
     - `websocket_manager.send_trace_event(session_id, "evaluator_complete", data)` sends the event to connected clients.

Frontend effects:

- Workflow chart:
  - EVALUATOR node transitions to completed, with metadata:
    - `evaluationScores` (the 4 scores).
    - `evaluationDuration`.
  - FINISH node is marked completed, picking up `reportLength` and `sourceCount` from pending finish metadata.
- Metrics dashboard:
  - Includes evaluation scores alongside latency, token, and cost metrics.

4. **Persistence in the evaluation store**
   - `save_end_to_end_evaluation` writes the evaluation into the DB with:
     - Scores, strengths, weaknesses, recommendations.
     - Tokens and cost.
   - `GET /api/research/{session_id}/evaluation` exposes this as `EvaluationResponse`.

### 6.4 Conceptual Role in the System

- The ResearcherAgent focuses on **coverage and synthesis**.
- The EvaluatorAgent focuses on **quality and trustworthiness**.
- Together they form a two‑agent architecture where:
  - One agent builds a strong draft report.
  - The other acts as a reviewer, providing a lightweight but structured quality bar.

---

## 7. LLM Orchestration and Provider Strategy

The **LLMManager** (`backend/app/llm/manager.py`) is the abstraction that lets agents treat "the LLM" as a single service, even though multiple providers and models may be involved behind the scenes.

### 7.1 Supported Providers and Configuration

Providers:

- **OpenAI** – models like `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`.
- **Gemini** – `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-pro`.
- **OpenRouter** – typically configured with `nvidia/llama-3.3-nemotron-super-49b-v1.5` and optional alternates.

Configuration (per session) includes:

- `primary` – which provider to try first.
- `fallback_order` – ordered list of backup providers.
- Per‑provider settings – API key, model name, temperature, max tokens.

### 7.2 Per‑Session Overrides (from the API)

`_prepare_session_context` applies overrides from the start request:

- `config.llm.provider` – override the primary provider.
- `config.llm.model` – request a specific model for that provider.
- `config.llm.fallback_order` – explicit fallback sequence.
- `config.llm.temperature` – used as the agent’s `llm_temperature`.
- `config.research.max_iterations` / `timeout_minutes` – adjust ReAct loop limits.

Model overrides are validated against `VALID_MODEL_OVERRIDES` to avoid unsupported names. If a requested model is not allowed, the system logs a warning and keeps the configured default.

If any of provider/model/fallback overrides are present, a new **session‑scoped LLMManager** is created so these changes do not affect other sessions.

### 7.3 Fallback and Provider Failover Logic

When an agent calls `LLMManager.complete(...)`:

1. Build a provider sequence:
   - Start with `primary`.
   - Append providers from `fallback_order` that are configured and not duplicates.
2. For each provider in sequence:
   - Skip if the provider is temporarily disabled due to repeated failures.
   - Attempt the completion:
     - Call the provider‑specific implementation (OpenAI/Gemini/OpenRouter).
     - Enforce `require_content` and `require_tool_calls` if requested.
   - On success:
     - Return content, tool calls, `usage`, `model`, and `provider_used`.
   - On failure (exception, empty response, invalid tool calls):
     - Increment a `provider_failure_counts` counter.
     - Optionally mark the provider disabled for a cooldown period.
     - Continue to the next provider.
3. If all providers fail:
   - Raise an error that eventually:
     - Causes the session to be marked `failed`.
     - Emits an `error` and/or `session_failed` event to the frontend.

This strategy gives resilience against:

- Per‑provider outages.
- Misconfigurations (e.g., missing API keys).
- Temporary rate limiting or network issues.

### 7.4 Cost and Token Accounting

Each provider returns usage metadata:

- Input tokens, output tokens, total tokens.
- Model name used.

The LLMManager and agents:

- Aggregate tokens and cost across all calls and providers per session.
- Use provider‑specific pricing to estimate `cost_usd`.
- Record per‑call latencies.

These numbers feed into:

- `ResearchResult` (total tokens and cost per session).
- `MetricsCollector` (per‑call + aggregate metrics).
- Completion payloads that the frontend uses in the metrics dashboard.

---

## 8. Tracing, Metrics, and Storage

Tracing and metrics are what make the system **observable** and **explainable**.

### 8.1 Trace Events: Shape and Storage

Every significant step in the ReAct + evaluation pipeline is a **trace event** with:

- `type` – event name (e.g. `session_start`, `iteration_start`, `thought`, `action`, `tool_execution`, `observation`, `finish_guard`, `finish`, `evaluator_start`, `evaluator_complete`).
- `session_id` – which research run this belongs to.
- `iteration` – which iteration (if applicable).
- `data` – structured payload for that event type.
- `timestamp` – when it happened.

Within ResearcherAgent, `_emit_trace(event_type, data, iteration)` is the single entry point that:

1. Normalizes data and injects default `message` strings.
2. Calls the **trace callback** if present:
   - `save_trace_event(session_id, event_type, data, iteration)` stores it in the DB.
3. Calls the **WebSocket manager** if present:
   - `send_trace_event(session_id, event_type, data)` broadcasts it to live clients.

If persisting fails (e.g., DB down), the error is logged but the agent continues so the session can still finish.

The `GET /api/research/{session_id}/trace` endpoint reads these stored events and returns them as a `TraceResponse` for offline inspection and analytics.

### 8.2 Metrics Collection During a Session

`_run_research_session` creates a `MetricsCollector` at the start:

- As the ResearcherAgent runs, it records:
  - Per‑iteration durations.
  - Tool executions (names, durations, success/failure).
  - LLM calls (provider, model, tokens, latency).
- After evaluation completes, the collector is finalized with:
  - End‑to‑end evaluation scores.
  - Final report metadata.

The result is a metrics object containing:

- Average and distribution of iteration latencies.
- Per‑tool average execution times and counts.
- End‑to‑end duration, total tokens, total cost.
- Iterations to completion.
- Tool success/failure counts.
- Provider failover counts and total LLM calls.

### 8.3 History Snapshots and Metrics Dashboard

A compact **history snapshot** is then created via `metrics.history.create_snapshot` and appended via `append_run`:

- This snapshot is designed for time‑series and comparative dashboards.
- It captures the essential metrics for that run in a stable schema.

Frontend usage:

- The `completion` event includes a simplified metrics payload for the **current run**.
- The research store also calls a metrics summary endpoint to fetch **historical aggregates**.
- The metrics dashboard combines both to show:
  - How this run compares to historical norms.
  - Trends in latency, tool performance, cost, and quality.

---

## 9. Real‑Time Transport Layer (WebSockets + SSE)

The **ConnectionManager** (`backend/app/api/websocket.py`) abstracts all real‑time delivery:

- Maintains active WebSocket connections per session.
- Maintains SSE (Server‑Sent Events) subscribers per session.
- Keeps message queues for sessions with temporarily no listeners.
- Provides helper methods to send trace events, completion events, progress updates, and errors.

Frontend connections:

- Start with WebSockets (`/ws/{session_id}`).
- If repeated WebSocket failures occur, fall back to SSE (`/ws/{session_id}/stream`).
- Both transports ultimately deliver the same JSON event shape.

---

## 10. Frontend Architecture Overview

Key frontend elements (`frontend/src`):

- **Main page**: `app/page.tsx` (ResearchPage)
  - Composes Header, QueryInput, WorkflowChart, ReactTraceTimeline, ResearchOutputPanel, MetricsDashboard.
- **Components**:
  - `components/research/react-trace-timeline.tsx` – ReAct trace timeline.
  - `components/workflow/WorkflowChart.tsx` – workflow chart.
  - `components/research/research-output-panel.tsx` – report display and export.
  - `components/research/metrics-dashboard.tsx` – current + historical metrics.
- **State stores**:
  - `store/research-store` – research session, iterations, activity state, tool output summaries, report, metrics.
  - `stores/workflowStore.ts` – workflow nodes/edges, stats, event history.
- **Hooks**:
  - `hooks/use-websocket.ts` – WebSocket/SSE lifecycle + normalization of backend messages.

The frontend treats the backend as:

- A small set of REST endpoints (start session, fetch history/metrics).
- A continuous event stream (WebSocket/SSE) that drives the live UI.

---

## 11. Real‑Time Updates in the Frontend

### 11.1 `useWebSocket` Hook Responsibilities

`useWebSocket`:

- Manages connection state: `connecting` → `connected` → `error` → `reconnecting`.
- Builds the correct WebSocket URL for a given `session_id` and base API URL.
- Normalizes raw server messages into `ResearchUpdate` objects with:
  - `type`, `sessionId`, `iteration`, `data`, `timestamp`, `message`.
- Dispatches updates to:
  - The **research store** (iterations, activity state, report, metrics, errors).
  - The **workflow store** (for supported workflow event types).
- Implements reconnection and WebSocket ↔ SSE fallback.

### 11.2 Activity State and Progress

The research store maintains an `activityState` with:

- `currentPhase` – one of `starting`, `thinking`, `acting`, `observing`, `evaluating`, `complete`, `failed`.
- `currentIteration` – best guess at the current iteration.
- `currentActivity` – human‑readable sentence describing what’s happening.
- `progress` – a 0–100 number derived from:
  - Iteration number vs max iterations.
  - Phase within an iteration.
- `elapsed` and `estimatedTimeRemaining` – derived from timestamps.

`useWebSocket` updates this state based on event types (e.g., `thought` → `thinking`, `tool_execution` → `observing`, `completion` → `complete`). This activity state is used in the center panel and indirectly reflected in the workflow chart progress bar.

---

## 12. ReAct Trace Timeline: Iteration View

The ReAct trace timeline (`ReactTraceTimeline`) renders a list of `Iteration` objects with four main phases:

- THOUGHT – reasoning text, tokens, latency.
- ACTION – tool name and parameters.
- EXECUTION – tool result summary, duration, result count, success/failure.
- OBSERVATION – the agent’s interpretation of the tool output.

Backend → frontend mapping:

- `iteration_start` – creates or resets an iteration entry and marks it `thinking`.
- `thought` / `thought_generated` – fills the THOUGHT block and keeps status `thinking`.
- `action` / `action_executing` – fills tool name and parameters, marks status `acting`.
- `tool_execution` / `action_complete` – fills EXECUTION details, marks status `observing`.
- `observation` / `observation_generated` – fills OBSERVATION text and marks iteration `complete`.
- `finish` – ensures there is a final iteration and records a pseudo‑tool `finish` with a summary of report synthesis.

The timeline is primarily driven by logic in `handleResearchUpdate` inside `use-websocket.ts`, which mutates the iteration list in the research store.

---

## 13. Workflow Chart: Node and Edge States

The workflow chart visualizes the ReAct + evaluation process as a state machine over nodes and edges.

### 13.1 Nodes and Their Meaning

- `start` – conceptual entry point before ReAct begins.
- `think` – LLM reasoning step (THOUGHT).
- `operate` – tool selection and execution (ACTION + EXECUTION).
- `reflect` – interpretation and loop/finish decision.
- `evaluator` – end‑to‑end quality review.
- `finish` – finalization of the run (report + evaluation).

Each node includes:

- `status` – `idle`, `active`, `completed`, `error`, `skipped`.
- `visitCount` and `currentVisitIteration` – how often this stage was visited.
- `metadata` – rich details (thought, tool, provider, observation, evaluation scores, report length, etc.).

### 13.2 Edges and Looping

Edges represent flow:

- Forward path:
  - `start->think`
  - `think->operate`
  - `operate->reflect`
  - `reflect->evaluator`
  - `evaluator->finish`
- Loop path:
  - `reflect->think` for additional iterations.

Edges track:

- `status` – `idle`, `active`, `completed`, `disabled`.
- `showFlowAnimation`, `showPulse` – used by SVG animations.
- `transitionCount` – number of times a path was taken.

### 13.3 How Events Drive the Workflow Store

The `workflowReducer` consumes `WorkflowEvent` objects (derived from backend events):

- `session_start` – resets state, sets max iterations.
- `iteration_start` – activates THINK node and either `start->think` or `reflect->think` depending on iteration.
- `thought` – marks THINK completed, activates OPERATE and `think->operate`.
- `action` – records selected tool in OPERATE metadata.
- `tool_execution` – marks OPERATE completed or errored, activates REFLECT and `operate->reflect` when successful.
- `observation` – stores observation text in REFLECT metadata.
- `finish_guard` – either loops (activate `reflect->think`) or moves forward (activate `reflect->evaluator`).
- `finish` – completes THINK/OPERATE/REFLECT and records pending finish metadata.
- `evaluator_start` – activates EVALUATOR node and `reflect->evaluator` edge.
- `evaluator_complete` – completes EVALUATOR and FINISH nodes and `evaluator->finish` edge.
- `error` – marks the currently active node as error.
- `session_complete` – records duration, total tokens, and cost in stats.

`WorkflowChart` then renders this state into SVG nodes/edges and a progress bar based on iteration and stage completion.

---

## 14. Backend–Frontend Mapping Reference

This table summarizes how backend events flow into frontend visualizations:

| Backend source                                           | Event type           | Frontend effects                                                                                  |
|----------------------------------------------------------|----------------------|---------------------------------------------------------------------------------------------------|
| `ResearcherAgent._emit_trace("session_start")`          | `session_start`      | Workflow reset + THINK entry; activity state set to "Session started".                           |
| `_emit_trace("iteration_start")`                        | `iteration_start`    | New iteration created; THINK node active; `start->think` or `reflect->think` edge animated.      |
| `_emit_trace("thought")`                                | `thought`            | THOUGHT block populated; THINK node completed; OPERATE node active; `think->operate` edge flows. |
| `_emit_trace("action")`                                 | `action`             | ACTION block populated; OPERATE metadata updated.                                                 |
| `_emit_trace("tool_execution")`                         | `tool_execution`     | EXECUTION block populated; OPERATE→REFLECT transition; stats updated.                             |
| `_emit_trace("observation")`                            | `observation`        | OBSERVATION block populated; REFLECT metadata updated.                                            |
| `_emit_trace("finish_guard")`                           | `finish_guard`       | REFLECT decision set; either loop (`reflect->think`) or progress (`reflect->evaluator`).         |
| `_emit_trace("finish")`                                 | `finish`             | Final iteration recorded; THINK/OPERATE/REFLECT completed; pending FINISH metadata stored.       |
| `_run_research_session` emits `evaluator_start`          | `evaluator_start`    | EVALUATOR node active; `reflect->evaluator` edge animated.                                       |
| `_run_research_session` emits `evaluator_complete`       | `evaluator_complete` | EVALUATOR + FINISH nodes completed; `evaluator->finish` edge completed; scores shown.            |
| `_run_research_session` emits completion payload         | `completion`         | Report + metrics stored; metrics dashboard updated; activity state "complete".                  |
| Error in `_run_research_session` or tools                | `error`              | Active node marked error; error banner shown; activity state "failed".                          |
| Session explicitly marked failed                         | `session_failed`     | Session history updated; activity state "failed"; error state persisted.                        |

---

## 15. Error Handling, Cancellation, and Resilience

### 15.1 Cancellation

- `POST /api/research/{session_id}/cancel`:
  - Verifies the session is `running`.
  - Sets `_active_sessions[session_id] = False`.
  - Updates DB status to `cancelled`.
- The ReAct loop periodically checks whether the session is still active and exits early if not.

Frontend effects:

- "Stop Research" button triggers the cancel endpoint.
- No further live events arrive after cancellation is processed.
- The UI shows a non‑completed session with partial trace and no evaluator/metrics.

### 15.2 Error Handling

- Exceptions in `_run_research_session` are caught:
  - `websocket_manager.send_error(...)` sends an `error` event with message and type.
  - Session status is updated to `failed` with a completion timestamp.
- Tool‑level timeouts/errors are surfaced via `tool_execution` (with `success=false`) and may also generate `error` events.

Frontend effects:

- `useWebSocket` sets an error message in the research store and marks researching as `false`.
- Workflow store marks the currently active node as `error` with an error message.
- Activity state switches to `failed`.

### 15.3 Transport Resilience

- WebSockets:
  - On close/error, `useWebSocket` attempts reconnection with increasing delay, up to a configured maximum.
  - After too many failures, it switches to SSE.
- SSE:
  - On repeated errors, SSE also gives up and the hook cycles back to WebSockets.

This design minimizes the chance that long‑running sessions lose their visual trace due to transient network problems.

---

## 16. Extensibility and Future Enhancements

The architecture is intended to be extended in three main directions:

- **New tools**:
  - Implement tool logic under `app/tools`.
  - Add tool definitions in `definitions.py` so the ReAct prompt and tool schema include it.
  - Emit standard `action` / `tool_execution` events with the new tool name.
  - Frontend will automatically show it in ACTION/EXECUTION blocks (and you can customize labels if desired).

- **New LLM providers or models**:
  - Implement a new provider class following `BaseLLMProvider`.
  - Register it in `LLMManager` and extend configuration.
  - Add it to `VALID_MODEL_OVERRIDES` in `routes/research.py` if you want user‑facing model overrides.

- **Richer workflows and traces**:
  - Add new event types to `_emit_trace` and to the frontend `WebSocketEventType` union.
  - Extend `workflowStore`’s event union and reducer to interpret new stages.
  - Add nodes or edges to the workflow chart (e.g., separate PLAN/SYNTHESIZE/CRITIQUE nodes).

Because the system cleanly separates:

- **Agent reasoning and tool orchestration** (backend agents),
- **Transport and persistence** (API, DB, WebSockets/SSE, traces, metrics),
- **Visualization** (frontend stores and React components),

you can evolve each layer independently while keeping the overall mental model the same: a transparent, measurable ReAct‑style research loop followed by an end‑to‑end AI evaluation.

