# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an **Agentic AI Research System** that uses the ReAct (Reasoning + Acting) pattern to perform autonomous research. The system features:

**Core Capabilities:**
- Multi-provider LLM support (OpenAI, Google Gemini, OpenRouter) with automatic fallback
- Research tools: multi-provider web search (Tavily, Serper, SerpAPI), ArXiv papers, GitHub repos, PDF extraction
- FastAPI backend with WebSocket support for real-time updates
- Next.js frontend with TypeScript and Tailwind CSS
- SQLite database for session persistence and tracing
- Built-in evaluation system with LLM-as-judge
- Content pipeline with classification, extraction, ranking, and caching

**Advanced Agent Features (New):**
- **Intelligent Tool Routing**: Keyword-based detection automatically determines which tools (web/arxiv/github) are appropriate
- **Heuristic Tool Gating**: Prevents wasteful specialized tool calls while remaining adaptive to agent needs
- **Finish Guard Quality Gate**: LLM-as-judge validates reports before allowing completion, prevents premature exits
- **Sparse Result Recovery**: Detects insufficient search results and prompts agent to refine queries
- **Domain Coverage Balancing**: Ensures comprehensive research across multiple discovery channels (web, academic, code)
- **Tool Timeout Management**: Configurable per-tool timeouts with graceful degradation
- **Auto-Finish Mechanism**: Guarantees report generation even when max iterations reached
- **Enhanced Observation Formatting**: Intelligent formatting of tool outputs for optimal agent comprehension

## Project Structure

```
research_agent_claude/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── agents/            # ReAct agent and evaluator implementations
│   │   ├── llm/               # LLM provider abstractions (OpenAI, Gemini, OpenRouter)
│   │   ├── tools/             # Research tools (web, arxiv, github, pdf)
│   │   ├── content/           # Content pipeline (classifier, extractor, ranker, cache)
│   │   ├── api/               # FastAPI routes and WebSocket handlers
│   │   ├── database/          # SQLAlchemy models and database operations
│   │   ├── export/            # PDF, Word, HTML export functionality
│   │   ├── metrics/           # Performance metrics collection and analysis
│   │   ├── tracing/           # LangSmith integration and decorators
│   │   ├── config/            # Configuration loading and validation
│   │   └── utils/             # Text processing, formatting, validators
│   ├── main.py                # CLI entry point for testing research
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Next.js React frontend
│   ├── package.json
│   └── ...
├── config.yaml                 # Main configuration file (LLM, tools, evaluation)
├── docker-compose.yml         # Container orchestration
└── .env                       # Environment variables (API keys)
```

## Development Commands

### Backend Development

```bash
# From repository root, navigate to backend
cd backend

# Activate virtual environment
# Windows:
backend\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_imports.py

# Run CLI research interface
python main.py

# Run API server (from backend directory)
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Run with Docker
cd ..  # back to root
docker-compose up -d
```

### Frontend Development

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Type checking
npm run type-check

# Lint
npm run lint
```

### Testing

```bash
# Backend tests
cd backend
pytest                        # Run all tests
pytest tests/test_agents.py   # Run specific test file
pytest -v                     # Verbose output
pytest --cov                  # With coverage

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend
cd backend
black .                       # Format code
flake8 .                      # Lint
mypy app                      # Type checking
isort .                       # Sort imports

