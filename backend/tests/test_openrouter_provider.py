import asyncio
from types import SimpleNamespace

import pytest

from app.llm.openrouter_provider import OpenRouterProvider


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            from httpx import HTTPStatusError

            raise HTTPStatusError("error", request=None, response=self)

    def json(self):
        return self._payload


def _build_payload(content: str):
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": content, "tool_calls": None},
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


@pytest.mark.asyncio
async def test_openrouter_falls_back_to_alternate_model(monkeypatch):
    provider = OpenRouterProvider(
        api_key="test-key",
        model="model-a",
        alternate_models=["model-b"],
    )

    async def fake_post(_url, _headers, json):
        if json["model"] == "model-a":
            raise Exception("primary failed")
        return DummyResponse(_build_payload("secondary"))

    provider.client.post = fake_post

    response = await provider.complete(
        messages=[{"role": "user", "content": "hi"}],
        tools=None,
        temperature=0.2,
        max_tokens=10,
    )

    assert response["model"] == "model-b"
    assert response["content"] == "secondary"

    await provider.close()


@pytest.mark.asyncio
async def test_openrouter_raises_when_all_models_fail(monkeypatch):
    provider = OpenRouterProvider(
        api_key="test-key",
        model="model-a",
        alternate_models=["model-b"],
    )

    async def fake_post(*args, **kwargs):
        raise Exception("unavailable")

    provider.client.post = fake_post

    with pytest.raises(Exception):
        await provider.complete(
            messages=[{"role": "user", "content": "hi"}],
            tools=None,
            temperature=0.2,
            max_tokens=10,
        )

    await provider.close()
