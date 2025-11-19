"""
Lightweight backend smoke checks that avoid external API calls.

These checks verify:
- Web search provider failover behaviour
- LLMManager fallback when primary provider returns empty content
- OpenRouter multi-model fallback logic
"""

import asyncio
import os
import sys
import types
from unittest.mock import patch


def _install_httpx_stub():
    if "httpx" in sys.modules:
        return

    class _StubAsyncClient:
        def __init__(self, *_, **__):
            pass

        async def post(self, *args, **kwargs):  # pragma: no cover - stub only
            raise NotImplementedError("httpx stub: post() should be patched in tests")

        async def aclose(self):
            return None

    class _HTTPStatusError(Exception):
        def __init__(self, message, request=None, response=None):
            super().__init__(message)
            self.request = request
            self.response = response

    stub = types.ModuleType("httpx")
    stub.AsyncClient = _StubAsyncClient
    stub.HTTPStatusError = _HTTPStatusError
    stub.TimeoutException = Exception
    sys.modules["httpx"] = stub


def _install_provider_stub(module_name: str):
    if module_name in sys.modules:
        return
    module = types.ModuleType(module_name)

    class _Placeholder:
        def __init__(self, *_, **__):
            pass

    attr_name = module_name.split(".")[-1].replace("_provider", "").capitalize() + "Provider"
    setattr(module, attr_name, _Placeholder)

    # Preserve canonical class names expected by imports
    if "openai" in module_name:
        module.OpenAIProvider = _Placeholder  # type: ignore[attr-defined]
    if "gemini" in module_name:
        module.GeminiProvider = _Placeholder  # type: ignore[attr-defined]
    sys.modules[module_name] = module


_install_httpx_stub()
_install_provider_stub("app.llm.openai_provider")
_install_provider_stub("app.llm.gemini_provider")
if "arxiv" not in sys.modules:
    sys.modules["arxiv"] = types.ModuleType("arxiv")

import importlib

web_search_module = importlib.import_module("app.tools.web_search")  # noqa: E402
from app.llm.manager import LLMManager  # noqa: E402
from app.llm.openrouter_provider import OpenRouterProvider  # noqa: E402


async def check_web_search_failover():
    os.environ["TAVILY_API_KEY"] = "primary-key"
    os.environ["SERPER_API_KEY"] = "secondary-key"
    os.environ["SERPAPI_API_KEY"] = "tertiary-key"

    async def failing_provider(*args, **kwargs):
        raise Exception("fail")

    async def serper_provider(query, num_results, date_filter, api_key):
        assert api_key == "secondary-key"
        return [
            {
                "title": "fallback",
                "snippet": "serper",
                "url": "https://serper.example.com",
                "domain": "serper.example.com",
                "is_pdf": False,
                "relevance_score": 0.9,
                "content_type": "web_page",
            }
        ]

    with patch.object(web_search_module, "_search_tavily", failing_provider), patch.object(
        web_search_module, "_search_serper", serper_provider
    ):
        result = await web_search_module.web_search("fallback test", num_results=2)

    assert result["provider"] == "serper", "Web search did not fall back to Serper.dev"


async def check_llm_manager_content_requirement():
    class EmptyProvider:
        def __init__(self, *_, **__):
            pass

        async def complete(self, *_args, **_kwargs):
            return {
                "content": "",
                "tool_calls": None,
                "usage": {"input_tokens": 1, "output_tokens": 0, "total_tokens": 1},
                "model": "empty",
                "provider": "stub",
            }

        def count_tokens(self, text):
            return len(text)

        def estimate_cost(self, *_):
            return 0.0

    class GoodProvider(EmptyProvider):
        async def complete(self, *_args, **_kwargs):
            return {
                "content": "ok",
                "tool_calls": None,
                "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                "model": "good",
                "provider": "stub",
            }

    config = {
        "primary": "openai",
        "fallback_order": ["gemini"],
        "openai": {"api_key": "test", "model": "empty"},
        "gemini": {"api_key": "test", "model": "good"},
    }

    with patch("app.llm.manager.OpenAIProvider", EmptyProvider), patch(
        "app.llm.manager.GeminiProvider", GoodProvider
    ):
        manager = LLMManager(config)
        response = await manager.complete(
            messages=[{"role": "user", "content": "hello"}],
            temperature=0.2,
            max_tokens=10,
            require_content=True,
        )

    assert response["provider_used"] == "gemini", "LLMManager did not fall back on empty output"


async def check_openrouter_model_fallback():
    provider = OpenRouterProvider(
        api_key="test",
        model="model-a",
        alternate_models=["model-b"],
    )

    async def fake_post(_url, headers=None, json=None):
        model = (json or {}).get("model")
        if model == "model-a":
            raise Exception("unavailable")
        return type(
            "Resp",
            (),
            {
                "status_code": 200,
                "text": "",
                "raise_for_status": lambda self: None,
                "json": lambda self: {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": "success", "tool_calls": None},
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
            },
        )()

    provider.client.post = fake_post

    response = await provider.complete(
        messages=[{"role": "user", "content": "hi"}],
        tools=None,
        temperature=0.2,
        max_tokens=10,
    )

    await provider.close()

    assert response["model"] == "model-b", "OpenRouterProvider did not try alternate model"


async def main():
    await check_web_search_failover()
    await check_llm_manager_content_requirement()
    await check_openrouter_model_fallback()
    print("✅ Backend smoke checks passed")


if __name__ == "__main__":
    asyncio.run(main())
