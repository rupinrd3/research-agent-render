"""
Content Management Pipeline

Orchestrates multi-stage content processing:
1. Classification - Identify content types
2. Extraction - Extract text from PDFs and web pages
3. Summarization - Generate LLM summaries
4. Ranking - Score by relevance
5. Caching - Store processed content
6. Serving - Provide content to agents
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from .classifier import ContentClassifier
from .extractor import ContentExtractor
from .summarizer import ContentSummarizer
from .ranker import ContentRanker
from .cache import ContentCache

logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    Multi-stage content processing pipeline.

    Stages:
    1. Classify content types
    2. Extract clean text
    3. Generate summaries
    4. Rank by relevance
    5. Cache results
    6. Serve to agents
    """

    def __init__(
        self,
        llm_manager,
        top_k: int = 10,
        max_content_length: int = 5000,
        cache_ttl_minutes: int = 15,
        enable_cache: bool = True,
    ):
        """
        Initialize content pipeline.

        Args:
            llm_manager: LLM manager for summarization
            top_k: Number of top items to select
            max_content_length: Max content sent to LLM for summarization
            cache_ttl_minutes: Cache TTL in minutes
            enable_cache: Enable caching
        """
        self.llm_manager = llm_manager
        self.top_k = top_k
        self.enable_cache = enable_cache

        # Initialize stages
        self.classifier = ContentClassifier()
        self.extractor = ContentExtractor()
        self.summarizer = ContentSummarizer(llm_manager, max_content_length)
        self.ranker = ContentRanker(top_k=top_k)

        if enable_cache:
            self.cache = ContentCache(ttl_minutes=cache_ttl_minutes)
        else:
            self.cache = None

        logger.info(
            f"Initialized ContentPipeline "
            f"(top_k: {top_k}, cache: {enable_cache})"
        )

    async def process(
        self, items: List[Dict[str, Any]], query: str
    ) -> Dict[str, Any]:
        """
        Process content items through the complete pipeline.

        Args:
            items: Raw content items from tools (web_search, arxiv_search, etc.)
            query: User research query for context

        Returns:
            Dict with 'top_items', 'all_summaries', 'stats'
        """
        logger.info(f"Starting pipeline for {len(items)} items")

        stats = {
            "input_items": len(items),
            "classified": 0,
            "extracted": 0,
            "summarized": 0,
            "ranked": 0,
            "cache_hits": 0,
            "failed_classification": 0,
            "failed_extraction": 0,
            "failed_summaries": 0,
            "extraction_errors": [],
        }

        # Stage 1: Classification
        classified_items = self.classifier.classify_batch(items)
        stats["classified"] = len(classified_items)
        notes: List[str] = []

        if not classified_items:
            logger.warning("No items passed classification")
            return {
                "top_items": [],
                "all_summaries": [],
                "stats": stats,
                "notes": notes,
            }

        # Stage 2: Check cache (if enabled)
        if self.enable_cache:
            classified_items, cached_items = self._check_cache(
                classified_items
            )
            stats["cache_hits"] = len(cached_items)
        else:
            cached_items = []

        # Stage 3: Extract content (for non-cached items)
        extracted_items = []
        extraction_errors: List[Dict[str, str]] = []
        if classified_items:
            async with self.extractor:
                extracted_items = await self.extractor.extract_batch(
                    classified_items, max_concurrent=5
                )
            stats["extracted"] = len(extracted_items)
            if hasattr(self.extractor, "pop_failures"):
                try:
                    extraction_errors = self.extractor.pop_failures()
                except Exception:
                    extraction_errors = []

        stats["failed_classification"] = stats["input_items"] - stats["classified"]
        stats["failed_extraction"] = max(
            0, len(classified_items) - len(extracted_items)
        )
        stats["extraction_errors"] = extraction_errors

        # Stage 4: Summarize (for non-cached items)
        summarized_items = []
        if extracted_items:
            summarized_items = await self.summarizer.summarize_batch(
                extracted_items, query, max_concurrent=3
            )
            stats["summarized"] = len(summarized_items)
            stats["failed_summaries"] = max(
                0, len(extracted_items) - len(summarized_items)
            )

            # Cache summarized items
            if self.enable_cache:
                self.cache.set_batch(summarized_items)
        else:
            stats["failed_summaries"] = 0

        # Combine cached and newly summarized
        all_summaries = cached_items + summarized_items

        # Stage 5: Rank and select top K
        top_items = self.ranker.rank(all_summaries)
        stats["ranked"] = len(top_items)

        if stats["failed_classification"]:
            notes.append(
                f"Filtered out {stats['failed_classification']} items during classification"
            )
        if stats["failed_extraction"]:
            sample_urls = ", ".join(
                err.get("url", "unknown")
                for err in stats["extraction_errors"][:2]
                if err.get("url")
            )
            snippet = f" (e.g., {sample_urls})" if sample_urls else ""
            notes.append(
                f"{stats['failed_extraction']} sources could not be extracted{snippet}"
            )
        if stats["failed_summaries"]:
            notes.append(
                f"{stats['failed_summaries']} items lacked usable summaries and were dropped"
            )
        if stats["cache_hits"]:
            notes.append(f"Reused {stats['cache_hits']} cached summaries")

        logger.info(
            f"Pipeline complete: {len(top_items)} top items selected "
            f"from {len(items)} input items"
        )

        return {
            "top_items": top_items,
            "all_summaries": all_summaries,
            "stats": stats,
            "notes": notes,
        }

    def _check_cache(
        self, items: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check cache for items and separate cached vs non-cached.

        Args:
            items: Classified items to check

        Returns:
            Tuple of (non_cached_items, cached_items)
        """
        non_cached = []
        cached = []

        for item in items:
            url = item.get("url")
            cached_data = self.cache.get(url)

            if cached_data:
                cached.append(cached_data)
            else:
                non_cached.append(item)

        logger.info(
            f"Cache check: {len(cached)} hits, {len(non_cached)} misses"
        )

        return non_cached, cached

    async def process_web_search_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> Dict[str, Any]:
        """
        Process web search results specifically.

        Convenience method for web_search tool integration.

        Args:
            results: Web search results from DuckDuckGo/SerpAPI
            query: User query

        Returns:
            Full pipeline result dictionary (top_items, stats, notes, etc.)
        """
        return await self.process(results, query)

    async def process_arxiv_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> Dict[str, Any]:
        """
        Process ArXiv search results specifically.

        Convenience method for arxiv_search tool integration.

        Args:
            results: ArXiv search results
            query: User query

        Returns:
            Full pipeline result dictionary (top_items, stats, notes, etc.)
        """
        return await self.process(results, query)

    async def process_github_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> Dict[str, Any]:
        """
        Process GitHub search results specifically.

        Convenience method for github_search tool integration.

        Args:
            results: GitHub search results
            query: User query

        Returns:
            Full pipeline result dictionary (top_items, stats, notes, etc.)
        """
        return await self.process(results, query)

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get cache statistics.

        Returns:
            Cache stats dict or None if caching disabled
        """
        if self.cache:
            return self.cache.get_stats()
        return None

    def clear_cache(self) -> None:
        """Clear cache (if enabled)."""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")

    def cleanup_cache(self) -> int:
        """
        Cleanup expired cache entries.

        Returns:
            Number of entries removed
        """
        if self.cache:
            return self.cache.cleanup_expired()
        return 0
