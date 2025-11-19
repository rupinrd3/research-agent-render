# Agentic AI Research Solution - Complete Design Document

## Executive Summary

This document outlines a comprehensive educational platform for Agentic AI Research that demonstrates autonomous research capabilities through a **ReAct (Reasoning + Acting)** architecture. The system provides complete transparency into agent reasoning, features flexible LLM provider support (OpenAI, Gemini, OpenRouter), implements comprehensive per-step and end-to-end evaluation, and delivers a modern, real-time web interface with full observability.

**Key Features:**
- 🤖 **2-Agent ReAct Architecture** (Researcher + Evaluator)
- 🔄 **Real-time Trace Visualization** of complete agent reasoning
- 🛠️ **4 Research Tools** (Web Search, ArXiv, GitHub, PDF Parser)
- 📊 **Comprehensive Multi-Level Evaluation** (Per-Step + End-to-End)
- 🎨 **Modern Animated UI** with real-time WebSocket updates
- 💰 **Cost-Effective** ($0.002-0.003 per research query)
- 🔧 **Flexible LLM Provider** (OpenAI, Gemini, OpenRouter with automatic fallback)
- 📝 **Complete Observability** (Every thought, action, and observation traced)
- 📤 **Multiple Export Formats** (Markdown, PDF, Word, JSON, HTML)

---

## 1. System Architecture

### 1.1 High-Level Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│              Web Frontend (Next.js 14 + React + TypeScript)        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   ReAct      │  │   Live       │  │   Evaluation          │  │
│  │   Trace      │  │   Research   │  │   Analytics           │  │
│  │   Timeline   │  │   Output     │  │   Dashboard           │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│           WebSocket (Real-time Updates) + REST API                │
└───────────────────────────────────────────────────────────────────┘
                                 ↕
┌───────────────────────────────────────────────────────────────────┐
│                   Backend Server (FastAPI + Python)                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              ReAct Orchestration Engine                      │ │
│  │  • Reasoning Loop Control    • State Management             │ │
│  │  • Action Execution          • Event Broadcasting           │ │
│  │  • Trace Collection          • Session Persistence          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           Agent System (2 Agents)                            │ │
│  │  ┌──────────────────────┐      ┌──────────────────────┐    │ │
│  │  │  Researcher Agent    │      │  Evaluator Agent     │    │ │
│  │  │  (ReAct Pattern)     │      │  (Multi-Level Eval)  │    │ │
│  │  │  • Think & Reason    │      │  • Per-Step Analysis │    │ │
│  │  │  • Select Tools      │      │  • End-to-End Review │    │ │
│  │  │  • Execute Actions   │      │  • Performance Metrics│   │ │
│  │  │  • Synthesize Report │      │  • Quality Scoring   │    │ │
│  │  └──────────────────────┘      └──────────────────────┘    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │        Flexible LLM Provider Layer (with Fallback)           │ │
│  │  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐ │ │
│  │  │   OpenAI      │  │   Gemini     │  │  OpenRouter     │ │ │
│  │  │   API         │  │   2.5 Flash  │  │  (DeepInfra)    │ │ │
│  │  │ (Configurable)│  │              │  │  Nemotron 49B   │ │ │
│  │  └───────────────┘  └──────────────┘  └─────────────────┘ │ │
│  │              ↓ Unified LLM Manager Interface ↓              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           Content Management Pipeline                        │ │
│  │  [Extract] → [Summarize] → [Rank] → [Cache] → [Serve]      │ │
│  │  • PDF Parsing      • Web Scraping     • Token Management   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  Tool Layer (4 Tools)                        │ │
│  │  [Web Search]  [ArXiv Search]  [GitHub Search]  [PDF Parse] │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Comprehensive Observability Layer               │ │
│  │  • LangSmith Integration     • Custom Trace Logger          │ │
│  │  • Performance Metrics       • Per-Step Evaluation          │ │
│  │  • End-to-End Evaluation     • Cost Tracking                │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
                                 ↕
┌───────────────────────────────────────────────────────────────────┐
│        Storage Layer (SQLite + Redis Cache + Local FS)            │
│  • Research Sessions    • Complete Traces     • Content Cache     │
│  • Evaluation Results   • Performance Metrics • Export Artifacts  │
└───────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

**Frontend:**
- **Next.js 14+** (App Router) with TypeScript
- **TailwindCSS** for utility-first styling
- **Framer Motion** for smooth animations
- **Zustand** for lightweight state management
- **React Flow** for agent workflow visualization
- **Recharts** for evaluation metrics charts
- **Socket.IO Client** for real-time updates
- **React Markdown** + **Prism.js** for syntax highlighting
- **Radix UI** for accessible primitives
- **Lucide React** for modern icons

**Backend:**
- Python 3.11+
- **FastAPI** for async REST API and WebSocket
- **LangChain 0.1+** with **LangGraph** for ReAct orchestration
- **SQLite** for data persistence
- **Redis** (optional) for content caching
- **Pydantic v2** for data validation and serialization
- **httpx** for async HTTP requests

**LLM Providers:**
- **OpenAI API** (configurable model: gpt-4o-mini, gpt-4o, etc.)
- **Google Gemini API** (Gemini 2.5 Flash)
- **OpenRouter API** (nvidia/llama-3.3-nemotron-super-49b-v1.5 via DeepInfra)

**Tools & Libraries:**
- **DuckDuckGo Search** (unlimited, free) primary
- **SerpAPI** (100 queries/month free) backup
- **ArXiv API** (free, unlimited)
- **GitHub API** (5000 req/hour authenticated, free)
- **PyMuPDF (fitz)** for PDF text extraction
- **Trafilatura** for clean web content extraction
- **BeautifulSoup4** for HTML parsing
- **tiktoken** for token counting
- **python-docx** for Word export
- **reportlab** for PDF export
- **markdown** for Markdown processing

**Observability:**
- **LangSmith** (free tier) for comprehensive tracing
- Custom trace logger with WebSocket broadcasting
- Performance metrics collection
- Cost tracking per query

---

## 2. Flexible LLM Provider System

### 2.1 Design Philosophy

The LLM Manager implements a **Strategy Pattern** with **automatic fallback** to ensure resilience. If the primary provider fails (API error, rate limit, timeout), the system automatically falls back to secondary providers without user intervention.

