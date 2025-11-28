"""
OpenAI Provider

Implements the BaseLLMProvider interface for OpenAI's API.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import tiktoken
from openai import AsyncOpenAI, BadRequestError

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider with configurable model support.

    Supports GPT and other OpenAI models with automatic token counting and cost estimation.
    """

    # Pricing per 1M tokens (official OpenAI pricing snapshot)
    PRICING = {
        # GPT-5 family
        "gpt-5.1": {"input": 1.25, "output": 10.00},
        "gpt-5": {"input": 1.25, "output": 10.00},
        "gpt-5-mini": {"input": 0.25, "output": 2.00},
        "gpt-5-nano": {"input": 0.05, "output": 0.40},
        "gpt-5.1-chat-latest": {"input": 1.25, "output": 10.00},
        "gpt-5-chat-latest": {"input": 1.25, "output": 10.00},
        "gpt-5.1-codex": {"input": 1.25, "output": 10.00},
        "gpt-5-codex": {"input": 1.25, "output": 10.00},
        "gpt-5-pro": {"input": 15.00, "output": 120.00},
        # GPT-4.1 family
        "gpt-4.1": {"input": 2.00, "output": 8.00},
        "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
        "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
        # GPT-4o family
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-nano",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-5-nano)
            temperature: Preferred default temperature
            max_tokens: Legacy max token budget
            max_completion_tokens: Responses API max token budget
            reasoning_effort: Optional reasoning effort override
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.is_gpt5 = model.startswith("gpt-5")
        self.default_temperature = (
            1.0 if self.is_gpt5 else (temperature if temperature is not None else 0.7)
        )
        self.default_max_tokens = max_tokens
        self.default_max_completion_tokens = max_completion_tokens
        if self.is_gpt5:
            self.reasoning_effort = reasoning_effort or "low"
        else:
            self.reasoning_effort = reasoning_effort

        # Initialize tokenizer for accurate token counting
        encoding_hint = "o200k_base" if self.is_gpt5 else "cl100k_base"
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            try:
                self.encoding = tiktoken.get_encoding(encoding_hint)
                logger.warning(
                    "Model %s not found in tiktoken, using %s", model, encoding_hint
                )
            except KeyError:
                self.encoding = tiktoken.get_encoding("cl100k_base")
                logger.warning(
                    "Model %s not found in tiktoken, using cl100k_base fallback", model
                )

        logger.info(f"Initialized OpenAI provider with model: {model}")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate completion using OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict containing completion result and metadata

        Raises:
            Exception: If API call fails
        """
        if self.is_gpt5:
            return await self._complete_responses_api(
                messages, tools, temperature, max_tokens, tool_choice
            )
        return await self._complete_chat_completions(
            messages, tools, temperature, max_tokens, tool_choice
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens using OpenAI's tokenizer."""
        return len(self.encoding.encode(text))

    def get_model_name(self) -> str:
        """Get current model name."""
        return self.model

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for given token usage."""
        model_key = self.model.split(":")[0]
        if model_key not in self.PRICING and "-" in model_key:
            base, maybe_version = model_key.rsplit("-", 1)
            if maybe_version.replace(".", "").isdigit():
                model_key = base
        pricing = self.PRICING.get(model_key, self.PRICING.get("gpt-5-mini"))
        if not pricing:
            pricing = {"input": 0.25, "output": 1.0}
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    async def _complete_chat_completions(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
        tool_choice: Optional[Any],
    ) -> Dict[str, Any]:
        """Invoke Chat Completions API (GPT-4.x and below)."""
        effective_temperature = (
            temperature if temperature is not None else self.default_temperature
        )
        token_budget = max_tokens or self.default_max_tokens
        if self.default_max_tokens and token_budget is None:
            token_budget = self.default_max_tokens

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": effective_temperature,
        }
        if token_budget:
            kwargs["max_tokens"] = token_budget

        if tools:
            kwargs["tools"] = tools
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice
            else:
                kwargs["tool_choice"] = "auto"

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except BadRequestError as e:
            error_message = str(e)
            if "max_completion_tokens" in error_message and "max_tokens" in kwargs:
                logger.info(
                    "OpenAI model %s requires 'max_completion_tokens'; retrying request",
                    self.model,
                )
                kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
                response = await self.client.chat.completions.create(**kwargs)
            else:
                logger.error(f"OpenAI Chat API error: {e}")
                raise
        except Exception as e:
            logger.error(f"OpenAI Chat API error: {e}")
            raise

        return self._format_chat_response(response)

    async def _complete_responses_api(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
        tool_choice: Optional[Any],
    ) -> Dict[str, Any]:
        """Invoke Responses API for GPT-5 models with reasoning support."""
        if temperature is not None and abs(temperature - 1.0) > 1e-6:
            logger.info(
                "gpt-5 models require temperature=1.0. Overriding requested temperature %.2f -> 1.0",
                temperature,
            )
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "input": self._to_responses_input(messages),
            "temperature": 1.0,
        }
        if self.reasoning_effort:
            kwargs["reasoning"] = {"effort": self.reasoning_effort}
        if tools:
            kwargs["tools"] = self._convert_tools_for_responses(tools)
        if tool_choice is not None:
            kwargs["tool_choice"] = self._convert_tool_choice_for_responses(tool_choice)

        try:
            response = await self.client.responses.create(**kwargs)
        except Exception as e:
            logger.error(f"OpenAI Responses API error: {e}")
            raise

        content_text, tool_calls = self._parse_responses_output(response)
        usage = self._parse_responses_usage(response)
        finish_reason = getattr(response, "status", None) or "completed"

        return {
            "content": content_text,
            "tool_calls": tool_calls or None,
            "finish_reason": finish_reason,
            "usage": usage,
            "model": self.model,
            "provider": "openai",
        }

    def _format_chat_response(self, response: Any) -> Dict[str, Any]:
        """Normalize chat.completions response to common schema."""
        message = response.choices[0].message
        content_text = self._normalize_message_content(message.content)
        tool_calls = None
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        return {
            "content": content_text,
            "tool_calls": tool_calls,
            "finish_reason": response.choices[0].finish_reason,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "model": self.model,
            "provider": "openai",
        }

    def _normalize_message_content(self, content) -> str:
        """Convert message content payloads to a single string."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join(part for part in parts if part)
        return str(content)

    def _to_responses_input(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert Chat Completions history into Responses API input items.

        Uses message items with `input_text` parts, `function_call` for assistant tool calls,
        and `function_call_output` for tool responses.
        """
        inputs: List[Dict[str, Any]] = []
        call_id_map: Dict[str, str] = {}  # Maps original IDs to normalized IDs
        for msg in messages:
            role = msg.get("role", "user")
            normalized_text = self._normalize_message_content(msg.get("content"))

            if role == "tool":
                orig_call_id = msg.get("tool_call_id") or ""
                normalized_call_id = call_id_map.get(orig_call_id) or self._normalize_function_call_id(
                    orig_call_id or "tool_call"
                )
                call_id_map[orig_call_id] = normalized_call_id
                inputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": normalized_call_id,
                        "output": normalized_text or "",
                    }
                )
                continue

            msg_role = (
                role if role in {"user", "assistant", "system", "developer"} else "user"
            )
            content_parts: List[Dict[str, Any]] = []

            if msg_role in {"user", "system", "developer"}:
                content_parts.append(
                    {"type": "input_text", "text": normalized_text or ""}
                )
            elif msg_role == "assistant":
                if normalized_text:
                    content_parts.append(
                        {"type": "output_text", "text": normalized_text}
                    )

                # Add function_calls as content parts within the assistant message
                # This matches the Responses API output format where function_calls
                # appear inside message content, not as standalone items in input
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {}) or {}
                        orig_id = tc.get("id") or func.get("name") or "function_call"
                        normalized_id = self._normalize_function_call_id(orig_id)
                        call_id_map[orig_id] = normalized_id

                        # Parse arguments to dict format for Responses API
                        arguments = func.get("arguments", "{}")
                        if isinstance(arguments, str):
                            try:
                                arguments = json.loads(arguments)
                            except Exception:
                                logger.warning(f"Failed to parse function arguments as JSON: {arguments}")
                                arguments = {}

                        # Add function_call as a content part (not standalone item)
                        # Note: Using call_id per Responses API spec
                        content_parts.append({
                            "type": "function_call",
                            "call_id": normalized_id,
                            "name": func.get("name"),
                            "arguments": arguments
                        })

            message_item: Dict[str, Any] = {"role": msg_role}
            if content_parts:
                message_item["content"] = content_parts

            inputs.append(message_item)

        # Final pass: ensure all function_call_output IDs are normalized
        # (function_calls are now in message content, not standalone items)
        for item in inputs:
            if item.get("type") == "function_call_output":
                raw_call_id = item.get("call_id") or ""
                # Normalize the call_id to ensure consistency
                normalized_id = self._normalize_function_call_id(raw_call_id)
                item["call_id"] = normalized_id

        return inputs

    def _normalize_function_call_id(self, call_id: Optional[str]) -> str:
        """
        Normalize function call IDs for the Responses API.

        GPT-5's Responses API expects function_call IDs to start with "fc".
        We keep IDs stable but coerce them into the required shape so that
        paired function_call_output entries are accepted.
        """
        base_id = str(call_id or "function_call")
        # Replace spaces/unsafe characters to keep IDs Responses-compatible
        safe_id = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in base_id)
        if not safe_id.startswith("fc"):
            safe_id = f"fc_{safe_id}"
        return safe_id

    def _parse_responses_output(
        self, response: Any
    ) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
        """Parse Responses API output into chat-style text + tool_calls."""
        text_chunks: List[str] = []
        tool_calls: List[Dict[str, Any]] = []

        outputs = getattr(response, "output", []) or []
        for item in outputs:
            item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)

            if item_type == "message":
                content_items = getattr(item, "content", None) or (item.get("content") if isinstance(item, dict) else [])
                for part in content_items or []:
                    part_type = getattr(part, "type", None) or (part.get("type") if isinstance(part, dict) else None)
                    if part_type == "output_text":
                        text_val = getattr(part, "text", None) or (part.get("text") if isinstance(part, dict) else None)
                        if text_val:
                            text_chunks.append(text_val)
                    elif part_type in {"tool_call", "function_call"}:
                        part_data = part if isinstance(part, dict) else {}
                        arguments = part_data.get("arguments") or "{}"
                        if not isinstance(arguments, str):
                            try:
                                arguments = json.dumps(arguments)
                            except Exception:
                                arguments = str(arguments)
                        tool_calls.append(
                            {
                                "id": part_data.get("id") or part_data.get("call_id") or "function_call",
                                "type": "function",
                                "function": {
                                    "name": part_data.get("name"),
                                    "arguments": arguments,
                                },
                            }
                        )
            elif item_type == "function_call":
                name = getattr(item, "name", None) or (item.get("name") if isinstance(item, dict) else None)
                arguments = getattr(item, "arguments", None) or (item.get("arguments") if isinstance(item, dict) else None)
                call_id = getattr(item, "id", None) or getattr(item, "call_id", None)
                if isinstance(item, dict):
                    call_id = call_id or item.get("id") or item.get("call_id")
                if isinstance(arguments, (dict, list)):
                    try:
                        arguments = json.dumps(arguments)
                    except Exception:
                        arguments = str(arguments)
                tool_calls.append(
                    {
                        "id": call_id or name or "function_call",
                        "type": "function",
                        "function": {"name": name, "arguments": arguments or "{}"},
                    }
                )

        if not text_chunks and getattr(response, "output_text", None):
            text_chunks.append(getattr(response, "output_text"))

        content_text = "\n".join(chunk for chunk in text_chunks if chunk)
        return content_text, tool_calls or None

    def _convert_tools_for_responses(
        self, tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert OpenAI Chat tool defs ({'function': {...}}) to Responses function tools.
        """
        converted: List[Dict[str, Any]] = []
        for tool in tools:
            func = tool.get("function", {}) or {}
            converted.append(
                {
                    "type": "function",
                    "name": func.get("name"),
                    "description": func.get("description"),
                    "parameters": func.get("parameters"),
                }
            )
        return converted

    def _convert_tool_choice_for_responses(self, tool_choice: Any) -> Any:
        """
        Normalize Chat-style tool_choice to Responses format.
        Accepts strings ('auto', 'none'), or dicts with nested function.
        """
        if isinstance(tool_choice, dict):
            # Chat style uses {"type": "function", "function": {"name": "..."}}
            if tool_choice.get("type") == "function" or tool_choice.get("function"):
                func = tool_choice.get("function") or {}
                name = func.get("name") or tool_choice.get("name")
                return {"type": "function", "name": name}
        return tool_choice

    def _parse_responses_usage(self, response: Any) -> Dict[str, int]:
        """Extract token usage from Responses API reply."""
        usage_obj = getattr(response, "usage", None) or {}
        input_tokens = getattr(usage_obj, "input_tokens", 0) or usage_obj.get(
            "input_tokens", 0
        )
        output_tokens = getattr(usage_obj, "output_tokens", 0) or usage_obj.get(
            "output_tokens", 0
        )
        total_tokens = getattr(usage_obj, "total_tokens", None)
        if total_tokens is None:
            total_tokens = usage_obj.get("total_tokens", 0)
        if not total_tokens:
            total_tokens = (input_tokens or 0) + (output_tokens or 0)

        reasoning_tokens = 0
        output_details = getattr(usage_obj, "output_tokens_details", None)
        if output_details is None and isinstance(usage_obj, dict):
            output_details = usage_obj.get("output_tokens_details", {})
        if output_details:
            if isinstance(output_details, dict):
                reasoning_tokens = output_details.get("reasoning_tokens", 0) or 0
            else:
                reasoning_tokens = getattr(output_details, "reasoning_tokens", 0) or 0

        return {
            "input_tokens": input_tokens or 0,
            "output_tokens": output_tokens or 0,
            "total_tokens": total_tokens or ((input_tokens or 0) + (output_tokens or 0)),
            "reasoning_tokens": reasoning_tokens or 0,
        }
