# 🔬 Agentic AI Research Lab

> **Production-grade autonomous research system powered by the ReAct (Reasoning + Acting) pattern with multi-provider LLM support, real-time metrics, and comprehensive evaluation.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-3178c6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

The **Agentic AI Research Lab** is an advanced autonomous research system that leverages Large Language Models (LLMs) to perform comprehensive research tasks. Unlike traditional search tools, this system employs the **ReAct pattern** (Reasoning + Acting) to iteratively gather information, analyze sources, and synthesize high-quality research reports.

### What Makes This Different?

- **Autonomous Decision Making**: The agent decides what tools to use, when to use them, and how many iterations are needed
- **Multi-Source Aggregation**: Combines web search, academic papers (ArXiv), code repositories (GitHub), and PDF documents
- **Quality Evaluation**: Built-in LLM-as-judge evaluator scores research quality on 4 dimensions (0-1 scale)
- **Real-Time Visibility**: WebSocket streaming shows live progress, metrics, and reasoning steps
- **Production-Ready**: Comprehensive metrics, tracing, error handling, and provider failover

---

## ✨ Key Features

### 🤖 Intelligent Research Agent

- **ReAct Pattern Implementation**: Iterative Think → Act → Observe cycles
- **Multi-Tool Orchestration**: Can call multiple research tools per iteration
- **Adaptive Reasoning**: Agent adjusts strategy based on findings
- **Citation Management**: Automatic source tracking and inline citations

### 🔧 Research Tools

| Tool | Purpose | Provider Options |
|------|---------|------------------|
| **Web Search** | Current news, articles, general info | Tavily (primary) → Serper → SerpAPI (failover) |
| **ArXiv Search** | Academic papers, research publications | ArXiv API |
| **GitHub Search** | Code examples, repositories, implementations | GitHub API |
| **PDF Extraction** | Extract text from PDF papers | PyMuPDF |

### 🔄 Multi-Provider LLM Support

- **Primary Providers**: OpenAI, Google Gemini, OpenRouter
- **Automatic Failover**: Falls back to secondary/tertiary providers on failure
- **Cost Tracking**: Real-time token usage and USD cost calculation
- **Provider Metrics**: Tracks failover rates and provider reliability

### 📊 Advanced Metrics & Observability

#### Current Run Metrics
- Iteration latency (avg & individual)
- Tool execution times (per-tool breakdown)
- End-to-end duration
- Token usage & cost
- Tool success rate
- Quality scores (4 metrics)

#### Historical Metrics (Inception Till Date)
- Median latencies across all sessions
- Average tokens/cost per session
- Session success rate
- Provider failover rate
- Quality score trends

### 🎯 Quality Evaluation System

**End-to-End Evaluation** (LLM-as-judge, 0-1 scale):
- **Relevance**: How well the report answers the query
- **Accuracy**: Factual correctness of information
- **Completeness**: Coverage of all key aspects
- **Source Quality**: Credibility and authority of sources

**Qualitative Feedback**:
- Strengths (3-5 points)
- Weaknesses (3-5 points)
- Recommendations for improvement

### 🌐 Modern Web Interface

- **Real-Time Updates**: WebSocket-based live progress tracking
- **Three-Panel Layout**:
  - **Left**: ReAct Trace Timeline (iteration history)
  - **Center**: Current Activity Panel (live tool execution)
  - **Right**: Research Output Panel (final report)
- **Metrics Dashboard**: Visual charts and statistics
- **Responsive Design**: Mobile-friendly, dark theme

### 🔍 Content Pipeline (Optional)

Advanced content processing for improved quality:
- **Classification**: Relevance scoring for search results
- **Extraction**: Key information extraction from documents
- **Ranking**: Rerank results by relevance
- **Caching**: TTL-based cache to reduce API calls

### 📦 Export Capabilities

