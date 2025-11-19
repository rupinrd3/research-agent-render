"""
Agentic AI Research Solution - Backend Entry Point

A simple command-line interface for testing the research system with
full database integration.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_settings, get_llm_config_dict
from app.llm import LLMManager
from app.agents import ResearcherAgent, EvaluatorAgent
from app.database import (
    init_database,
    create_session,
    update_session,
    save_trace_event,
    save_end_to_end_evaluation,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def trace_callback(event_type: str, data: dict, iteration: int = None):
    """
    Callback to save trace events to database.

    Args:
        event_type: Type of trace event
        data: Event data
        iteration: Optional iteration number
    """
    try:
        # Extract session_id from data if present
        session_id = data.get("session_id")
        if not session_id and hasattr(trace_callback, 'current_session_id'):
            session_id = trace_callback.current_session_id

        if session_id:
            await save_trace_event(
                session_id=session_id,
                event_type=event_type,
                data=data,
                iteration=iteration,
            )
    except Exception as e:
        logger.error(f"Failed to save trace event: {e}")


async def main():
    """Main application entry point."""
    print("=" * 60)
    print("Agentic AI Research Solution")
    print("=" * 60)
    print()

    # Load configuration
    try:
        print("Loading configuration...")
        settings = load_settings("../config.yaml")
        print("✓ Configuration loaded")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return

    # Initialize database
    try:
        print("Initializing database...")
        await init_database(settings.database.get_async_url(), settings.database.echo)
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return

    # Initialize LLM Manager
    try:
        print("Initializing LLM providers...")
        llm_config = get_llm_config_dict(settings)
        llm_manager = LLMManager(llm_config)
        print(f"✓ LLM Manager initialized (primary: {settings.llm.primary})")
    except Exception as e:
        print(f"✗ Failed to initialize LLM Manager: {e}")
        return

    # Initialize agents
        print("Initializing agents...")
    researcher = ResearcherAgent(
        llm_manager=llm_manager,
        max_iterations=settings.research.max_iterations,
        timeout_minutes=settings.research.timeout_minutes,
        trace_callback=trace_callback,
        tool_settings=settings.tools,
        llm_temperature=None,
        policy_overrides={
            'finish_guard_enabled': settings.research.finish_guard_enabled,
            'finish_guard_retry_on_auto_finish': settings.research.finish_guard_retry_on_auto_finish,
            'sparse_result_threshold': settings.research.sparse_result_threshold,
            'sufficient_result_count': settings.research.sufficient_result_count,
            'ascii_prompts': settings.research.ascii_prompts,
        },
    )
    evaluator = EvaluatorAgent(llm_manager=llm_manager)
    print("✓ Agents initialized")

    print()
    print("=" * 60)
    print("System ready!")
    print("=" * 60)
    print()

    # Example research query
    query = input("Enter your research query (or press Enter for demo): ").strip()

    if not query:
        query = "What are the latest advances in retrieval-augmented generation (RAG) for LLMs?"
        print(f"Using demo query: {query}")

    print()
    print("Starting research...")
    print("-" * 60)

    # Create database session
    try:
        session = await create_session(
            session_id=None,  # Will be generated
            query=query,
            config={
                "max_iterations": settings.research.max_iterations,
                "timeout_minutes": settings.research.timeout_minutes,
                "llm_primary": settings.llm.primary,
            }
        )
        session_id = session.id

        # Set session_id in trace callback
        trace_callback.current_session_id = session_id

        print(f"Created session: {session_id}")
        print()
    except Exception as e:
        print(f"✗ Failed to create session: {e}")
        session_id = None

    # Perform research
    try:
        result = await researcher.research(query, session_id=session_id)

        print()
        print("=" * 60)
        print("RESEARCH COMPLETED")
        print("=" * 60)
        print()
        print(f"Status: {result.status}")
        print(f"Iterations: {result.total_iterations}")
        print(f"Duration: {result.total_duration_seconds:.1f}s")
        print(f"Tokens: {result.total_tokens:,}")
        print(f"Cost: ${result.total_cost_usd:.4f}")
        print(f"Sources: {len(result.sources)}")
        print()

        # Update database session
        if session_id:
            try:
                await update_session(
                    session_id=session_id,
                    status=result.status,
                    completed_at=datetime.utcnow(),
                    total_duration_seconds=result.total_duration_seconds,
                    total_iterations=result.total_iterations,
                    total_cost_usd=result.total_cost_usd,
                    total_tokens=result.total_tokens,
                    final_report=result.report,
                    sources=result.sources,
                )
                print(f"Session updated in database: {session_id}")
                print()
            except Exception as e:
                logger.error(f"Failed to update session: {e}")

        if result.report:
            print("=" * 60)
            print("FINAL REPORT")
            print("=" * 60)
            print()
            print(result.report)
            print()

        # Perform evaluation
        if result.status == "completed":
            print("=" * 60)
            print("EVALUATING RESEARCH...")
            print("=" * 60)

            eval_result = await evaluator.evaluate_research(
                result,
                evaluate_steps=False  # Per-step evaluation removed
            )

            print()

            end_eval = eval_result.end_to_end_evaluation
            print("Quality Scores (0-1 scale):")
            print(f"  - Relevance: {end_eval.relevance_score:.2f}")
            print(f"  - Accuracy: {end_eval.accuracy_score:.2f}")
            print(f"  - Completeness: {end_eval.completeness_score:.2f}")
            print(f"  - Source Quality: {end_eval.source_quality_score:.2f}")
            print()

            if end_eval.strengths:
                print("Strengths:")
                for strength in end_eval.strengths:
                    print(f"  • {strength}")
                print()

            if end_eval.weaknesses:
                print("Weaknesses:")
                for weakness in end_eval.weaknesses:
                    print(f"  • {weakness}")
                print()

            if end_eval.recommendations:
                print("Recommendations:")
                for rec in end_eval.recommendations:
                    print(f"  • {rec}")
                print()

            # Save evaluation to database
            if session_id:
                try:
                    # Save end-to-end evaluation (0-1 scale, 4 metrics only)
                    await save_end_to_end_evaluation(
                        session_id=session_id,
                        evaluation={
                            "relevance_score": end_eval.relevance_score,
                            "accuracy_score": end_eval.accuracy_score,
                            "completeness_score": end_eval.completeness_score,
                            "source_quality_score": end_eval.source_quality_score,
                            "strengths": end_eval.strengths,
                            "weaknesses": end_eval.weaknesses,
                            "recommendations": end_eval.recommendations,
                            "tokens_used": end_eval.tokens_used,
                            "cost_usd": end_eval.cost_usd,
                        }
                    )

                    print(f"Evaluations saved to database: {session_id}")
                    print()
                except Exception as e:
                    logger.error(f"Failed to save evaluations: {e}")

    except Exception as e:
        print(f"✗ Research failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())



