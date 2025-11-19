"""
System Validation Script

Tests the system components to ensure everything is working correctly.
This script checks imports, configuration, and basic functionality without
requiring API keys.
"""

import sys
import asyncio
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import os
    os.system('chcp 65001 >nul 2>&1')  # Set UTF-8 encoding

sys.path.insert(0, str(Path(__file__).parent))

# Use ASCII symbols for compatibility
PASS = "[PASS]"
FAIL = "[FAIL]"


def print_test(name: str, status: bool, message: str = ""):
    """Print test result."""
    symbol = PASS if status else FAIL
    print(f"{symbol} {name}")
    if message:
        print(f"  {message}")


def test_imports():
    """Test that all modules can be imported."""
    print("\n[1/6] Testing Imports")
    print("-" * 60)

    tests = [
        ("LLM Providers", lambda: __import__('app.llm', fromlist=['LLMManager'])),
        ("Research Tools", lambda: __import__('app.tools', fromlist=['web_search'])),
        ("Agents", lambda: __import__('app.agents', fromlist=['ResearcherAgent'])),
        ("Database", lambda: __import__('app.database', fromlist=['init_database'])),
        ("Configuration", lambda: __import__('app.config', fromlist=['Settings'])),
    ]

    results = []
    for name, import_func in tests:
        try:
            import_func()
            print_test(name, True)
            results.append(True)
        except Exception as e:
            print_test(name, False, str(e))
            results.append(False)

    return all(results)


def test_configuration():
    """Test configuration loading."""
    print("\n[2/6] Testing Configuration")
    print("-" * 60)

    try:
        # Test with mock config
        from app.config import Settings

        # Create minimal config
        test_config = {
            "llm": {
                "primary": "openai",
                "fallback_order": ["gemini"],
                "openai": {
                    "api_key": "test-key",
                    "model": "gpt-4o-mini",
                },
            },
        }

        settings = Settings(**test_config)
        print_test("Configuration parsing", True)
        print_test("Primary provider set", settings.llm.primary == "openai")
        print_test("OpenAI model set", settings.llm.openai.model == "gpt-4o-mini")
        return True
    except Exception as e:
        print_test("Configuration", False, str(e))
        return False


async def test_database():
    """Test database operations."""
    print("\n[3/6] Testing Database")
    print("-" * 60)

    try:
        from app.database import init_database, create_session

        # Use in-memory database for testing
        await init_database("sqlite+aiosqlite:///:memory:", echo=False)
        print_test("Database initialization", True)

        # Test session creation
        session = await create_session(
            session_id=None,
            query="Test query",
            config={"test": True}
        )
        print_test("Session creation", True)
        print_test("Session ID generated", session.id is not None)

        return True
    except Exception as e:
        print_test("Database", False, str(e))
        return False


def test_tools_definitions():
    """Test that tool definitions are valid."""
    print("\n[4/6] Testing Tool Definitions")
    print("-" * 60)

    try:
        from app.tools import get_all_tool_definitions

        tools = get_all_tool_definitions()
        print_test("Tool definitions loaded", len(tools) == 5)

        required_tools = ["web_search", "arxiv_search", "github_search", "pdf_to_text", "finish"]
        tool_names = [t["function"]["name"] for t in tools]

        for tool_name in required_tools:
            print_test(f"  {tool_name}", tool_name in tool_names)

        return len(tools) == 5
    except Exception as e:
        print_test("Tool definitions", False, str(e))
        return False


def test_agent_initialization():
    """Test agent initialization without API calls."""
    print("\n[5/6] Testing Agent Initialization")
    print("-" * 60)

    try:
        from app.llm import LLMManager
        from app.agents import ResearcherAgent, EvaluatorAgent

        # Create mock LLM config
        llm_config = {
            "primary": "openai",
            "fallback_order": [],
            "openai": {
                "api_key": "test-key",
                "model": "gpt-4o-mini",
            }
        }

        llm_manager = LLMManager(llm_config)
        print_test("LLM Manager initialization", True)

        researcher = ResearcherAgent(llm_manager, max_iterations=5)
        print_test("Researcher Agent initialization", True)

        evaluator = EvaluatorAgent(llm_manager)
        print_test("Evaluator Agent initialization", True)

        return True
    except Exception as e:
        print_test("Agent initialization", False, str(e))
        return False


def test_file_structure():
    """Test that all required files exist."""
    print("\n[6/6] Testing File Structure")
    print("-" * 60)

    project_root = Path(__file__).parent.parent
    required_files = [
        "config.yaml",
        ".env.example",
        "README.md",
        "GETTING_STARTED.md",
        "QUICK_REFERENCE.md",
        "backend/requirements.txt",
        "backend/main.py",
        "backend/test_imports.py",
        "setup.bat",
        "setup.sh",
        "start.bat",
        "start.sh",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        print_test(f"  {file_path}", exists)
        all_exist = all_exist and exists

    return all_exist


async def main():
    """Run all validation tests."""
    print("=" * 60)
    print("System Validation")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Configuration": test_configuration(),
        "Database": await test_database(),
        "Tool Definitions": test_tools_definitions(),
        "Agent Initialization": test_agent_initialization(),
        "File Structure": test_file_structure(),
    }

    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name}: {status}")

    print()

    all_passed = all(results.values())
    if all_passed:
        print("[SUCCESS] All validation tests passed!")
        print()
        print("Next steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your API keys to .env")
        print("3. Run: python main.py")
        return 0
    else:
        print("[ERROR] Some validation tests failed")
        print()
        print("Please fix the issues above before running the system.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
