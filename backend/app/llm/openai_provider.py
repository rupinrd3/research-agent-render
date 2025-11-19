"""
OpenAI Provider

Implements the BaseLLMProvider interface for OpenAI's API.
"""

import logging
from typing import Dict, Any, List, Optional
import tiktoken
from openai import AsyncOpenAI, BadRequestError

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider with configurable model support.

    Supports GPT and other OpenAI models with
    automatic token counting and cost estimation.
    """

    # Pricing per 1M tokens (placeholder estimates, update when official rates change)
    PRICING = {
        "gpt-5-nano": {"input": 0.10, "output": 0.40},
        "gpt-5-mini": {"input": 0.25, "output": 1.00},
        "gpt-5": {"input": 1.00, "output": 5.00},
    }

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-nano",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
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
        self.reasoning_effort = None  # Responses API only; chat.completions ignores

        # Initialize tokenizer for accurate token counting
        encoding_hint = "o200k_base" if self.is_gpt5 else "cl100k_base"
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            try:
                self.encoding = tiktoken.get_encoding(encoding_hint)
                logger.warning(
                    "Model %s not found in tiktoken, using %s",
                    model,
                    encoding_hint,
                )
            except KeyError:
                self.encoding = tiktoken.get_encoding("cl100k_base")
                logger.warning(
                    "Model %s not found in tiktoken, using cl100k_base fallback",
                    model,
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
        try:
            effective_temperature = (
                temperature if temperature is not None else self.default_temperature
            )
            if self.is_gpt5 and abs(effective_temperature - 1.0) > 1e-6:
                logger.info(
                    "gpt-5 models require temperature=1.0. "
                    "Overriding requested temperature %.2f → 1.0.",
                    effective_temperature,
                )
                effective_temperature = 1.0

            token_budget = max_tokens or self.default_max_tokens
            if self.is_gpt5:
                if (
                    self.default_max_completion_tokens
                    and token_budget
                    and token_budget > self.default_max_completion_tokens
                ):
                    token_budget = self.default_max_completion_tokens
            elif self.default_max_tokens and token_budget is None:
                token_budget = self.default_max_tokens

            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": effective_temperature,
            }

            if token_budget:
                token_param = (
                    "max_completion_tokens" if self.is_gpt5 else "max_tokens"
                )
                kwargs[token_param] = token_budget

            # Add tools if provided
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
                if (
                    "max_completion_tokens" in error_message
                    and "max_tokens" in kwargs
                ):
                    logger.info(
                        "OpenAI model %s requires 'max_completion_tokens'; retrying request",
                        self.model,
                    )
                    kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
                    response = await self.client.chat.completions.create(**kwargs)
                else:
                    raise

            # Extract tool calls if present
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

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using OpenAI's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def get_model_name(self) -> str:
        """
        Get current model name.

        Returns:
            Model identifier string
        """
        return self.model

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost in USD for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
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

    def _normalize_message_content(self, content) -> str:
        """
        Convert OpenAI message content payloads to a single string.
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
        return str(content)