# Frontend
cd frontend
npm run lint                  # ESLint
npm run type-check           # TypeScript checking
```

## Architecture

### Core Agent Flow (ReAct Pattern)

The system implements the ReAct pattern in `backend/app/agents/react_agent.py`:

1. **THOUGHT**: Agent reasons about what information is needed
2. **ACTION**: Selects and executes appropriate tool (web_search, arxiv_search, github_search, pdf_to_text)
3. **OBSERVATION**: Analyzes tool results
4. **REPEAT**: Continues until sufficient information gathered or max_iterations reached
5. **FINISH**: Produces final "Deep Research Report" with citations

The agent includes sophisticated control mechanisms:

#### Intelligent Tool Routing
- **Query Analysis**: Automatically analyzes queries for keywords to determine which tools are appropriate
  - `GITHUB_KEYWORDS`: Detects needs for implementations, repos, libraries, benchmarks
  - `ARXIV_KEYWORDS`: Identifies academic/research topics requiring scholarly sources
- **Dynamic Tool Policy**: `_derive_tool_policy()` creates heuristic rules based on query intent
- **Tool Gating**: `_is_tool_allowed()` blocks specialized tools (github_search, arxiv_search) until the query demonstrates clear need
- **Adaptive Unlocking**: Tools can be unlocked mid-research if agent reasoning mentions relevant keywords

#### Finish Guard System
- **Quality Gate**: `_run_finish_guard()` validates draft reports before allowing completion
- **Readiness Check**: Uses LLM-as-judge to assess if report is complete, well-sourced, and addresses the query
- **Guided Recovery**: If report is insufficient, provides specific feedback and next-action hints
- **Prevents Premature Exit**: Ensures agent gathers sufficient evidence before finishing

#### Sparse Result Handling
- **Result Monitoring**: `_handle_sparse_web_results()` detects when web searches return too few relevant results
- **Automatic Refinement**: Prompts agent to refine queries with more specific keywords, synonyms, or filters
- **Threshold-based**: Triggers when results fall below configurable threshold (default: 2)

#### Domain Coverage Guidance
- **Balance Enforcement**: `_inject_domain_guidance()` reminds agent about unused discovery channels
- **Coverage Tracking**: Monitors which tools (web_search, arxiv_search, github_search) have been used
- **Smart Disabling**: Stops reminders when early evidence is already sufficient (`_maybe_mark_sufficient_evidence()`)

#### Tool Execution Safety
- **Configurable Timeouts**: Per-tool timeout settings via `tool_settings` configuration
- **Graceful Timeout Handling**: Tools that exceed timeout return error observations instead of crashing
- **Timeout Context**: Timeout durations are included in trace events for debugging

#### Auto-finish Mechanism
- **Max Iteration Safety**: `_force_finish_if_needed()` automatically generates report when iterations are exhausted
- **Forced Tool Choice**: Uses LLM tool_choice parameter to ensure finish is called
- **Fallback Report**: Synthesizes report from gathered observations even if agent didn't explicitly finish

#### Report Structure
The agent generates a "Deep Research Report" with standardized sections:
- **Title + TL;DR**: 3-5 bullet executive summary
- **Context & Signal**: Why this topic matters now
- **Evidence Deep Dive**: Thematic subsections with cited sources
- **Implementation/Applications**: Real-world solutions, code, products
- **Risks, Gaps & Open Questions**: Critical analysis
- **Recommended Next Steps**: Actionable guidance
- **Sources**: Numbered reference list matching inline citations

Key files:
- `backend/app/agents/react_agent.py`: ResearcherAgent implementation (lines 31-1444)
- `backend/app/agents/evaluator_agent.py`: Evaluation logic (per-step and end-to-end)
- `backend/app/agents/models.py`: Pydantic models for agent state

### LLM Provider System

Multi-provider architecture with automatic fallback in `backend/app/llm/`:

- `manager.py`: LLMManager orchestrates multiple providers
- `base.py`: BaseLLMProvider abstract interface
- `openai_provider.py`: OpenAI API integration
- `gemini_provider.py`: Google Gemini integration
- `openrouter_provider.py`: OpenRouter integration (Nemotron 49B)

Configuration in `config.yaml`:
```yaml
llm:
  primary: "openai"
  fallback_order: ["gemini", "openrouter"]
