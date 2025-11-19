import pytest

from app.llm.manager import LLMManager


class _BaseStubProvider:
    def __init__(self, *_, **__):
        pass

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0


class EmptyProvider(_BaseStubProvider):
    async def complete(self, messages, tools, temperature, max_tokens, tool_choice=None):
        return {
            "content": "",
            "tool_calls": None,
            "usage": {"input_tokens": 1, "output_tokens": 0, "total_tokens": 1},
            "model": "empty-model",
            "provider": "stub",
        }


class GoodProvider(_BaseStubProvider):
    async def complete(self, messages, tools, temperature, max_tokens, tool_choice=None):
        return {
            "content": "ok",
            "tool_calls": None,
            "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            "model": "good-model",
            "provider": "stub",
        }


@pytest.mark.asyncio
async def test_llm_manager_falls_back_when_content_empty(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-gemini")

    monkeypatch.setattr("app.llm.manager.OpenAIProvider", EmptyProvider)
    monkeypatch.setattr("app.llm.manager.GeminiProvider", GoodProvider)

    manager = LLMManager(
        {
            "primary": "openai",
            "fallback_order": ["gemini"],
            "openai": {"api_key": "test-openai", "model": "empty"},
            "gemini": {"api_key": "test-gemini", "model": "good"},
        }
    )

    response = await manager.complete(
        messages=[{"role": "user", "content": "test"}],
        temperature=0.3,
        max_tokens=10,
        require_content=True,
    )

    assert response["content"] == "ok"
    assert response["provider_used"] == "gemini"