### 2.2 LLM Provider Architecture

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import openai
import google.generativeai as genai
import httpx
import tiktoken
import logging

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate completion with optional tool calling support"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get current model name"""
        pass
    
    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD"""
        pass

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider with configurable model"""
    
    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    }
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**kwargs)
            
            return {
                "content": response.choices[0].message.content,
                "tool_calls": getattr(response.choices[0].message, "tool_calls", None),
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": self.model,
                "provider": "openai"
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def get_model_name(self) -> str:
        return self.model
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-4o-mini"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""
    
    PRICING = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    }
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = None  # Initialized per request with tools
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        try:
            # Convert OpenAI format to Gemini format
            gemini_messages = self._convert_messages(messages)
            gemini_tools = self._convert_tools(tools) if tools else None
            
            # Initialize model with tools
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=gemini_tools
            )
            
            response = await self.model.generate_content_async(
                gemini_messages,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            
            # Extract tool calls if present
            tool_calls = None
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        # Convert Gemini function call to OpenAI format
                        tool_calls = self._convert_function_calls(part.function_call)
            
            return {
                "content": response.text if hasattr(response, 'text') else None,
                "tool_calls": tool_calls,
                "finish_reason": "stop",
                "usage": {
                    "input_tokens": response.usage_metadata.prompt_token_count,
                    "output_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                },
                "model": self.model_name,
                "provider": "gemini"
            }
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        # Approximate (Gemini uses different tokenizer)
        return len(text) // 4
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(self.model_name, self.PRICING["gemini-2.5-flash"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI message format to Gemini prompt"""
        prompt_parts = []
        for msg in messages:
            if msg["role"] == "system":
                prompt_parts.append(f"System: {msg['content']}")
            elif msg["role"] == "user":
                prompt_parts.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                prompt_parts.append(f"Assistant: {msg['content']}")
        return "\n\n".join(prompt_parts)
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List:
        """Convert OpenAI tool format to Gemini FunctionDeclaration"""
        from google.generativeai.types import FunctionDeclaration
        
        gemini_tools = []
        for tool in tools:
            func = tool.get("function", {})
            gemini_tools.append(
                FunctionDeclaration(
                    name=func.get("name"),
                    description=func.get("description"),
                    parameters=func.get("parameters")
                )
            )
        return gemini_tools
    
    def _convert_function_calls(self, function_call) -> List[Dict]:
        """Convert Gemini function call to OpenAI format"""
        return [{
            "id": f"call_{hash(function_call.name)}",
            "type": "function",
            "function": {
                "name": function_call.name,
                "arguments": str(function_call.args)
            }
        }]

class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API provider (supports DeepInfra models)"""
    
    PRICING = {
        "nvidia/llama-3.3-nemotron-super-49b-v1.5": {
            "input": 0.40,
            "output": 0.40
        }
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://agentic-research-lab.com",
                "X-Title": "Agentic Research Lab",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            choice = data["choices"][0]
            message = choice["message"]
            
            return {
                "content": message.get("content"),
                "tool_calls": message.get("tool_calls"),
                "finish_reason": choice.get("finish_reason"),
                "usage": {
                    "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": data.get("usage", {}).get("total_tokens", 0)
                },
                "model": self.model,
                "provider": "openrouter"
            }
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        # Approximate for Llama-based models
        return int(len(text) / 3.5)
    
    def get_model_name(self) -> str:
        return self.model
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(self.model, {"input": 0.40, "output": 0.40})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

class LLMManager:
    """
    Manages multiple LLM providers with automatic fallback.
    
    Supports three providers:
    1. OpenAI (configurable model)
    2. Gemini 2.5 Flash
    3. OpenRouter (Nemotron 49B via DeepInfra)
    
    Features:
    - Automatic fallback on provider failure
    - Cost tracking across providers
    - Token counting
    - Unified interface
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.primary_provider: Optional[LLMProvider] = None
        self.fallback_order: List[LLMProvider] = []
        
        # Initialize providers
        if config.get("openai"):
            self.providers[LLMProvider.OPENAI] = OpenAIProvider(
                api_key=config["openai"]["api_key"],
                model=config["openai"].get("model", "gpt-4o-mini")
            )
            logger.info(f"Initialized OpenAI provider with model: {config['openai'].get('model', 'gpt-4o-mini')}")
        
        if config.get("gemini"):
            self.providers[LLMProvider.GEMINI] = GeminiProvider(
                api_key=config["gemini"]["api_key"],
                model=config["gemini"].get("model", "gemini-2.5-flash")
            )
            logger.info(f"Initialized Gemini provider")
        
        if config.get("openrouter"):
            self.providers[LLMProvider.OPENROUTER] = OpenRouterProvider(
                api_key=config["openrouter"]["api_key"],
                model=config["openrouter"].get(
                    "model",
                    "nvidia/llama-3.3-nemotron-super-49b-v1.5"
                )
            )
            logger.info(f"Initialized OpenRouter provider with Nemotron 49B")
        
        # Set primary and fallback
        self.primary_provider = LLMProvider(config.get("primary", "openai"))
        self.fallback_order = [
            LLMProvider(p) for p in config.get("fallback_order", ["gemini", "openrouter"])
            if LLMProvider(p) in self.providers
        ]
        
        logger.info(f"Primary provider: {self.primary_provider.value}")
        logger.info(f"Fallback order: {[p.value for p in self.fallback_order]}")
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        retry_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Generate completion with automatic fallback on failure.
        
        Returns:
            Dict containing:
            - content: Generated text
            - tool_calls: Tool calls if requested
            - usage: Token usage statistics
            - model: Model name used
            - provider: Provider name used
        """
        
        # Try primary provider
        if self.primary_provider not in self.providers:
            raise ValueError(f"Primary provider {self.primary_provider} not configured")
        
        provider = self.providers[self.primary_provider]
        try:
            logger.info(f"Attempting completion with primary provider: {self.primary_provider.value}")
            result = await provider.complete(messages, tools, temperature, max_tokens)
            result["provider_used"] = self.primary_provider.value
            logger.info(f"Successfully completed with {self.primary_provider.value}")
            return result
            
        except Exception as e:
            logger.warning(f"Primary provider {self.primary_provider.value} failed: {e}")
            
            if not retry_on_failure:
                raise
            
            # Try fallback providers
            for fallback_provider in self.fallback_order:
                if fallback_provider not in self.providers:
                    continue
                
                try:
                    logger.info(f"Attempting fallback to: {fallback_provider.value}")
                    provider = self.providers[fallback_provider]
                    result = await provider.complete(
                        messages, tools, temperature, max_tokens
                    )
                    result["provider_used"] = fallback_provider.value
                    logger.info(f"Successfully fell back to {fallback_provider.value}")
                    return result
                    
                except Exception as fallback_error:
                    logger.warning(
                        f"Fallback provider {fallback_provider.value} failed: {fallback_error}"
                    )
                    continue
            
            # All providers failed
            raise Exception("All LLM providers failed. Check API keys and connectivity.")
    
    def get_provider(self, provider_type: LLMProvider) -> Optional[BaseLLMProvider]:
        """Get specific provider instance"""
        return self.providers.get(provider_type)
    
    def count_tokens(self, text: str, provider_type: Optional[LLMProvider] = None) -> int:
        """Count tokens using specified provider or primary"""
        provider_type = provider_type or self.primary_provider
        if provider_type not in self.providers:
            # Fallback to approximate counting
            return len(text) // 4
        return self.providers[provider_type].count_tokens(text)
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        provider_type: Optional[LLMProvider] = None
    ) -> float:
        """Estimate cost for given token usage"""
        provider_type = provider_type or self.primary_provider
        if provider_type not in self.providers:
            return 0.0
        return self.providers[provider_type].estimate_cost(input_tokens, output_tokens)
```

### 2.3 Configuration

```yaml
# config.yaml
llm:
  primary: "openai"  # Primary provider: openai, gemini, or openrouter
  fallback_order: ["gemini", "openrouter"]  # Fallback sequence
  
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o-mini"  # Options: gpt-4o-mini, gpt-4o, gpt-4-turbo
    temperature: 0.7
    max_tokens: 2000
  
  gemini:
    api_key: "${GOOGLE_API_KEY}"
    model: "gemini-2.5-flash"  # Options: gemini-2.5-flash, gemini-1.5-pro
    temperature: 0.7
    max_tokens: 2000
  
  openrouter:
    api_key: "${OPENROUTER_API_KEY}"
    model: "nvidia/llama-3.3-nemotron-super-49b-v1.5"
    temperature: 0.7
    max_tokens: 2000

research:
  max_iterations: 10
  timeout_minutes: 15
  parallel_tool_execution: false

tools:
  web_search:
    provider: "duckduckgo"  # or "serpapi"
    max_results: 10
  arxiv:
    max_results: 20
  github:
    max_results: 10
  pdf:
    max_pages: 50

evaluation:
  run_per_step: true
  run_end_to_end: true
  llm_as_judge: true

tracing:
  enabled: true
  provider: "langsmith"  # or "custom"
  langsmith_api_key: "${LANGSMITH_API_KEY}"
  log_tool_outputs: true
  log_llm_calls: true
```

### 2.4 Cost Comparison

| Provider | Model | Input $/1M | Output $/1M | Est. $/Query |
|----------|-------|------------|-------------|--------------|
| **OpenAI** | gpt-4o-mini | $0.15 | $0.60 | **$0.0019** ✨ |
| **Gemini** | 2.5 Flash | $0.075 | $0.30 | **$0.0009** ✨ |
| **OpenRouter** | Nemotron 49B | $0.40 | $0.40 | **$0.0032** |

*Estimates based on avg 5 iterations, 8K tokens in, 6K tokens out*

**Average cost per research query: $0.002 - $0.003** ✅

---

## 3. Agent System Architecture

### 3.1 ReAct Pattern Implementation

**ReAct (Reasoning + Acting)** is the core agentic pattern:

```
Thought → Action → Observation → Thought → ... → Answer
```

**Why ReAct:**
- ✅ Transparent reasoning at each step
- ✅ Adaptive tool selection
- ✅ Easy to trace and debug
- ✅ Educational value (users see how agent thinks)
- ✅ Proven production pattern

### 3.2 Two-Agent System

#### **Agent 1: Researcher Agent (ReAct Pattern)**

**Role:** Autonomous research through iterative reasoning and tool use

**Capabilities:**
- Reasons about what information is needed
- Selects appropriate tools for each need
- Executes tool calls via function calling
- Processes and synthesizes results
- Decides when research is complete
- Generates comprehensive final report

**ReAct Loop Example:**
```
Iteration 1:
  THOUGHT: "I need recent academic papers on X"
  ACTION: arxiv_search(query="X", date_from="2024-01-01")
  OBSERVATION: "Found 15 papers. Top papers discuss Y and Z..."

Iteration 2:
  THOUGHT: "Now I need practical implementations"
  ACTION: github_search(query="X implementation", sort="stars")
  OBSERVATION: "Found 10 repositories. Most popular is..."

Iteration N:
  THOUGHT: "I have sufficient information to synthesize"
  ACTION: finish(report="[Comprehensive report]")
```

**System Prompt:**
```
You are a research assistant using the ReAct (Reasoning + Acting) pattern.

For each iteration:
1. THOUGHT: Think about what information you need next
2. ACTION: Select and use an appropriate tool
3. OBSERVATION: Analyze the tool's output
4. Repeat until you have sufficient information

Available tools:
- web_search: Search the web for current information
- arxiv_search: Find academic papers on ArXiv
- github_search: Find code implementations on GitHub
- pdf_to_text: Extract text from PDF papers
- finish: Complete research with final report

Guidelines:
- Be thorough but efficient (max 10 iterations)
- Cite all sources in your report
- Extract key information from PDFs when needed
- Synthesize information clearly
- Use the "finish" action when you have enough information

Current query: {user_query}
```

#### **Agent 2: Evaluator Agent (Multi-Level Assessment)**

**Role:** Comprehensive quality control and performance evaluation

**Capabilities:**
- **Per-Step Evaluation**: Assesses each ReAct iteration
- **End-to-End Evaluation**: Reviews complete research output
- **Performance Analysis**: Measures efficiency metrics
- **Quality Scoring**: Rates on multiple dimensions
- **Feedback Generation**: Provides actionable improvements

**Evaluation Dimensions:**
1. **Relevance** (0-10): How well does output answer query?
2. **Accuracy** (0-10): Is information factually correct?
3. **Completeness** (0-10): Are all aspects covered?
4. **Coherence** (0-10): Is it well-structured and clear?
5. **Source Quality** (0-10): Are sources authoritative?
6. **Recency** (0-10): Is information current?

**System Prompt:**
```
You are an expert research evaluator. Assess research quality comprehensively.

Your tasks:
1. Per-Step Evaluation (after each iteration):
   - Was the tool selection appropriate?
   - Did the action address the information need?
   - Were the results well-processed?

2. End-to-End Evaluation (after completion):
   - Rate on 6 dimensions (0-10 scale)
   - Identify strengths and weaknesses
   - Detect potential inaccuracies
   - Suggest improvements

Be thorough, constructive, and educational in your feedback.
```

### 3.3 Agent Communication Flow

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│    Researcher Agent (ReAct Loop)     │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ Iteration 1:                   │ │
│  │  • THOUGHT: Reason             │ │◄── Per-Step Evaluation
│  │  • ACTION: Execute tool        │ │    (Optional, Real-time)
│  │  • OBSERVATION: Process        │ │
│  └────────────────────────────────┘ │
│               │                      │
│               ▼                      │
│  ┌────────────────────────────────┐ │
│  │ Iterations 2-N:                │ │◄── Per-Step Evaluation
│  │  • Continue until sufficient   │ │    (Each Iteration)
│  │  • Max 10 iterations           │ │
│  └────────────────────────────────┘ │
│               │                      │
│               ▼                      │
│  ┌────────────────────────────────┐ │
│  │ FINISH: Generate Report        │ │
│  └────────────────────────────────┘ │
└────────────┬─────────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│    Evaluator Agent                 │
│                                    │
│  • Review all per-step evaluations │
│  • Perform end-to-end assessment   │
│  • Calculate performance metrics   │
│  • Generate comprehensive feedback │
└────────────┬───────────────────────┘
             │
             ▼
        ┌────────┐
        │ Quality│
        │ Score? │
        └───┬────┘
            │
    ┌───────┴────────┐
    │ < 6.0          │ >= 6.0
    ▼                ▼
┌─────────┐    ┌──────────┐
│Optionally│    │ Output   │
│Re-research│   │ Final    │
│  (Rare)  │    │ Report   │
└─────────┘    └──────────┘
```

---

## 4. Tool System

### 4.1 Tool Definitions

All tools follow **OpenAI Function Calling format** for compatibility across LLM providers.

#### **Tool 1: Web Search**

```python
WEB_SEARCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information, news, articles, "
            "and general knowledge. Best for recent events, trends, "
            "and practical information. Returns up to 20 results."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query. Be specific and use keywords."
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-20)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                },
                "date_filter": {
                    "type": "string",
                    "enum": ["day", "week", "month", "year", null],
                    "description": "Filter by recency. Use for time-sensitive queries.",
                    "default": null
                }
            },
            "required": ["query"]
        }
    }
}

# Implementation
async def web_search(
    query: str,
    num_results: int = 10,
    date_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search the web and return results with summaries.
    
    Returns:
        {
            "results": [
                {
                    "title": str,
                    "snippet": str,
                    "url": str,
                    "domain": str,
                    "date_published": Optional[str],
                    "is_pdf": bool,
                    "summary": str,  # 200-word summary
                    "relevance_score": float  # 0-1
                }
            ],
            "total_found": int,
            "timestamp": str
        }
    """
```

#### **Tool 2: ArXiv Search**

```python
ARXIV_SEARCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "arxiv_search",
        "description": (
            "Search academic papers on ArXiv. Best for research papers, "
            "ML/AI topics, physics, math, and computer science. "
            "Returns paper metadata and abstracts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query. Use technical terms."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum papers to return (1-50)",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 50
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                    "description": "Sort order for results",
                    "default": "relevance"
                },
                "date_from": {
                    "type": "string",
                    "description": "Filter papers from this date (YYYY-MM-DD)",
                    "default": null
                }
            },
            "required": ["query"]
        }
    }
}

# Implementation
async def arxiv_search(
    query: str,
    max_results: int = 20,
    sort_by: str = "relevance",
    date_from: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search ArXiv and return papers with abstracts.
    
    Returns:
        {
            "papers": [
                {
                    "title": str,
                    "authors": List[str],
                    "abstract": str,
                    "pdf_url": str,
                    "arxiv_id": str,
                    "published_date": str,
                    "categories": List[str],
                    "summary": str  # 200-word summary
                }
            ],
            "total_found": int
        }
    """
```

#### **Tool 3: GitHub Search**

```python
GITHUB_SEARCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "github_search",
        "description": (
            "Search GitHub for repositories, code, or users. "
            "Best for finding implementations, libraries, and "
            "open-source projects."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query. Use project names or keywords."
                },
                "search_type": {
                    "type": "string",
                    "enum": ["repositories", "code", "users"],
                    "description": "What to search for",
                    "default": "repositories"
                },
                "sort": {
                    "type": "string",
                    "enum": ["stars", "forks", "updated"],
                    "description": "Sort order (repositories only)",
                    "default": "stars"
                },
                "language": {
                    "type": "string",
                    "description": "Filter by language (e.g., 'Python', 'JavaScript')",
                    "default": null
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results (1-30)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    }
}

# Implementation
async def github_search(
    query: str,
    search_type: str = "repositories",
    sort: str = "stars",
    language: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search GitHub and return results.
    
    Returns:
        {
            "repositories": [
                {
                    "name": str,
                    "full_name": str,
                    "description": str,
                    "url": str,
                    "stars": int,
                    "forks": int,
                    "language": str,
                    "topics": List[str],
                    "last_updated": str,
                    "readme_summary": str  # First 500 chars
                }
            ],
            "total_found": int
        }
    """
```

#### **Tool 4: PDF to Text**

```python
PDF_TO_TEXT_DEFINITION = {
    "type": "function",
    "function": {
        "name": "pdf_to_text",
        "description": (
            "Extract text from PDF documents. Use when you find a "
            "relevant PDF paper or document that you need to read. "
            "Returns structured text content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "PDF URL (https://...) or file path"
                },
                "max_pages": {
                    "type": "integer",
                    "description": "Maximum pages to extract (default: 50)",
                    "default": 50
                }
            },
            "required": ["source"]
        }
    }
}

# Implementation
async def pdf_to_text(
    source: str,
    max_pages: int = 50
) -> Dict[str, Any]:
    """
    Extract text from PDF.
    
    Returns:
        {
            "title": str,
            "authors": List[str],
            "abstract": Optional[str],
            "sections": [
                {
                    "heading": str,
                    "content": str,
                    "page_number": int
                }
            ],
            "total_pages": int,
            "extracted_pages": int,
            "full_text": str,  # All text concatenated
            "summary": str  # 500-word summary
        }
    """
```

#### **Tool 5: Finish (Special)**

```python
FINISH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "finish",
        "description": (
            "Use this when you have gathered sufficient information "
            "and are ready to provide the final research report. "
            "This ends the research loop."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "report": {
                    "type": "string",
                    "description": (
                        "Comprehensive research report in markdown format "
                        "with proper citations, sections, and analysis"
                    )
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of all source URLs cited in report"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence in answer completeness (0-1)",
                    "default": 0.8
                }
            },
            "required": ["report", "sources"]
        }
    }
}
```

### 4.2 Tool Selection Logic

Embedded in Researcher Agent's system prompt:

```
Tool Selection Guidelines:

1. web_search: Use for:
   - Recent news, trends, current events
   - General knowledge
   - Real-world applications
   - Company or product information
   - When you need up-to-date information

2. arxiv_search: Use for:
   - Research papers and academic citations
   - Technical methodologies
   - Theoretical foundations
   - ML/AI techniques and algorithms
   - When you need academic rigor

3. github_search: Use for:
   - Code implementations
   - Open-source libraries and frameworks
   - Practical examples
   - Tool comparisons
   - When you need working code

4. pdf_to_text: Use when:
   - You found a relevant PDF (from web or arxiv)
   - You need detailed information from a paper
   - Abstract isn't sufficient for analysis
   - Paper contains critical technical details

5. finish: Use when:
   - You have comprehensive information
   - Multiple aspects of query are covered
   - Sources are diverse and high-quality
   - Answer fully addresses user's query
   - You're confident in the completeness
```

---

## 5. Content Management Pipeline

### 5.1 Challenge

When web_search returns 20 results:
- Each URL could be a complex webpage (10K-50K words)
- Some URLs may be PDFs (10-100 pages)
- Total content could exceed 200K+ tokens
- Agent's context window: limited to ~8K tokens per iteration

**Solution:** Multi-stage content processing pipeline

### 5.2 Pipeline Architecture

```
Search Results (20 items)
    ↓
┌─────────────────────────────────────┐
│  Stage 1: Classification            │
│  • Identify PDFs vs web pages       │
│  • Check content type and size      │
│  • Filter spam/irrelevant domains   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Stage 2: Parallel Extraction       │
│  • PDFs: Use PyMuPDF                │
│  • Web: Use Trafilatura             │
│  • Extract main content only        │
│  • Remove ads, nav, boilerplate     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Stage 3: LLM Summarization         │
│  • Generate 200-word summaries      │
│  • Extract 3-5 key points           │
│  • Calculate relevance score (0-1)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Stage 4: Ranking & Selection       │
│  • Rank by relevance score          │
│  • Select top 10 sources            │
│  • Cache full content               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Stage 5: Serve to Agent            │
│  • Provide summaries initially      │
│  • Agent can request full content   │
│  • Progressive detail loading       │
└─────────────────────────────────────┘
```

### 5.3 Implementation

```python
class ContentPipeline:
    """Manages content extraction, summarization, and caching"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager
        self.extractor = ContentExtractor()
        self.cache = ContentCache()  # Redis or in-memory
    
    async def process_search_results(
        self,
        results: List[SearchResult],
        user_query: str
    ) -> ProcessedResults:
        """
        Process search results through complete pipeline.
        
        Returns summaries of top 10 results with full content cached.
        """
        
        # Stage 1: Classify
        classified = self._classify_results(results)
        
        # Stage 2: Extract in parallel
        extraction_tasks = [
            self._extract_content(item)
            for item in classified
        ]
        extracted = await asyncio.gather(*extraction_tasks)
        
        # Stage 3: Summarize with LLM
        summaries = []
        for item, content in zip(classified, extracted):
            if content is None:
                continue
            
            summary = await self._summarize_content(
                content=content.text,
                context=user_query,
                max_words=200
            )
            
            summaries.append({
                "original": item,
                "summary": summary,
                "cache_key": self.cache.store(content)
            })
        
        # Stage 4: Rank and select
        ranked = sorted(
            summaries,
            key=lambda x: x["summary"]["relevance_score"],
            reverse=True
        )[:10]
        
        # Stage 5: Format for agent
        return {
            "summaries": [
                {
                    "title": s["original"].title,
                    "url": s["original"].url,
                    "summary": s["summary"]["text"],
                    "key_points": s["summary"]["key_points"],
                    "relevance": s["summary"]["relevance_score"],
                    "full_content_available": True,
                    "cache_key": s["cache_key"]
                }
                for s in ranked
            ],
            "note": (
                "Summaries provided. Use pdf_to_text(url) "
                "to get full content if needed."
            )
        }
    
    async def _extract_content(self, item: SearchResult) -> Optional[ExtractedContent]:
        """Extract clean content from URL or PDF"""
        try:
            if item.is_pdf:
                return await self._extract_pdf(item.url)
            else:
                return await self._extract_webpage(item.url)
        except Exception as e:
            logger.error(f"Failed to extract {item.url}: {e}")
            return None
    
    async def _extract_webpage(self, url: str) -> ExtractedContent:
        """Extract main content from webpage using Trafilatura"""
        downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )
        
        return ExtractedContent(
            url=url,
            text=text,
            word_count=len(text.split()),
            content_type="webpage"
        )
    
    async def _extract_pdf(self, url: str) -> ExtractedContent:
        """Extract text from PDF (first 50 pages)"""
        response = await asyncio.to_thread(requests.get, url, timeout=30)
        pdf_doc = fitz.open(stream=response.content)
        
        text_parts = []
        for page_num in range(min(50, pdf_doc.page_count)):
            page = pdf_doc[page_num]
            text_parts.append(page.get_text())
        
        full_text = "\n\n".join(text_parts)
        
        return ExtractedContent(
            url=url,
            text=full_text,
            word_count=len(full_text.split()),
            content_type="pdf",
            total_pages=pdf_doc.page_count
        )
    
    async def _summarize_content(
        self,
        content: str,
        context: str,
        max_words: int = 200
    ) -> Dict[str, Any]:
        """Generate focused summary using LLM"""
        
        # If content is already short, use as-is
        if len(content.split()) < 500:
            return {
                "text": content,
                "key_points": [],
                "relevance_score": 1.0
            }
        
        # Generate summary with LLM
        prompt = f"""Summarize the following content in ~{max_words} words, 
        focusing on information relevant to: "{context}"
        
        Extract:
        1. A concise summary
        2. 3-5 key points
        3. Relevance score (0-1) to the query
        
        Content:
        {content[:10000]}  # Truncate very long content
        
        Format your response as JSON:
        {{
            "summary": "...",
            "key_points": ["...", "..."],
            "relevance": 0.X
        }}
        """
        
        result = await self.llm.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse JSON response
        try:
            parsed = json.loads(result["content"])
            return {
                "text": parsed["summary"],
                "key_points": parsed["key_points"],
                "relevance_score": parsed["relevance"]
            }
        except:
            # Fallback
            return {
                "text": content[:1000] + "...",
                "key_points": [],
                "relevance_score": 0.5
            }
```

### 5.4 Token Management

```python
# Limits to prevent context overflow
MAX_TOKENS_PER_ITERATION = 8000
MAX_SEARCH_RESULTS_TO_AGENT = 10
MAX_SUMMARY_LENGTH_WORDS = 200
MAX_FULL_CONTENT_WORDS = 5000  # When agent requests full text

# Token budget breakdown per iteration:
# - System prompt: 800 tokens
# - Conversation history: 2000 tokens
# - Tool results (10 summaries @ 300 tokens): 3000 tokens
# - Agent reasoning/response: 1000 tokens
# - Buffer: 1200 tokens
# TOTAL: ~8000 tokens ✅
```

---

## 6. Comprehensive Trace System

### 6.1 What Gets Traced

**Complete observability across all dimensions:**

```
Research Session (Top Level)
├── Session Metadata
│   ├── ID
│   ├── User Query
│   ├── Start/End Time
│   ├── Configuration
│   └── Final Status
│
├── ReAct Loop Trace
│   ├── Iteration 1
│   │   ├── THOUGHT
│   │   │   ├── Agent reasoning text
│   │   │   ├── LLM call details
│   │   │   ├── Tokens used
│   │   │   ├── Latency
│   │   │   └── Cost
│   │   ├── ACTION
│   │   │   ├── Tool selected
│   │   │   ├── Parameters
│   │   │   ├── Selection rationale
│   │   │   └── Timestamp
│   │   ├── TOOL EXECUTION
│   │   │   ├── Tool name
│   │   │   ├── Input parameters
│   │   │   ├── Execution time
│   │   │   ├── Success/failure
│   │   │   ├── Error details (if failed)
│   │   │   ├── Results summary
│   │   │   └── Full output (cached)
│   │   ├── OBSERVATION
│   │   │   ├── Agent analysis
│   │   │   ├── LLM call details
│   │   │   ├── Tokens used
│   │   │   ├── Latency
│   │   │   └── Decision for next step
│   │   └── Per-Step Evaluation
│   │       ├── Tool appropriateness (0-10)
│   │       ├── Execution quality (0-10)
│   │       ├── Progress made (0-10)
│   │       └── Suggestions
│   │
│   ├── Iteration 2-N
│   │   └── [Same structure]
│   │
│   └── FINISH
│       ├── Final synthesis
│       ├── Report generated
│       └── Sources compiled
│
├── End-to-End Evaluation
│   ├── Quality Scores (6 dimensions)
│   ├── Performance Metrics
│   ├── Cost Analysis
│   ├── Strengths
│   ├── Weaknesses
│   └── Overall Assessment
│
└── Aggregated Metrics
    ├── Total duration
    ├── Total iterations
    ├── Total tokens (in/out)
    ├── Total cost
    ├── LLM provider usage
    ├── Tool usage distribution
    └── Success rates
```

### 6.2 Trace Implementation

**Using LangSmith (Recommended):**

```python
from langsmith import Client, traceable
from langsmith.run_trees import RunTree
import os

# Initialize LangSmith
langsmith_client = Client(
    api_key=os.getenv("LANGSMITH_API_KEY"),
    api_url="https://api.smith.langchain.com"
)

@traceable(
    name="research_session",
    client=langsmith_client,
    tags=["research", "react"]
)
async def run_research_session(
    user_query: str,
    config: Dict[str, Any]
) -> ResearchOutput:
    """
    Top-level traced research session.
    All child operations are automatically traced.
    """
    
    with RunTree(
        name="research_session",
        run_type="chain",
        inputs={"query": user_query, "config": config},
        tags=["research", "react"],
        client=langsmith_client
    ) as session_trace:
        
        # Initialize
        session_id = str(uuid.uuid4())
        session_trace.extra = {"session_id": session_id}
        
        # ReAct Loop
        with session_trace.create_child(
            name="react_loop",
            run_type="chain"
        ) as react_trace:
            
            iteration = 1
            done = False
            
            while not done and iteration <= config["max_iterations"]:
                
                # Trace each iteration
                with react_trace.create_child(
                    name=f"iteration_{iteration}",
                    run_type="chain",
                    inputs={"iteration": iteration}
                ) as iter_trace:
                    
                    # THOUGHT
                    with iter_trace.create_child(
                        name="thought",
                        run_type="llm"
                    ) as thought_trace:
                        thought_result = await agent.reason(context)
                        thought_trace.end(
                            outputs={
                                "thought": thought_result.thought,
                                "tokens_used": thought_result.tokens,
                                "latency_ms": thought_result.latency * 1000,
                                "cost_usd": thought_result.cost
                            }
                        )
                    
                    # ACTION
                    with iter_trace.create_child(
                        name="action_selection",
                        run_type="llm"
                    ) as action_trace:
                        action_result = await agent.select_action(thought_result)
                        action_trace.end(
                            outputs={
                                "tool": action_result.tool_name,
                                "parameters": action_result.parameters,
                                "rationale": action_result.rationale
                            }
                        )
                    
                    # TOOL EXECUTION
                    with iter_trace.create_child(
                        name=f"execute_{action_result.tool_name}",
                        run_type="tool",
                        inputs=action_result.parameters
                    ) as tool_trace:
                        start_time = time.time()
                        try:
                            tool_result = await execute_tool(
                                action_result.tool_name,
                                **action_result.parameters
                            )
                            execution_time = time.time() - start_time
                            
                            tool_trace.end(
                                outputs={
                                    "success": True,
                                    "result_summary": tool_result.summary,
                                    "execution_time_ms": execution_time * 1000,
                                    "results_count": len(tool_result.items)
                                }
                            )
                        except Exception as e:
                            execution_time = time.time() - start_time
                            tool_trace.end(
                                outputs={
                                    "success": False,
                                    "error": str(e),
                                    "execution_time_ms": execution_time * 1000
                                },
                                error=str(e)
                            )
                            raise
                    
                    # OBSERVATION
                    with iter_trace.create_child(
                        name="observation",
                        run_type="llm"
                    ) as obs_trace:
                        obs_result = await agent.observe(tool_result)
                        obs_trace.end(
                            outputs={
                                "observation": obs_result.observation,
                                "should_continue": obs_result.should_continue,
                                "tokens_used": obs_result.tokens,
                                "cost_usd": obs_result.cost
                            }
                        )
                    
                    # PER-STEP EVALUATION
                    with iter_trace.create_child(
                        name="per_step_evaluation",
                        run_type="llm"
                    ) as eval_trace:
                        step_eval = await evaluator.evaluate_step(
                            iteration=iteration,
                            thought=thought_result,
                            action=action_result,
                            tool_result=tool_result,
                            observation=obs_result
                        )
                        eval_trace.end(
                            outputs={
                                "tool_appropriateness": step_eval.tool_score,
                                "execution_quality": step_eval.execution_score,
                                "progress_made": step_eval.progress_score,
                                "suggestions": step_eval.suggestions
                            }
                        )
                    
                    # Update state
                    done = obs_result.is_complete
                    iteration += 1
                    
                    iter_trace.end(
                        outputs={
                            "done": done,
                            "iteration_completed": True
                        }
                    )
            
            react_trace.end(
                outputs={
                    "total_iterations": iteration - 1,
                    "final_report": obs_result.final_report,
                    "sources": obs_result.sources
                }
            )
        
        # END-TO-END EVALUATION
        with session_trace.create_child(
            name="end_to_end_evaluation",
            run_type="chain"
        ) as eval_trace:
            final_evaluation = await evaluator.evaluate_end_to_end(
                query=user_query,
                report=obs_result.final_report,
                sources=obs_result.sources,
                per_step_evals=per_step_evaluations,
                iterations=iteration - 1
            )
            eval_trace.end(
                outputs={
                    "scores": final_evaluation.scores,
                    "overall_quality": final_evaluation.overall_score,
                    "strengths": final_evaluation.strengths,
                    "weaknesses": final_evaluation.weaknesses
                }
            )
        
        # Aggregate metrics
        total_cost = sum(
            step.thought_cost + step.observation_cost
            for step in all_steps
        )
        
        session_trace.end(
            outputs={
                "final_report": obs_result.final_report,
                "evaluation": final_evaluation,
                "metrics": {
                    "total_duration_seconds": time.time() - session_start,
                    "total_iterations": iteration - 1,
                    "total_cost_usd": total_cost,
                    "total_tokens": total_tokens
                }
            }
        )
        
        return ResearchOutput(
            report=obs_result.final_report,
            evaluation=final_evaluation,
            trace_id=session_trace.id,
            trace_url=f"https://smith.langchain.com/o/{org_id}/projects/p/{project_id}/r/{session_trace.id}"
        )
```

### 6.3 Custom Trace Logger (Fallback)

For users without LangSmith, custom logger with database storage:

```python
class TraceLogger:
    """
    Custom trace logger with WebSocket broadcasting.
    Stores traces in SQLite and broadcasts to frontend.
    """
    
    def __init__(self, session_id: str, websocket_manager: WebSocketManager):
        self.session_id = session_id
        self.ws = websocket_manager
        self.events: List[TraceEvent] = []
        self.current_iteration: Optional[int] = None
    
    async def log_thought(
        self,
        iteration: int,
        thought: str,
        llm_details: Dict[str, Any]
    ):
        """Log agent reasoning"""
        event = TraceEvent(
            session_id=self.session_id,
            type="thought",
            iteration=iteration,
            data={
                "thought": thought,
                "model": llm_details["model"],
                "tokens_in": llm_details["tokens_in"],
                "tokens_out": llm_details["tokens_out"],
                "latency_ms": llm_details["latency_ms"],
                "cost_usd": llm_details["cost_usd"],
                "provider": llm_details["provider"]
            },
            timestamp=datetime.utcnow()
        )
        
        self.events.append(event)
        await self._save_to_db(event)
        await self._broadcast(event)
    
    async def log_action(
        self,
        iteration: int,
        tool_name: str,
        parameters: Dict[str, Any],
        rationale: str
    ):
        """Log tool selection"""
        event = TraceEvent(
            session_id=self.session_id,
            type="action",
            iteration=iteration,
            data={
                "tool": tool_name,
                "parameters": parameters,
                "rationale": rationale
            },
            timestamp=datetime.utcnow()
        )
        
        self.events.append(event)
        await self._save_to_db(event)
        await self._broadcast(event)
    
    async def log_tool_execution(
        self,
        iteration: int,
        tool_name: str,
        success: bool,
        duration_ms: float,
        result_summary: str,
        error: Optional[str] = None
    ):
        """Log tool execution results"""
        event = TraceEvent(
            session_id=self.session_id,
            type="tool_execution",
            iteration=iteration,
            data={
                "tool": tool_name,
                "success": success,
                "duration_ms": duration_ms,
                "result_summary": result_summary,
                "error": error
            },
            timestamp=datetime.utcnow()
        )
        
        self.events.append(event)
        await self._save_to_db(event)
        await self._broadcast(event)
    
    async def log_observation(
        self,
        iteration: int,
        observation: str,
        should_continue: bool,
        llm_details: Dict[str, Any]
    ):
        """Log agent observation"""
        event = TraceEvent(
            session_id=self.session_id,
            type="observation",
            iteration=iteration,
            data={
                "observation": observation,
                "should_continue": should_continue,
                "tokens_in": llm_details["tokens_in"],
                "tokens_out": llm_details["tokens_out"],
                "cost_usd": llm_details["cost_usd"]
            },
            timestamp=datetime.utcnow()
        )
        
        self.events.append(event)
        await self._save_to_db(event)
        await self._broadcast(event)
    
    async def log_per_step_evaluation(
        self,
        iteration: int,
        scores: Dict[str, float],
        suggestions: List[str]
    ):
        """Log per-step evaluation"""
        event = TraceEvent(
            session_id=self.session_id,
            type="per_step_evaluation",
            iteration=iteration,
            data={
                "scores": scores,
                "suggestions": suggestions
            },
            timestamp=datetime.utcnow()
        )
        
        self.events.append(event)
        await self._save_to_db(event)
        await self._broadcast(event)
    
    async def log_end_to_end_evaluation(
        self,
        evaluation: EndToEndEvaluation
    ):
        """Log final evaluation"""
        event = TraceEvent(
            session_id=self.session_id,
            type="end_to_end_evaluation",
            iteration=None,
            data={
                "scores": evaluation.scores,
                "overall_score": evaluation.overall_score,
                "strengths": evaluation.strengths,
                "weaknesses": evaluation.weaknesses,
                "performance_metrics": evaluation.performance_metrics
            },
            timestamp=datetime.utcnow()
        )
        
        self.events.append(event)
        await self._save_to_db(event)
        await self._broadcast(event)
    
    async def _save_to_db(self, event: TraceEvent):
        """Persist event to database"""
        async with aiosqlite.connect("research.db") as db:
            await db.execute(
                """
                INSERT INTO trace_events 
                (session_id, type, iteration, data, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.session_id,
                    event.type,
                    event.iteration,
                    json.dumps(event.data),
                    event.timestamp.isoformat()
                )
            )
            await db.commit()
    
    async def _broadcast(self, event: TraceEvent):
        """Broadcast event to frontend via WebSocket"""
        await self.ws.broadcast(
            session_id=self.session_id,
            message={
                "type": "trace_event",
                "event": {
                    "type": event.type,
                    "iteration": event.iteration,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat()
                }
            }
        )
    
    def get_all_events(self) -> List[TraceEvent]:
        """Get complete trace"""
        return self.events
    
    def get_iteration_events(self, iteration: int) -> List[TraceEvent]:
        """Get events for specific iteration"""
        return [
            e for e in self.events
            if e.iteration == iteration
        ]
```

### 6.4 Trace Database Schema

```sql
-- Research sessions table
CREATE TABLE research_sessions (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    config JSON NOT NULL,
    status TEXT NOT NULL,  -- 'running', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_duration_seconds REAL,
    total_iterations INTEGER,
    total_cost_usd REAL,
    final_report TEXT,
    evaluation JSON
);

-- Trace events table
CREATE TABLE trace_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'thought', 'action', 'tool_execution', etc.
    iteration INTEGER,
    data JSON NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id)
);

-- Per-step evaluations
CREATE TABLE per_step_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    iteration INTEGER NOT NULL,
    tool_appropriateness REAL,
    execution_quality REAL,
    progress_made REAL,
    suggestions TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id)
);

-- End-to-end evaluations
CREATE TABLE end_to_end_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    relevance_score REAL,
    accuracy_score REAL,
    completeness_score REAL,
    coherence_score REAL,
    source_quality_score REAL,
    recency_score REAL,
    overall_score REAL,
    strengths TEXT,  -- JSON array
    weaknesses TEXT,  -- JSON array
    performance_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id)
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id)
);

-- Content cache (for repeated queries)
CREATE TABLE content_cache (
    url TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    summary TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_trace_events_session ON trace_events(session_id);
CREATE INDEX idx_trace_events_iteration ON trace_events(session_id, iteration);
CREATE INDEX idx_content_cache_expires ON content_cache(expires_at);
```

### 6.5 Trace Export

```python
async def export_trace(
    session_id: str,
    format: str = "json"
) -> Union[str, bytes]:
    """
    Export complete trace in various formats.
    
    Args:
        session_id: Research session ID
        format: 'json', 'html', 'markdown'
    
    Returns:
        Formatted trace data
    """
    
    # Fetch complete trace from database
    async with aiosqlite.connect("research.db") as db:
        # Get session
        cursor = await db.execute(
            "SELECT * FROM research_sessions WHERE id = ?",
            (session_id,)
        )
        session = await cursor.fetchone()
        
        # Get all events
        cursor = await db.execute(
            "SELECT * FROM trace_events WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        events = await cursor.fetchall()
        
        # Get evaluations
        cursor = await db.execute(
            "SELECT * FROM per_step_evaluations WHERE session_id = ? ORDER BY iteration",
            (session_id,)
        )
        per_step_evals = await cursor.fetchall()
        
        cursor = await db.execute(
            "SELECT * FROM end_to_end_evaluations WHERE session_id = ?",
            (session_id,)
        )
        end_to_end_eval = await cursor.fetchone()
    
    if format == "json":
        return json.dumps({
            "session": dict(session),
            "events": [dict(e) for e in events],
            "per_step_evaluations": [dict(e) for e in per_step_evals],
            "end_to_end_evaluation": dict(end_to_end_eval) if end_to_end_eval else None
        }, indent=2)
    
    elif format == "html":
        # Generate interactive HTML with charts
        template = jinja2.Template(TRACE_HTML_TEMPLATE)
        return template.render(
            session=session,
            events=events,
            per_step_evals=per_step_evals,
            end_to_end_eval=end_to_end_eval
        )
    
    elif format == "markdown":
        # Generate markdown report
        md = f"# Research Session Trace\n\n"
        md += f"**Query:** {session['query']}\n\n"
        md += f"**Duration:** {session['total_duration_seconds']:.1f}s\n\n"
        
        # Add events grouped by iteration
        current_iter = None
        for event in events:
            if event['iteration'] != current_iter:
                current_iter = event['iteration']
                md += f"\n## Iteration {current_iter}\n\n"
            
            md += f"### {event['type'].upper()}\n\n"
            md += f"```json\n{json.dumps(json.loads(event['data']), indent=2)}\n```\n\n"
        
        return md
```

---

[CONTINUED IN NEXT PART DUE TO LENGTH...]

Would you like me to continue with the rest of the document? I need to add:
- Section 7: Comprehensive Evaluation System
- Section 8: Modern UI Design with Animations
- Section 9: Research Workflow
- Section 10: Export Options
- Section 11: Implementation Roadmap
- Section 12: Quick Start Guide
- Section 13: Conclusion

The document is getting quite large. Should I continue, or would you like me to split it into multiple files?
## 7. Comprehensive Evaluation System

### 7.1 Three-Tier Evaluation Framework

#### **Tier 1: Per-Step Evaluation** (Real-time During Research)

Evaluates each ReAct iteration as it happens:

```python
@dataclass
class PerStepEvaluation:
    """Evaluation of a single ReAct iteration"""
    iteration: int
    tool_appropriateness: float  # 0-10: Was the right tool selected?
    execution_quality: float     # 0-10: Did the tool execute well?
    progress_made: float          # 0-10: How much progress towards answer?
    information_gain: float       # 0-10: How much new info acquired?
    efficiency: float             # 0-10: Was this iteration efficient?
    
    # Detailed feedback
    what_went_well: List[str]
    what_could_improve: List[str]
    suggestions_for_next: List[str]
    
    # Metrics
    tokens_used: int
    latency_seconds: float
    cost_usd: float

async def evaluate_step(
    iteration: int,
    thought: str,
    action: ToolCall,
    tool_result: ToolResult,
    observation: str,
    query_context: str
) -> PerStepEvaluation:
    """Evaluate a single ReAct iteration"""
    
    eval_prompt = f"""Evaluate this research iteration step-by-step.

Original Query: {query_context}

Iteration {iteration}:
THOUGHT: {thought}
ACTION: {action.tool_name}({action.parameters})
RESULT: {tool_result.summary}
OBSERVATION: {observation}

Rate on 0-10 scale:
1. Tool Appropriateness: Was this the right tool for the information need?
2. Execution Quality: Did the tool return useful results?
3. Progress Made: How much closer are we to answering the query?
4. Information Gain: How valuable was the new information?
5. Efficiency: Could this have been done more efficiently?

Also provide:
- What went well (2-3 points)
- What could improve (2-3 points)
- Suggestions for next iteration

Format as JSON:
{{
    "tool_appropriateness": X.X,
    "execution_quality": X.X,
    "progress_made": X.X,
    "information_gain": X.X,
    "efficiency": X.X,
    "what_went_well": ["...", "..."],
    "what_could_improve": ["...", "..."],
    "suggestions_for_next": ["...", "..."]
}}
"""
    
    result = await llm_manager.complete(
        messages=[{"role": "user", "content": eval_prompt}],
        temperature=0.3
    )
    
    eval_data = json.loads(result["content"])
    
    return PerStepEvaluation(
        iteration=iteration,
        **eval_data,
        tokens_used=result["usage"]["total_tokens"],
        latency_seconds=result.get("latency", 0),
        cost_usd=llm_manager.estimate_cost(
            result["usage"]["input_tokens"],
            result["usage"]["output_tokens"]
        )
    )
```

#### **Tier 2: Metadata-Based Metrics** (Automatic Collection)

Objective performance metrics collected during execution:

```python
@dataclass
class MetadataMetrics:
    """Automatically collected performance metrics"""
    
    # Timing Metrics
    total_duration_seconds: float
    planning_time_seconds: float = 0  # Time in thought phases
    execution_time_seconds: float = 0  # Time in tool execution
    synthesis_time_seconds: float = 0  # Time generating final report
    average_iteration_time: float = 0
    
    # Token Metrics
    total_tokens_in: int
    total_tokens_out: int
    total_tokens: int
    tokens_by_provider: Dict[str, int]  # Provider usage breakdown
    
    # Cost Metrics
    total_cost_usd: float
    cost_by_provider: Dict[str, float]
    cost_by_agent: Dict[str, float]  # Researcher vs Evaluator
    cost_per_iteration: float
    
    # Research Metrics
    iterations_completed: int
    tools_used: Dict[str, int]  # tool_name → count
    successful_tool_calls: int
    failed_tool_calls: int
    tool_success_rate: float
    
    # Source Metrics
    sources_found: int
    unique_sources: int
    sources_by_type: Dict[str, int]  # arxiv, github, web, pdf
    source_recency_avg_years: float  # Average age of sources
    
    # Quality Indicators
    query_keywords: List[str]
    keywords_addressed: List[str]
    coverage_percentage: float  # % of keywords covered
    report_word_count: int
    citation_count: int
    unique_citations: int

def collect_metadata_metrics(session: ResearchSession) -> MetadataMetrics:
    """Collect all metadata metrics from session"""
    
    # Calculate timing
    total_duration = (
        session.completed_at - session.created_at
    ).total_seconds()
    
    planning_time = sum(
        e.data.get("latency_seconds", 0)
        for e in session.trace.events
        if e.type == "thought"
    )
    
    execution_time = sum(
        e.data.get("duration_ms", 0) / 1000
        for e in session.trace.events
        if e.type == "tool_execution"
    )
    
    # Calculate tokens and costs
    total_tokens_in = sum(
        e.data.get("tokens_in", 0)
        for e in session.trace.events
        if "tokens_in" in e.data
    )
    
    total_tokens_out = sum(
        e.data.get("tokens_out", 0)
        for e in session.trace.events
        if "tokens_out" in e.data
    )
    
    total_cost = sum(
        e.data.get("cost_usd", 0)
        for e in session.trace.events
    )
    
    # Tool usage stats
    tool_calls = [
        e for e in session.trace.events
        if e.type == "tool_execution"
    ]
    
    tools_used = {}
    successful = 0
    failed = 0
    
    for call in tool_calls:
        tool_name = call.data["tool"]
        tools_used[tool_name] = tools_used.get(tool_name, 0) + 1
        
        if call.data["success"]:
            successful += 1
        else:
            failed += 1
    
    # Source analysis
    sources = session.sources
    sources_by_type = {
        "arxiv": sum(1 for s in sources if "arxiv" in s.url),
        "github": sum(1 for s in sources if "github" in s.url),
        "pdf": sum(1 for s in sources if s.url.endswith(".pdf")),
        "web": sum(1 for s in sources if all(x not in s.url for x in ["arxiv", "github", ".pdf"]))
    }
    
    # Source recency
    current_year = 2025
    source_years = [s.year for s in sources if s.year]
    avg_age = (
        (current_year - sum(source_years) / len(source_years))
        if source_years else 0
    )
    
    return MetadataMetrics(
        total_duration_seconds=total_duration,
        planning_time_seconds=planning_time,
        execution_time_seconds=execution_time,
        average_iteration_time=total_duration / session.iterations,
        total_tokens_in=total_tokens_in,
        total_tokens_out=total_tokens_out,
        total_tokens=total_tokens_in + total_tokens_out,
        total_cost_usd=total_cost,
        cost_per_iteration=total_cost / session.iterations,
        iterations_completed=session.iterations,
        tools_used=tools_used,
        successful_tool_calls=successful,
        failed_tool_calls=failed,
        tool_success_rate=successful / len(tool_calls) if tool_calls else 0,
        sources_found=len(sources),
        unique_sources=len(set(s.url for s in sources)),
        sources_by_type=sources_by_type,
        source_recency_avg_years=avg_age,
        report_word_count=len(session.final_report.split()),
        citation_count=len(session.citations),
        unique_citations=len(set(session.citations))
    )
```

#### **Tier 3: End-to-End LLM-as-Judge Evaluation**

Comprehensive quality assessment of final research output:

```python
@dataclass
class EndToEndEvaluation:
    """Complete evaluation of research output"""
    
    # Core Quality Scores (0-10)
    relevance: float          # Directly answers query?
    accuracy: float           # Factually correct?
    completeness: float       # All aspects covered?
    coherence: float          # Well-structured and clear?
    source_quality: float     # Sources authoritative and diverse?
    recency: float            # Information current?
    
    # Composite Score
    overall_score: float      # Weighted average
    quality_tier: str         # excellent/good/acceptable/poor
    
    # Detailed Feedback
    strengths: List[str]      # 3-5 key strengths
    weaknesses: List[str]     # 3-5 areas for improvement
    missing_aspects: List[str] # Information gaps
    improvement_suggestions: List[str]
    
    # Quality Flags
    hallucinations_detected: bool
    contradictions: List[str]
    unsupported_claims: List[str]
    
    # Performance Context
    per_step_evaluations: List[PerStepEvaluation]
    metadata_metrics: MetadataMetrics
    
    # Recommendation
    needs_revision: bool
    revision_priority: str    # high/medium/low/none
    evaluator_notes: str

async def evaluate_end_to_end(
    query: str,
    report: str,
    sources: List[Source],
    per_step_evals: List[PerStepEvaluation],
    metadata: MetadataMetrics
) -> EndToEndEvaluation:
    """Comprehensive end-to-end evaluation"""
    
    eval_prompt = f"""You are an expert research evaluator. Conduct a comprehensive evaluation.

**Original Query:**
{query}

**Research Report:**
{report}

**Sources Used ({len(sources)}):**
{format_sources(sources)}

**Per-Step Performance:**
- Average tool appropriateness: {avg([e.tool_appropriateness for e in per_step_evals]):.1f}/10
- Average progress per step: {avg([e.progress_made for e in per_step_evals]):.1f}/10
- Total iterations: {len(per_step_evals)}

**Metadata:**
- Duration: {metadata.total_duration_seconds:.1f}s
- Sources: {metadata.sources_found} ({metadata.unique_sources} unique)
- Cost: ${metadata.total_cost_usd:.4f}

**Evaluation Task:**

Rate on 0-10 scale (be honest and constructive):

1. **Relevance**: Does the report directly and comprehensively answer the query?
   - 10: Perfect match, addresses all aspects
   - 7-9: Addresses main aspects well
   - 4-6: Partially relevant
   - 0-3: Off-topic or misses key points

2. **Accuracy**: Is the information factually correct and properly sourced?
   - 10: All facts verified, perfectly accurate
   - 7-9: Mostly accurate, minor issues
   - 4-6: Several inaccuracies or unverified claims
   - 0-3: Major factual errors or hallucinations

3. **Completeness**: Are all important aspects of the query covered?
   - 10: Comprehensive, nothing missing
   - 7-9: Covers most aspects
   - 4-6: Missing some important points
   - 0-3: Superficial or very incomplete

4. **Coherence**: Is the report well-organized, clear, and easy to follow?
   - 10: Excellent structure and clarity
   - 7-9: Well-organized
   - 4-6: Somewhat disorganized
   - 0-3: Confusing or poorly structured

5. **Source Quality**: Are sources authoritative, diverse, and well-cited?
   - 10: Excellent sources, diverse types, proper citations
   - 7-9: Good quality sources
   - 4-6: Acceptable but limited
   - 0-3: Poor or unreliable sources

6. **Recency**: Is the information current and up-to-date?
   - 10: Very recent (2024-2025)
   - 7-9: Recent (2022-2023)
   - 4-6: Somewhat dated (2020-2021)
   - 0-3: Outdated (<2020)

**Also identify:**
- **Strengths**: 3-5 specific things done well
- **Weaknesses**: 3-5 specific areas for improvement
- **Missing Aspects**: Important information not covered
- **Hallucinations**: Any unsupported claims or potential inaccuracies
- **Contradictions**: Any conflicting information in the report
- **Improvement Suggestions**: Specific actionable recommendations

**Output Format (JSON):**
{{
    "relevance": X.X,
    "accuracy": X.X,
    "completeness": X.X,
    "coherence": X.X,
    "source_quality": X.X,
    "recency": X.X,
    "strengths": ["...", "...", "..."],
    "weaknesses": ["...", "...", "..."],
    "missing_aspects": ["...", "..."],
    "hallucinations_detected": false,
    "contradictions": [],
    "unsupported_claims": [],
    "improvement_suggestions": ["...", "..."],
    "evaluator_notes": "Overall assessment and context..."
}}

Be thorough, honest, and educational. The goal is to help users learn what makes excellent research.
"""
    
    result = await llm_manager.complete(
        messages=[{"role": "user", "content": eval_prompt}],
        temperature=0.3,
        max_tokens=2000
    )
    
    eval_data = json.loads(result["content"])
    
    # Calculate overall score (weighted average)
    overall_score = (
        eval_data["relevance"] * 0.25 +
        eval_data["accuracy"] * 0.20 +
        eval_data["completeness"] * 0.20 +
        eval_data["coherence"] * 0.15 +
        eval_data["source_quality"] * 0.10 +
        eval_data["recency"] * 0.10
    )
    
    # Determine quality tier
    if overall_score >= 8.5:
        quality_tier = "excellent"
    elif overall_score >= 7.0:
        quality_tier = "good"
    elif overall_score >= 5.5:
        quality_tier = "acceptable"
    else:
        quality_tier = "poor"
    
    # Determine if revision needed
    needs_revision = (
        overall_score < 6.0 or
        eval_data["relevance"] < 5.0 or
        eval_data["accuracy"] < 5.0 or
        eval_data["hallucinations_detected"]
    )
    
    if needs_revision:
        if overall_score < 4.0:
            revision_priority = "high"
        elif overall_score < 5.5:
            revision_priority = "medium"
        else:
            revision_priority = "low"
    else:
        revision_priority = "none"
    
    return EndToEndEvaluation(
        relevance=eval_data["relevance"],
        accuracy=eval_data["accuracy"],
        completeness=eval_data["completeness"],
        coherence=eval_data["coherence"],
        source_quality=eval_data["source_quality"],
        recency=eval_data["recency"],
        overall_score=overall_score,
        quality_tier=quality_tier,
        strengths=eval_data["strengths"],
        weaknesses=eval_data["weaknesses"],
        missing_aspects=eval_data["missing_aspects"],
        improvement_suggestions=eval_data["improvement_suggestions"],
        hallucinations_detected=eval_data["hallucinations_detected"],
        contradictions=eval_data.get("contradictions", []),
        unsupported_claims=eval_data.get("unsupported_claims", []),
        per_step_evaluations=per_step_evals,
        metadata_metrics=metadata,
        needs_revision=needs_revision,
        revision_priority=revision_priority,
        evaluator_notes=eval_data["evaluator_notes"]
    )
```

### 7.2 Evaluation Visualization

The UI displays all three tiers of evaluation in an integrated dashboard.

---

## 8. Modern UI Design & Animations

### 8.1 Design Principles

**Modern, Minimalist, Animated**
- Dark theme with vibrant accents
- Smooth micro-animations for all state changes
- Real-time updates feel instant and fluid
- Visual hierarchy guides attention
- Accessibility-first design

### 8.2 Complete UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  [🔬] Agentic Research Lab       [⚙️ Settings] [📊 History] [👤]   │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  🔍 Research Query                                            │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │ What are the latest advances in multimodal LLMs?      │  │ │
│  │  │                                                         │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  │  [🎯 Example Queries ▼]  [⚙️ Advanced]  [▶️ Start Research]  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─────────────┐ ┌──────────────────────┐ ┌───────────────────┐ │
│  │ REACT TRACE │ │  CURRENT ACTIVITY    │ │  RESEARCH OUTPUT  │ │
│  │ (Left 30%)  │ │  (Center 40%)        │ │  (Right 30%)      │ │
│  ├─────────────┤ ├──────────────────────┤ ├───────────────────┤ │
│  │             │ │                      │ │                   │ │
│  │ [Iteration  │ │  🤖 Researcher Agent │ │  Executive        │ │
│  │  Timeline]  │ │  Status: Active      │ │  Summary          │ │
│  │             │ │  ┌────────────────┐  │ │                   │ │
│  │ ▼ Iter 1 ✓ │ │  │  Currently:    │  │ │  Recent advances  │ │
│  │   💭THOUGHT │ │  │  📊 Analyzing  │  │ │  in multimodal... │ │
│  │   🛠️ACTION  │ │  │     ArXiv      │  │ │                   │ │
│  │   📊OBSERVE │ │  │     results    │  │ │  Key Findings:    │ │
│  │   ⚡EVAL     │ │  │                │  │ │  • Vision-lang... │ │
│  │             │ │  │  Progress:     │  │ │  • New efficient..│ │
│  │ ▼ Iter 2 ⏳ │ │  │  ████████░ 80% │  │ │                   │ │
│  │   💭...     │ │  └────────────────┘  │ │  [Detailed        │ │
│  │             │ │                      │ │   Analysis        │ │
│  │ [Filters]   │ │  🔄 Tool Outputs:    │ │   Below...]       │ │
│  │ [Expand]    │ │  ┌────────────────┐  │ │                   │ │
│  │             │ │  │ ArXiv: 15      │  │ │  Sources:         │ │
│  │             │ │  │ [Summary] [+]  │  │ │  [1] Paper...     │ │
│  └─────────────┘ │  └────────────────┘  │ └───────────────────┘ │
│                  │  ┌────────────────┐  │                       │
│                  │  │ GitHub: 10     │  │                       │
│                  │  │ [Summary] [+]  │  │                       │
│                  │  └────────────────┘  │                       │
│                  └──────────────────────┘                       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  📊 EVALUATION DASHBOARD (Appears after completion)          │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  Overall Quality: ████████░░ 8.7/10 ⭐ Excellent             │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │ │
│  │  │Relevance │ │ Accuracy │ │Coherence │ │ Duration │       │ │
│  │  │  9.0/10  │ │  8.5/10  │ │  7.8/10  │ │ 3m 42s   │       │ │
│  │  │ ★★★★★    │ │ ★★★★☆    │ │ ★★★★☆    │ │ ⚡Fast   │       │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │ │
│  │  [View Detailed Evaluation] [Export] [Compare]              │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### 8.3 Component-Level UI Design

#### **Header**
```tsx
// Modern glassmorphism header
<header className="fixed top-0 w-full z-50 backdrop-blur-xl bg-slate-900/80 border-b border-slate-700/50">
  <div className="container mx-auto px-6 py-4 flex items-center justify-between">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
        <Microscope className="w-6 h-6 text-white" />
      </div>
      <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
        Agentic Research Lab
      </h1>
    </div>
    
    <div className="flex items-center gap-4">
      <Button variant="ghost" size="icon">
        <Settings className="w-5 h-5" />
      </Button>
      <Button variant="ghost" size="icon">
        <History className="w-5 h-5" />
      </Button>
      <Avatar>
        <AvatarImage src="/user-avatar.png" />
        <AvatarFallback>U</AvatarFallback>
      </Avatar>
    </div>
  </div>
</header>
```

#### **Query Input with Auto-Suggestions**
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  className="mb-8"
>
  <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur">
    <CardContent className="p-6">
      <div className="relative">
        <Textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What would you like to research? Try: 'Latest advances in quantum computing' or 'Compare RAG vs fine-tuning'"
          className="min-h-[100px] text-lg bg-slate-900/50 border-slate-700 focus:border-indigo-500 transition-colors"
        />
        
        {/* Character count with color gradient */}
        <div className="absolute bottom-3 right-3 text-sm">
          <span className={cn(
            "transition-colors",
            query.length > 500 ? "text-amber-400" :
            query.length > 200 ? "text-slate-400" : "text-slate-500"
          )}>
            {query.length} / 1000
          </span>
        </div>
      </div>
      
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Sparkles className="w-4 h-4 mr-2" />
            Example Queries
          </Button>
          <Button variant="ghost" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Advanced Options
          </Button>
        </div>
        
        <Button
          size="lg"
          onClick={startResearch}
          disabled={!query.trim() || isResearching}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
        >
          {isResearching ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Researching...
            </>
          ) : (
            <>
              <Play className="w-5 h-5 mr-2" />
              Start Research
            </>
          )}
        </Button>
      </div>
    </CardContent>
  </Card>
</motion.div>
```

#### **ReAct Trace Timeline (Left Panel)**
```tsx
<Card className="h-full border-slate-700/50 bg-slate-800/50 backdrop-blur">
  <CardHeader className="border-b border-slate-700/50">
    <CardTitle className="flex items-center gap-2">
      <Activity className="w-5 h-5 text-indigo-400" />
      ReAct Trace
    </CardTitle>
    <div className="flex gap-2 mt-2">
      <Badge variant="outline">
        {iterations.length} Iterations
      </Badge>
      <Badge variant="outline">
        {formatDuration(elapsed)}
      </Badge>
    </div>
  </CardHeader>
  
  <CardContent className="p-4 overflow-y-auto h-[calc(100%-80px)]">
    <div className="space-y-4">
      {iterations.map((iter, idx) => (
        <motion.div
          key={iter.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.1 }}
        >
          <Collapsible
            open={expandedIter === iter.id}
            onOpenChange={() => setExpandedIter(expandedIter === iter.id ? null : iter.id)}
          >
            <CollapsibleTrigger className="w-full">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 hover:bg-slate-900 transition-colors cursor-pointer">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center font-bold",
                    iter.status === "complete" ? "bg-green-500/20 text-green-400" :
                    iter.status === "active" ? "bg-indigo-500/20 text-indigo-400 animate-pulse" :
                    "bg-slate-700 text-slate-400"
                  )}>
                    {idx + 1}
                  </div>
                  <span className="font-medium">
                    Iteration {idx + 1}
                  </span>
                  {iter.status === "complete" && (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  )}
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">
                    {iter.duration}s
                  </span>
                  <ChevronDown className={cn(
                    "w-4 h-4 transition-transform",
                    expandedIter === iter.id && "rotate-180"
                  )} />
                </div>
              </div>
            </CollapsibleTrigger>
            
            <CollapsibleContent className="pt-2 pl-11">
              <div className="space-y-3">
                {/* THOUGHT */}
                <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-4 h-4 text-purple-400" />
                    <span className="font-medium text-purple-300">THOUGHT</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {iter.thought}
                  </p>
                  <div className="flex gap-2 mt-2 text-xs text-slate-500">
                    <span>🪙 {iter.thought_tokens} tokens</span>
                    <span>⏱️ {iter.thought_latency}ms</span>
                  </div>
                </div>
                
                {/* ACTION */}
                <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-4 h-4 text-cyan-400" />
                    <span className="font-medium text-cyan-300">ACTION</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Code className="w-4 h-4 text-cyan-400" />
                    <code className="text-sm font-mono text-cyan-300">
                      {iter.tool_name}({JSON.stringify(iter.tool_params)})
                    </code>
                  </div>
                </div>
                
                {/* TOOL EXECUTION */}
                <div className={cn(
                  "p-3 rounded-lg",
                  iter.tool_success
                    ? "bg-green-500/10 border border-green-500/20"
                    : "bg-red-500/10 border border-red-500/20"
                )}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {iter.tool_success ? (
                        <CheckCircle2 className="w-4 h-4 text-green-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span className={cn(
                        "font-medium",
                        iter.tool_success ? "text-green-300" : "text-red-300"
                      )}>
                        EXECUTION
                      </span>
                    </div>
                    <span className="text-xs text-slate-400">
                      {iter.tool_duration}ms
                    </span>
                  </div>
                  <p className="text-sm text-slate-300">
                    {iter.tool_result_summary}
                  </p>
                </div>
                
                {/* OBSERVATION */}
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Eye className="w-4 h-4 text-emerald-400" />
                    <span className="font-medium text-emerald-300">OBSERVATION</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {iter.observation}
                  </p>
                </div>
                
                {/* PER-STEP EVAL */}
                {iter.evaluation && (
                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="w-4 h-4 text-amber-400" />
                      <span className="font-medium text-amber-300">EVALUATION</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-slate-400">Tool:</span>
                        <span className="ml-2 text-slate-200">{iter.evaluation.tool_score}/10</span>
                      </div>
                      <div>
                        <span className="text-slate-400">Progress:</span>
                        <span className="ml-2 text-slate-200">{iter.evaluation.progress_score}/10</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </motion.div>
      ))}
    </div>
  </CardContent>
</Card>
```

#### **Current Activity Panel (Center)**
```tsx
<Card className="h-full border-slate-700/50 bg-slate-800/50 backdrop-blur">
  <CardHeader className="border-b border-slate-700/50">
    <div className="flex items-center justify-between">
      <CardTitle className="flex items-center gap-2">
        <motion.div
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          <Bot className="w-5 h-5 text-indigo-400" />
        </motion.div>
        Current Activity
      </CardTitle>
      <Badge variant="outline" className="animate-pulse">
        {currentPhase}
      </Badge>
    </div>
  </CardHeader>
  
  <CardContent className="p-6 space-y-6">
    {/* Agent Status */}
    <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700/50">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center animate-pulse">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold">Researcher Agent</h3>
            <p className="text-sm text-slate-400">Iteration {currentIteration}/10</p>
          </div>
        </div>
      </div>
      
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-slate-400">Currently:</span>
            <span className="text-slate-200">{currentActivity}</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
        
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span>⏱️ {elapsed}s elapsed</span>
          <span>🔄 ETA {estimatedTimeRemaining}s</span>
        </div>
      </div>
    </div>
    
    {/* Latest Update */}
    <AnimatePresence mode="wait">
      <motion.div
        key={latestUpdate.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20"
      >
        <div className="flex items-start gap-3">
          <MessageSquare className="w-5 h-5 text-indigo-400 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-slate-200 leading-relaxed">
              {latestUpdate.message}
            </p>
            <span className="text-xs text-slate-500 mt-1 block">
              {formatTimeAgo(latestUpdate.timestamp)}
            </span>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
    
    {/* Tool Outputs */}
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
        <Wrench className="w-4 h-4" />
        Tool Outputs
      </h4>
      
      {toolOutputs.map((output) => (
        <Collapsible key={output.id}>
          <Card className="bg-slate-900/30 border-slate-700/30">
            <CollapsibleTrigger className="w-full">
              <div className="p-3 flex items-center justify-between hover:bg-slate-900/50 transition-colors">
                <div className="flex items-center gap-3">
                  {getToolIcon(output.tool)}
                  <div className="text-left">
                    <div className="font-medium text-sm">{output.tool}</div>
                    <div className="text-xs text-slate-400">
                      {output.results_count} results
                    </div>
                  </div>
                </div>
                <ChevronDown className="w-4 h-4 text-slate-400" />
              </div>
            </CollapsibleTrigger>
            
            <CollapsibleContent>
              <div className="p-3 border-t border-slate-700/30 space-y-2">
                {output.summaries.slice(0, 3).map((summary, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded bg-slate-900/50 text-sm text-slate-300"
                  >
                    <div className="font-medium mb-1">{summary.title}</div>
                    <p className="text-xs text-slate-400 line-clamp-2">
                      {summary.summary}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="text-xs">
                        Relevance: {(summary.relevance * 10).toFixed(1)}/10
                      </Badge>
                    </div>
                  </div>
                ))}
                
                {output.summaries.length > 3 && (
                  <Button variant="ghost" size="sm" className="w-full">
                    View all {output.results_count} results
                  </Button>
                )}
              </div>
            </CollapsibleContent>
          </Card>
        </Collapsible>
      ))}
    </div>
  </CardContent>
</Card>
```

#### **Research Output Panel (Right)**
```tsx
<Card className="h-full border-slate-700/50 bg-slate-800/50 backdrop-blur">
  <CardHeader className="border-b border-slate-700/50">
    <div className="flex items-center justify-between">
      <CardTitle className="flex items-center gap-2">
        <FileText className="w-5 h-5 text-indigo-400" />
        Research Output
      </CardTitle>
      {isGenerating && (
        <Badge variant="outline" className="animate-pulse">
          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
          Generating...
        </Badge>
      )}
    </div>
  </CardHeader>
  
  <CardContent className="p-6 overflow-y-auto h-[calc(100%-80px)]">
    {report ? (
      <div className="prose prose-invert prose-sm max-w-none">
        <AnimatePresence>
          {report.sections.map((section, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
            >
              <ReactMarkdown
                components={{
                  h1: ({ node, ...props }) => (
                    <h1 className="text-2xl font-bold mb-4 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent" {...props} />
                  ),
                  h2: ({ node, ...props }) => (
                    <h2 className="text-xl font-semibold mt-6 mb-3 text-slate-200" {...props} />
                  ),
                  h3: ({ node, ...props }) => (
                    <h3 className="text-lg font-medium mt-4 mb-2 text-slate-300" {...props} />
                  ),
                  p: ({ node, ...props }) => (
                    <p className="text-slate-300 leading-relaxed mb-4" {...props} />
                  ),
                  code: ({ node, inline, ...props }) =>
                    inline ? (
                      <code className="px-1.5 py-0.5 rounded bg-slate-900/80 text-cyan-400 text-sm font-mono" {...props} />
                    ) : (
                      <Prism language="python" className="rounded-lg" {...props} />
                    ),
                  a: ({ node, ...props }) => (
                    <a
                      className="text-indigo-400 hover:text-indigo-300 underline decoration-indigo-500/30 hover:decoration-indigo-500 transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                      {...props}
                    />
                  ),
                  ul: ({ node, ...props }) => (
                    <ul className="list-disc list-inside space-y-2 mb-4 text-slate-300" {...props} />
                  ),
                  ol: ({ node, ...props }) => (
                    <ol className="list-decimal list-inside space-y-2 mb-4 text-slate-300" {...props} />
                  ),
                }}
              >
                {section.content}
              </ReactMarkdown>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {/* Sources Section */}
        {report.sources && report.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-8 p-4 rounded-lg bg-slate-900/50 border border-slate-700/50"
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Link2 className="w-5 h-5" />
              Sources ({report.sources.length})
            </h3>
            <div className="space-y-2">
              {report.sources.map((source, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded bg-slate-900/50 hover:bg-slate-900 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-mono text-slate-500">
                      [{idx + 1}]
                    </span>
                    <div className="flex-1">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-indigo-400 hover:text-indigo-300 hover:underline"
                      >
                        {source.title}
                      </a>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">
                          {source.type}
                        </Badge>
                        {source.date && (
                          <span className="text-xs text-slate-500">
                            {source.date}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    ) : (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <FileQuestion className="w-16 h-16 text-slate-600 mb-4" />
        <p className="text-slate-400 text-lg mb-2">No research output yet</p>
        <p className="text-slate-500 text-sm">
          Start a research query to see results here
        </p>
      </div>
    )}
  </CardContent>
  
  {report && (
    <CardFooter className="border-t border-slate-700/50 p-4">
      <div className="flex items-center gap-2 w-full">
        <Button variant="outline" size="sm" onClick={() => copyToClipboard(report.text)}>
          <Copy className="w-4 h-4 mr-2" />
          Copy
        </Button>
        <Button variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
        <Button variant="outline" size="sm">
          <Share2 className="w-4 h-4 mr-2" />
          Share
        </Button>
      </div>
    </CardFooter>
  )}
</Card>
```

### 8.4 Key Animations

```tsx
// Framer Motion animation variants
const animations = {
  // Page load
  pageLoad: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5, ease: "easeOut" }
  },
  
  // Stagger children
  staggerChildren: {
    animate: {
      transition: {
        staggerChildren: 0.1
      }
    }
  },
  
  // Fade in from bottom
  fadeInUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
  },
  
  // Pulse (for active elements)
  pulse: {
    animate: {
      scale: [1, 1.05, 1],
      transition: {
        repeat: Infinity,
        duration: 2,
        ease: "easeInOut"
      }
    }
  },
  
  // Shimmer (for loading states)
  shimmer: {
    animate: {
      backgroundPosition: ["200% 0", "-200% 0"],
      transition: {
        repeat: Infinity,
        duration: 2,
        ease: "linear"
      }
    }
  },
  
  // Bounce (for notifications)
  bounce: {
    initial: { scale: 0, opacity: 0 },
    animate: {
      scale: [0, 1.1, 1],
      opacity: 1,
      transition: {
        duration: 0.5,
        ease: "easeOut"
      }
    }
  },
  
  // Slide in from side
  slideIn: {
    initial: { x: -100, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: 100, opacity: 0 }
  }
};

// Progress bar animation
<motion.div
  className="h-2 bg-indigo-600 rounded-full"
  initial={{ width: 0 }}
  animate={{ width: `${progress}%` }}
  transition={{ duration: 0.5, ease: "easeOut" }}
/>

// Typing indicator
<motion.div className="flex gap-1">
  {[0, 1, 2].map((i) => (
    <motion.div
      key={i}
      className="w-2 h-2 rounded-full bg-indigo-400"
      animate={{ y: [0, -10, 0] }}
      transition={{
        repeat: Infinity,
        duration: 0.6,
        delay: i * 0.2
      }}
    />
  ))}
</motion.div>

// Success checkmark
<motion.div
  initial={{ scale: 0, rotate: -180 }}
  animate={{ scale: 1, rotate: 0 }}
  transition={{ type: "spring", stiffness: 200, damping: 15 }}
>
  <CheckCircle2 className="w-6 h-6 text-green-400" />
</motion.div>
```

### 8.5 Real-Time WebSocket Updates

```tsx
// WebSocket hook for real-time updates
function useResearchUpdates(sessionId: string) {
  const [updates, setUpdates] = useState<ResearchUpdate[]>([]);
  const { toast } = useToast();
  
  useEffect(() => {
    const socket = io('ws://localhost:8000', {
      query: { session_id: sessionId }
    });
    
    socket.on('research_update', (data: ResearchUpdate) => {
      setUpdates(prev => [...prev, data]);
      
      // Show toast for important events
      if (data.type === 'iteration_complete') {
        toast({
          title: `Iteration ${data.iteration} complete`,
          description: data.message,
          duration: 3000
        });
      }
      
      // Animate new content
      if (data.type === 'report_chunk') {
        // Append to report with animation
        animateReportUpdate(data.content);
      }
    });
    
    socket.on('error', (error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    });
    
    return () => socket.disconnect();
  }, [sessionId]);
  
  return updates;
}
```

---

## 9. Implementation Summary

### 9.1 Final Architecture

- **Pattern:** ReAct (Reasoning + Acting)
- **Agents:** 2 (Researcher + Evaluator)
- **LLM Providers:** 3 with automatic fallback (OpenAI, Gemini, OpenRouter)
- **Tools:** 4 (Web Search, ArXiv, GitHub, PDF Parser)
- **Evaluation:** 3-tier (Per-Step, Metadata, End-to-End)
- **Tracing:** Complete observability via LangSmith or custom logger
- **UI:** Modern Next.js with real-time animations
- **Cost:** ~$0.002-0.003 per research query

### 9.2 Key Features

✅ **Complete Transparency:** Every thought, action, and observation traced  
✅ **Flexible LLMs:** Switch providers on the fly, automatic fallback  
✅ **Comprehensive Evaluation:** Per-step + end-to-end + performance metrics  
✅ **Modern UI:** Real-time updates, smooth animations, dark theme  
✅ **Content Management:** Smart pipeline handles 20+ search results efficiently  
✅ **Educational:** Perfect for learning agentic AI concepts  
✅ **Cost-Effective:** Affordable for experimentation  
✅ **Production-Ready:** Error handling, retry logic, caching

### 9.3 Development Timeline

**Week 1-2: Backend Core**
- LLM Manager with 3 providers
- ReAct orchestration
- Tool implementations
- Content pipeline
- Trace logging

**Week 3-4: Frontend**
- Next.js setup
- Three-panel UI
- Real-time WebSocket
- Animations

**Week 5: Evaluation & Polish**
- Per-step evaluation
- End-to-end evaluation
- Export options
- Documentation

**Total: 5 weeks to MVP**

### 9.4 Success Metrics

**Technical:**
- ✅ <10 min per research query
- ✅ >80% tool success rate
- ✅ <$0.005 per query
- ✅ Zero data loss

**Educational:**
- ✅ Users understand ReAct
- ✅ Clear agent reasoning
- ✅ Comprehensive evaluation
- ✅ Learning value

**UX:**
- ✅ <3s first interaction
- ✅ <500ms WebSocket latency
- ✅ Mobile responsive
- ✅ Accessible (WCAG 2.1 AA)

---

## 10. Conclusion

This Agentic AI Research solution delivers a comprehensive, educational platform with:

🎯 **Clear Architecture:** ReAct pattern with 2 agents  
🔧 **Flexible LLMs:** 3 providers with fallback  
📊 **Complete Evaluation:** Per-step + end-to-end + metrics  
🎨 **Modern UI:** Real-time, animated, beautiful  
📝 **Full Traces:** Every decision visible  
💰 **Affordable:** $0.002-0.003 per query  

**Ready to build!** All components defined, architecture proven, costs minimal.

---

**Document Version:** 3.0  
**Last Updated:** 2025-11-03  
**Status:** Ready for Implementation ✅