```

### Tool System

All research tools are defined in `backend/app/tools/`:

- `web_search.py`: Multi-provider web search with automatic failover
  - Primary: Tavily API (AI-optimized, 1000 free/month)
  - Secondary: Serper.dev (Google results, 2500 free)
  - Tertiary: SerpAPI (Backup, 100 free/month)
- `arxiv_search.py`: Academic paper search
- `github_search.py`: Code repository search
- `pdf_parser.py`: PDF text extraction using PyMuPDF
- `definitions.py`: OpenAI function definitions for tool calling

Tools return structured data that the agent uses for reasoning. Web search automatically tries providers in order until one succeeds.

### Content Pipeline

Advanced content processing in `backend/app/content/`:

- `classifier.py`: Classifies content relevance to query
- `extractor.py`: Extracts key information from web content
- `summarizer.py`: Generates summaries of documents
- `ranker.py`: Ranks search results by relevance
- `cache.py`: Caches processed content to reduce API calls
- `pipeline.py`: Orchestrates the full pipeline

The pipeline is optional and can be enabled/disabled in config.

### API Structure

FastAPI application in `backend/app/api/`:

- `main.py`: Application initialization, CORS, lifespan management
- `websocket.py`: Real-time research progress updates
- `routes/research.py`: POST /api/research endpoint for queries
- `routes/history.py`: GET /api/history for past sessions
- `routes/export.py`: Export reports as PDF/Word/HTML
- `routes/config.py`: Runtime configuration management
- `models/`: Pydantic request/response models
- `dependencies.py`: FastAPI dependency injection

### Database Schema

SQLAlchemy models in `backend/app/database/models.py`:

- `ResearchSession`: Main session record with query, config, status, final report
- `TraceEvent`: Individual agent steps/events during research
- `PerStepEvaluation`: Evaluation of each ReAct iteration
- `EndToEndEvaluation`: Overall research quality assessment

Database operations in `backend/app/database/database.py`.

### Evaluation System

Two-tier evaluation in `backend/app/agents/evaluator_agent.py`:

1. **Per-Step Evaluation**: Assesses each ReAct iteration
   - Tool appropriateness
   - Execution quality
   - Progress made
   - Information gain
   - Efficiency

2. **End-to-End Evaluation**: Evaluates final report
   - Relevance to query
   - Accuracy of information
   - Completeness of coverage
   - Coherence and clarity
   - Source quality
   - Recency of information

Uses LLM-as-judge approach with structured prompts.

## Configuration

### Environment Variables (.env)

Required API keys (at least one LLM provider):
```bash
# LLM Providers (need at least one)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=sk-or-...

