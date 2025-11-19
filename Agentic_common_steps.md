Agentic common steps- 
Planning 
Code execution
Tool Use 
Reflection 

OR
Reason - Plan - Act - Reflect - Adapt

1] REFLECTION

Evaluating reflection - 
Objective Evals - Code based evals are easier. Also build a ground truth dataset.
Subjective Evals - Use LLM as a Judge - Rubric grading (0/1 score on multiple criteria) is better. 

Reflection with External Feedback
This is much better than internal reflection
No reflection -> reflection -> reflection with external feedback. 

External feedback can be 
code execution to get the answer and then reflect
Maintain a list of competitor names. If the name appears in the answer then send instructions to suppress the competitor names. 
Tool use - Web Search or Word Count
Part 6: Multiple Tool Calls
The LLM can request multiple tools in one go:
python
# User asks: "Compare weather in Paris and Tokyo"

# LLM might output:
{
    "content": [
        {"type": "tool_use", "name": "get_weather", "input": {"city": "Paris"}},
        {"type": "tool_use", "name": "get_weather", "input": {"city": "Tokyo"}}
    ]
}

# Your code executes both, sends both results back
# LLM then compares them in its final response
________________________________________
Part 7: Why This Design?
Q: Why doesn't the LLM just execute tools directly?
A: Security and control!
●	LLMs run on remote servers - you don't want them executing arbitrary code
●	You maintain control over what functions can be called
●	You can add logging, rate limiting, error handling
●	You can validate inputs before execution
Q: Why send results back instead of LLM waiting?
A: It's stateless!
●	Each LLM request is independent
●	The conversation history is built up by YOU sending previous messages
●	This makes it scalable and easier to debug

TOOL DESIGN 
●	Keep tool docstrings short, imperative, and specific to the action.
●	Return consistent, compact JSON so the model can chain results.
●	Prefer one clear responsibility per tool (single route, single effect).


Preparing the agent prompt
Before assigning tasks to the email assistant agent, you’ll create a small helper function called build_prompt(). This function wraps the natural language request in a system-style preamble so the LLM:
●	Recognizes that it’s acting as an email assistant agent
●	Understands it has permission to use the available tools
●	Executes actions directly, without asking for confirmation (no human-in-the-loop)

3] CODE EXECUTION [ON THE FLY TOOLS]
Creating a tool for every possible activity can become cumbersome. One way to solve this is to ask LLM to write python code (like tool code), execute it using python, reflect on the answer and then use the answer. This gives more flexibility but introduces risk of rogue code. 
MODULE 4 - Practical Tips for Building Agentic AI



TWO AXES of EVALUATION 

1] Do you have per example ground truth vs no per example ground truth
2] Evaluate with code (objective) vs LLM as Judge (subjective)



Why component-level evaluations?
As Andrew mentioned in the lecture:
●	If the problem lies in web search (usually the first step in a graded lab workflow), rerunning the entire pipeline (search → draft → reflect) every time can be expensive and noisy.
●	Small improvements in web search quality may be hidden by randomness introduced by later components.
●	By evaluating the web search alone, you get a clearer signal of whether that component is improving.
Component-level evals are also efficient when multiple teams are working on different pieces of a system: each team can optimize its own component using a clear metric, without needing to run or wait for full end-to-end tests.
How do we evaluate?
Our evaluation here is objective, and so can be evaluated using code. It has an example-specific ground truth - the list of preferred sources for this black hole query. To build the eval, you will:
1.	Extract the URLs returned by Tavily.
2.	Compare them against a predefined list of preferred domains (e.g., arxiv.org, nature.com, nasa.gov).
3.	Compute the ratio of preferred vs. total results.
4.	Return a PASS/FAIL flag along with a Markdown-formatted summary.
This provides a reproducible, low-cost metric that tells us whether the research component — and only this step from the graded lab — is pulling from trusted sources.

Why this is an objective evaluation:

Each URL retrieved from Tavily is compared against a predefined list of preferred domains (TOP_DOMAINS):
• If the domain matches → ✅ PREFERRED
• Otherwise → ❌ NOT PREFERRED

This yields a clear PASS/FAIL signal depending on whether the ratio of preferred sources exceeds a given threshold. Because the ground truth (preferred vs. not preferred) is explicitly defined for each example, the evaluation is both objective and reproducible.

Evaluation Summary
<pre>
### Evaluation — Tavily Preferred Domains
- Total results: 2
- Preferred results: 2
- Ratio: 100.00%
- Threshold: 40%
- Status: ✅ PASS

**Details:**
- http://arxiv.org/abs/gr-qc/0501025v1 → ✅ PREFERRED
- http://arxiv.org/abs/1501.02937v3 → ✅ PREFERRED
</pre>


MODULE 5 – Patterns for Highly Autonomous Agents


5.2 Create and Execute Plan
The LLM needs to create a plan basis the user query
The PLAN will be formatted in JSON with [Step Number, Description, tool name, and args]