Export research reports in multiple formats:
- Markdown (`.md`)
- PDF (with styling)
- Microsoft Word (`.docx`)
- HTML
- JSON (full session data)

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│  (Next.js 14 + TypeScript + Tailwind CSS + WebSocket Client)   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ REST API     │  │ WebSocket    │  │ Background   │         │
│  │ Routes       │  │ Manager      │  │ Tasks        │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            ResearcherAgent (ReAct Loop)                  │  │
│  │  Think → Select Tools → Execute → Process → Observe     │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐    │
│  │ LLM Manager │  │ Tool System │  │ Content Pipeline   │    │
│  │ (Multi-     │  │ (Web, ArXiv,│  │ (Classification,   │    │
│  │  provider   │  │  GitHub,    │  │  Extraction,       │    │
│  │  failover)  │  │  PDF)       │  │  Ranking, Cache)   │    │
│  └─────────────┘  └─────────────┘  └────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐    │
│  │ Evaluator   │  │ Metrics     │  │ Trace & History    │    │
│  │ Agent       │  │ Collector   │  │ Manager            │    │
│  └─────────────┘  └─────────────┘  └────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                   ┌──────────────────┐
                   │  SQLite Database │
                   │  (Sessions,      │
                   │   Trace Events,  │
                   │   Evaluations)   │
                   └──────────────────┘
```

### ReAct Loop Flow

```
User Query
    ↓
Initialize Session + MetricsCollector
    ↓
┌─────────────── ReAct Loop (Max 10 Iterations) ───────────────┐
│                                                               │
│  1. Think & Plan (LLM Reasoning)                            │
│         ↓                                                     │
│  2. Select Tools (web_search, arxiv, github, pdf, finish)   │
│         ↓                                                     │
│  3. Execute Tools (sequential, multiple allowed)            │
│         ↓                                                     │
│  4. Process Results (optional Content Pipeline)             │
│         ↓                                                     │
│  5. Observation (analyze tool outputs)                      │
│         ↓                                                     │
│  Add to conversation history → LOOP BACK (or exit if       │
│  "finish" action called)                                     │
│                                                               │
│  Real-time: Record metrics, save trace, emit WebSocket      │
└───────────────────────────────────────────────────────────────┘
    ↓
Save Final Report
    ↓
Evaluator Agent (LLM-as-Judge)
    ↓
Finalize Metrics + Save to History
    ↓