# Optional
GITHUB_TOKEN=ghp_...          # Higher GitHub API rate limits
TAVILY_API_KEY=tvly-...       # Primary web search (1000 free/month)
SERPER_API_KEY=...            # Secondary web search (2500 free)
SERPAPI_API_KEY=...           # Tertiary web search (100 free/month)
LANGSMITH_API_KEY=...         # Optional tracing
```

### config.yaml

Main configuration file controls:
- LLM provider selection and fallback order
- Model selection (gpt-4o-mini, gemini-2.5-flash, etc.)
- Research parameters (max_iterations, timeout)
- Tool settings (max_results, date filters)
- Evaluation toggles
- Tracing and observability
- Database path
- API server settings

When modifying behavior, edit `config.yaml` first before changing code.

## Advanced Agent Features

### Keyword-Based Tool Routing

The agent uses intelligent keyword detection to determine which research tools are appropriate for a given query:

**GitHub Keywords** (lines 42-65): `implementation`, `library`, `repo`, `code`, `tool`, `framework`, `sdk`, `benchmark`, `open-source`, etc.

**ArXiv Keywords** (lines 67-104): `paper`, `research`, `study`, `academic`, `arxiv`, `theory`, `algorithm`, `neural`, `model`, `dataset`, `ml`, `ai`, `deep learning`, `rag`, `llm`, etc.

**Technical Signals**: Queries containing AI/ML terms automatically enable both github_search and arxiv_search.

The `_derive_tool_policy()` method creates a policy dict that controls:
- Which specialized tools are allowed initially
- Default tool for first iteration
- Result count thresholds for determining sufficiency
- Sparse result detection thresholds

### Heuristic Tool Gating

Specialized tools (github_search, arxiv_search) are blocked by default unless:
1. Query contains relevant keywords during initial policy derivation, OR
2. Agent's reasoning (THOUGHT) explicitly mentions tool-specific keywords, OR
3. Tool has been denied once already (second attempt is always allowed)

This prevents wasteful tool calls while remaining adaptive to agent needs. Example:
- Query: "What is the capital of France?" → arxiv_search blocked (not academic)
- Query: "Latest RAG architectures" → arxiv_search allowed (academic signals detected)
- Agent reasoning: "I need to find implementation code..." → github_search unlocked

### Finish Guard Quality Gate

Before allowing the agent to finish, `_run_finish_guard()` performs a critical review:

1. **Sends draft report to LLM critic** with query and sources
2. **Receives structured JSON decision**: `allow_finish` (bool), `feedback` (string), `next_action_hint` (string)
3. **If rejected**: Injects feedback and hint back into conversation, agent continues research
4. **If approved**: Allows finish to proceed

This prevents premature exits with incomplete research. The guard uses temperature=0.2 for consistent evaluation.

### Sparse Result Recovery

When web_search returns fewer results than `sparse_result_threshold` (default: 2):

1. **Detection**: `_handle_sparse_web_results()` compares result count to threshold
2. **Guidance Injection**: Adds system message prompting query refinement
3. **Deduplication**: Tracks last sparse query to avoid redundant prompts
4. **Agent Response**: Agent reformulates query with more specific keywords, filters, or domain hints

This ensures comprehensive coverage even when initial searches miss relevant content.

### Domain Coverage Balancing

The agent tracks which discovery tools have been used (`tool_usage_counts`) and reminds about unused channels:

- **Missing Tool Detection**: `_missing_domain_tools()` identifies unused tools (web, arxiv, github)
- **Guidance Injection**: `_inject_domain_guidance()` adds system reminders about unused domains
- **Smart Disabling**: Once "sufficient evidence" is detected (`early_evidence_sufficient`), reminders stop
- **Sufficiency Heuristic**: 5+ results in first 3 iterations from primary tool = sufficient

This balances comprehensive coverage with efficiency, avoiding tool spam when early evidence is rich.

### Tool Timeout Management

All tool executions are protected by configurable timeouts:

- **Per-tool Configuration**: `web_search_timeout_seconds`, `tool_execution_timeout_seconds` in config
- **Graceful Degradation**: Timeouts return error observations instead of crashing session
- **Trace Integration**: Timeout events include duration in trace for debugging
- **Default**: 60 seconds (configurable via `tool_settings`)

### Conversation History Cleanup

`_prune_incomplete_tool_calls()` maintains valid message structure by:
- Removing trailing assistant messages with tool_calls but no tool response
- Removing mismatched tool responses (wrong tool_call_id)
- Preventing conversation format errors that break LLM API calls

### Auto-Finish at Max Iterations

When max_iterations is reached without finish, `_force_finish_if_needed()`:
1. Adds user message explicitly instructing agent to call finish
2. Uses `tool_choice={"type": "function", "function": {"name": "finish"}}` to force finish call
3. Synthesizes final report from gathered observations
4. Creates finish step and returns completed research result

This ensures every session produces a report, even if agent gets "stuck" exploring.

### Enhanced Observation Formatting

Tool outputs are intelligently formatted for agent consumption:

- **Top Results Preview**: Shows first 3 results with title, source, and 220-char snippets
- **Pipeline Statistics**: Includes classification, extraction, summarization, and cache hit counts
- **Failure Reporting**: Notes extraction issues and missing summaries
- **Concise JSON Fallback**: For non-standard outputs, returns compact JSON
- **3000 Character Limit**: Prevents context overflow while retaining key information

## Key Implementation Details

### ResearcherAgent Constructor Parameters

The `ResearcherAgent` class (lines 149-212) accepts several configuration parameters:

**Required:**
- `llm_manager`: LLMManager instance for LLM provider orchestration

**Optional Research Configuration:**
- `max_iterations`: Maximum ReAct iterations (default: 10)
- `timeout_minutes`: Session timeout in minutes (default: 15)
- `llm_temperature`: Temperature for reasoning calls (default: 0.7, clamped to 0.0-1.0)

**Optional Integration Components:**
- `trace_callback`: Async callback function for trace events (for database storage)
- `content_pipeline`: ContentPipeline instance for result processing/ranking/caching
- `websocket_manager`: WebSocketManager for real-time updates
- `metrics_collector`: MetricsCollector for performance tracking
- `tool_settings`: ToolsSettings instance for tool configuration (timeouts, result limits)

**Internal State Tracking:**
- `tool_usage_counts`: Dict tracking successful uses of web_search, arxiv_search, github_search
- `tool_policy`: Dict with tool routing rules (allow_github, allow_arxiv, default_tool, thresholds)
- `early_evidence_sufficient`: Flag indicating if domain coverage reminders should be disabled
- `_tool_denials`: Counter tracking how many times each tool has been blocked
- `_last_sparse_query`: Tracks last query that triggered sparse result guidance
- `_last_guidance_missing`: Tuple of tools mentioned in last domain coverage reminder

Example initialization:
```python
from app.llm import LLMManager
from app.content.pipeline import ContentPipeline
from app.agents.react_agent import ResearcherAgent
from app.config.settings import ToolsSettings

