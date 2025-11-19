"""
Test Script - Verify Imports

Simple script to verify all modules can be imported correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all module imports."""
    print("Testing imports...")
    print()

    try:
        print("Testing LLM providers...")
        from app.llm import (
            LLMManager,
            OpenAIProvider,
            GeminiProvider,
            OpenRouterProvider,
        )
        print("✓ LLM providers")

        print("Testing tools...")
        from app.tools import (
            web_search,
            arxiv_search,
            github_search,
            pdf_to_text,
            get_all_tool_definitions,
        )
        print("✓ Research tools")

        print("Testing agents...")
        from app.agents import ResearcherAgent, EvaluatorAgent
        print("✓ Agents")

        print("Testing database...")
        from app.database import (
            init_database,
            ResearchSession,
            TraceEvent,
        )
        print("✓ Database")

        print("Testing configuration...")
        from app.config import Settings, load_settings
        print("✓ Configuration")

        print()
        print("=" * 60)
        print("All imports successful!")
        print("=" * 60)
        print()
        print("System components:")
        print("  • LLM Providers: OpenAI, Gemini, OpenRouter")
        print("  • Tools: Web Search, ArXiv, GitHub, PDF Parser")
        print("  • Agents: Researcher (ReAct), Evaluator")
        print("  • Database: SQLite with async support")
        print("  • Configuration: YAML-based settings")
        print()
        print("Next steps:")
        print("  1. Copy .env.example to .env and add your API keys")
        print("  2. Run: python main.py")
        print()

        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print()
        print("Make sure to install dependencies:")
        print("  pip install -r requirements.txt")
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