Display Results + Metrics Dashboard
```

---

## 🛠️ Tech Stack

### Backend

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | FastAPI 0.115+ | High-performance async API framework |
| **Runtime** | Python 3.11+ | Core programming language |
| **Database** | SQLite + SQLAlchemy | Async ORM for session persistence |
| **LLM Providers** | OpenAI, Google Gemini, OpenRouter | Multi-provider language model support |
| **Search APIs** | Tavily, Serper, SerpAPI | Web search with failover |
| **Academic** | ArXiv API | Research paper search |
| **Code Search** | GitHub API (PyGithub) | Repository search |
| **PDF Processing** | PyMuPDF (fitz) | PDF text extraction |
| **WebSocket** | FastAPI WebSockets | Real-time streaming |
| **Export** | python-docx, ReportLab | Document generation |
| **Tracing** | LangSmith (optional) | Observability and debugging |
| **Caching** | Redis (optional) | Distributed caching |

### Frontend

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | Next.js 14.2+ | React framework with SSR |
| **Language** | TypeScript 5.4+ | Type-safe JavaScript |
| **Styling** | Tailwind CSS 3.4+ | Utility-first CSS framework |
| **State** | Zustand 4.5+ | Lightweight state management |
| **WebSocket** | Socket.IO Client 4.7+ | Real-time communication |
| **UI Components** | Radix UI | Accessible component primitives |
| **Icons** | Lucide React | Icon library |
| **Markdown** | react-markdown + remark-gfm | Render markdown reports |
| **Charts** | Recharts 2.12+ | Data visualization |

### DevOps

- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **pytest**: Backend testing
- **Black, Flake8, MyPy**: Code quality tools
- **ESLint**: Frontend linting

---

## 📁 Project Structure

```
research_agent/
├── backend/                       # Python FastAPI backend
│   ├── app/
│   │   ├── agents/               # ReAct agent & evaluator implementations
│   │   │   ├── react_agent.py   # Main ResearcherAgent (ReAct loop)
│   │   │   ├── evaluator_agent.py  # Quality evaluation (LLM-as-judge)
│   │   │   └── models.py         # Pydantic models (AgentStep, ResearchResult)
│   │   ├── llm/                  # LLM provider abstractions
│   │   │   ├── manager.py        # Multi-provider manager with failover
│   │   │   ├── openai_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   └── openrouter_provider.py
│   │   ├── tools/                # Research tools
│   │   │   ├── web_search.py     # Multi-provider web search
│   │   │   ├── arxiv_search.py   # Academic paper search
│   │   │   ├── github_search.py  # Code repository search
│   │   │   ├── pdf_parser.py     # PDF text extraction
│   │   │   └── definitions.py    # OpenAI function definitions
│   │   ├── content/              # Content processing pipeline
│   │   │   ├── pipeline.py       # Orchestrates classification/extraction/ranking
│   │   │   ├── classifier.py     # Relevance classification
│   │   │   ├── extractor.py      # Key information extraction
│   │   │   ├── ranker.py         # Result ranking
│   │   │   └── cache.py          # TTL-based caching
│   │   ├── api/                  # FastAPI routes & WebSocket
│   │   │   ├── main.py           # App initialization, CORS, lifespan
│   │   │   ├── websocket.py      # WebSocket manager for real-time updates
│   │   │   ├── routes/
│   │   │   │   ├── research.py   # POST /api/research/start
│   │   │   │   ├── history.py    # GET /api/history
│   │   │   │   ├── export.py     # Export endpoints (PDF, Word, etc.)
│   │   │   │   └── config.py     # Runtime config management
│   │   │   └── models/
│   │   │       ├── requests.py   # Request schemas
│   │   │       └── responses.py  # Response schemas
│   │   ├── database/             # SQLAlchemy models & operations
│   │   │   ├── models.py         # ResearchSession, TraceEvent, Evaluations
│   │   │   └── database.py       # CRUD operations
│   │   ├── metrics/              # Performance metrics system
│   │   │   ├── collector.py      # MetricsCollector (records LLM/tool/iteration)
│   │   │   ├── models.py         # MetricsData model
│   │   │   └── history.py        # Persistent metrics storage (JSON)
│   │   ├── export/               # Document export functionality
│   │   │   ├── pdf_exporter.py
│   │   │   ├── word_exporter.py
│   │   │   └── html_exporter.py
│   │   ├── tracing/              # Observability & logging
│   │   │   └── langsmith.py      # LangSmith integration
│   │   ├── config/               # Configuration management
│   │   │   └── settings.py       # Pydantic Settings for config.yaml
│   │   └── utils/                # Utility functions
│   ├── main.py                   # CLI entry point for testing
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Backend container image
│
├── frontend/                      # Next.js React frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Main research page
│   │   │   └── layout.tsx        # Root layout
│   │   ├── components/
│   │   │   └── research/         # Research UI components
│   │   │       ├── header.tsx
│   │   │       ├── query-input.tsx
│   │   │       ├── react-trace-timeline.tsx  # Left panel: iteration history
│   │   │       ├── current-activity-panel.tsx  # Center: live activity
│   │   │       ├── research-output-panel.tsx  # Right: final report
│   │   │       ├── metrics-dashboard.tsx  # Metrics visualization
│   │   │       ├── metric-card.tsx
│   │   │       ├── score-bar.tsx
│   │   │       └── tool-breakdown.tsx
│   │   ├── store/
│   │   │   └── research-store.ts  # Zustand state management
│   │   ├── hooks/
│   │   │   └── use-websocket.ts   # WebSocket connection hook
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript type definitions
│   │   └── lib/
│   │       └── utils.ts          # Utility functions
│   ├── package.json
│   └── Dockerfile                # Frontend container image (optional)
│
├── config.yaml                    # Main configuration file (LLM, tools, evaluation)
├── .env.example                   # Environment variable template
├── docker-compose.yml            # Container orchestration
├── setup.bat / setup.sh          # Setup scripts (Windows/Unix)
├── start.bat / start.sh          # Start scripts
├── stop.bat                      # Stop script (Windows)
├── GETTING_STARTED.md            # Quick start guide
└── README.md                     # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **Git**
- **API Keys** (at least one LLM provider):
  - OpenAI API key, OR
  - Google API key (Gemini), OR
  - OpenRouter API key