llm_manager = LLMManager(config)
pipeline = ContentPipeline(llm_manager, config)
tool_settings = ToolsSettings(
    web_search_timeout_seconds=90,
    tool_execution_timeout_seconds=60
)

agent = ResearcherAgent(
    llm_manager=llm_manager,
    max_iterations=12,
    timeout_minutes=20,
    content_pipeline=pipeline,
    tool_settings=tool_settings,
    llm_temperature=0.6
)

result = await agent.research("What are the latest advances in RAG?")
```

### Research Method Flow

The `research(query, session_id)` method (lines 214-766) orchestrates the complete research session:

**Initialization Phase (lines 227-276):**
1. Generate or use provided session_id
2. Emit `session_start` trace event
3. Initialize conversation history with SYSTEM_PROMPT and user query
4. Derive tool policy from query keywords (`_derive_tool_policy()`)
5. Add tool policy message to conversation
6. Reset all tracking state (tool_usage_counts, tool_denials, etc.)

**ReAct Loop Phase (lines 278-689):**
For each iteration (up to max_iterations):
1. **Timeout Check**: Verify session hasn't exceeded timeout_seconds
2. **Emit iteration_start**: Broadcast iteration start event
3. **Prune History**: Clean incomplete tool calls (`_prune_incomplete_tool_calls()`)
4. **Inject Guidance**: Add domain coverage reminders if needed (`_inject_domain_guidance()`)
5. **LLM Call**: Request next action with tool definitions (temperature=llm_temperature, require_tool_calls=True)
6. **Extract Response**: Parse thought content and tool_calls
7. **Emit thought**: Broadcast reasoning with tokens/provider/latency
8. **Process Tool Calls**: For each tool_call:
   - Parse arguments (with malformed JSON repair if needed)
   - Check if tool is allowed (`_is_tool_allowed()`)
   - If blocked: Emit `tool_blocked`, append tool response with block message, continue
   - If allowed: Emit `action` event
   - **Special handling for finish**:
     - Run finish guard (`_run_finish_guard()`)
     - If rejected: Emit `finish_guard` (approved=false), append rejection, optionally add hint, continue
     - If approved: Emit `finish_guard` (approved=true), extract report/sources, set done=True, break
   - **For other tools**:
     - Execute with timeout (`_execute_tool_with_timeout()`)
     - Handle timeout errors gracefully
     - Record tool execution in metrics collector
     - Format observation (`_format_observation()`)
     - Emit `tool_execution` and `observation` events
     - Append tool response message to conversation
     - For web_search: Check for sparse results (`_handle_sparse_web_results()`)
     - Record tool usage (`_record_tool_usage()`)
     - Update sufficiency flag (`_maybe_mark_sufficient_evidence()`)
9. **Iteration Complete**: Create AgentStep, add to steps list, record in metrics

**Finalization Phase (lines 691-764):**
1. **Auto-finish if needed**: If not done and steps exist, call `_force_finish_if_needed()`
2. **Calculate metrics**: Total duration, tokens, cost
3. **Determine status**: "completed", "failed", or "incomplete"
4. **Create ResearchResult**: Aggregate all data (query, report, sources, steps, metrics, status)
5. **Emit session_complete**: Broadcast final metrics
6. **Return result**: Return ResearchResult to caller

**Exception Handling:**
- Iteration errors: Log, emit error trace, break loop, return partial result
- Session errors: Log, emit session_failed, return empty result with error status
- Finally block: Always clear session_id

The method is fully async and supports cancellation, timeout enforcement, and graceful degradation.

### Adding a New Research Tool

1. Create tool function in `backend/app/tools/` (e.g., `my_tool.py`)
2. Add OpenAI function definition in `backend/app/tools/definitions.py`
3. Register in `backend/app/tools/__init__.py`
4. Update agent's SYSTEM_PROMPT in `backend/app/agents/react_agent.py` to mention the new tool
5. (Optional) Add tool to `domain_tools` list if it should participate in coverage guidance
6. (Optional) Update `_execute_tool()` if tool needs special handling (like content_pipeline integration)

Example tool signature:
```python
async def my_tool(
    param: str,
    content_pipeline=None,  # Optional for result processing
    **kwargs
) -> Dict[str, Any]:
    """Tool implementation."""
    results = [...] # Gather results

    # Optional: Process through content pipeline
    if content_pipeline:
        results = await content_pipeline.process(results, param)

    return {
        "results": results,
        "total_found": len(results),
        "metadata": {...},
        "notes": [],  # Optional warnings/info
        "pipeline_stats": {...}  # If using content_pipeline
    }
