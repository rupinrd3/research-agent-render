"""Quick integration test for web_search"""
import asyncio
from app.tools.web_search import web_search

async def test_response_format():
    """Test that web_search returns expected format even when all providers fail"""
    # This will likely fail due to no API keys, but should return proper error format
    result = await web_search('test query', num_results=1)

    print("=== Response Structure Test ===")
    print(f"Response keys: {sorted(result.keys())}")
    print(f"Status: {result['status']}")
    print(f"Provider: {result['provider']}")
    print(f"Results count: {result['total_found']}")
    print(f"Has 'query' field: {'query' in result}")
    print(f"Has 'timestamp' field: {'timestamp' in result}")

    # Verify required fields
    required_fields = ['results', 'total_found', 'timestamp', 'query', 'provider', 'status']
    missing_fields = [f for f in required_fields if f not in result]

    if missing_fields:
        print(f"\nERROR: Missing required fields: {missing_fields}")
    else:
        print("\nSUCCESS: All required response fields present")

    return result

if __name__ == "__main__":
    asyncio.run(test_response_format())
