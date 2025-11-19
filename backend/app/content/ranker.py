"""
Content Ranker

Ranks and selects top content items by relevance.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ContentRanker:
    """
    Ranks content by relevance score and selects top items.

    Ranking factors:
    - LLM-generated relevance score (primary)
    - Basic keyword relevance (secondary)
    - Recency (if available)
    - Source quality (if available)
    """

    def __init__(self, top_k: int = 10):
        """
        Initialize content ranker.

        Args:
            top_k: Number of top items to select
        """
        self.top_k = top_k
        logger.info(f"Initialized ContentRanker (top_k: {top_k})")

    def rank(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank items by relevance and select top K.

        Args:
            items: List of summarized items with relevance_score

        Returns:
            Top K ranked items with 'rank' field added
        """
        if not items:
            return []

        # Calculate composite scores
        scored_items = []
        for item in items:
            score = self._calculate_composite_score(item)
            scored_items.append((score, item))

        # Sort by score (descending)
        scored_items.sort(key=lambda x: x[0], reverse=True)

        # Select top K
        top_items = []
        for rank, (score, item) in enumerate(scored_items[: self.top_k], 1):
            item["rank"] = rank
            item["composite_score"] = score
            top_items.append(item)

        logger.info(
            f"Ranked and selected top {len(top_items)} items "
            f"from {len(items)} total"
        )

        return top_items

    def _calculate_composite_score(self, item: Dict[str, Any]) -> float:
        """
        Calculate composite relevance score.

        Combines:
        - LLM relevance score (weight: 0.7)
        - Basic keyword relevance (weight: 0.2)
        - Recency bonus (weight: 0.1)

        Args:
            item: Content item

        Returns:
            Composite score 0.0-1.0
        """
        # LLM relevance score (primary factor)
        llm_score = item.get("relevance_score", 0.5)

        # Basic keyword relevance (secondary)
        basic_score = item.get("basic_relevance", 0.5)

        # Recency bonus (if available)
        recency_score = self._calculate_recency_score(item)

        # Weighted average
        composite = (
            llm_score * 0.7 +
            basic_score * 0.2 +
            recency_score * 0.1
        )

        return min(1.0, max(0.0, composite))

    def _calculate_recency_score(self, item: Dict[str, Any]) -> float:
        """
        Calculate recency score.

        Args:
            item: Content item

        Returns:
            Recency score 0.0-1.0
        """
        # Check if publication date available
        metadata = item.get("original_metadata", {})

        # For now, return neutral score
        # TODO: Implement date parsing and scoring when dates are available
        return 0.5

    def filter_by_threshold(
        self, items: List[Dict[str, Any]], min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Filter items by minimum relevance threshold.

        Args:
            items: List of items with relevance_score
            min_score: Minimum score to keep

        Returns:
            Filtered list
        """
        filtered = [
            item
            for item in items
            if item.get("relevance_score", 0) >= min_score
        ]

        logger.info(
            f"Filtered {len(filtered)}/{len(items)} items "
            f"above threshold {min_score}"
        )

        return filtered

    def deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate items based on URL.

        Args:
            items: List of items

        Returns:
            Deduplicated list (keeps highest ranked)
        """
        seen_urls = set()
        unique_items = []

        for item in items:
            url = item.get("url", "")

            # Normalize URL (remove trailing slash, query params)
            normalized_url = url.split("?")[0].rstrip("/")

            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_items.append(item)

        if len(unique_items) < len(items):
            logger.info(
                f"Removed {len(items) - len(unique_items)} duplicate items"
            )

        return unique_items