```

### Modifying Agent Behavior

Edit `backend/app/agents/react_agent.py`:

#### Core Prompts & Configuration
- `SYSTEM_PROMPT` (lines 106-138): Change agent instructions, guidelines, and report structure
- `FINISH_GUARD_PROMPT` (lines 140-147): Modify quality gate criteria for report approval
- `max_iterations`: Adjust in config.yaml or constructor (default: 10)
- `llm_temperature`: Control reasoning temperature (default: 0.7, configurable via constructor)

#### Tool Routing & Policy
- `GITHUB_KEYWORDS` / `ARXIV_KEYWORDS` (lines 42-104): Add/remove keywords that trigger specialized tools
- `_derive_tool_policy()` (lines 1242-1273): Customize initial tool allowances based on query analysis
- `_build_tool_policy_message()` (lines 1275-1292): Modify tool routing hints shown to agent
- `_is_tool_allowed()` (lines 1294-1325): Adjust heuristic gating logic for tool blocking/unlocking
- `tool_policy` dict (lines 196-202): Configure default tool, result thresholds, sparse result handling

#### Quality & Safety Mechanisms
- `_run_finish_guard()` (lines 1377-1414): Customize finish validation logic and LLM-as-judge criteria
- `_handle_sparse_web_results()` (lines 1334-1353): Adjust sparse result detection threshold and guidance
- `_maybe_mark_sufficient_evidence()` (lines 1355-1375): Modify early sufficiency detection logic
- `_inject_domain_guidance()` (lines 906-931): Customize domain coverage reminders
- `_get_tool_timeout_seconds()` (lines 861-886): Configure per-tool timeout durations

#### Tool Execution
- `_execute_tool()` (lines 794-843): Add pre/post-processing for tools, modify tool parameters
- `_execute_tool_with_timeout()` (lines 845-859): Customize timeout behavior
- `_format_observation()` (lines 1033-1089): Change how tool outputs are formatted for agent consumption
- `_summarize_tool_output()` (lines 1091-1127): Modify logging summaries

#### Error Handling & Recovery
- `_handle_malformed_arguments()` (lines 1129-1154): Customize JSON repair strategies
- `_prune_incomplete_tool_calls()` (lines 768-792): Adjust conversation history cleanup logic
- `_force_finish_if_needed()` (lines 933-1031): Modify auto-finish behavior at max iterations

#### Utility Methods
- `_record_tool_usage()` (lines 888-894): Track tool usage for coverage guidance
- `_missing_domain_tools()` (lines 896-904): Determine which discovery domains need coverage
- `_infer_result_count()` (lines 1229-1240): Extract result counts from tool outputs
- `_parse_guard_response()` (lines 1416-1443): Parse finish guard JSON responses

### Custom LLM Provider

1. Create provider class in `backend/app/llm/` extending `BaseLLMProvider`
2. Implement `generate()` and `generate_with_tools()` methods
3. Register in `backend/app/llm/manager.py`
4. Add configuration to `config.yaml`

### WebSocket Events

The system emits real-time events via WebSocket for comprehensive research monitoring:

#### Session Lifecycle Events
- `session_start`: Research session begins (includes session_id, query, timestamp)
- `session_complete`: Session finished successfully (includes status, iterations, duration, tokens, cost)
- `session_failed`: Session encountered fatal error (includes error message)

#### Iteration Events
- `iteration_start`: New ReAct iteration begins (includes iteration number, timestamp)
- `thought`: Agent reasoning step (includes thought content, tokens_used, provider, latency_ms)
- `action`: Tool selection (includes tool name, parameters, index for parallel calls)
- `tool_execution`: Tool completed (includes duration_ms, success, result_summary, provider, result_count, pipeline_stats)
- `observation`: Agent analyzed tool results (includes observation text, index)

#### Control & Quality Events
- `tool_blocked`: Specialized tool blocked by heuristic gating (includes tool, reason)
- `finish_guard`: Finish quality gate evaluation (includes approved boolean, feedback, hint)
- `finish`: Agent called finish tool (includes report_length, num_sources, report, sources)
- `error`: Error occurred during iteration (includes iteration, error message)

All events include optional `message` field for human-readable summaries.

Connect to `ws://localhost:8000/ws` to receive events. Events are also stored in the database as `TraceEvent` records for historical analysis.