### Quick Start (Windows)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd research_agent
   ```

2. **Set up environment variables**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and add your API keys:
   ```bash
   # Required: At least one LLM provider
   OPENAI_API_KEY=sk-...
   # OR
   GOOGLE_API_KEY=...
   # OR
   OPENROUTER_API_KEY=sk-or-...

   # Optional: Search providers (automatic failover)
   TAVILY_API_KEY=tvly-...
   SERPER_API_KEY=...
   SERPAPI_API_KEY=...

   # Optional: GitHub token (higher rate limits)
   GITHUB_TOKEN=ghp_...

   # Optional: Tracing
   LANGSMITH_API_KEY=...
   ```

3. **Run setup script**
   ```bash
   setup.bat
   ```
   This will:
   - Create Python virtual environment
   - Install backend dependencies
   - Install frontend dependencies

4. **Start the application**
   ```bash
   start.bat
   ```
   This will start:
   - Backend API at `http://localhost:8000`
   - Frontend UI at `http://localhost:3000`

### Quick Start (Linux/macOS)

```bash
# Clone repository
git clone <repository-url>
cd research_agent

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Make scripts executable
chmod +x setup.sh start.sh

# Run setup
./setup.sh

# Start application
./start.sh
```

### Docker Setup (Alternative)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## ⚙️ Configuration

The `config.yaml` file controls all application behavior. Key sections:

### LLM Provider Configuration

```yaml
llm:
  primary: "openrouter"  # Preferred provider
  fallback_order: ["openai", "gemini"]  # Fallback sequence

  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o-mini"  # Fast, cost-effective
    temperature: 0.7

  gemini:
    api_key: "${GOOGLE_API_KEY}"
    model: "gemini-2.5-flash"  # Options: gemini-2.5-pro, gemini-2.0-flash
    temperature: 0.7
    max_tokens: 8000

  openrouter:
    api_key: "${OPENROUTER_API_KEY}"
    model: "nvidia/llama-3.3-nemotron-super-49b-v1.5"
    temperature: 0.7
```

### Research Settings

```yaml
research:
  max_iterations: 10  # Maximum ReAct iterations
  timeout_minutes: 15  # Timeout for complete research session
  parallel_tool_execution: false  # Execute tools in parallel (experimental)
```

### Tool Settings

```yaml
tools:
  web_search_max_results: 10
  web_search_timeout_seconds: 90  # Total timeout across all providers
  tool_execution_timeout_seconds: 60  # Safety timeout per tool

  use_content_pipeline: true  # Advanced content processing
  pipeline_top_k: 10  # Number of top results to select
  pipeline_cache_ttl: 15  # Cache TTL in minutes

  # API keys (loaded from .env)
  tavily_api_key: "${TAVILY_API_KEY}"
  serper_api_key: "${SERPER_API_KEY}"
  serpapi_api_key: "${SERPAPI_API_KEY}"
  github_token: "${GITHUB_TOKEN}"
```

### Evaluation Settings

```yaml
evaluation:
  run_per_step: false  # Per-step evaluation REMOVED
  run_end_to_end: true  # End-to-end evaluation only (0-1 scale, 4 metrics)
  llm_as_judge: true  # Use LLM for evaluation
```

