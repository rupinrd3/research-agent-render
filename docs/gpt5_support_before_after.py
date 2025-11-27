"""
Snapshots of code that must change to enable ChatGPT-5 (Responses API) support.

Each entry captures the current code ("before") and the proposed replacement
("after") for the specific file/path section that needs to be edited.
"""

SNAPSHOTS = [
    {
        "file": "backend/app/llm/openai_provider.py",
        "section": "__init__ signature and defaults",
        "before": '''
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
''',
        "after": '''
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-nano",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-5-nano)
            temperature: Preferred default temperature
            max_tokens: Legacy chat.completions token budget
            max_output_tokens: Responses API max token budget
            reasoning_effort: Optional reasoning effort override
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.is_gpt5 = model.startswith("gpt-5")
        self.default_temperature = (
            1.0 if self.is_gpt5 else (temperature if temperature is not None else 0.7)
        )
        self.default_max_tokens = max_tokens
        self.default_max_output_tokens = max_output_tokens
        self.reasoning_effort = reasoning_effort
''',
    },
    {
        "file": "backend/app/llm/openai_provider.py",
        "section": "complete() implementation",
        "before": '''
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        ...
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

            if tools:
                kwargs["tools"] = tools
                if tool_choice is not None:
                    kwargs["tool_choice"] = tool_choice
                else:
                    kwargs["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**kwargs)
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
''',
        "after": '''
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        try:
            effective_temperature = (
                temperature if temperature is not None else self.default_temperature
            )
            if self.is_gpt5:
                effective_temperature = 1.0

            token_budget = max_tokens
            if token_budget is None:
                token_budget = (
                    self.default_max_output_tokens
                    if self.is_gpt5
                    else self.default_max_tokens
                )

            if self.is_gpt5 and self.default_max_output_tokens:
                token_budget = min(token_budget, self.default_max_output_tokens)
            elif (not self.is_gpt5) and token_budget is None:
                token_budget = self.default_max_tokens

            if self.is_gpt5:
                kwargs = {
                    "model": self.model,
                    "temperature": effective_temperature,
                    "modalities": ["text"],
                    "parallel_tool_calls": True,
                    "input": [
                        {
                            "role": msg["role"],
                            "content": [{"type": "text", "text": msg["content"]}],
                        }
                        for msg in messages
                    ],
                }
                if token_budget:
                    kwargs["max_output_tokens"] = token_budget
                kwargs["reasoning"] = {
                    "effort": self.reasoning_effort or "medium",
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = tool_choice or "auto"

                response = await self.client.responses.create(**kwargs)
                text_parts: List[str] = []
                tool_calls: List[Dict[str, Any]] = []
                finish_reason = None
                for item in getattr(response, "output", []):
                    item_type = getattr(item, "type", None)
                    if item_type == "message":
                        for block in getattr(item, "content", []):
                            if getattr(block, "type", None) == "text":
                                text_value = getattr(block, "text", "")
                                text_parts.append(str(text_value))
                            finish_reason = finish_reason or getattr(
                                block, "finish_reason", None
                            )
                    elif item_type == "tool_call":
                        fn = getattr(item, "function", None)
                        tool_calls.append(
                            {
                                "id": getattr(item, "id", None),
                                "type": "function",
                                "function": {
                                    "name": getattr(fn, "name", ""),
                                    "arguments": getattr(fn, "arguments", ""),
                                }
                                if fn
                                else {},
                            }
                        )
                content_text = "\n".join(part for part in text_parts if part)
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            else:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": effective_temperature,
                }
                if token_budget:
                    kwargs["max_tokens"] = token_budget
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = tool_choice or "auto"

                response = await self.client.chat.completions.create(**kwargs)
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
                finish_reason = response.choices[0].finish_reason
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return {
                "content": content_text,
                "tool_calls": tool_calls or [],
                "finish_reason": finish_reason,
                "usage": usage,
                "model": self.model,
                "provider": "openai",
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
''',
    },
    {
        "file": "backend/app/config/settings.py",
        "section": "LLMConfig fields + llm config builder",
        "before": '''
class LLMConfig(BaseModel):
    """LLM provider configuration."""

    api_key: Optional[str] = None
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    max_completion_tokens: Optional[int] = None
    reasoning_effort: Optional[str] = None
    alternate_models: List[str] = Field(default_factory=list)

...

    if settings.llm.openai and settings.llm.openai.api_key:
        llm_config["openai"] = {
            "api_key": settings.llm.openai.api_key,
            "model": settings.llm.openai.model,
        }
        if settings.llm.openai.temperature is not None:
            llm_config["openai"]["temperature"] = settings.llm.openai.temperature
        if settings.llm.openai.max_tokens is not None:
            llm_config["openai"]["max_tokens"] = settings.llm.openai.max_tokens
        if settings.llm.openai.max_completion_tokens is not None:
            llm_config["openai"]["max_completion_tokens"] = (
                settings.llm.openai.max_completion_tokens
            )
        if settings.llm.openai.reasoning_effort:
            llm_config["openai"]["reasoning_effort"] = (
                settings.llm.openai.reasoning_effort
            )
''',
        "after": '''
class LLMConfig(BaseModel):
    """LLM provider configuration."""

    api_key: Optional[str] = None
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    max_output_tokens: Optional[int] = None
    reasoning_effort: Optional[str] = None
    alternate_models: List[str] = Field(default_factory=list)

...

    if settings.llm.openai and settings.llm.openai.api_key:
        llm_config["openai"] = {
            "api_key": settings.llm.openai.api_key,
            "model": settings.llm.openai.model,
        }
        if settings.llm.openai.temperature is not None:
            llm_config["openai"]["temperature"] = settings.llm.openai.temperature
        if settings.llm.openai.max_tokens is not None:
            llm_config["openai"]["max_tokens"] = settings.llm.openai.max_tokens
        if settings.llm.openai.max_output_tokens is not None:
            llm_config["openai"]["max_output_tokens"] = (
                settings.llm.openai.max_output_tokens
            )
        if settings.llm.openai.reasoning_effort:
            llm_config["openai"]["reasoning_effort"] = (
                settings.llm.openai.reasoning_effort
            )
''',
    },
    {
        "file": "backend/app/llm/manager.py",
        "section": "OpenAI provider instantiation",
        "before": '''
        if config.get("openai"):
            openai_cfg = config["openai"]
            self.providers[LLMProvider.OPENAI] = OpenAIProvider(
                api_key=openai_cfg["api_key"],
                model=openai_cfg.get("model", "gpt-5-nano"),
                temperature=openai_cfg.get("temperature"),
                max_tokens=openai_cfg.get("max_tokens"),
                max_completion_tokens=openai_cfg.get("max_completion_tokens"),
            )
''',
        "after": '''
        if config.get("openai"):
            openai_cfg = config["openai"]
            self.providers[LLMProvider.OPENAI] = OpenAIProvider(
                api_key=openai_cfg["api_key"],
                model=openai_cfg.get("model", "gpt-5-nano"),
                temperature=openai_cfg.get("temperature"),
                max_tokens=openai_cfg.get("max_tokens"),
                max_output_tokens=openai_cfg.get("max_output_tokens"),
                reasoning_effort=openai_cfg.get("reasoning_effort"),
            )
''',
]


def print_snapshots() -> None:
    """Utility helper for quickly dumping all before/after sections."""
    for entry in SNAPSHOTS:
        print(f"=== {entry['file']} :: {entry['section']} ===")
        print("\n[BEFORE]\n")
        print(entry["before"].strip())
        print("\n[AFTER]\n")
        print(entry["after"].strip())
        print("\n")


if __name__ == "__main__":
    print_snapshots()
