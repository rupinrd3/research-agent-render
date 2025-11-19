"""
Evaluator Agent

Provides comprehensive multi-level evaluation of research quality.
"""

import json
import logging
from typing import Dict, Any, List

from ..llm import LLMManager
from .models import (
    ResearchResult,
    EndToEndEval,
    EvaluationResult,
)

logger = logging.getLogger(__name__)


class EvaluatorAgent:
    """
    Evaluates research quality using LLM-as-judge approach.
    Performs end-to-end evaluation of complete research output.
    """

    END_TO_END_PROMPT = """Evaluate this research comprehensively.

Query: {query}

Final Report:
{report}

Sources ({num_sources}):
{sources}

Rate each dimension on a 0-1 scale (0.0 = poor, 1.0 = excellent):

1. Relevance (0-1): How well does the report answer the query?
2. Accuracy (0-1): Is the information factually correct?
3. Completeness (0-1): Are all key aspects of the query covered?
4. Source Quality (0-1): Are sources authoritative and credible?

Also provide:
- Strengths (3-5 points)
- Weaknesses (3-5 points)
- Recommendations for improvement (3-5 points)

Format as JSON:
{{
    "relevance_score": 0.XX,
    "accuracy_score": 0.XX,
    "completeness_score": 0.XX,
    "source_quality_score": 0.XX,
    "strengths": ["...", "...", "..."],
    "weaknesses": ["...", "...", "..."],
    "recommendations": ["...", "...", "..."]
}}"""

    def __init__(self, llm_manager: LLMManager):
        """
        Initialize EvaluatorAgent.

        Args:
            llm_manager: LLM manager instance
        """
        self.llm = llm_manager
        logger.info("Initialized EvaluatorAgent")

    def _clamp_score(self, score: float) -> float:
        """Ensure score is between 0 and 1."""
        return max(0.0, min(1.0, float(score)))

    async def evaluate_end_to_end(
        self, result: ResearchResult
    ) -> EndToEndEval:
        """
        Evaluate complete research output.

        Args:
            result: Research result to evaluate

        Returns:
            EndToEndEval with 4 quality scores (0-1 scale)
        """
        try:
            logger.info("Performing end-to-end evaluation")

            # Format sources
            sources_str = "\n".join(
                f"- {source}" for source in result.sources[:20]
            )

            prompt = self.END_TO_END_PROMPT.format(
                query=result.query,
                report=result.report[:5000],  # Limit size
                num_sources=len(result.sources),
                sources=sources_str,
            )

            response = await self.llm.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
                require_content=True,
            )

            # Parse JSON response
            eval_data = self._parse_json_response(response["content"])

            return EndToEndEval(
                relevance_score=self._clamp_score(eval_data.get("relevance_score", 0.5)),
                accuracy_score=self._clamp_score(eval_data.get("accuracy_score", 0.5)),
                completeness_score=self._clamp_score(eval_data.get("completeness_score", 0.5)),
                source_quality_score=self._clamp_score(eval_data.get("source_quality_score", 0.5)),
                strengths=eval_data.get("strengths", []),
                weaknesses=eval_data.get("weaknesses", []),
                recommendations=eval_data.get("recommendations", []),
                tokens_used=response["usage"]["total_tokens"],
                cost_usd=self.llm.estimate_cost(
                    response["usage"]["input_tokens"],
                    response["usage"]["output_tokens"],
                ),
            )

        except Exception as e:
            logger.error(f"End-to-end evaluation failed: {e}")
            # Return neutral scores on failure
            return EndToEndEval(
                relevance_score=0.5,
                accuracy_score=0.5,
                completeness_score=0.5,
                source_quality_score=0.5,
                strengths=[],
                weaknesses=[f"Evaluation failed: {str(e)}"],
                recommendations=[],
                tokens_used=0,
                cost_usd=0.0,
            )

    async def evaluate_research(
        self, result: ResearchResult, evaluate_steps: bool = False  # Ignored now
    ) -> EvaluationResult:
        """
        Perform end-to-end evaluation only.

        Args:
            result: Research result to evaluate
            evaluate_steps: Deprecated, ignored

        Returns:
            EvaluationResult with end-to-end evaluation
        """
        logger.info(f"Evaluating research session: {result.session_id}")

        # Only end-to-end evaluation now
        end_to_end_eval = await self.evaluate_end_to_end(result)

        return EvaluationResult(
            session_id=result.session_id,
            end_to_end_evaluation=end_to_end_eval,
        )

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.

        Args:
            content: LLM response content

        Returns:
            Parsed JSON dict
        """
        # Add null/empty check
        if not content:
            logger.warning("[EvaluatorAgent] Received empty or null content from LLM")
            return {}

        try:
            # Try to parse as JSON
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                # Return empty dict on failure
                logger.warning("[EvaluatorAgent] Failed to parse JSON from response")
                return {}