### Metrics & Tracing

```yaml
metrics:
  enabled: true
  collect_tool_metrics: true
  collect_llm_metrics: true
  collect_source_metrics: true

tracing:
  enabled: true
  provider: "custom"  # "langsmith" or "custom"
  log_level: "info"  # debug, info, warning, error
```

---

## 📖 Usage

### Web Interface

1. **Open browser**: Navigate to `http://localhost:3000`

2. **Enter research query**:
   - Example: "What are the latest advances in Retrieval-Augmented Generation (RAG)?"
   - Click "Start Research" button

3. **Watch real-time progress**:
   - **Left Panel**: ReAct trace showing each iteration's thought, action, and observation
   - **Center Panel**: Current activity with live tool execution status
   - **Right Panel**: Final report appears when research completes

4. **Review metrics**: Scroll down to see:
   - Current run metrics (latency, tokens, cost, quality scores)
   - Historical metrics (if multiple sessions completed)

5. **Export report**: Click export button to download as PDF, Word, or Markdown

### CLI Interface (Testing)

For quick testing without the frontend:

```bash
cd backend
python main.py
```

Enter your research query when prompted. The CLI will:
- Display iteration-by-iteration progress
- Show final report
- Display quality scores (0-1 scale)
- Save session to database

### Programmatic API Usage

```python
import httpx
import asyncio

async def research():
    async with httpx.AsyncClient() as client:
        # Start research
        response = await client.post(
            "http://localhost:8000/api/research/start",
            json={"query": "Explain quantum computing basics"}
        )
        session_id = response.json()["session_id"]

        # Poll for completion (or use WebSocket)
        session = await client.get(f"http://localhost:8000/api/history/{session_id}")
        print(session.json()["final_report"])

asyncio.run(research())
```

---

## 🌐 API Documentation

### Interactive API Docs

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Research

**POST** `/api/research/start`
- **Description**: Start a new research session
- **Request Body**:
  ```json
  {
    "query": "Research query here",
    "config": {  // Optional overrides
      "llm": {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.7
      },
      "research": {
        "max_iterations": 10
      }
    }
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "uuid-here",
    "message": "Research started",
    "websocket_url": "ws://localhost:8000/ws?session_id=uuid-here"
  }
  ```

**GET** `/api/history/{session_id}`
- **Description**: Get session details and final report
- **Response**: Full session data including report, trace, metadata

**GET** `/api/history/{session_id}/trace`
- **Description**: Get complete trace of all ReAct iterations
- **Response**: Array of trace events (thoughts, actions, observations)

**GET** `/api/history/{session_id}/evaluations`
- **Description**: Get quality evaluation scores
- **Response**:
  ```json
  {
    "session_id": "uuid",
    "end_to_end_evaluation": {
      "relevance_score": 0.95,
      "accuracy_score": 0.88,
      "completeness_score": 0.92,
      "source_quality_score": 0.90,
      "strengths": ["..."],
      "weaknesses": ["..."],
      "recommendations": ["..."]
    }
  }
  ```

#### Export

**GET** `/api/export/{session_id}?format=pdf`
- **Formats**: `pdf`, `word`, `html`, `markdown`, `json`
- **Response**: File download

#### Metrics

**GET** `/api/metrics/summary`
- **Description**: Get aggregated metrics across all sessions
- **Response**: Current run + historical metrics

#### WebSocket

**WS** `/ws?session_id={session_id}`
- **Events**:
  - `session_start`
  - `iteration_start` (iteration number)
  - `thought` (LLM reasoning)
  - `action` (tool selection)
  - `tool_execution` (tool running, duration, results)
  - `observation` (analysis of tool output)
  - `iteration_complete`
  - `finish` (final report ready)
  - `session_complete` (includes metrics and evaluation)
  - `error` (error occurred)

---

## 👨‍💻 Development

