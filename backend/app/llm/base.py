"""
Base LLM Provider

Abstract base class defining the interface for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM provider types."""

    OPENAI = "openai"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    This class defines the interface that all LLM providers must implement,
    ensuring consistent behavior across different providers.
    """

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate completion with optional tool calling support.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict containing:
                - content: Generated text
                - tool_calls: Tool calls if requested
                - finish_reason: Why generation stopped
                - usage: Token usage statistics
                - model: Model name used
                - provider: Provider name
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using provider's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get current model name.

        Returns:
            Model identifier string
        """
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost in USD for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pass