5.3 Planning with code execution
Instead of asking the LLM to output a plan in JSON format and then manually executing each step, we will allow it to write Python code that directly captures multiple steps of a plan. 

By executing this code, we can carry out complex queries automatically.

Planning with Code gives huge advantages in terms of accuracy but letting the llm write the code means unpredictable outcomes can increase. 

5.5 Multi-agentic workflows
•	Use multi-agent LLM pipelines to automate a creative workflow end-to-end.
•	Combine reasoning, tool-calling, and external data to ground your outputs in reality.
•	Apply multimodal models (like gpt-4o) that process both text and images for tasks such as generating campaign quotes.
•	Extend the model’s abilities with tools (tavily_search_tool, product_catalog_tool) so your outputs are not only imaginative but also practical.
•	Keep execution transparent and debuggable with structured logging and HTML-styled blocks.
•	Deliver a polished, executive-ready report in Markdown format that blends insights, visuals, and justifications into a single artifact.

5.6 Communication patterns for multi-agent systems

Communication Patterns:
•	Sequential / Linear
•	Hierarchical (all agents talk to one master agent)
•	Deeper Hierarchy (agents have sub agents)
•	All-to-All communication pattern






##################################################################################################################################################################





 Here’s a focused mapping of the guidance in Agentic_common_steps.md to what the app actually implements, with special attention to Evaluations and the “Two Axes” framework.

  What I Read

  - Guidance: Agentic_common_steps.md
  - Key code: backend/app/agents/react_agent.py:31, backend/app/agents/evaluator_agent.py:21, backend/app/agents/models.py:50, backend/app/tools/definitions.py:10, backend/app/api/routes/research.py:323,
    backend/app/config/settings.py:66, backend/app/database/models.py:99, backend/app/metrics/collector.py:18, backend/app/metrics/models.py:39, backend/app/content/pipeline.py:26

  Major Recommendations → Status

  - Reason-Plan-Act-Reflect-Adapt
      - Status: Implemented via ReAct loop. The researcher agent iterates thought → action (tool calls) → observation with explicit guidance to reflect after each observation (prompt-level reflection), and
        auto-finish if needed. See backend/app/agents/react_agent.py:31.
      - Notes: Reflection is “internal” (prompt discipline) rather than a separate external feedback loop.
  - Tool Use and “Multiple Tool Calls”
      - Status: Implemented. The agent can issue multiple tool calls in one assistant message and processes them sequentially with timeouts and tracing. See _execute_tool(_with_timeout) and tool-call handling
        in backend/app/agents/react_agent.py.
      - Notes: Execution is sequential (not truly parallel), but batching in one turn is supported. Domain-coverage nudges are injected to encourage breadth (web/arxiv/github) via _inject_domain_guidance.
  - Tool Design (docstrings, single responsibility, compact JSON)
      - Status: Implemented. Tool definitions are concise, imperative, and normalized. See backend/app/tools/definitions.py:10 and tools under backend/app/tools/.
      - Notes: Responses are normalized and content-pipeline-aware (processed stats, result counts, provider, etc.).
  - Security and Control of Tools
      - Status: Implemented. LLM doesn’t execute arbitrary code. It calls only whitelisted tools; the app controls inputs/outputs, timeouts, and logs/traces each call. Safe by design.
  - Preparing the Agent Prompt (role, permissions, direct execution)
      - Status: Implemented. A comprehensive system prompt instructs ReAct, tool permissions, loop discipline, and finish spec. See SYSTEM_PROMPT in backend/app/agents/react_agent.py.
  - “On-the-fly Code Execution” as a tool alternative
      - Status: Not implemented (by design). There’s no generic “execute code” tool; code execution would increase risk. The app chose safer tool usage + content pipeline.
  - Reflection with External Feedback
      - Status: Partially. The agent reflects on tool outputs (external data) and metrics are collected, but there’s no independent external validator orchestrating a reflect-then-adapt cycle (e.g., automatic
        checks that feed back instructions), aside from domain-coverage system messages.
  - Multi-agent Workflows and Communication Patterns
      - Status: Minimal. The system uses a linear two-agent flow (Researcher → Evaluator). No deeper hierarchy or all-to-all patterns. Evaluator runs once at end (no iterative back-and-forth). See backend/app/
        api/routes/research.py:323.
  - Component-level Focus (evaluate smaller steps independently)
      - Status: Reduced. The database indicates per-step evaluation existed but is deprecated in favor of end-to-end only. See save_per_step_evaluation deprecation markers in backend/app/database/database.py
        and only end-to-end persisted in backend/app/database/models.py:99.

  Evaluations: Two Axes Classification
  The doc’s 2x2 matrix:

  - Axis A: Per-example ground truth vs no ground truth
  - Axis B: Code/objective vs LLM-as-judge/subjective

  Here’s how current evaluations fit:

  - No Ground Truth + LLM-as-Judge (subjective)
      - Implemented: End-to-end quality scoring (relevance, accuracy, completeness, source quality) with rubric-like prompt; returns 0–1 scores plus strengths/weaknesses/recommendations. See backend/app/agents/
        evaluator_agent.py:21, backend/app/agents/models.py:50, backend/app/api/models/responses.py:52, invoked in backend/app/api/routes/research.py:323.
  - No Ground Truth + Code (objective)
      - Implemented: Rich operational metrics via MetricsCollector (tokens, costs, durations, tool success/failure, source diversity, citations count, etc.). See backend/app/metrics/collector.py:18, backend/
        app/metrics/models.py:39. This is “objective” analytics but not judged against ground truth.
  - Ground Truth + Code (objective)
      - Not implemented. The doc’s Tavily “Preferred Domains Ratio PASS/FAIL” example (URL/domain list threshold) is not present. No component-level PASS/FAIL against a per-example label set.
  - Ground Truth + LLM-as-Judge (subjective with references)
      - Not implemented. There’s no dataset of references and rubric-graded judging against them.

  In short: the app currently covers 2/4 buckets (No-GT/LLM-judge and No-GT/Code). Ground-truth-based evaluations (both code and judge) are missing.

  Does the App Have Better Logic Where It Diverges?

  - Skipping on-the-fly code execution: Yes, this is safer and more controllable for a production research agent. The system prefers curated tools, robust timeouts, content pipeline processing, and consistent
    JSON responses over arbitrary code execution. For many scenarios this is a preferable tradeoff.
  - External reflection: The system emphasizes tight ReAct loops, a structured content pipeline, and end-to-end LLM judging. Adding formal “external feedback” stages (e.g., automatic validations that inject
    corrective instructions) would improve reliability, but the current simplification is reasonable.

  Recommendations To Fill Missing Evaluation Buckets

  - Ground Truth + Code (component-level)
      - Web Search Preferred Domains: For a labeled set of queries, compute preferred-domain ratio and PASS/FAIL per the doc’s example. Integrate into pipeline stats and store as a component-level evaluation
        artifact. Simple to add alongside the web search tool.
      - Citation Coverage Checks: For a query with a set of canonical sources or key facts, compute coverage (exact domain matches or embedding-based nearest-neighbor match) and threshold PASS/FAIL. Store to DB
        under a “search” or “evidence” component evaluation.
      - Minimal Overhead Script: Add a scripts/eval_search_domains.py that loads N queries with preferred_domains per query, runs web search only, computes metrics, persists summary.
  - Ground Truth + LLM-as-Judge (end-to-end and/or component)
      - Small Reference Set: Build 20–50 curated examples (query → reference notes or expected key points). Ask the evaluator to grade coverage, factual alignment, and source credibility against the reference
        (0/1 or 0–1 rubric per dimension).
      - Schema: Extend evaluator prompt with “reference” context for these runs and store results in a new table or in end_to_end_evaluations with a flag for “has_reference”.
      - Where to fit: Wrap in a script that reads the dataset and runs the existing end-to-end flow, then evaluates with the augmented “with reference” judge.
  - Strengthen No Ground Truth + Code (already present)
      - Add targeted quality heuristics:
          - Domain diversity and “trusted domains” share thresholds.
          - Citations-to-claims ratio or minimum citations per section.
          - Recency thresholds on sources for time-sensitive topics.
      - Surface these as PASS/FAIL “health checks” in metrics to give actionable feedback beyond raw numbers.
  - Optional: External Feedback Reflection Loop
      - “Competitor suppression” rule from the doc: maintain a blocklist and inject corrective instructions on detection (e.g., add guidance when offending terms appear in observations or drafts).
      - “Word count” and “section completeness” checks: run post-draft code checks and feed back corrective prompts (one corrective iteration before final).

  Where This Shows Up In Code

  - Researcher Agent: ReAct implementation, multi-tool calls, reflection guidance, auto-finish, content pipeline usage, metrics/tracing hooks. See backend/app/agents/react_agent.py:31.
  - Evaluator Agent: LLM-as-judge with 4 scores and qualitative feedback. See backend/app/agents/evaluator_agent.py:21.
  - Evaluation Persistence: End-to-end evaluation model/table. See backend/app/database/models.py:99.
  - Metrics: Extensive objective instrumentation. See backend/app/metrics/collector.py:18, backend/app/metrics/models.py:39.
  - Config toggles (evaluation model): backend/app/config/settings.py:66.
  - API flow where eval runs at end: backend/app/api/routes/research.py:323.

  If you’d like, I can draft:

  - A small “preferred domains ratio” evaluator for web search (GT+Code).
  - A JSONL template and evaluator script for reference-based LLM grading (GT+Judge).
  - A couple of lightweight health checks added to MetricsCollector.