### Backend Development

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with auto-reload
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Code quality
black .                # Format code
flake8 .              # Lint
mypy app              # Type checking
isort .               # Sort imports
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server (with hot reload)
npm run dev

# Type checking
npm run type-check

# Lint
npm run lint

# Build for production
npm run build

# Start production server
npm start
```

### Adding a New Research Tool

1. **Create tool function** in `backend/app/tools/my_tool.py`:
   ```python
   async def my_tool(param: str) -> Dict[str, Any]:
       """Tool implementation."""
       return {"results": [...], "metadata": {...}}
   ```

2. **Add OpenAI function definition** in `backend/app/tools/definitions.py`:
   ```python
   {
       "type": "function",
       "function": {
           "name": "my_tool",
           "description": "What this tool does",
           "parameters": {
               "type": "object",
               "properties": {
                   "param": {"type": "string", "description": "Parameter description"}
               },
               "required": ["param"]
           }
       }
   }
   ```

3. **Register in** `backend/app/tools/__init__.py`

4. **Update agent prompt** in `backend/app/agents/react_agent.py` (SYSTEM_PROMPT)

### Adding a New LLM Provider

1. **Create provider class** in `backend/app/llm/my_provider.py`:
   ```python
   from .base import BaseLLMProvider

   class MyLLMProvider(BaseLLMProvider):
       async def generate(self, messages, **kwargs):
           # Implementation
           pass
   ```

2. **Register in** `backend/app/llm/manager.py`

3. **Add configuration** to `config.yaml`:
   ```yaml
   llm:
     my_provider:
       api_key: "${MY_PROVIDER_API_KEY}"
       model: "model-name"
   ```

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Scale backend (if needed)
docker-compose up -d --scale backend=3

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Considerations

1. **Environment Variables**:
   - Never commit `.env` file
   - Use secrets management (AWS Secrets Manager, Azure Key Vault, etc.)

2. **Database**:
   - For production, consider PostgreSQL instead of SQLite
   - Uncomment PostgreSQL service in `docker-compose.yml`

3. **Scaling**:
   - Backend is stateless (except WebSocket connections)
   - Can scale horizontally with load balancer
   - Use Redis for distributed caching

4. **Security**:
   - Enable HTTPS
   - Set `require_https: true` in `config.yaml`
   - Enable API key authentication
   - Configure CORS origins properly

5. **Monitoring**:
   - Enable LangSmith for tracing
   - Set up application monitoring (Sentry, New Relic, etc.)
   - Configure alerts for errors and high latency

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest                        # Run all tests
pytest tests/test_agents.py   # Run specific test file
pytest -v                     # Verbose output
pytest --cov                  # With coverage report
pytest -k "test_web_search"   # Run tests matching pattern
```

### Frontend Tests

```bash
cd frontend
npm test                      # Run tests
npm test -- --coverage        # With coverage
```

### Manual Testing Checklist

- [ ] CLI research completes successfully
- [ ] Web UI loads and displays correctly
- [ ] WebSocket connection established
- [ ] Real-time updates appear during research
- [ ] Final report displays correctly
- [ ] Metrics dashboard shows data
- [ ] All 4 tools can execute (web, arxiv, github, pdf)
- [ ] Multi-tool execution in single iteration works
- [ ] LLM provider failover triggers correctly
- [ ] Quality evaluation completes (4 scores)
- [ ] Export to PDF/Word/Markdown works
- [ ] Session persists in database
- [ ] Metrics history saved to JSON

---

## 🔧 Troubleshooting

### Common Issues

#### Backend won't start

**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
cd backend
# Ensure virtual environment is activated
pip install -r requirements.txt
```

---

#### "No API key configured"

**Problem**: LLM provider API key not found

**Solution**:
1. Check `.env` file exists
2. Verify key is set: `OPENAI_API_KEY=sk-...`
3. Restart backend to reload environment variables

---

#### Frontend can't connect to backend

**Problem**: `CORS` errors or connection refused

**Solution**:
1. Verify backend is running at `http://localhost:8000`
2. Check `config.yaml` CORS settings:
   ```yaml
   api:
     cors_origins:
       - "http://localhost:3000"
   ```
