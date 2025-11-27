"""
LLM Manager

Manages multiple LLM providers with automatic fallback support.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .base import BaseLLMProvider, LLMProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        """
        Initialize LLM Manager with provider configuration.

        Args:
            config: Configuration dict containing provider settings
                Example:
                {
                    "primary": "openai",
                    "fallback_order": ["gemini", "openrouter"],
                    "openai": {"api_key": "...", "model": "gpt-4o-mini"},
                    "gemini": {"api_key": "...", "model": "gemini-2.5-flash"},
                    "openrouter": {"api_key": "...", "model": "..."}
                }
        """
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.primary_provider: Optional[LLMProvider] = None
        self.fallback_order: List[LLMProvider] = []
        self.provider_failure_counts = defaultdict(int)
        self.disabled_providers: Dict[LLMProvider, datetime] = {}
        self.failure_threshold = 2

        # Initialize OpenAI provider if configured
        if config.get("openai"):
            openai_cfg = config["openai"]
            self.providers[LLMProvider.OPENAI] = OpenAIProvider(
                api_key=openai_cfg["api_key"],
                model=openai_cfg.get("model", "gpt-4.1-mini"),
                temperature=openai_cfg.get("temperature"),
                max_tokens=openai_cfg.get("max_tokens"),
                max_completion_tokens=openai_cfg.get("max_completion_tokens"),
                reasoning_effort=openai_cfg.get("reasoning_effort"),
            )
            logger.info(
                f"Initialized OpenAI provider with model: "
                f"{config['openai'].get('model', 'gpt-4.1-mini')}"
            )

        # Initialize Gemini provider if configured
        if config.get("gemini"):
            self.providers[LLMProvider.GEMINI] = GeminiProvider(
                api_key=config["gemini"]["api_key"],
                model=config["gemini"].get("model", "gemini-2.5-flash"),
            )
            logger.info("Initialized Gemini provider")

        # Initialize OpenRouter provider if configured
        if config.get("openrouter"):
            self.providers[LLMProvider.OPENROUTER] = OpenRouterProvider(
                api_key=config["openrouter"]["api_key"],
                model=config["openrouter"].get(
                    "model", "nvidia/llama-3.3-nemotron-super-49b-v1.5"
                ),
                alternate_models=config["openrouter"].get("alternate_models", []),
            )
            logger.info("Initialized OpenRouter provider with Nemotron 49B")

        # Set primary and fallback providers
        primary_name = config.get("primary", "openai")
        requested_primary = LLMProvider(primary_name)

        # Validate primary provider is actually configured
        if requested_primary in self.providers:
            self.primary_provider = requested_primary
            logger.info(f"Primary provider: {self.primary_provider.value}")
        else:
            # Fall back to first available provider
            if self.providers:
                self.primary_provider = list(self.providers.keys())[0]
                logger.warning(
                    f"Requested primary provider '{primary_name}' not configured. "
                    f"Falling back to {self.primary_provider.value}. "
                    f"Check API key for {primary_name} in .env file."
                )
                print(
                    f"⚠️  PRIMARY PROVIDER '{primary_name}' NOT CONFIGURED\n"
                    f"   Using {self.primary_provider.value} instead.\n"
                    f"   Set {primary_name.upper()}_API_KEY in .env to use {primary_name}."
                )
            else:
                raise ValueError(
                    "No LLM providers configured. Set at least one API key in .env:\n"
                    "  - OPENAI_API_KEY\n"
                    "  - GOOGLE_API_KEY\n"
                    "  - OPENROUTER_API_KEY"
                )

        fallback_names = config.get("fallback_order", ["gemini", "openrouter"])
        self.fallback_order = [
            LLMProvider(p)
            for p in fallback_names
            if LLMProvider(p) in self.providers and LLMProvider(p) != self.primary_provider
        ]

        logger.info(
            f"Active providers: {[p.value for p in self.providers.keys()]}"
        )
        logger.info(
            f"Fallback order: {[p.value for p in self.fallback_order]}"
        )

    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        retry_on_failure: bool = True,
        require_content: bool = False,
        require_tool_calls: bool = False,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate completion with automatic fallback on failure.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            retry_on_failure: If True, try fallback providers on failure
            require_content: If True, treat empty text responses as failures
            require_tool_calls: Require tool calls when tools are provided
            tool_choice: Optional explicit tool selection (e.g., force a function)

        Returns:
            Dict containing:
                - content: Generated text
                - tool_calls: Tool calls if requested
                - usage: Token usage statistics
                - model: Model name used
                - provider: Provider name used
                - provider_used: Provider that successfully completed

        Raises:
            ValueError: If primary provider not configured
            Exception: If all providers fail
        """
        # Validate primary provider
        if self.primary_provider not in self.providers:
            raise ValueError(
                f"Primary provider {self.primary_provider} not configured"
            )
        if self._is_disabled(self.primary_provider):
            logger.warning(
                "Primary provider %s temporarily disabled until %s",
                self.primary_provider.value,
                self.disabled_providers[self.primary_provider].isoformat()
                if self.primary_provider in self.disabled_providers
                else "unknown",
            )

        provider_sequence = [self.primary_provider] + [
            p for p in self.fallback_order if p != self.primary_provider
        ]

        attempted: List[str] = []

        for provider_type in provider_sequence:
            if provider_type not in self.providers:
                logger.info("Provider %s not configured, skipping", provider_type.value)
                continue

            if self._is_disabled(provider_type):
                logger.warning(
                    "Provider %s disabled due to repeated failures; skipping",
                    provider_type.value,
                )
                continue

            attempted.append(provider_type.value)
            try:
                result = await self._execute_provider_call(
                    provider_type,
                    messages,
                    tools,
                    temperature,
                    max_tokens,
                    tool_choice,
                )
                if require_content and not (result.get("content") or "").strip():
                    raise ValueError(f"{provider_type.value} returned empty content")
                if require_tool_calls and tools and not result.get("tool_calls"):
                    raise ValueError(
                        f"{provider_type.value} did not return required tool calls"
                    )

                self._reset_failure(provider_type)
                result["provider_used"] = provider_type.value
                log_msg = (
                    f"Successfully completed with {provider_type.value}"
                    if provider_type == self.primary_provider
                    else f"Successfully fell back to {provider_type.value}"
                )
                logger.info(log_msg)
                print("✅ Successfully using", provider_type.value)
                return result

            except Exception as error:
                self._register_failure(provider_type, error)
                if provider_type == self.primary_provider:
                    logger.warning(
                        "Primary provider %s failed: %s",
                        provider_type.value,
                        error,
                        exc_info=True,
                    )
                    print(f"⚠️  Primary provider {provider_type.value} failed: {error}")
                else:
                    logger.warning(
                        "Fallback provider %s failed: %s",
                        provider_type.value,
                        error,
                        exc_info=True,
                    )
                    print(f"⚠️  Fallback provider {provider_type.value} failed: {error}")
                continue

        if not retry_on_failure:
            raise ValueError("All providers skipped due to configuration/disablement")

        error_msg = (
            f"All LLM providers failed. Attempted: {', '.join(attempted)}. "
            "Check API keys in .env file and network connectivity."
        )
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

    async def _execute_provider_call(
        self,
        provider_type: LLMProvider,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
        tool_choice: Optional[Any],
    ) -> Dict[str, Any]:
        provider = self.providers[provider_type]
        logger.info("Attempting completion with provider: %s", provider_type.value)
        result = await provider.complete(
            messages, tools, temperature, max_tokens, tool_choice=tool_choice
        )
        return result

    def _is_disabled(self, provider_type: LLMProvider) -> bool:
        if provider_type in self.disabled_providers:
            if datetime.utcnow() >= self.disabled_providers[provider_type]:
                del self.disabled_providers[provider_type]
                return False
            return True
        return False

    def _register_failure(self, provider_type: LLMProvider, error: Exception) -> None:
        self.provider_failure_counts[provider_type] += 1
        failure_count = self.provider_failure_counts[provider_type]
        threshold = 2 if provider_type == self.primary_provider else 3

        if failure_count >= threshold:
            cooldown = timedelta(minutes=5)
            self.disabled_providers[provider_type] = datetime.utcnow() + cooldown
            logger.warning(
                "Disabling provider %s for %s seconds after %s failures. Last error: %s",
                provider_type.value,
                int(cooldown.total_seconds()),
                failure_count,
                error,
            )

    def _reset_failure(self, provider_type: LLMProvider) -> None:
        self.provider_failure_counts[provider_type] = 0
        if provider_type in self.disabled_providers:
            del self.disabled_providers[provider_type]

    def get_provider(
        self, provider_type: LLMProvider
    ) -> Optional[BaseLLMProvider]:
        """
        Get specific provider instance.

        Args:
            provider_type: Provider type enum

        Returns:
            Provider instance or None if not configured
        """
        return self.providers.get(provider_type)

    def count_tokens(
        self, text: str, provider_type: Optional[LLMProvider] = None
    ) -> int:
        """
        Count tokens using specified provider or primary.

        Args:
            text: Text to count tokens for
            provider_type: Provider to use (defaults to primary)

        Returns:
            Number of tokens
        """
        provider_type = provider_type or self.primary_provider
        if provider_type not in self.providers:
            # Fallback to approximate counting
            return len(text) // 4
        return self.providers[provider_type].count_tokens(text)

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        provider_type: Optional[LLMProvider] = None,
    ) -> float:
        """
        Estimate cost for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider_type: Provider to use for estimation (defaults to primary)

        Returns:
            Estimated cost in USD
        """
        provider_type = provider_type or self.primary_provider
        if provider_type not in self.providers:
            return 0.0
        return self.providers[provider_type].estimate_cost(
            input_tokens, output_tokens
        )
