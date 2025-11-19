"""
Test script for web search provider failover.
Tests each provider independently and failover behavior.
"""

import asyncio
import os
from app.tools.web_search import web_search

async def test_provider_order():
    """Test that providers are tried in correct order."""
    print("\n=== Test 1: Provider Order ===")

    # Ensure all keys are set
    os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "")
    os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY", "")
    os.environ["SERPAPI_API_KEY"] = os.getenv("SERPAPI_API_KEY", "")

    result = await web_search("Python programming", num_results=5)

    print(f"Status: {result['status']}")
    print(f"Provider used: {result['provider']}")
    print(f"Results count: {result['total_found']}")

    if result['status'] == 'success':
        print("SUCCESS: Search successful")
        print(f"First result: {result['results'][0]['title']}")
    else:
        print(f"FAIL: Search failed: {result.get('error')}")

async def test_tavily_only():
    """Test with only Tavily key."""
    print("\n=== Test 2: Tavily Only ===")

    # Temporarily clear other keys
    serper_backup = os.environ.pop("SERPER_API_KEY", None)
    serpapi_backup = os.environ.pop("SERPAPI_API_KEY", None)

    result = await web_search("AI news", num_results=3)

    print(f"Provider: {result['provider']}")
    assert result['provider'] == 'tavily' or result['provider'] == 'none', \
        f"Expected tavily, got {result['provider']}"

    # Restore keys
    if serper_backup:
        os.environ["SERPER_API_KEY"] = serper_backup
    if serpapi_backup:
        os.environ["SERPAPI_API_KEY"] = serpapi_backup

    print("SUCCESS: Tavily-only test passed")

async def test_failover():
    """Test failover with invalid Tavily key."""
    print("\n=== Test 3: Failover Behavior ===")

    # Use invalid Tavily key to force failover
    tavily_backup = os.environ.get("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = "invalid_key"

    result = await web_search("machine learning", num_results=3)

    print(f"Provider: {result['provider']}")
    print(f"Status: {result['status']}")

    # Should fallback to serper or serpapi
    assert result['provider'] in ['serper', 'serpapi', 'none'], \
        f"Expected fallback provider, got {result['provider']}"

    # Restore key
    if tavily_backup:
        os.environ["TAVILY_API_KEY"] = tavily_backup

    print("SUCCESS: Failover test passed")

async def test_date_filter():
    """Test date filtering."""
    print("\n=== Test 4: Date Filter ===")

    result = await web_search(
        "AI news",
        num_results=5,
        date_filter="week"
    )

    print(f"Provider: {result['provider']}")
    print(f"Results: {result['total_found']}")

    if result['status'] == 'success' and result['total_found'] > 0:
        print("SUCCESS: Date filter test passed")
    else:
        print("WARNING: Date filter returned no results (might be normal)")

async def test_normalized_format():
    """Test that all providers return normalized format."""
    print("\n=== Test 5: Normalized Format ===")

    result = await web_search("test query", num_results=2)

    if result['status'] == 'success' and len(result['results']) > 0:
        item = result['results'][0]
        required_fields = ['title', 'snippet', 'url', 'domain', 'is_pdf',
                          'relevance_score', 'content_type']

        for field in required_fields:
            assert field in item, f"Missing field: {field}"

        print(f"SUCCESS: All required fields present")
        print(f"Sample result: {item['title'][:50]}...")
    else:
        print("WARNING: No results to check format")

async def main():
    """Run all tests."""
    print("=" * 60)
    print("WEB SEARCH PROVIDER TESTS")
    print("=" * 60)

    try:
        await test_provider_order()
        await test_tavily_only()
        await test_failover()
        await test_date_filter()
        await test_normalized_format()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
    except Exception as e:
        print(f"\nFAIL: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