3. Restart backend after config changes

---

#### WebSocket disconnects immediately

**Problem**: WebSocket connection fails

**Solution**:
1. Check browser console for errors
2. Verify session ID is valid
3. Ensure no firewall blocking WebSocket port
4. Try different browser

---

#### Research gets stuck / hangs

**Problem**: Agent loops without finishing

**Solution**:
1. Check `max_iterations` in `config.yaml` (default 10)
2. Verify timeout setting (`timeout_minutes: 15`)
3. Check backend logs for errors
4. LLM may not be calling `finish` action - try different model

---

#### Metrics show zeros

**Problem**: Metrics not being tracked

**Solution**:
1. Verify `metrics.enabled: true` in `config.yaml`
2. Check if `MetricsCollector` instrumentation is in place
3. See `ALL_FIXES_COMPLETE.md` for details on metrics fixes

---

#### Tool execution fails

**Problem**: Specific tool returns errors

**Solution**:
- **Web search**: Check API keys (Tavily, Serper, SerpAPI)
- **GitHub**: Verify `GITHUB_TOKEN` is set
- **PDF**: Ensure URL is accessible
- **ArXiv**: Check internet connection

---

### Debug Mode

Enable detailed logging:

1. **Backend**: Set in `config.yaml`
   ```yaml
   tracing:
     log_level: "debug"
   ```

2. **Frontend**: Open browser DevTools (F12) → Console

3. **Check logs**:
   ```bash
   # Backend logs (if running directly)
   tail -f backend/logs/app.log

   # Docker logs
   docker-compose logs -f backend
   ```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Follow code style**:
   - Backend: Black, Flake8, MyPy
   - Frontend: ESLint, Prettier
4. **Add tests** for new functionality
5. **Update documentation** (README, docstrings)
6. **Commit with clear messages**: `git commit -m "Add: Feature description"`
7. **Push to your fork**: `git push origin feature/my-feature`
8. **Open a Pull Request**

### Development Guidelines

- Follow existing code structure and patterns
- Add type hints for Python code
- Use TypeScript for frontend code
- Write docstrings for public functions
- Keep functions small and focused
- Add comments for complex logic
- Update `CHANGELOG.md` for significant changes

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ReAct Pattern**: Inspired by the paper "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022)
- **FastAPI**: For the excellent async framework
- **Next.js**: For the powerful React framework
- **OpenAI**: For pioneering function calling
- **LangChain/LangSmith**: For observability patterns
- **Tavily**: For AI-optimized search API
- **ArXiv**: For open access to research papers
- **GitHub**: For code search API

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

## 🗺️ Roadmap

### v1.0 (Current)
- ✅ ReAct agent with 4 research tools
- ✅ Multi-provider LLM support (OpenAI, Gemini, OpenRouter)
- ✅ Real-time WebSocket updates
- ✅ Comprehensive metrics & evaluation
- ✅ Modern Next.js frontend
- ✅ Export to PDF/Word/Markdown

### v1.1 (Planned)
- [ ] Multi-session management UI
- [ ] Collaborative research (share sessions)
- [ ] Custom tool creation via UI
- [ ] Advanced query templates
- [ ] Mobile app (React Native)

### v2.0 (Future)
- [ ] Multi-agent collaboration
- [ ] Knowledge graph integration
- [ ] Long-term memory system
- [ ] Voice interface
- [ ] Plugin system for third-party tools

---

<div align="center">

**Built with ❤️ using ReAct, FastAPI, and Next.js**

[⭐ Star on GitHub](https://github.com/your-repo) • [📖 Documentation](https://docs.example.com) • [💬 Discord](https://discord.gg/example)

</div>
