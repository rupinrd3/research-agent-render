"""
Researcher Agent (ReAct Pattern)

Implements autonomous research through iterative reasoning and tool use.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import uuid
import ast

from ..llm import LLMManager
from ..config.settings import ToolsSettings
from ..tools import (
    web_search,
    arxiv_search,
    github_search,
    pdf_to_text,
    get_all_tool_definitions,
)
from .models import AgentStep, ResearchResult

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ResearcherAgent:
    """
    Autonomous research agent using ReAct (Reasoning + Acting) pattern.

    The agent iteratively:
    1. THINKS about what information is needed
    2. ACTS by selecting and using appropriate tools
    3. OBSERVES the results and decides next steps
    4. Repeats until sufficient information is gathered
    """

    GITHUB_KEYWORDS = {
        "implementation",
        "implementations",
        "library",
        "libraries",
        "repo",
        "repos",
        "repository",
        "repositories",
        "code",
        "codes",
        "tool",
        "tools",
        "application",
        "applications",
        "framework",
        "frameworks",
        "sdk",
        "benchmark",
        "benchmarks",
        "open source",
        "open-source",
        "github",
    }

    ARXIV_KEYWORDS = {
        "paper",
        "papers",
        "research",
        "study",
        "studies",
        "academic",
        "arxiv",
        "preprint",
        "pre-print",
        "theory",
        "algorithm",
        "algorithms",
        "proof",
        "methodology",
        "evaluation",
        "neural",
        "model",
        "models",
        "dataset",
        "datasets",
        "science",
        "scientific",
        "physics",
        "math",
        "mathematics",
        "statistical",
        "statistics",
        "ml",
        "ai",
        "artificial intelligence",
        "deep learning",
        "machine learning",
        "generative ai",
        "rag",
        "llm",
        "data science",
    }

    CURRENT_YEAR = "2025"

    SYSTEM_PROMPT = """You are a senior research analyst operating with the ReAct (Reasoning + Acting) pattern.

Loop discipline (per iteration):
1. THOUGHT – spell out what you have learned, what is still unclear, and which data source would best close the gap. Think about what information you need next, if any.
2. ACTION – select only the tools that actually help. Default to web_search unless the topic clearly calls for repositories/implementations (github_search) or academic/scholarly evidence (arxiv_search). Use pdf_to_text whenever a PDF is referenced.
3. OBSERVATION — study the tool output, extract the most decision-relevant evidence, and explicitly note any follow-up questions that arise. Those notes must inform the next THOUGHT turn.
4. Repeat until the topic is well understood or you have exhausted trustworthy evidence. As soon as the key deliverables above are satisfied, immediately call the `finish` tool—do not use additional iterations "just in case."

Available tools:
- web_search — news, articles, practical information, timely updates.
- arxiv_search — peer-reviewed or pre-print academic literature.
- github_search — implementations, libraries, benchmarks, active projects.
- pdf_to_text — extract text/snippets from PDFs discovered by other tools.
- finish — emit the final Deep Research Report and end the loop.