## Common Tasks

### Running a Research Query

**CLI**:
```bash
cd backend
python main.py
# Enter query when prompted
```

**API**:
```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest advances in RAG?"}'
```

### Accessing Session History

```bash
# Get all sessions
curl http://localhost:8000/api/history

# Get specific session
curl http://localhost:8000/api/history/{session_id}

# Get trace for session
curl http://localhost:8000/api/history/{session_id}/trace
```

### Exporting Reports

```bash
# Export as PDF
curl http://localhost:8000/api/export/pdf/{session_id} --output report.pdf

# Export as Word
curl http://localhost:8000/api/export/word/{session_id} --output report.docx

# Export as HTML
curl http://localhost:8000/api/export/html/{session_id} --output report.html
```

### Monitoring Performance

The system tracks:
- Token usage per provider
- Cost in USD
- Iteration counts
- Tool execution times
- Overall session duration

Metrics are stored in database and returned in ResearchResult.

## Platform Notes

This codebase is developed on **Windows** (note .bat scripts for setup/start/stop). Paths use backslashes in documentation but Python code uses pathlib for cross-platform compatibility.

The virtual environment is located at `backend\venv\` and should be activated before running Python commands.


## Troubleshooting

**Import errors**: Ensure virtual environment is activated and dependencies installed
**API key errors**: Check .env file exists and has valid keys
**Config errors**: Verify running from correct directory (backend for CLI, root for Docker)
**Rate limits**: System automatically falls back to next provider
**Database locked**: Close any open SQLite connections/viewers

## Important Files to Review

- `backend/app/agents/react_agent.py`: Core agent logic
- `backend/app/llm/manager.py`: LLM orchestration
- `config.yaml`: All configurable parameters
- `backend/main.py`: Simple usage example
- `backend/app/api/main.py`: API server setup
