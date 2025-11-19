import asyncio
from typing import List, Dict

import pytest

from app.tools import web_search as web_search_module


@pytest.mark.asyncio
async def test_web_search_prefers_primary_provider(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "primary-key")
    monkeypatch.setenv("SERPER_API_KEY", "secondary-key")
    monkeypatch.setenv("SERPAPI_API_KEY", "tertiary-key")

    async def fake_tavily(query: str, num_results: int, date_filter, api_key: str):
        assert api_key == "primary-key"
        return [
            {
                "title": "Primary result",
                "snippet": "Example",
                "url": "https://primary.example.com",
                "domain": "primary.example.com",
                "is_pdf": False,
                "relevance_score": 1.0,
                "content_type": "web_page",
            }
        ]

    monkeypatch.setattr(web_search_module, "_search_tavily", fake_tavily)

    result = await web_search_module.web_search("test query", num_results=1)

    assert result["provider"] == "tavily"
    assert result["total_found"] == 1


@pytest.mark.asyncio
async def test_web_search_falls_back_to_serper(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "primary-key")
    monkeypatch.setenv("SERPER_API_KEY", "secondary-key")
    monkeypatch.setenv("SERPAPI_API_KEY", "tertiary-key")

    async def failing_tavily(*args, **kwargs):
        raise Exception("boom")

    async def fake_serper(query: str, num_results: int, date_filter, api_key: str):
        assert api_key == "secondary-key"
        return [
            {
                "title": "Fallback result",
                "snippet": "From serper",
                "url": "https://serper.example.com",
                "domain": "serper.example.com",
                "is_pdf": False,
                "relevance_score": 0.9,
                "content_type": "web_page",
            }
        ]

    monkeypatch.setattr(web_search_module, "_search_tavily", failing_tavily)
    monkeypatch.setattr(web_search_module, "_search_serper", fake_serper)

    result = await web_search_module.web_search("fallback query", num_results=2)

    assert result["provider"] == "serper"
    assert result["total_found"] == 1


@pytest.mark.asyncio
async def test_web_search_reports_error_when_all_providers_fail(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "primary-key")
    monkeypatch.setenv("SERPER_API_KEY", "secondary-key")
    monkeypatch.setenv("SERPAPI_API_KEY", "tertiary-key")

    async def failing_provider(*args, **kwargs):
        raise Exception("unavailable")

    monkeypatch.setattr(web_search_module, "_search_tavily", failing_provider)
    monkeypatch.setattr(web_search_module, "_search_serper", failing_provider)
    monkeypatch.setattr(web_search_module, "_search_serpapi", failing_provider)

    result = await web_search_module.web_search("no results", num_results=1)

    assert result["status"] == "error"
    assert result["provider"] == "none"
