"""
Web Search Tool - Multi-Provider Implementation

Implements web search using multiple providers with automatic fallback:
1. Tavily API (primary) - Fast, AI-optimized search
2. Serper.dev (secondary) - Google search results
3. SerpAPI (tertiary) - Backup Google search

Features:
- Automatic provider failover with proper gating
- Unified response normalization across providers
- Content pipeline integration
- Comprehensive logging for debugging
- Backward compatibility with legacy parameters
"""

import logging
import os
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Import Tavily (conditional - graceful degradation if not installed)
try:
    from tavily import AsyncTavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    AsyncTavilyClient = None

from ..utils.text import extract_domain

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log Tavily availability at module load time
if not TAVILY_AVAILABLE:
    logger.warning(
        "tavily-python not installed. Tavily search will be unavailable. "
        "Install with: pip install tavily-python"
    )


# ============================================================
# MAIN SEARCH FUNCTION
# ============================================================

async def web_search(
    query: str,
    num_results: int = 10,
    date_filter: Optional[str] = None,
    content_pipeline=None,
    **kwargs  # Catch legacy parameters for backward compatibility
) -> Dict[str, Any]:
    """
    Search the web using multiple providers with automatic fallback.

    Provider priority order: Tavily → Serper.dev → SerpAPI

    The system automatically tries each provider in sequence until one succeeds.
    Providers without API keys are skipped automatically.

    Args:
        query: Search query string
        num_results: Number of results to return (1-20)
        date_filter: Time filter ('day', 'week', 'month', 'year', or None)
        content_pipeline: Optional content pipeline for processing results
        **kwargs: Legacy parameters (ignored with warning)

    Returns:
        Dict containing:
            - results: List of normalized search results
            - total_found: Total number of results
            - timestamp: Search timestamp (ISO format)
            - query: Original query
            - provider: Provider successfully used
            - status: "success" or "error"
            - pipeline_stats: Pipeline statistics (if pipeline used)
            - error: Error message (only if status="error")

    Example:
        >>> result = await web_search("Python programming", num_results=5)
        >>> print(f"Found {result['total_found']} results using {result['provider']}")
        >>> for item in result['results']:
        ...     print(f"- {item['title']}: {item['url']}")
    """
    # Ensure .env is loaded
    load_dotenv(override=False)

    # Log warning for legacy parameters
    if "provider" in kwargs or "serpapi_key" in kwargs:
        logger.warning(
            "Legacy parameters 'provider' and/or 'serpapi_key' ignored. "
            "Provider selection is now automatic."
        )

    # Validate and clamp num_results
    num_results = int(num_results)
    num_results = max(1, min(num_results, 20))

    logger.info(
        f"[WebSearch] Initiating search: query='{query}', "
        f"num_results={num_results}, date_filter={date_filter}"
    )

    # Define provider chain with their API keys from environment
    providers = [
        ("tavily", os.getenv("TAVILY_API_KEY")),
        ("serper", os.getenv("SERPER_API_KEY")),
        ("serpapi", os.getenv("SERPAPI_API_KEY")),
    ]

    provider_status = {
        name: ("configured" if api_key else "missing_api_key")
        for name, api_key in providers
    }
    logger.info("[WebSearch] Provider availability: %s", provider_status)

    raw_results = None
    provider_used = None
    last_error = None
    attempts = 0

    # Try each provider in sequence until one succeeds
    for provider_name, api_key in providers:
        attempts += 1

        # Skip provider if API key not configured
        if not api_key:
            logger.info(f"[WebSearch] Skipping {provider_name}: API key not configured")
            continue

        try:
            logger.info(
                "[WebSearch] Attempt %s/%s using provider='%s'",
                attempts,
                len(providers),
                provider_name,
            )
            logger.info(f"[WebSearch] Attempting provider: {provider_name}")

            # Route to appropriate provider implementation
            if provider_name == "tavily":
                raw_results = await _search_tavily(query, num_results, date_filter, api_key)
            elif provider_name == "serper":
                raw_results = await _search_serper(query, num_results, date_filter, api_key)
            elif provider_name == "serpapi":
                raw_results = await _search_serpapi(query, num_results, date_filter, api_key)

            # Check if results are valid (non-empty or explicitly successful)
            if raw_results and len(raw_results) > 0:
                provider_used = provider_name
                logger.info(
                    f"[WebSearch] ✓ Success with {provider_name}: "
                    f"{len(raw_results)} results retrieved"
                )
                break
            else:
                # Empty results - treat as soft failure, try next provider
                logger.warning(
                    f"[WebSearch] {provider_name} returned empty results, "
                    f"trying next provider..."
                )
                last_error = Exception(f"{provider_name} returned no results")

        except Exception as e:
            last_error = e
            logger.warning(
                f"[WebSearch] {provider_name} failed: {type(e).__name__}: {str(e)}"
            )
            # Continue to next provider
            continue

    # All providers failed or returned empty results
    if not raw_results or len(raw_results) == 0:
        logger.error(
            f"[WebSearch] All providers failed for query: '{query}' "
            f"(attempted {attempts} providers)"
        )
        error_msg = (
            f"All {attempts} search providers failed or returned no results. "
            f"Last error: {last_error}" if last_error else
            "All search providers failed or returned no results"
        )
        return {
            "results": [],
            "total_found": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "provider": "none",
            "status": "error",
            "error": error_msg,
        }

    # Process results through content pipeline if provided
    processed_results = raw_results
    pipeline_stats = None
    pipeline_notes: List[str] = []

    if content_pipeline:
        try:
            logger.info(
                f"[WebSearch] Processing {len(raw_results)} results "
                f"through content pipeline..."
            )
            pipeline_output = await content_pipeline.process_web_search_results(
                raw_results, query
            )
            processed_results = pipeline_output.get("top_items", [])
            pipeline_stats = pipeline_output.get("stats")
            pipeline_notes = pipeline_output.get("notes", [])
            logger.info(
                f"[WebSearch] Pipeline complete: "
                f"{len(raw_results)} → {len(processed_results)} results"
            )
        except Exception as e:
            logger.error(f"[WebSearch] Content pipeline failed: {e}. Using raw results.")
            # Graceful degradation: fall back to raw results
            processed_results = raw_results

    # Build response
    response = {
        "results": processed_results,
        "total_found": len(processed_results),
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "provider": provider_used,
        "status": "success",
        "notes": pipeline_notes,
    }

    if pipeline_stats:
        response["pipeline_stats"] = pipeline_stats

    logger.info(
        f"[WebSearch] Complete: {len(processed_results)} results from {provider_used}"
    )

    if processed_results:
        summary_lines = []
        for idx, result in enumerate(processed_results[:3]):
            title = result.get("title") or result.get("domain") or "untitled"
            domain = result.get("domain") or ""
            summary_lines.append(f"{idx + 1}. {title} ({domain})")
        logger.info(
            "[WebSearch] Result summary (%s): %s",
            provider_used,
            " | ".join(summary_lines),
        )
    else:
        logger.warning(
            "[WebSearch] No results returned for query='%s' despite successful provider %s",
            query,
            provider_used,
        )

    return response


