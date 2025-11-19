"""
Validation script to test the fixes made to the research agent.

This script validates:
1. All imports work correctly
2. No syntax errors in modified files
3. Schema cleaning works as expected
4. Basic functionality is intact
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from app.llm.gemini_provider import GeminiProvider
        from app.llm.openrouter_provider import OpenRouterProvider
        from app.llm.manager import LLMManager
        from app.agents.evaluator_agent import EvaluatorAgent
        from app.tools.definitions import get_all_tool_definitions
        print("[PASS] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_schema_cleaner():
    """Test the schema cleaning function."""
    print("\nTesting schema cleaner...")
    try:
        from app.llm.gemini_provider import GeminiProvider

        # Create a dummy provider (won't actually call API)
        provider = GeminiProvider.__new__(GeminiProvider)

        # Test schema with unsupported fields
        test_schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                },
                "date_filter": {
                    "type": "string",
                    "enum": ["day", "week", "month", None],
                    "default": None
                }
            },
            "required": ["query"]
        }

        cleaned = provider._clean_schema_for_gemini(test_schema)

        # Check that unsupported fields are removed
        props = cleaned.get("properties", {})
        num_results = props.get("num_results", {})

        if "default" in num_results:
            print("[FAIL] 'default' field not removed")
            return False
        if "minimum" in num_results:
            print("[FAIL] 'minimum' field not removed")
            return False
        if "maximum" in num_results:
            print("[FAIL] 'maximum' field not removed")
            return False

        # Check that None is filtered from enum
        date_filter = props.get("date_filter", {})
        enum_values = date_filter.get("enum", [])
        if None in enum_values:
            print("[FAIL] None not filtered from enum")
            return False

        # Check that supported fields are kept
        if "type" not in num_results:
            print("[FAIL] 'type' field removed incorrectly")
            return False
        if "description" not in num_results:
            print("[FAIL] 'description' field removed incorrectly")
            return False

        print("[PASS] Schema cleaner working correctly")
        print(f"   Original schema had: default, minimum, maximum")
        print(f"   Cleaned schema removed all unsupported fields")
        print(f"   Enum: {enum_values}")
        return True

    except Exception as e:
        print(f"[FAIL] Schema cleaner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_evaluator_null_safety():
    """Test that evaluator handles null content."""
    print("\nTesting evaluator null safety...")
    try:
        from app.agents.evaluator_agent import EvaluatorAgent

        # Create a dummy evaluator (won't actually call LLM)
        evaluator = EvaluatorAgent.__new__(EvaluatorAgent)

        # Test with None
        result = evaluator._parse_json_response(None)
        if result != {}:
            print("[FAIL] None not handled correctly")
            return False

        # Test with empty string
        result = evaluator._parse_json_response("")
        if result != {}:
            print("[FAIL] Empty string not handled correctly")
            return False

        # Test with valid JSON
        result = evaluator._parse_json_response('{"score": 8.5}')
        if result.get("score") != 8.5:
            print("[FAIL] Valid JSON not parsed correctly")
            return False

        print("[PASS] Evaluator null safety working correctly")
        return True

    except Exception as e:
        print(f"[FAIL] Evaluator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_definitions():
    """Test that tool definitions are valid."""
    print("\nTesting tool definitions...")
    try:
        from app.tools.definitions import get_all_tool_definitions

        tools = get_all_tool_definitions()

        if not tools:
            print("[FAIL] No tool definitions found")
            return False

        print(f"[PASS] Found {len(tools)} tool definitions")

        # Check each tool has required fields
        for tool in tools:
            if "type" not in tool:
                print(f"[FAIL] Tool missing 'type' field")
                return False
            if "function" not in tool:
                print(f"[FAIL] Tool missing 'function' field")
                return False

            func = tool["function"]
            if "name" not in func:
                print(f"[FAIL] Tool function missing 'name' field")
                return False

            print(f"   - {func['name']}")

        print("[PASS] All tool definitions are valid")
        return True

    except Exception as e:
        print(f"[FAIL] Tool definitions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("VALIDATION TESTS FOR RESEARCH AGENT FIXES")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Schema Cleaner", test_schema_cleaner()))
    results.append(("Evaluator Null Safety", test_evaluator_null_safety()))
    results.append(("Tool Definitions", test_tool_definitions()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "[PASS] PASS" if passed else "[FAIL] FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(result[1] for result in results)

    print("=" * 60)
    if all_passed:
        print("[PASS] ALL TESTS PASSED - Fixes are working correctly!")
        print("\nNext steps:")
        print("1. Ensure API keys are set in .env file")
        print("2. Start the backend server: uvicorn app.api.main:app --reload")
        print("3. Test with a simple research query")
    else:
        print("[FAIL] SOME TESTS FAILED - Please review the errors above")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
