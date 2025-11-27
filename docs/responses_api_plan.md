# OpenAI GPT-5 Responses API Integration Plan

## Current Behavior (baseline)
- Providers: `OpenAIProvider` uses Chat Completions for all models; `GeminiProvider` and `OpenRouterProvider` already handle their own formats.
- Agent flow: `LLMManager.complete()` forwards `messages`/`tools` to provider, expecting `{content, tool_calls, usage, model, provider}`. `ResearcherAgent` depends on tool calls for ReAct; `EvaluatorAgent` only needs plain text.
- UI: Settings modal lists OpenAI 3.5/4.x models separately from other providers; model choice is sent to backend via `/api/research/start`.

## Goals & Constraints
- Keep Chat Completions pipeline for GPT-4.x; add Responses API pipeline for GPT-5 family (`gpt-5-mini`, `gpt-5-nano`, `gpt-5.1` or other `gpt-5*`).
- Present all OpenAI models (4.x + 5.x) in a single list; backend auto-routes to the correct API based on model name.
- Maintain ReAct tool-calling compatibility and cost/usage tracking; do not break Gemini/OpenRouter.

## Design Overview
1. **Dual-path OpenAI adapter:** In `OpenAIProvider.complete`, branch on `model.startswith("gpt-5")`. Chat Completions handles GPT-4.x; a new `_complete_responses_api` handles GPT-5.
2. **Message → Responses conversion:** Convert existing OpenAI message schema to `input` for Responses:
   ```python
   def _to_responses_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
       inputs = []
       for msg in messages:
           role = msg["role"]
           parts = []
           if msg.get("content"):
               parts.append({"type": "text", "text": str(msg["content"])})
           for tc in msg.get("tool_calls", []) or []:
               parts.append({
                   "type": "tool_call",
                   "id": tc["id"],
                   "name": tc["function"]["name"],
                   "arguments": tc["function"]["arguments"],
               })
           if role == "tool":  # convert tool results
               parts = [{
                   "type": "tool_result",
                   "tool_call_id": msg.get("tool_call_id", "unknown_call"),
                   "output": msg.get("content", ""),
               }]
               role = "user"  # Responses expects tool_result paired with user
           inputs.append({"role": role, "content": parts or [{"type": "text", "text": ""}]})
       return inputs
   ```
3. **Responses call & parsing:** New helper:
   ```python
   async def _complete_responses_api(...):
       resp = await self.client.responses.create(
           model=self.model,
           input=self._to_responses_input(messages),
           tools=self._to_responses_tools(tools) if tools else None,
           reasoning={"effort": self.reasoning_effort or "medium"},
           temperature=1.0,
           max_output_tokens=max_tokens or self.default_max_completion_tokens,
       )
       content_text, tool_calls = self._parse_responses_output(resp.output)
       usage = {
           "input_tokens": resp.usage.input_tokens,
           "output_tokens": resp.usage.output_tokens,
           "total_tokens": resp.usage.total_tokens,
           "reasoning_tokens": getattr(resp.usage.output_tokens_details, "reasoning_tokens", 0),
       }
       return {"content": content_text, "tool_calls": tool_calls, "finish_reason": resp.status, "usage": usage, "model": self.model, "provider": "openai"}
   ```
   Parsing maps `tool_call` content items back to the Chat-Completions-style `{"id","type":"function","function":{"name","arguments"}}` that `ResearcherAgent` expects; text parts are concatenated.
4. **LLMManager glue:** No API break; ensure `max_tokens` is passed through as `max_output_tokens` for GPT-5 models and keep `temperature` forced to 1.0 for reasoning models. Add optional `reasoning_effort` from config to pass into `OpenAIProvider`.
5. **Config & defaults:** Keep default model `gpt-4.1-mini`. Expand allowed OpenAI models to include `gpt-5-mini`, `gpt-5-nano`, `gpt-5.1` (and future `gpt-5*`). Preserve `max_iterations=7`.
6. **UI updates:** In `LLM_PROVIDERS` for OpenAI, append the GPT-5 entries; adjust helper text to indicate GPT-5 uses the Responses API automatically. No new form fields required.

## Code Touchpoints
- `backend/app/llm/openai_provider.py`: branch logic, new Responses helpers (`_to_responses_input`, `_to_responses_tools`, `_parse_responses_output`), usage mapping for reasoning tokens, and temperature/max-output handling.
- `backend/app/llm/manager.py` and config models: accept `reasoning_effort`/`max_completion_tokens` for GPT-5; route `max_tokens` correctly.
- `frontend/src/lib/constants.ts` and related store defaults: expand OpenAI model list and keep default to `gpt-4.1-mini`.
- (Optional) `config.yaml` and `backend/config.example.yaml`: document new GPT-5 options and the Responses pipeline note.

## Testing & Validation
- Unit-level: add tests for `_parse_responses_output` to ensure tool calls/text normalization mirrors Chat Completions shape.
- Integration smoke: run a short ReAct session with `gpt-4.1-mini` (Chat) and `gpt-5-mini` (Responses) ensuring tool calls flow and final report generation works.
- UI: verify settings modal shows new models and persists selection; backend receives chosen model in `/api/research/start`.

## Risks / Open Questions
- Responses API tool-call payloads may differ slightly; confirm field names against the latest SDK and adjust parsing accordingly.
- Cost estimation for GPT-5 should surface reasoning token counts; consider exposing them in traces/metrics later.
