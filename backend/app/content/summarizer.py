"""
Content Summarizer

Generates LLM-based summaries and relevance scores for content.
"""

import ast
import logging
from typing import Dict, Any, List, Optional
import asyncio
import json

logger = logging.getLogger(__name__)


class ContentSummarizer:
    """
    Generates summaries and relevance scores using LLM.

    Features:
    - 200-word summaries
    - 3-5 key points extraction
    - Relevance scoring (0-1)
    - Context-aware summarization
    """

    SUMMARY_PROMPT_TEMPLATE = """You are a research assistant helping to summarize content for a research query.

USER QUERY: {query}

CONTENT FROM: {url}

CONTENT:
{content}

Generate a structured summary with:
1. A concise summary (max 200 words) focused on aspects relevant to the query
2. 3-5 key points as bullet points
3. A relevance score (0.0-1.0) indicating how useful this content is for answering the query

Return ONLY valid JSON in this exact format:
{{
  "summary": "your 200-word summary here",
  "key_points": ["point 1", "point 2", "point 3"],
  "relevance_score": 0.85,
  "topics": ["topic1", "topic2"]
}}"""

    SUMMARY_SYSTEM_PROMPT = (
        "You are an extraction assistant. When tools are available you must call "
        "the `submit_summary` function exactly once with a valid JSON object that "
        "matches its schema. Do not return free-form text."
    )

    SUMMARY_FUNCTION_DEF = [
        {
            "type": "function",
            "function": {
                "name": "submit_summary",
                "description": (
                    "Return a structured summary highlighting key points relevant to the user query."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Concise 200-word summary focused on the query.",
                        },
                        "key_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 3,
                            "description": "3-5 bullet points capturing the most important takeaways.",
                        },
                        "relevance_score": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Relevance between 0.0 (unrelated) and 1.0 (highly relevant).",
                        },
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of topical tags mentioned in the content.",
                        },
                    },
                    "required": ["summary", "key_points", "relevance_score", "topics"],
                },
            },
        }
    ]

    def __init__(self, llm_manager, max_content_length: int = 5000):
        """
        Initialize content summarizer.

        Args:
            llm_manager: LLM manager instance for making API calls
            max_content_length: Maximum content length to send to LLM
        """
        self.llm_manager = llm_manager
        self.max_content_length = max_content_length

        logger.info(
            f"Initialized ContentSummarizer "
            f"(max_content_length: {max_content_length})"
        )

    async def summarize(
        self, item: Dict[str, Any], query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate summary for a single content item.

        Args:
            item: Extracted content item with 'content' field
            query: User research query for context

        Returns:
            Dict with summary, key_points, relevance_score or None if failed
        """
        url = item.get("url", "")
        content = item.get("content", "")

        if not content:
            logger.warning(f"No content to summarize for {url}")
            return None

        try:
            # Truncate content if too long
            truncated_content = self._truncate_content(content)

            # Build prompt
            prompt = self.SUMMARY_PROMPT_TEMPLATE.format(
                query=query, url=url, content=truncated_content
            )

            # Call LLM
            messages = [
                {"role": "system", "content": self.SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

            response = await self.llm_manager.complete(
                messages=messages,
                tools=self.SUMMARY_FUNCTION_DEF,
                temperature=0.2,
                max_tokens=400,
                require_content=False,
                require_tool_calls=True,
                tool_choice={"type": "function", "function": {"name": "submit_summary"}},
            )

            # Parse response
            content_text = self._normalize_response_content(
                response.get("content", "")
            )

            tool_calls = response.get("tool_calls") or []
            summary_data: Optional[Dict[str, Any]] = None

            if tool_calls:
                try:
                    arguments = tool_calls[0]["function"].get("arguments", "{}")
                    summary_data = json.loads(arguments)
                except (KeyError, json.JSONDecodeError):
                    summary_data = None

            if not summary_data and not content_text:
                logger.warning(f"Empty LLM response for {url}")
                return None

            if not summary_data:
                # Try to extract JSON from text output as a fallback
                summary_data = self._extract_json(content_text)

            if not summary_data:
                logger.warning(
                    f"Failed to parse LLM response for {url}; using fallback summary"
                )
                return self.create_fallback_summary(item, query)

            # Add original metadata
            summary_data["url"] = url
            summary_data["original_metadata"] = item.get("metadata", {})

            return summary_data

        except Exception as e:
            logger.error(f"Summarization failed for {url}: {e}")
            return None

    async def summarize_batch(
        self,
        items: List[Dict[str, Any]],
        query: str,
        max_concurrent: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Generate summaries for multiple items in parallel.

        Args:
            items: List of extracted content items
            query: User research query
            max_concurrent: Maximum concurrent LLM calls

        Returns:
            List of summarized items (failed items filtered)
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def summarize_with_semaphore(item):
            async with semaphore:
                return await self.summarize(item, query)

        results = await asyncio.gather(
            *[summarize_with_semaphore(item) for item in items],
            return_exceptions=True
        )

        # Filter out None and exceptions
        summarized = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Summarization error: {result}")
            elif result is not None:
                summarized.append(result)

        logger.info(
            f"Summarized {len(summarized)}/{len(items)} items "
            f"({len(items) - len(summarized)} failed)"
        )

        return summarized

    def _truncate_content(self, content: str) -> str:
        """
        Truncate content to max length.

        Args:
            content: Full content text

        Returns:
            Truncated content
        """
        if len(content) <= self.max_content_length:
            return content

        # Try to truncate at paragraph boundary
        truncated = content[: self.max_content_length]

        # Find last paragraph break
        last_para = truncated.rfind("\n\n")
        if last_para > self.max_content_length * 0.8:
            truncated = truncated[:last_para]

        return truncated + "\n\n[... content truncated ...]"

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from LLM response.

        Handles cases where LLM adds extra text around JSON.

        Args:
            text: LLM response text

        Returns:
            Parsed JSON dict or None
        """
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in text
        start = text.find("{")
        end = text.rfind("}") + 1

        if start >= 0 and end > start:
            try:
                json_text = text[start:end]
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass

        # Try to find code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                try:
                    json_text = text[start:end].strip()
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass

        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                try:
                    json_text = text[start:end].strip()
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass

        try:
            repaired = ast.literal_eval(text)
            if isinstance(repaired, dict):
                return repaired
        except (ValueError, SyntaxError):
            pass

        logger.warning("Could not extract valid JSON from LLM response after repair attempts")
        return None

    def _normalize_response_content(self, raw_content: Any) -> str:
        """
        Convert provider-specific content payloads into a plain string.
        """
        if raw_content is None:
            return ""

        if isinstance(raw_content, str):
            return raw_content

        if isinstance(raw_content, list):
            parts = []
            for item in raw_content:
                if isinstance(item, dict):
                    if "text" in item and item["text"]:
                        parts.append(item["text"])
                    elif item.get("type") == "text" and item.get("text"):
                        parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join(part.strip() for part in parts if part)

        return str(raw_content)

    def create_fallback_summary(
        self, item: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """
        Create a basic summary without LLM (fallback).

        Args:
            item: Content item
            query: User query

        Returns:
            Basic summary dict
        """
        content = item.get("content", "")
        url = item.get("url", "")

        # Take first 200 words
        words = content.split()[:200]
        summary = " ".join(words)

        if len(words) == 200:
            summary += "..."

        return {
            "url": url,
            "summary": summary,
            "key_points": ["Content available at source"],
            "relevance_score": 0.5,  # Neutral
            "topics": [],
            "original_metadata": item.get("metadata", {}),
            "fallback": True,
        }
