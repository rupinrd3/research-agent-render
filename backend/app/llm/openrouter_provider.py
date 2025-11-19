"""
OpenRouter Provider

Implements the BaseLLMProvider interface for OpenRouter's API.
Supports access to models via DeepInfra and other providers.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Set
import httpx

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter API provider.

    Provides access to various models including Nvidia's Nemotron 49B
    via DeepInfra and other providers through OpenRouter's unified API.
    """

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        "nvidia/llama-3.3-nemotron-super-49b-v1.5": {
            "input": 0.40,
            "output": 0.40,
        },
        "meta-llama/llama-3.1-70b-instruct": {
            "input": 0.35,
            "output": 0.40,
        },
        "deepseek/deepseek-r1-0528:free": {"input": 0.0, "output": 0.0},
        "minimax/minimax-m2:free": {"input": 0.0, "output": 0.0},
        "meta-llama/llama-3.3-70b-instruct:free": {"input": 0.0, "output": 0.0},
    }

    DEFAULT_MODEL_PRIORITY = [
        "deepseek/deepseek-r1-0528:free",
        "minimax/minimax-m2:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    ]

    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        alternate_models: Optional[List[str]] = None,
    ):
        """
        Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            model: Model name (default: nvidia nemotron-49b)
        """
        self.api_key = api_key
        model_priority: List[str] = []
        for candidate in [model, *(alternate_models or []), *self.DEFAULT_MODEL_PRIORITY]:
            if candidate and candidate not in model_priority:
                model_priority.append(candidate)
        self.model_priority = model_priority
        if not self.model_priority:
            raise ValueError("OpenRouter provider requires at least one model")
        self.current_model = self.model_priority[0]
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.model_failures: Dict[str, int] = {}
        self.model_cooldowns: Dict[str, datetime] = {}
        self.tool_incompatible_models: Set[str] = set()
        self.model_backoff_seconds = 300

        logger.info(
            "Initialized OpenRouter provider with models: %s",
            ", ".join(self.model_priority),
        )

    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate completion using OpenRouter API.

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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://agentic-research-lab.com",
            "X-Title": "Agentic Research Lab",
            "Content-Type": "application/json",
        }

        last_error: Optional[Exception] = None

        for model_name in self.model_priority:
            if tools and model_name in self.tool_incompatible_models:
                logger.debug(
                    "Skipping OpenRouter model %s (does not support tools)", model_name
                )
                continue
            if not self._is_model_available(model_name):
                logger.debug(
                    "Skipping OpenRouter model %s (cooldown active until %s)",
                    model_name,
                    self.model_cooldowns.get(model_name).isoformat()
                    if model_name in self.model_cooldowns
                    else "unknown",
                )
                continue
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if tools:
                payload["tools"] = tools
                if tool_choice is not None:
                    payload["tool_choice"] = tool_choice
                else:
                    payload["tool_choice"] = "auto"

            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response else "unknown"
                detail = e.response.text if e.response is not None else str(e)
                logger.warning(
                    "OpenRouter HTTP error for model %s: %s - %s",
                    model_name,
                    status,
                    detail,
                )
                if self._is_tool_unsupported(detail):
                    self._mark_tool_incompatible(model_name)
                    continue
                last_error = Exception(
                    f"OpenRouter HTTP error ({model_name}): {status}"
                )
                self._register_model_failure(model_name, last_error)
                continue
            except Exception as e:
                logger.warning(
                    "OpenRouter request failed for model %s: %s",
                    model_name,
                    e,
                )
                if self._is_tool_unsupported(str(e)):
                    self._mark_tool_incompatible(model_name)
                    continue
                last_error = e
                self._register_model_failure(model_name, last_error)
                continue

            if "choices" not in data or not data["choices"]:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                last_error = Exception(
                    f"Invalid response from OpenRouter ({model_name}): {error_msg}"
                )
                logger.warning(str(last_error))
                continue

            choice = data["choices"][0]
            message = choice.get("message", {}) or {}
            content_text = self._normalize_message_content(message.get("content"))
            if not content_text:
                fallback_text = choice.get("text") or choice.get("content")
                if fallback_text:
                    content_text = self._normalize_message_content(fallback_text)
            has_tool_calls = bool(message.get("tool_calls"))

            if tools and not message.get("tool_calls"):
                finish_reason = choice.get("finish_reason")
                if finish_reason not in ["stop", "length"]:
                    logger.warning(
                        "Model %s may not support function calling (finish_reason=%s)",
                        model_name,
                        finish_reason,
                    )

            if not content_text and not has_tool_calls:
                logger.warning(
                    "OpenRouter model %s returned empty content; trying next available model",
                    model_name,
                )
                last_error = ValueError(f"{model_name} returned empty content")
                self._register_model_failure(model_name, last_error)
                continue

            self.current_model = model_name
            self._reset_model_failure(model_name)
            return {
                "content": content_text,
                "tool_calls": message.get("tool_calls"),
                "finish_reason": choice.get("finish_reason"),
                "usage": {
                    "input_tokens": data.get("usage", {}).get(
                        "prompt_tokens", 0
                    ),
                    "output_tokens": data.get("usage", {}).get(
                        "completion_tokens", 0
                    ),
                    "total_tokens": data.get("usage", {}).get(
                        "total_tokens", 0
                    ),
                },
                "model": model_name,
                "provider": "openrouter",
            }

        if last_error:
            raise last_error
        raise Exception("OpenRouter call failed - no models available")

    def count_tokens(self, text: str) -> int:
        """
        Approximate token count for Llama-based models.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate number of tokens
        """
        # Approximate: ~3.5 characters per token for Llama models
        return int(len(text) / 3.5)

    def get_model_name(self) -> str:
        """
        Get current model name.

        Returns:
            Model identifier string
        """
        return self.current_model

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost in USD for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(
            self.current_model, {"input": 0.40, "output": 0.40}
        )
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _normalize_message_content(self, content) -> str:
        """
        Normalize OpenRouter message content into a text string.
        """
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
        if isinstance(content, dict) and "text" in content:
            return content.get("text", "")
        return str(content)

    def _is_model_available(self, model_name: str) -> bool:
        cooldown_until = self.model_cooldowns.get(model_name)
        if cooldown_until:
            if datetime.utcnow() >= cooldown_until:
                del self.model_cooldowns[model_name]
                return True
            return False
        return True

    def _register_model_failure(
        self, model_name: str, error: Union[str, Exception]
    ) -> None:
        count = self.model_failures.get(model_name, 0) + 1
        self.model_failures[model_name] = count
        if count < 2:
            return
        cooldown_until = datetime.utcnow() + timedelta(
            seconds=self.model_backoff_seconds
        )
        self.model_cooldowns[model_name] = cooldown_until
        logger.warning(
            "Temporarily disabling OpenRouter model %s for %ss after repeated failures. Last error: %s",
            model_name,
            self.model_backoff_seconds,
            error,
        )

    def _reset_model_failure(self, model_name: str) -> None:
        self.model_failures[model_name] = 0
        if model_name in self.model_cooldowns:
            del self.model_cooldowns[model_name]

    def _is_tool_unsupported(self, detail: str) -> bool:
        if not detail:
            return False
        detail_lower = detail.lower()
        keywords = [
            "tools are not supported",
            "no endpoints found that support tool use",
            "tool use not supported",
        ]
        return any(keyword in detail_lower for keyword in keywords)

    def _mark_tool_incompatible(self, model_name: str) -> None:
        logger.warning(
            "OpenRouter model %s does not support tool calls; skipping for future tool requests",
            model_name,
        )
        self.tool_incompatible_models.add(model_name)
