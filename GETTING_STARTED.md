# Getting Started Guide

## Prerequisites

- **Python 3.11 or higher**
- **API Keys** for at least one LLM provider:
  - OpenAI API key (recommended), OR
  - Google Gemini API key, OR
  - OpenRouter API key

## Installation Steps

### 1. Set Up Python Environment

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
backend\venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- FastAPI and Uvicorn (API server)
- OpenAI, Google GenAI (LLM providers)
- DuckDuckGo Search, ArXiv, PyMuPDF (research tools)
- SQLAlchemy, Pydantic (data management)
- And more...

### 3. Configure API Keys

```bash
# Copy the example environment file
copy .env.example .env    # On Windows
# OR
cp .env.example .env      # On macOS/Linux

# Edit .env and add your API keys
notepad .env              # On Windows
# OR
nano .env                 # On macOS/Linux
```

**Minimum Required:** Add at least ONE of these API keys to `.env`:

```env
# Option 1: OpenAI (Recommended - most reliable)
OPENAI_API_KEY=sk-...

# Option 2: Google Gemini (Free tier available)
GOOGLE_API_KEY=...

# Option 3: OpenRouter (Various models)
OPENROUTER_API_KEY=sk-or-...
```

**Optional API Keys:**
```env
# GitHub token for higher rate limits (optional)
GITHUB_TOKEN=ghp_...

# SerpAPI for web search backup (optional)
SERPAPI_API_KEY=...
```

### 4. Verify Installation

```bash
python test_imports.py
```

If all imports succeed, you should see:
```
Testing imports...
✓ LLM providers
✓ Research tools
✓ Agents
✓ Database
✓ Configuration

All imports successful!
```

### 5. Run Your First Research

```bash
python main.py
```

You'll be prompted to enter a research query. Try examples like:
- "What are the latest advances in retrieval-augmented generation?"
- "Explain recent breakthroughs in multimodal LLMs"
- "What are the best practices for prompt engineering in 2025?"

Or press Enter to use the default demo query.

## Understanding the Output

When you run a research query, you'll see:

### 1. Research Progress
```
Iteration 1/10
Action: web_search
...
```

### 2. Research Results
```
RESEARCH COMPLETED
Status: completed
Iterations: 5
Duration: 45.2s
Tokens: 12,450
Cost: $0.0025
Sources: 15
```

### 3. Final Report
The agent's comprehensive research report in markdown format

### 4. Evaluation
```
EVALUATING RESEARCH...
Overall Quality Score: 8.5/10
Average Per-Step Score: 8.2/10

Dimension Scores:
  - Relevance: 9.0/10
  - Accuracy: 8.5/10
  - Completeness: 8.0/10
  ...

Strengths:
  • Comprehensive coverage...
  • Well-cited sources...

Weaknesses:
  • Could include more recent papers...
```

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:** Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### API Key Errors

**Problem:** `ValueError: Environment variable OPENAI_API_KEY is not set`

**Solution:**
1. Copy `.env.example` to `.env`
2. Add your API keys to `.env`
3. Make sure you're in the `backend` directory when running

### Configuration Errors

**Problem:** `FileNotFoundError: Config file not found: config.yaml`

**Solution:** Make sure you're running from the `backend` directory:
```bash
cd backend
python main.py
```

### Rate Limit Errors

**Problem:** API provider returns rate limit error

**Solution:** The system automatically falls back to the next provider. Make sure you have configured multiple providers in `config.yaml`:

```yaml
llm:
  primary: "openai"
  fallback_order: ["gemini", "openrouter"]
```

## Configuration Options

### Adjusting Research Parameters

Edit `config.yaml` to customize:

```yaml
research:
  max_iterations: 10      # Maximum research iterations
  timeout_minutes: 15     # Maximum duration
  parallel_tool_execution: false

tools:
  web_search_max_results: 10   # Results per search
  arxiv_max_results: 20
  github_max_results: 10
  pdf_max_pages: 50

evaluation:
  run_per_step: true      # Evaluate each iteration
  run_end_to_end: true    # Evaluate final report
  llm_as_judge: true      # Use LLM for evaluation
```

### Changing LLM Providers

To use Gemini as primary instead of OpenAI:

```yaml
llm:
  primary: "gemini"
  fallback_order: ["openai", "openrouter"]
```

### Adjusting Model Selection

To use GPT-4o instead of GPT-4o-mini:

```yaml
llm:
  openai:
    model: "gpt-4o"  # More capable but higher cost
```

## Cost Estimation

Typical costs per research query:
- **GPT-4o-mini**: $0.0015 - $0.0025
- **Gemini 2.5 Flash**: $0.0009 - $0.0015  (cheapest)
- **GPT-4o**: $0.015 - $0.025  (highest quality)

The system tracks exact costs and displays them after each query.

## Next Steps

### 1. Try Different Queries

Experiment with various research topics:
- Technical topics (AI, ML, programming)
- Academic research questions
- Current events and trends
- Product comparisons

### 2. Analyze the Trace

Review how the agent:
- Breaks down the query
- Selects appropriate tools
- Synthesizes information
- Decides when to stop

### 3. Evaluate Results

Pay attention to:
- Quality scores across the four 0-1 metrics (relevance, accuracy, completeness, source quality)
- Strengths, weaknesses, and recommendations surfaced by the EvaluatorAgent
- Session-level latency, token, cost, and tool success metrics in the dashboard

### 4. Customize for Your Needs

Modify:
- System prompts in `backend/app/agents/react_agent.py`
- Tool parameters in `config.yaml`
- Evaluation criteria in `backend/app/agents/evaluator_agent.py`

## Advanced Usage

### Using the System Programmatically

```python
import asyncio
from app.config import load_settings, get_llm_config_dict
from app.llm import LLMManager
from app.agents import ResearcherAgent, EvaluatorAgent
from app.database import init_database

async def my_research():
    # Initialize
    settings = load_settings("config.yaml")
    await init_database(settings.database.url)
    llm_manager = LLMManager(get_llm_config_dict(settings))

    # Create agents
    researcher = ResearcherAgent(llm_manager)
    evaluator = EvaluatorAgent(llm_manager)

    # Research
    result = await researcher.research("Your query here")

    # Evaluate
    evaluation = await evaluator.evaluate_research(result)

    return result, evaluation

# Run
result, evaluation = asyncio.run(my_research())
print(f"Quality: {evaluation.overall_quality_score}/10")
```

### Accessing the Database

Research sessions are stored in SQLite:

```python
from app.database import get_session, get_session_trace

# Get a specific session
session = await get_session("session-id")
print(session.final_report)

# Get trace events
trace = await get_session_trace("session-id")
for event in trace:
    print(f"{event.type}: {event.data}")
```

## Getting Help

- **Documentation**: See `README.md` for architecture details
- **Implementation**: See `IMPLEMENTATION_SUMMARY.md` for component details
- **Issues**: Check error messages carefully - they're descriptive
- **Logs**: The system logs extensively - check console output

## Summary

You now have a fully functional Agentic AI Research System! The agent can:
- ✅ Search the web, ArXiv, and GitHub
- ✅ Extract text from PDFs
- ✅ Reason about information needs
- ✅ Synthesize comprehensive reports
- ✅ Self-evaluate its performance
- ✅ Track costs and metrics

**Enjoy researching! 🚀**