# ============================================================
# PROVIDER IMPLEMENTATIONS
# ============================================================

async def _search_tavily(
    query: str,
    num_results: int,
    date_filter: Optional[str] = None,
    api_key: str = "",
) -> List[Dict[str, Any]]:
    """
    Search using Tavily API (AI-optimized search).

    Tavily provides search results specifically optimized for LLM/AI applications
    with built-in relevance scoring and content extraction.

    Args:
        query: Search query
        num_results: Number of results (1-20, Tavily supports up to 20)
        date_filter: Time filter ('day', 'week', 'month', 'year')
        api_key: Tavily API key

    Returns:
        List of normalized search results

    Raises:
        ImportError: If tavily-python package not installed
        Exception: If API request fails (timeout, auth error, rate limit, etc.)
    """
    if not TAVILY_AVAILABLE:
        raise ImportError(
            "tavily-python package not installed. "
            "Install with: pip install tavily-python"
        )

    logger.info(f"[Tavily] Searching: query='{query}', max_results={num_results}")

    # Initialize Tavily async client
    client = AsyncTavilyClient(api_key=api_key)

    # Build search parameters
    search_params = {
        "query": query,
        "max_results": num_results,
        "search_depth": "basic",  # "basic" is faster, "advanced" is more thorough
        "include_answer": False,  # We don't need LLM-generated answer
        "include_raw_content": False,  # We only need snippets
    }

    # Map date_filter to Tavily's time_range parameter
    # Tavily uses the same values: 'day', 'week', 'month', 'year'
    if date_filter:
        search_params["time_range"] = date_filter

    # Execute search with timeout
    try:
        response = await client.search(**search_params)
    except Exception as e:
        # Enhance error message for common issues
        if "401" in str(e) or "Unauthorized" in str(e):
            raise Exception(f"Invalid Tavily API key: {e}")
        elif "429" in str(e) or "rate limit" in str(e).lower():
            raise Exception(f"Tavily rate limit exceeded: {e}")
        else:
            raise Exception(f"Tavily API error: {e}")

    # Normalize results to common format
    results = []
    for idx, result in enumerate(response.get("results", [])):
        # Extract and truncate snippet
        snippet = result.get("content", "")
        if len(snippet) > 500:
            snippet = snippet[:497] + "..."

        normalized_result = {
            "title": result.get("title", ""),
            "snippet": snippet,
            "url": result.get("url", ""),
            "domain": extract_domain(result.get("url", "")),
            "is_pdf": result.get("url", "").lower().endswith(".pdf"),
            "relevance_score": result.get("score", 1.0 - (idx * 0.05)),
            "content_type": "web_page",
        }

        # Add published date if available
        if "published_date" in result and result["published_date"]:
            normalized_result["date_published"] = result["published_date"]

        results.append(normalized_result)

    logger.info(f"[Tavily] Retrieved {len(results)} results")
    return results