Guidelines:
- Max iterations: {max_iterations}. Use them deliberately; batch multiple tool calls in the same action only when they are clearly warranted.
- Always cite sources inline as [#] and maintain a numbered reference list.
- After every observation, reflect on: "What critical questions remain? Which tool best addresses them?" If you already have all required evidence and every section of the report can be written, call `finish` instead of launching more tools.
- Treat the content pipeline output as structured evidence: highlight why each source matters rather than copying text.
- Use the gathered sources as primary evidence; you may layer in well-established background context from your own knowledge, but corroborate it with at least one verifiable source whenever possible.
- If a web_search returns fewer than 3 relevant results or clearly misses key subtopics, immediately refine the query (add specifics, synonyms, filters, or site/domain hints) and run web_search again before moving on.
- When freshness matters, set the `date_filter` argument (day/week/month/year) or state "past month"/"latest" explicitly. Treat the "current year" as {current_year} unless the user explicitly asks for another year, and prefer mentioning {current_year} when you must cite recency.
- When the topic is historical, keep the referenced years and focus on the core topic instead of recency filters.
- Domain coverage reminders are hints, not quotas. Once you have enough credible evidence for every section, skip additional tools and call `finish`.
- When you eventually call finish, follow the Deep Research Report spec:
  - Title + TL;DR (4-6 bullets with quantified takeaways when possible).
  - Methodology & Evidence Quality: explain which tools/sources were used, recency filters applied, remaining blind spots, and confidence.
  - Findings & Analysis: create domain-appropriate sections (business impact, policy implications, architecture, market sizing, etc.). Feel free to add or rename sections so the outline matches the query. Blend retrieved evidence with trustworthy prior knowledge, but cite only verifiable sources inline as [#].
  - Implementation / Impact (deployments, costs, adoption, code-level insights) when relevant.
  - Risks, Gaps & Open Questions.
  - Recommended Next Steps (clear actions or experiments).
  - Sources: numbered list matching inline [#] citations plus any optional appendices (tables, glossaries) that aid comprehension.
- Summaries must stay flexible: write for both technical and general readers by mixing crisp paragraphs with occasional bullet lists when that improves clarity.

Current query: {query}"""

    FINISH_GUARD_PROMPT = """Assess whether the draft Deep Research Report is complete, well-sourced, and ready.
Reply with strict JSON:
{
  "allow_finish": true or false,
  "feedback": "Short critique explaining readiness or missing evidence.",
  "next_action_hint": "If allow_finish=false, specify the most useful follow-up query/tool."
}
Approve only if the report covers the query, cites authoritative sources, and addresses remaining risks."""

    def __init__(
        self,
        llm_manager: LLMManager,
        max_iterations: int = 10,
        timeout_minutes: int = 15,
        trace_callback: Optional[Callable] = None,
        content_pipeline=None,
        websocket_manager=None,
        metrics_collector=None,
        tool_settings: Optional[ToolsSettings] = None,
        llm_temperature: Optional[float] = None,
        policy_overrides: Optional[dict] = None,
    ): 
        """
        Initialize ResearcherAgent.

        Args:
            llm_manager: LLM manager instance
            max_iterations: Maximum ReAct iterations
            timeout_minutes: Timeout for complete research session
            trace_callback: Optional callback for trace events
            content_pipeline: Optional content pipeline for result processing
            websocket_manager: Optional WebSocket manager for real-time updates
            metrics_collector: Optional metrics collector for performance tracking
            tool_settings: Optional ToolsSettings for default tool configuration
            llm_temperature: Optional temperature override for reasoning calls
        """
        self.llm = llm_manager
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_minutes * 60
        self.tool_definitions = get_all_tool_definitions()
        self.trace_callback = trace_callback
        self.content_pipeline = content_pipeline
        self.websocket_manager = websocket_manager
        self.metrics_collector = metrics_collector
        self.tool_settings = tool_settings
        self.default_tool_timeout = (
            getattr(tool_settings, "tool_execution_timeout_seconds", 60)
            if tool_settings
            else 60
        )
        self.session_id: Optional[str] = None
        self.llm_temperature = (
            max(0.0, min(llm_temperature, 1.0)) if llm_temperature is not None else 0.7
        )
        self.current_year = self.CURRENT_YEAR
        self.domain_tools = ["web_search", "arxiv_search", "github_search"]
        self.tool_usage_counts: Dict[str, int] = {}
        self._last_guidance_missing: Optional[tuple[str, ...]] = None
        self.tool_policy: Dict[str, Any] = {
            "allow_github": True,
            "allow_arxiv": True,
            "default_tool": "web_search",
            "sufficient_result_count": 5,
            "sparse_result_threshold": 2,
        }
        self.early_evidence_sufficient = False
        self._tool_denials: Dict[str, int] = {}
        self._last_sparse_query: Optional[str] = None
        self.finish_guard_enabled = True
        self.finish_guard_retry_on_auto_finish = True
        self.ascii_prompts = True
        if policy_overrides:
            self.finish_guard_enabled = bool(
                policy_overrides.get("finish_guard_enabled", True)
            )
            self.finish_guard_retry_on_auto_finish = bool(
                policy_overrides.get("finish_guard_retry_on_auto_finish", True)
            )
            if "sufficient_result_count" in policy_overrides:
                self.tool_policy["sufficient_result_count"] = int(
                    policy_overrides["sufficient_result_count"]
                )
            if "sparse_result_threshold" in policy_overrides:
                self.tool_policy["sparse_result_threshold"] = int(
                    policy_overrides["sparse_result_threshold"]
                )
            self.ascii_prompts = bool(policy_overrides.get("ascii_prompts", True))

        logger.info(
            f"Initialized ResearcherAgent (max_iterations={max_iterations}, "
            f"timeout={timeout_minutes}min, "
            f"pipeline={'enabled' if content_pipeline else 'disabled'}, "
            f"websocket={'enabled' if websocket_manager else 'disabled'})"
        )
    def _normalize_for_windows(self, s: str) -> str:
        if not s:
            return s
        repl={
            '—':'-','–':'-','‒':'-',
            '‘':''', '’':''', '“':'"', '”':'"',
            '…':'...'
        }
        for k,v in repl.items():
            s=s.replace(k,v)
        return s
    async def research(
        self, query: str, session_id: Optional[str] = None
    ) -> ResearchResult:
        """
        Perform research on a query.

        Args:
            query: Research question
            session_id: Optional session ID

        Returns:
            ResearchResult with report and metadata
        """
        session_id = session_id or str(uuid.uuid4())
        self.session_id = session_id
        start_time = time.time()

        logger.info("[Lifecycle] research(query) called: %s", query)
        logger.info("[Lifecycle] Initialize State for session %s", session_id)

        logger.info(f"Starting research session: {session_id}")
        logger.info(f"Query: {query}")

        # Emit session start event
        await self._emit_trace("session_start", {
            "session_id": session_id,
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Initialize state
        steps: List[AgentStep] = []
        conversation_history: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (self._normalize_for_windows(self.SYSTEM_PROMPT.format(
                    max_iterations=self.max_iterations, query=query, current_year=self.current_year
                )) if self.ascii_prompts else self.SYSTEM_PROMPT.format(
                    max_iterations=self.max_iterations, query=query, current_year=self.current_year
                )),
            },
            {
                "role": "user",
                "content": (
                    "You are about to start the research process described above. "
                    f"Restate the plan and begin reasoning about the query:\n\n{query}"
                ),
            },
        ]
        logger.info("[Lifecycle] Create conversation history: [system_msg, user_msg]")
        self.tool_policy = self._derive_tool_policy(query)
        self.recency_intent = self._detect_recency_intent(query)
        self.preferred_date_filter = self._preferred_date_filter(self.recency_intent)
        policy_message = self._build_tool_policy_message(self.tool_policy, self.recency_intent)
        if policy_message:
            conversation_history.append({"role": "system", "content": (self._normalize_for_windows(policy_message) if self.ascii_prompts else policy_message)})

        iteration = 0
        done = False
        final_report = ""
        sources: List[str] = []
        error = None
        self.tool_usage_counts = {tool: 0 for tool in self.domain_tools}
        self._last_guidance_missing = None

        try:
            logger.info("[Lifecycle] START REACT LOOP (max_iterations=%s)", self.max_iterations)
            while not done and iteration < self.max_iterations:
                iteration += 1
                logger.info("[Lifecycle] Repeats Until Complete - iteration %s", iteration)

                # Check timeout
                if time.time() - start_time > self.timeout_seconds:
                    logger.warning("Research timeout exceeded")
                    error = "Timeout exceeded"
                    break

                logger.info(f"Iteration {iteration}/{self.max_iterations}")

                # Emit iteration start
                await self._emit_trace("iteration_start", {
                    "iteration": iteration,
                    "timestamp": datetime.utcnow().isoformat(),
                    "mode": "normal",
                    "message": f"Iteration {iteration} started",
                }, iteration)

                # Get agent's next action
                step_start = time.time()

                try:
                    # Add user prompt if needed
                    self._prune_incomplete_tool_calls(conversation_history)

                    if len(conversation_history) > 1 and conversation_history[-1]["role"] != "user":
                        conversation_history.append({
                            "role": "user",
                            "content": "Continue with the next action or finish if you have enough information.",
                        })

                    self._inject_domain_guidance(conversation_history)

                    logger.info(
                        "[ResearcherAgent] Starting LLM call (iteration=%s, messages=%s)",
                        iteration,
                        len(conversation_history),
                    )
                    response = await self.llm.complete(
                        messages=conversation_history,
                        tools=self.tool_definitions,
                        temperature=self.llm_temperature,
                        max_tokens=6000,
                        # Allow tool-call-only replies; we synthesize a thought if content is empty
                        require_tool_calls=True,
                        require_content=False,
                    )

                    step_latency = time.time() - step_start

                    # Record LLM call in metrics collector
                    if self.metrics_collector:
                        self.metrics_collector.record_llm_call(
                            provider=response.get("provider_used", "unknown"),
                            input_tokens=response["usage"]["input_tokens"],
                            output_tokens=response["usage"]["output_tokens"],
                            cost=self.llm.estimate_cost(
                                response["usage"]["input_tokens"],
                                response["usage"]["output_tokens"],
                            ),
                            model=response.get("model"),
                        )

                    # Extract thought and action
                    thought = response.get("content", "") or ""
                    tool_calls = response.get("tool_calls") or []
                    if not thought.strip():
                        if tool_calls:
                            thought = self._fallback_thought(tool_calls, iteration)
                        else:
                            logger.warning(
                                "[ResearcherAgent] LLM returned empty content "
                                "(iteration %s, provider=%s)",
                                iteration,
                                response.get("provider_used", "unknown"),
                            )
                    provider_used = response.get("provider_used", "unknown")
                    provider_note = ""
                    if (
                        hasattr(self.llm, "primary_provider")
                        and self.llm.primary_provider
                        and provider_used != self.llm.primary_provider.value
                    ):
                        provider_note = (
                            f" (fallback from {self.llm.primary_provider.value})"
                        )

                    logger.info(
                        "[ResearcherAgent] LLM call complete (iteration=%s, provider=%s, total_tokens=%s)",
                        iteration,
                        response.get("provider_used", "unknown"),
                        response.get("usage", {}).get("total_tokens", "n/a"),
                    )
                    logger.info("[Lifecycle] Decides Next Steps based on latest reasoning")

                    # Emit thought
                    await self._emit_trace("thought", {
                        "thought": thought,
                        "tokens_used": response["usage"]["total_tokens"],
                        "provider": provider_used,
                        "latency_ms": step_latency * 1000,
                        "message": self._shorten(
                            f"[{provider_used}{provider_note}] {thought.strip() or 'Reasoning step'}",
                            600,
                        ),
                    }, iteration)

                    if not tool_calls:
                        # No tool call - agent providing reasoning without action
                        logger.warning("[ResearcherAgent] Agent did not call a tool, prompting for action")
                        conversation_history.append({
                            "role": "assistant",
                            "content": thought or "I need to take an action.",
                        })
                        continue

                    assistant_message = {
                        "role": "assistant",
                        "content": thought,
                        "tool_calls": tool_calls,
                    }
                    conversation_history.append(assistant_message)

                    for idx, tool_call in enumerate(tool_calls):
                        action_name = tool_call["function"]["name"]

                        raw_arguments = tool_call["function"]["arguments"]
                        try:
                            action_input = json.loads(raw_arguments)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse tool arguments: {e}")
                            action_input = self._handle_malformed_arguments(
                                action_name, raw_arguments
                            )

                        logger.info(f"Action: {action_name}")

                        allowed, block_message = self._is_tool_allowed(
                            action_name, thought, action_input
                        )
                        if not allowed:
                            observation = block_message
                            logger.info(
                                "[ResearcherAgent] Tool '%s' blocked by heuristics: %s",
                                action_name,
                                block_message,
                            )
                            await self._emit_trace(
                                "tool_blocked",
                                {
                                    "tool": action_name,
                                    "reason": block_message,
                                    "index": idx,
                                },
                                iteration,
                            )
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": observation,
                            }
                            conversation_history.append(tool_message)
                            continue

                        await self._emit_trace("action", {
                            "tool": action_name,
                            "parameters": action_input,
                            "index": idx,
                            "message": self._summarize_action(action_name, action_input),
                        }, iteration)
                        logger.info(
                            "[Lifecycle] Decides Next Steps -> executing action '%s'",
                            action_name,
                        )

                        if action_name == "finish":
                            guard_allowed, guard_feedback, guard_hint = (
                                await self._run_finish_guard(
                                    query, action_input, iteration
                                )
                            )
                            if not guard_allowed:
                                rejection = guard_feedback or (
                                    "Finish guard check failed: gather at least one more high-quality source "
                                    "before calling finish again."
                                )
                                await self._emit_trace(
                                    "finish_guard",
                                    {
                                        "approved": False,
                                        "feedback": rejection,
                                        "hint": guard_hint,
                                    },
                                    iteration,
                                )
                                await self._emit_trace(
                                    "observation",
                                    {
                                        "observation": rejection[:1000],
                                        "index": idx,
                                        "message": self._shorten(rejection, 400),
                                    },
                                    iteration,
                                )
                                conversation_history.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_call["id"],
                                        "content": rejection
                                        + (f" Next step: {guard_hint}" if guard_hint else ""),
                                    }
                                )
                                if guard_hint:
                                    conversation_history.append(
                                        {
                                            "role": "system",
                                            "content": (
                                                "Finish guard guidance: "
                                                f"{guard_hint} Use the most relevant tool to close the gap."
                                            ),
                                        }
                                    )
                                if self.metrics_collector and idx == 0:
                                    self.metrics_collector.add_iteration(
                                        {
                                            "iteration": iteration,
                                            "duration": step_latency,
                                            "timestamp": datetime.utcnow().isoformat(),
                                            "thought": thought[:200],
                                            "action": "finish_guard_rejected",
                                        }
                                    )
                                continue

                            await self._emit_trace(
                                "finish_guard",
                                {
                                    "approved": True,
                                    "feedback": guard_feedback,
                                    "hint": guard_hint,
                                },
                                iteration,
                            )

                            final_report = action_input.get("report", "")
                            sources = action_input.get("sources", [])
                            done = True

                            await self._emit_trace("finish", {
                                "report_length": len(final_report),
                                "num_sources": len(sources),
                                "report": final_report,
                                "sources": sources,
                                "message": self._shorten(
                                    "Final report drafted with cited sources", 400
                                ),
                            }, iteration)

                            finish_step = AgentStep(
                                iteration=iteration,
                                thought=thought,
                                action="finish",
                                action_input=action_input,
                                observation="Final report generated",
                                tool_output={
                                    "report": final_report,
                                    "sources": sources,
                                },
                                timestamp=datetime.utcnow(),
                                tokens_used=response["usage"]["total_tokens"],
                                cost_usd=self.llm.estimate_cost(
                                    response["usage"]["input_tokens"],
                                    response["usage"]["output_tokens"],
                                ),
                                latency_seconds=step_latency,
                            )
                            steps.append(finish_step)

                            if self.metrics_collector:
                                self.metrics_collector.add_iteration(
                                    {
                                        "iteration": iteration,
                                        "duration": step_latency,
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "thought": thought[:200],
                                        "action": "finish",
                                    }
                                )

                            logger.info("Agent finished research")
                            logger.info("[Lifecycle] Generates Report and cites %s sources", len(sources))
                            break

                        timeout_seconds = self._get_tool_timeout_seconds(action_name)
                        tool_start = time.time()
                        tool_success = True
                        timeout_message = None

                        try:
                            tool_output = await self._execute_tool_with_timeout(
                                action_name, action_input, timeout_seconds
                            )
                        except asyncio.TimeoutError:
                            tool_success = False
                            timeout_message = (
                                f"Tool '{action_name}' timed out after "
                                f"{int(timeout_seconds)} seconds"
                                if timeout_seconds
                                else f"Tool '{action_name}' timed out"
                            )
                            logger.error(
                                "[ResearcherAgent] %s", timeout_message
                            )
                            tool_output = {
                                "status": "error",
                                "error": timeout_message,
                                "tool": action_name,
                                "notes": [timeout_message],
                            }

                        tool_duration = time.time() - tool_start

                        result_summary = (
                            timeout_message
                            if timeout_message
                            else self._summarize_tool_output(action_name, tool_output)
                        )
                        logger.info(
                            "[ResearcherAgent] Tool '%s' (call %s) completed in %.2fs | summary=%s",
                            action_name,
                            idx,
                            tool_duration,
                            result_summary,
                        )
                        provider = None
                        pipeline_stats = None
                        notes: List[str] = []
                        result_count = 0
                        if isinstance(tool_output, dict):
                            provider = tool_output.get("provider")
                            pipeline_stats = tool_output.get("pipeline_stats")
                            notes = tool_output.get("notes", [])
                            result_count = self._infer_result_count(tool_output)
                        else:
                            result_count = 0

                        self._maybe_mark_sufficient_evidence(
                            action_name, result_count, iteration
                        )

                        await self._emit_trace("tool_execution", {
                            "tool": action_name,
                            "duration_ms": tool_duration * 1000,
                            "success": tool_success,
                            "result_summary": result_summary,
                            "index": idx,
                            "provider": provider,
                            "result_count": result_count,
                            "pipeline_stats": pipeline_stats,
                            "notes": notes,
                            "timeout_seconds": timeout_seconds if not tool_success else None,
                            "message": result_summary,
                        }, iteration)
                        self._record_tool_usage(action_name, tool_success)

                        # Record tool execution in metrics collector
                        if self.metrics_collector:
                            self.metrics_collector.record_tool_execution(
                                tool_name=action_name,
                                duration=tool_duration,
                                success=tool_success,
                                results_count=result_count,
                                metadata={"provider": provider} if provider else None,
                            )

                        observation = (
                            timeout_message
                            if timeout_message
                            else self._format_observation(action_name, tool_output)
                        )
                        logger.info(
                            "[Lifecycle] Analyzes Results from '%s'",
                            action_name,
                        )

                        await self._emit_trace("observation", {
                            "observation": observation[:1000],
                            "index": idx,
                            "message": self._shorten(observation, 400),
                        }, iteration)

                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": observation,
                        }
                        conversation_history.append(tool_message)

                        if action_name == "web_search":
                            self._handle_sparse_web_results(
                                conversation_history,
                                action_input.get("query"),
                                result_count,
                            )

                        if idx == 0:
                            step = AgentStep(
                                iteration=iteration,
                                thought=thought,
                                action=action_name,
                                action_input=action_input,
                                observation=observation,
                                tool_output=tool_output,
                                timestamp=datetime.utcnow(),
                                tokens_used=response["usage"]["total_tokens"],
                                cost_usd=self.llm.estimate_cost(
                                    response["usage"]["input_tokens"],
                                    response["usage"]["output_tokens"],
                                ),
                                latency_seconds=step_latency,
                            )
                            steps.append(step)

                            # Record iteration in metrics collector
                            if self.metrics_collector:
                                self.metrics_collector.add_iteration({
                                    "iteration": iteration,
                                    "duration": step_latency,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "thought": thought[:200],  # Truncated
                                    "action": action_name,
                                })

                    if done:
                        break

                except Exception as e:
                    logger.error(f"Error in iteration {iteration}: {e}")
                    await self._emit_trace("error", {
                        "iteration": iteration,
                        "error": str(e),
                    }, iteration)
                    error = str(e)
                    break

            # Calculate total metrics
            if not done:
                if steps:
                    auto_finish_iteration = iteration + 1
                    (
                        done,
                        final_report,
                        sources,
                        finish_step,
                    ) = await self._force_finish_if_needed(
                        conversation_history, query, auto_finish_iteration
                    )
                    if done and finish_step:
                        steps.append(finish_step)
                        iteration = auto_finish_iteration
                else:
                    logger.error(
                        "Research ended without any tool outputs; unable to auto-generate final report."
                    )

            total_duration = time.time() - start_time
            total_tokens = sum(step.tokens_used for step in steps)
            total_cost = sum(step.cost_usd for step in steps)

            status = "completed" if done else ("failed" if error else "incomplete")

            result = ResearchResult(
                session_id=session_id,
                query=query,
                report=final_report,
                sources=sources,
                steps=steps,
                total_iterations=iteration,
                total_duration_seconds=total_duration,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                status=status,
                error=error,
            )

            # Emit session complete
            await self._emit_trace("session_complete", {
                "status": status,
                "iterations": iteration,
                "duration_seconds": total_duration,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost,
            })

            logger.info(
                f"Research completed: {iteration} iterations, "
                f"{total_duration:.1f}s, ${total_cost:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Research failed: {e}")
            await self._emit_trace("session_failed", {
                "error": str(e),
            })

            return ResearchResult(
                session_id=session_id,
                query=query,
                report="",
                sources=[],
                steps=steps,
                total_iterations=iteration,
                total_duration_seconds=time.time() - start_time,
                total_tokens=sum(step.tokens_used for step in steps),
                total_cost_usd=sum(step.cost_usd for step in steps),
                status="failed",
                error=str(e),
            )
        finally:
            self.session_id = None

    def _prune_incomplete_tool_calls(self, history: List[Dict[str, Any]]) -> None:
        """
        Remove trailing assistant messages that include tool_calls but have no tool response.
        """
        while len(history) >= 1:
            last = history[-1]
            if last.get("role") == "assistant" and last.get("tool_calls"):
                logger.warning(
                    "[ResearcherAgent] Removing incomplete assistant tool_call entry"
                )
                history.pop()
                continue
            if (
                last.get("role") == "tool"
                and history[-2:][:1]
                and history[-2]["role"] == "assistant"
                and history[-2].get("tool_calls")
                and history[-2]["tool_calls"][0]["id"] != last.get("tool_call_id")
            ):
                logger.warning(
                    "[ResearcherAgent] Removing mismatched tool response entry"
                )
                history.pop()
                continue
            break

    async def _execute_tool(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool with given input.

        Args:
            tool_name: Name of tool to execute
            tool_input: Tool parameters

        Returns:
            Tool output
        """
        logger.info(f"[ResearcherAgent] Executing tool: {tool_name}")

        # Pass content_pipeline to tools that support it
        if tool_name == "web_search":
            # Note: Provider selection is now automatic (Tavily → Serper → SerpAPI)
            # No need to pass provider or API keys - they're read from environment
            web_kwargs = dict(tool_input)

            # Log web search initiation
            logger.info(
                "[ResearcherAgent] Initiating web search: query='%s', num_results=%s",
                web_kwargs.get("query", ""),
                web_kwargs.get("num_results", 10),
            )
            logger.info("[Lifecycle] Searches Web via web_search tool")

            if self.preferred_date_filter and not web_kwargs.get("date_filter"):
                web_kwargs["date_filter"] = self.preferred_date_filter
                logger.info(
                    "[ResearcherAgent] Applying default date_filter='%s' based on recency intent",
                    self.preferred_date_filter,
                )

            return await web_search(
                content_pipeline=self.content_pipeline,
                **web_kwargs
            )
        elif tool_name == "arxiv_search":
            logger.info("[Lifecycle] Searches Academic Papers via arxiv_search")
            return await arxiv_search(
                content_pipeline=self.content_pipeline,
                **tool_input
            )
        elif tool_name == "github_search":
            logger.info("[Lifecycle] Searches Code Repos via github_search")
            return await github_search(
                content_pipeline=self.content_pipeline,
                **tool_input
            )
        elif tool_name == "pdf_to_text":
            logger.info("[Lifecycle] Extracts from PDFs via pdf_to_text")
            return await pdf_to_text(**tool_input)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _execute_tool_with_timeout(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        timeout_seconds: Optional[float],
    ) -> Any:
        """
        Execute a tool with an optional timeout safeguard.
        """
        if timeout_seconds and timeout_seconds > 0:
            return await asyncio.wait_for(
                self._execute_tool(tool_name, tool_input),
                timeout=timeout_seconds,
            )
        return await self._execute_tool(tool_name, tool_input)

    def _get_tool_timeout_seconds(self, tool_name: str) -> Optional[float]:
        """
        Determine the timeout to apply for the given tool.
        """
        timeout = self.default_tool_timeout

        if self.tool_settings:
            specific: Optional[float] = None
            if tool_name == "web_search":
                specific = getattr(
                    self.tool_settings,
                    "web_search_timeout_seconds",
                    None,
                )
            if specific is None:
                specific = getattr(
                    self.tool_settings,
                    "tool_execution_timeout_seconds",
                    None,
                )
            if specific is not None:
                timeout = specific

        if timeout is None or timeout <= 0:
            return None
        return float(timeout)

    def _record_tool_usage(self, tool_name: str, success: bool) -> None:
        """
        Track successful uses of key discovery tools for coverage guidance.
        """
        if success and tool_name in self.tool_usage_counts:
            self.tool_usage_counts[tool_name] += 1
            self._last_guidance_missing = None

    def _missing_domain_tools(self) -> List[str]:
        """
        Determine which discovery domains still need coverage.
        """
        return [
            tool
            for tool in self.domain_tools
            if self.tool_usage_counts.get(tool, 0) == 0
        ]

    def _inject_domain_guidance(self, conversation_history: List[Dict[str, Any]]) -> None:
        """
        Remind the agent about missing discovery channels to balance tool usage.
        """
        if self.early_evidence_sufficient:
            self._last_guidance_missing = None
            return

        missing = self._missing_domain_tools()
        if not missing:
            self._last_guidance_missing = None
            return

        missing_tuple = tuple(missing)
        if self._last_guidance_missing == missing_tuple:
            return

        guidance = (
            "Optional coverage reminder: consider evidence from "
            f"{', '.join(missing)} if it would materially improve coverage. Use one of these tools only if justified by the query."
        )
        conversation_history.append({
            "role": "system",
            "content": (self._normalize_for_windows(guidance) if self.ascii_prompts else guidance),
        })
        self._last_guidance_missing = missing_tuple

    async def _force_finish_if_needed(
        self,
        conversation_history: List[Dict[str, Any]],
        query: str,
        iteration: int,
    ) -> tuple[bool, str, List[str], Optional[AgentStep]]:
        """
        If the agent ran out of iterations without finishing, call the finish tool automatically.
        """
        logger.warning(
            "Max iterations reached without finish; generating final report automatically."
        )
        auto_start = time.time()
        await self._emit_trace("iteration_start", {
            "iteration": iteration,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "auto_finish",
            "message": f"Auto-finish iteration {iteration} started",
        }, iteration)
        self._prune_incomplete_tool_calls(conversation_history)
        conversation_history.append({
            "role": "user",
            "content": (
                "You have reached the iteration limit. Using only the observations gathered so far, "
                "call the finish tool now and generate the Deep Research Report. "
                "Required structure: Title, TL;DR (4-6 bullets), Methodology & Evidence Quality, dynamic Findings & Analysis sections (### ... tailored to the query), "
                "Implementation / Impact, Risks & Open Questions, Recommended Next Steps, Sources. "
                "Blend retrieved evidence with trusted background context, cite sources inline as [#], and adapt headings if the topic demands. "
                "Do NOT call any other tools."
            ),
        })

        try:
            response = await self.llm.complete(
                messages=conversation_history,
                tools=self.tool_definitions,
                temperature=self.llm_temperature,
                max_tokens=6000,
                require_tool_calls=True,
                tool_choice={"type": "function", "function": {"name": "finish"}},
            )
        except Exception as e:
            logger.error(f"Automatic finish attempt failed: {e}")
            return False, "", [], None

        thought = response.get("content", "") or ""
        tool_calls = response.get("tool_calls") or []
        if not tool_calls:
            logger.error("Automatic finish attempt did not return the finish tool")
            return False, "", [], None

        finish_call = tool_calls[0]
        try:
            finish_args = json.loads(finish_call["function"]["arguments"])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse finish arguments: {e}")
            return False, "", [], None

        report = finish_args.get("report", "")
        sources = finish_args.get("sources", []) or []

        # Finish guard on auto-finish
        if self.finish_guard_enabled:
            approved, feedback, hint = await self._run_finish_guard(query, finish_args, iteration)
            await self._emit_trace("finish_guard", {"approved": bool(approved), "feedback": feedback, "hint": hint, "auto": True}, iteration)
            if not approved and self.finish_guard_retry_on_auto_finish:
                conversation_history.append({"role": "system", "content": (self._normalize_for_windows(f"Finish guard feedback: {feedback}. Revise the report using ONLY existing observations; do not call any tools. Then call finish again.") if self.ascii_prompts else f"Finish guard feedback: {feedback}. Revise the report using ONLY existing observations; do not call any tools. Then call finish again.")})
                if hint:
                    conversation_history.append({"role": "system", "content": (self._normalize_for_windows(f"Next step: {hint}") if self.ascii_prompts else f"Next step: {hint}")})
                try:
                    response2 = await self.llm.complete(messages=conversation_history, tools=self.tool_definitions, temperature=self.llm_temperature, max_tokens=6000, require_tool_calls=True, tool_choice={"type": "function", "function": {"name": "finish"}},)
                    thought = response2.get("content", "") or thought
                    tool_calls2 = response2.get("tool_calls") or []
                    if tool_calls2:
                        finish_call = tool_calls2[0]
                        finish_args = json.loads(finish_call["function"]["arguments"])
                        report = finish_args.get("report", report)
                        sources = finish_args.get("sources", sources) or []
                except Exception as e:
                    logger.warning(f"Auto-finish guard retry failed: {e}")

        assistant_message = {
            "role": "assistant",
            "content": thought,
            "tool_calls": tool_calls,
        }
        conversation_history.append(assistant_message)

        observation = "Final report generated automatically."
        conversation_history.append({
            "role": "tool",
            "tool_call_id": finish_call["id"],
            "content": observation,
        })

        await self._emit_trace("finish", {
            "report_length": len(report),
            "num_sources": len(sources),
            "auto_generated": True,
            "report": report,
            "sources": sources,
            "message": self._shorten("Auto-finish generated the final report", 400),
        }, iteration)

        if self.metrics_collector:
            auto_duration = time.time() - auto_start
            self.metrics_collector.add_iteration(
                {
                    "iteration": iteration,
                    "duration": auto_duration,
                    "timestamp": datetime.utcnow().isoformat(),
                    "thought": thought[:200],
                    "action": "auto_finish",
                }
            )

        step = AgentStep(
            iteration=iteration,
            thought=thought,
            action="finish",
            action_input=finish_args,
            observation=observation,
            tool_output=finish_args,
            timestamp=datetime.utcnow(),
            tokens_used=response["usage"]["total_tokens"],
            cost_usd=self.llm.estimate_cost(
                response["usage"]["input_tokens"],
                response["usage"]["output_tokens"],
            ),
            latency_seconds=0.0,
        )

        return True, report, sources, step

    def _format_observation(self, tool_name: str, tool_output: Any) -> str:
        """
        Format tool output as observation for agent with both highlights and insights.
        """
        if isinstance(tool_output, dict):
            if tool_output.get("status") == "error":
                return tool_output.get("error", "Tool error")

            evidence_lines: List[str] = []
            insight_lines: List[str] = []
            notes = tool_output.get("notes") or []
            stats = tool_output.get("pipeline_stats") or {}
            result_count = self._infer_result_count(tool_output)

            def add_items(items: List[Dict[str, Any]], attrs: List[str]):
                for item in items[:3]:
                    title = item.get("title") or item.get("name") or "result"
                    meta = item.get(attrs[0]) if attrs else ""
                    snippet = item.get("summary") or item.get("abstract") or item.get("description") or ""
                    source = meta or item.get("domain") or item.get("url", "")
                    snippet = snippet.replace("\n", " " ).strip()
                    evidence_lines.append(
                        f"- {title} ({source}) - {self._shorten(snippet or 'No summary provided', 220)}"
                    )

            if tool_name == "web_search" and isinstance(tool_output.get("results"), list):
                add_items(tool_output["results"], ["domain"])
            elif tool_name == "arxiv_search" and isinstance(tool_output.get("papers"), list):
                add_items(tool_output["papers"], ["published_date"])
            elif tool_name == "github_search" and isinstance(tool_output.get("repositories"), list):
                add_items(tool_output["repositories"], ["language"])

            if result_count:
                insight_lines.append(
                    f"{tool_name} surfaced {result_count} relevant items; focus on the strongest evidence for upcoming report sections."
                )

            if stats:
                stats_line = (
                    f"Pipeline coverage: classified {stats.get('classified', 0)}/{stats.get('input_items', 0)}, "
                    f"extracted {stats.get('extracted', 0)}, summarized {stats.get('summarized', 0)}, "
                    f"cache hits {stats.get('cache_hits', 0)}"
                )
                insight_lines.append(stats_line)
                if stats.get("failed_extraction"):
                    insight_lines.append(
                        f"Extraction gaps on {stats['failed_extraction']} sources - rerun or sample manually if signal feels thin."
                    )
                if stats.get("failed_summaries"):
                    insight_lines.append(
                        f"Summaries missing for {stats['failed_summaries']} sources; review raw snippets before finalizing conclusions."
                    )

            for note in notes[:3]:
                insight_lines.append(note)

            sections: List[str] = []
            if evidence_lines:
                sections.append("Evidence Highlights:\n" + "\n".join(evidence_lines))
            if insight_lines:
                sections.append("Insights & Next Steps:\n- " + "\n- ".join(insight_lines))

            if sections:
                return "\n\n".join(sections)[:3000]

            summary = {
                k: v
                for k, v in tool_output.items()
                if k not in ["full_text", "raw_data"]
            }
            return json.dumps(summary, indent=2)[:3000]

        return str(tool_output)[:3000]

    def _summarize_tool_output(self, tool_name: str, tool_output: Any) -> str:
        """
        Create brief summary of tool output for logging.
        """
        if isinstance(tool_output, dict):
            if tool_output.get("status") == "error":
                return tool_output.get("error", f"{tool_name} failed")

            provider = tool_output.get("provider")
            stats = tool_output.get("pipeline_stats") or {}
            notes = tool_output.get("notes") or []

            def with_context(base: str) -> str:
                if provider:
                    base += f" via {provider}"
                if stats.get("extracted") and stats.get("input_items"):
                    base += (
                        f" (processed {stats['extracted']}/{stats['input_items']} sources)"
                    )
                if notes:
                    base += f"; {notes[0]}"
                return base

            if "results" in tool_output:
                base = f"{tool_output.get('total_found', 0)} web results"
                return with_context(base)
            elif "papers" in tool_output:
                base = f"{tool_output.get('total_found', 0)} papers"
                return with_context(base)
            elif "repositories" in tool_output:
                base = f"{tool_output.get('total_found', 0)} repositories"
                return with_context(base)
            elif "full_text" in tool_output:
                return f"PDF extracted: {tool_output.get('word_count', 0)} words"
            else:
                return with_context("Tool output received")
        return "Tool output received"

    def _handle_malformed_arguments(self, action_name: str, raw_arguments: str) -> Dict[str, Any]:
        """
        Attempt to repair malformed JSON tool arguments so research can continue.
        """
        text = (raw_arguments or "").strip()
        if not text:
            return {}

        try:
            repaired = ast.literal_eval(text)
            if isinstance(repaired, dict):
                return repaired
        except (ValueError, SyntaxError):
            pass

        if action_name == "finish":
            logger.warning(
                "Finish arguments malformed; treating raw payload as report text."
            )
            return {
                "report": text,
                "sources": [],
                "__raw_arguments": text,
            }

        return {"__raw_arguments": text}

    def _log_animation_stage(
        self, event_type: str, iteration: Optional[int], data: Dict[str, Any]
    ) -> None:
        """
        Temporary instrumentation: surface the stage transitions that drive the
        frontend workflow animation through the backend logger so they show up in
        error.txt for analysis.
        """

        if event_type == "finish_guard":
            stage = (
                "evaluate->finish" if data.get("approved") else "evaluate->think"
            )
        else:
            stage = self.STAGE_EVENT_MAP.get(event_type)

        if not stage:
            return

        payload = {
            "stage": stage,
            "event": event_type,
            "iteration": iteration,
        }

        # Include a few helpful fields when they exist
        for key in ("tool", "success", "result_count", "approved", "duration_ms"):
            if key in data:
                payload[key] = data[key]

        logger.info("[WorkflowAnimation] %s", payload)

    async def _emit_trace(
        self, event_type: str, data: Dict[str, Any], iteration: Optional[int] = None
    ):
        """
        Emit trace event via callback and WebSocket.

        Args:
            event_type: Type of trace event
            data: Event data
            iteration: Optional iteration number
        """
        data = dict(data)
        if iteration is not None:
            data.setdefault("iteration", iteration)
        data.setdefault("message", self._format_trace_message(event_type, iteration))

        self._log_animation_stage(event_type, iteration, data)

        # Call trace callback (for database storage)
        if self.trace_callback:
            try:
                await self.trace_callback(event_type, data, iteration)
            except Exception as e:
                logger.error(f"Trace callback failed: {e}")

        # Broadcast via WebSocket (for real-time updates)
        if self.websocket_manager:
            try:
                session_id = data.get("session_id") or self.session_id
                if session_id:
                    data.setdefault("session_id", session_id)
                    await self.websocket_manager.send_trace_event(
                        session_id, event_type, data
                    )
            except Exception as e:
                logger.error(f"WebSocket broadcast failed: {e}")

    def _format_trace_message(self, event_type: str, iteration: Optional[int]) -> str:
        """Provide a human-friendly default message for trace events."""
        if event_type == "iteration_start" and iteration is not None:
            return f"Starting iteration {iteration}"
        if event_type == "thought":
            return "Agent is reasoning"
        if event_type == "action":
            return "Selecting next tool"
        if event_type == "tool_execution":
            return "Tool execution complete"
        if event_type == "observation":
            return "Observation recorded"
        if event_type == "session_complete":
            return "Session completed"
        if event_type == "session_failed":
            return "Session failed"
        if event_type == "finish":
            return "Final report drafted"
        return event_type.replace("_", " ").title()

    def _shorten(self, text: str, max_len: int = 400) -> str:
        """Truncate text with ellipsis."""
        if not text:
            return ""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _fallback_thought(self, tool_calls: List[Dict[str, Any]], iteration: int) -> str:
        """
        Provide a readable placeholder thought when the LLM omits reasoning text.
        """
        if not tool_calls:
            return f"Iteration {iteration}: continuing reasoning without explicit notes."
        tool_names: List[str] = []
        for call in tool_calls:
            name = (
                call.get("function", {})
                if isinstance(call, dict)
                else {}
            )
            if isinstance(name, dict):
                fn = name.get("name")
            else:
                fn = None
            if not fn and isinstance(call, dict):
                fn = call.get("name")
            if fn:
                tool_names.append(fn)
        deduped = []
        for name in tool_names:
            if name not in deduped:
                deduped.append(name)
        if not deduped:
            return f"Iteration {iteration}: planning next action."
        tools_text = ", ".join(deduped)
        return (
            f"Planning to call {tools_text} based on the previous observation set; "
            "goal is to close remaining evidence gaps."
        )

    def _summarize_action(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Create a concise action summary."""
        if not params:
            return f"Executing {tool_name}"
        try:
            preview = json.dumps(params, ensure_ascii=False)[:200]
        except Exception:
            preview = str(params)[:200]
        return f"Executing {tool_name} with {preview}"

    def _infer_result_count(self, tool_output: Dict[str, Any]) -> int:
        """Best-effort count of returned items."""
        for key in ("results", "papers", "repositories"):
            items = tool_output.get(key)
            if isinstance(items, list):
                return len(items)
        if "total_found" in tool_output:
            try:
                return int(tool_output["total_found"])
            except (TypeError, ValueError):
                return 0
        return 0

    def _derive_tool_policy(self, query: str) -> Dict[str, Any]:
        """Derive initial tool allowances based on the query."""
        text = (query or "").lower()
        allow_github = any(keyword in text for keyword in self.GITHUB_KEYWORDS)
        allow_arxiv = any(keyword in text for keyword in self.ARXIV_KEYWORDS)

        technical_signals = [
            "ai",
            "ml",
            "machine learning",
            "deep learning",
            "data science",
            "rag",
            "retrieval augmented",
            "neural",
            "model",
            "algorithm",
        ]
        if any(signal in text for signal in technical_signals):
            allow_github = True
            allow_arxiv = True

        policy = {
            "allow_github": allow_github,
            "allow_arxiv": allow_arxiv,
            "default_tool": "arxiv_search"
            if allow_arxiv and not allow_github
            else "web_search",
            "sufficient_result_count": 5 if allow_arxiv else 4,
            "sparse_result_threshold": 2,
        }
        return policy

    def _detect_recency_intent(self, query: str) -> str:
        """Rudimentary recency classifier: 'fresh', 'historical', or 'general'."""
        evergreen_signals = ["history", "timeline", "origin", "evolution", "since", "from "]
        fresh_signals = [
            "latest",
            "recent",
            "202",
            self.current_year,
            "today",
            "this year",
            "upcoming",
            "roadmap",
            "forecast",
            "trend",
            "2024",
        ]
        q = (query or "").lower()
        if any(sig in q for sig in fresh_signals):
            return "fresh"
        if any(sig in q for sig in evergreen_signals):
            return "historical"
        return "general"

    def _preferred_date_filter(self, recency_intent: str) -> Optional[str]:
        """Map recency signal to a default date_filter hint."""
        if recency_intent == "fresh":
            return "month"
        return None

    def _build_tool_policy_message(self, policy: Dict[str, Any], recency_intent: str) -> str:
        """Create a natural-language reminder about tool heuristics."""
        hints: List[str] = [
            "Tool routing guidance: default to web_search for broad discovery."
        ]
        if recency_intent == "fresh":
            hints.append(
                "This topic appears time-sensitive. Prefer web_search with date_filter='week' or 'month' to capture the latest developments before using other tools."
            )
        elif recency_intent == "historical":
            hints.append(
                "This topic reads as historical; avoid forcing recency filters unless explicitly requested and focus on core context."
            )
        if policy.get("default_tool") == "arxiv_search":
            hints.append(
                "The topic reads as academic, so consider starting with arxiv_search before general web coverage."
            )
        if not policy.get("allow_github", True):
            hints.append(
                "Skip github_search unless you explicitly see references to implementations, repositories, benchmarks, or SDKs."
            )
        if not policy.get("allow_arxiv", True):
            hints.append(
                "Use arxiv_search only if later evidence shows a clear need for scholarly or scientific sources."
            )
        return " ".join(hints)

    def _is_tool_allowed(
        self, tool_name: str, thought: str, action_input: Dict[str, Any]
    ) -> tuple[bool, str]:
        """Apply heuristic gating for specialized tools."""
        if tool_name == "github_search":
            allow_key = "allow_github"
            keywords = self.GITHUB_KEYWORDS
            block_message = (
                "Tool routing heuristic: stay on web_search or arxiv_search until you "
                "discover a concrete need for code repositories, implementations, libraries, or benchmarks."
            )
        elif tool_name == "arxiv_search":
            allow_key = "allow_arxiv"
            keywords = self.ARXIV_KEYWORDS
            block_message = (
                "Tool routing heuristic: this topic has not been identified as academic yet. "
                "Gather more context via web_search unless you uncover explicit scholarly cues."
            )
        else:
            return True, ""

        allowed = self.tool_policy.get(allow_key, True)
        if allowed:
            return True, ""
        if self._tool_denials.get(tool_name, 0) >= 1:
            return True, ""
        if self._thought_allows_tool(thought, keywords):
            self.tool_policy[allow_key] = True
            return True, ""

        self._tool_denials[tool_name] = self._tool_denials.get(tool_name, 0) + 1
        return False, block_message

    def _thought_allows_tool(self, thought: Optional[str], keywords: set[str]) -> bool:
        """Check if the agent explicitly reasoned about a tool-worthy need."""
        if not thought:
            return False
        lowered = thought.lower()
        return any(keyword in lowered for keyword in keywords)

    def _handle_sparse_web_results(
        self,
        conversation_history: List[Dict[str, Any]],
        query: Optional[str],
        result_count: int,
    ) -> None:
        """Inject guidance when web_search returns too little evidence."""
        threshold = max(1, int(self.tool_policy.get("sparse_result_threshold", 2)))
        if result_count is None or result_count > threshold:
            return
        if not query or self._last_sparse_query == query:
            return

        recency_hint = ""
        if self.recency_intent == "fresh":
            recency_hint = (
                " Because the topic is time-sensitive, try setting date_filter='week' or 'month' "
                f"or adding words like 'latest'/'{self.current_year}' if explicitly required."
            )
        elif self.recency_intent == "historical":
            recency_hint = " Stick with the historical framing; avoid forcing current-year filters unless specified."

        guidance = (
            f"Web search for \"{query}\" returned only {result_count} relevant results. "
            "Refine the query with more specific keywords, synonyms, recency filters, or site/domain operators "
            "and run web_search again before moving on."
            + recency_hint
        )
        conversation_history.append({"role": "system", "content": (self._normalize_for_windows(guidance) if self.ascii_prompts else guidance)})
        self._last_sparse_query = query

    def _maybe_mark_sufficient_evidence(
        self, tool_name: str, result_count: int, iteration: int
    ) -> None:
        """Mark when early evidence is already rich enough to skip coverage nudges."""
        if self.early_evidence_sufficient:
            return
        try:
            count = int(result_count)
        except (TypeError, ValueError):
            return
        min_results = max(3, int(self.tool_policy.get("sufficient_result_count", 5)))
        default_tool = self.tool_policy.get("default_tool", "web_search")
        if (
            count >= min_results
            and iteration <= 3
            and tool_name in {default_tool, "web_search", "arxiv_search"}
        ):
            self.early_evidence_sufficient = True
            logger.info(
                "[ResearcherAgent] Early evidence threshold met; domain coverage nudges disabled."
            )

    async def _run_finish_guard(
        self, query: str, finish_args: Dict[str, Any], iteration: int
    ) -> tuple[bool, str, Optional[str]]:
        """Run a lightweight critic before honoring the finish call."""
        report = finish_args.get("report", "") or ""
        sources = finish_args.get("sources", []) or []
        report_excerpt = report[:4000]
        sources_excerpt = "\n".join(f"- {src}" for src in sources[:12]) or "None provided"

        guard_prompt = self.FINISH_GUARD_PROMPT + (
            "\n\nQuery:\n" + query + "\n\nDraft report:\n" + report_excerpt + "\n\nSources:\n" + sources_excerpt
        )

        messages = [
            {"role": "system", "content": "You are a critical reviewer deciding if the report can finish."},
            {"role": "user", "content": guard_prompt},
        ]

        try:
            response = await self.llm.complete(
                messages=messages,
                temperature=0.2,
                max_tokens=400,
                require_content=True,
            )
            decision = self._parse_guard_response(response.get("content"))
        except Exception as exc:
            logger.warning(f"Finish guard failed: {exc}")
            return True, "Finish guard unavailable; proceeding.", None

        allow_finish = decision.get("allow_finish")
        if allow_finish is None:
            allow_finish = True
        feedback = decision.get("feedback") or (
            "Coverage looks solid; ready to finalize." if allow_finish else ""
        )
        hint = decision.get("next_action_hint")
        return bool(allow_finish), feedback, hint

    def _parse_guard_response(self, content: Optional[str]) -> Dict[str, Any]:
        """Parse JSON guard response, tolerating fenced blocks."""
        if not content:
            return {}

        def try_parse(candidate: str) -> Optional[Dict[str, Any]]:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return None

        parsed = try_parse(content.strip())
        if parsed is not None:
            return parsed

        if "```" in content:
            segments = content.split("```")
            for segment in segments:
                segment = segment.strip()
                if not segment:
                    continue
                if segment.lower().startswith("json"):
                    segment = segment[4:].strip()
                parsed = try_parse(segment)
                if parsed is not None:
                    return parsed

        return {}
    STAGE_EVENT_MAP = {
        "iteration_start": "start->think",
        "thought": "think->act",
        "action": "act->execute",
        "tool_execution": "execute->evaluate",
        "observation": "execute->evaluate",
        "finish": "evaluate->finish",
    }