async def _search_serper(
    query: str,
    num_results: int,
    date_filter: Optional[str] = None,
    api_key: str = "",
) -> List[Dict[str, Any]]:
    """
    Search using Serper.dev API (Google Search Results).

    Serper.dev provides fast access to Google search results via API.
    It's faster and cheaper than traditional SERP APIs.

    Args:
        query: Search query
        num_results: Number of results (1-20)
        date_filter: Time filter ('day', 'week', 'month', 'year')
        api_key: Serper.dev API key

    Returns:
        List of normalized search results

    Raises:
        Exception: If API request fails (timeout, auth error, rate limit, etc.)
    """
    logger.info(f"[Serper] Searching: query='{query}', num={num_results}")

    # Build request payload
    payload = {
        "q": query,
        "num": num_results,
        "gl": "us",  # Geographic location (United States)
        "hl": "en",  # Language (English)
    }

    # Map date_filter to Serper's tbs parameter
    # Google's tbs format: qdr:d (day), qdr:w (week), qdr:m (month), qdr:y (year)
    if date_filter == "day":
        payload["tbs"] = "qdr:d"
    elif date_filter == "week":
        payload["tbs"] = "qdr:w"
    elif date_filter == "month":
        payload["tbs"] = "qdr:m"
    elif date_filter == "year":
        payload["tbs"] = "qdr:y"

    # Make POST request to Serper.dev
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise Exception(f"Invalid Serper.dev API key: {e}")
        elif e.response.status_code == 429:
            raise Exception(f"Serper.dev rate limit exceeded: {e}")
        else:
            raise Exception(f"Serper.dev HTTP error {e.response.status_code}: {e}")
    except httpx.TimeoutException:
        raise Exception("Serper.dev request timeout after 30s")
    except Exception as e:
        raise Exception(f"Serper.dev API error: {e}")

    # Extract organic results
    organic_results = data.get("organic", [])

    # Normalize results to common format
    results = []
    for idx, result in enumerate(organic_results[:num_results]):
        normalized_result = {
            "title": result.get("title", ""),
            "snippet": result.get("snippet", ""),
            "url": result.get("link", ""),
            "domain": extract_domain(result.get("link", "")),
            "is_pdf": result.get("link", "").lower().endswith(".pdf"),
            "relevance_score": 1.0 - (idx * 0.05),
            "content_type": "web_page",
        }

        # Add date if available (Serper returns relative dates like "2 days ago")
        if "date" in result and result["date"]:
            normalized_result["date_published"] = result["date"]

        results.append(normalized_result)

    logger.info(f"[Serper] Retrieved {len(results)} results")
    return results


async def _search_serpapi(
    query: str,
    num_results: int,
    date_filter: Optional[str] = None,
    api_key: str = "",
) -> List[Dict[str, Any]]:
    """
    Search using SerpAPI (Google Search).

    SerpAPI is a well-established SERP API provider with comprehensive
    Google search result parsing.

    Args:
        query: Search query
        num_results: Number of results (1-20)
        date_filter: Time filter ('day', 'week', 'month', 'year')
        api_key: SerpAPI key

    Returns:
        List of normalized search results

    Raises:
        Exception: If API request fails (timeout, auth error, rate limit, etc.)
    """
    logger.info(f"[SerpAPI] Searching: query='{query}', num={num_results}")

    # Map date_filter to SerpAPI's tbs parameter
    tbs_param = None
    if date_filter == "day":
        tbs_param = "qdr:d"
    elif date_filter == "week":
        tbs_param = "qdr:w"
    elif date_filter == "month":
        tbs_param = "qdr:m"
    elif date_filter == "year":
        tbs_param = "qdr:y"

    # Build request parameters
    params = {
        "q": query,
        "num": num_results,
        "api_key": api_key,
        "engine": "google",
    }

    if tbs_param:
        params["tbs"] = tbs_param

    # Make GET request to SerpAPI
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://serpapi.com/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise Exception(f"Invalid SerpAPI key: {e}")
        elif e.response.status_code == 429:
            raise Exception(f"SerpAPI rate limit exceeded: {e}")
        else:
            raise Exception(f"SerpAPI HTTP error {e.response.status_code}: {e}")
    except httpx.TimeoutException:
        raise Exception("SerpAPI request timeout after 30s")
    except Exception as e:
        raise Exception(f"SerpAPI error: {e}")

    # Extract organic results
    organic_results = data.get("organic_results", [])

    # Normalize results to common format
    results = []
    for idx, result in enumerate(organic_results[:num_results]):
        normalized_result = {
            "title": result.get("title", ""),
            "snippet": result.get("snippet", ""),
            "url": result.get("link", ""),
            "domain": extract_domain(result.get("link", "")),
            "is_pdf": result.get("link", "").lower().endswith(".pdf"),
            "relevance_score": 1.0 - (idx * 0.05),
            "content_type": "web_page",
        }

        # Add date if available
        if "date" in result and result["date"]:
            normalized_result["date_published"] = result["date"]

        results.append(normalized_result)

    logger.info(f"[SerpAPI] Retrieved {len(results)} results")
    return results
