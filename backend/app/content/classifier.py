"""
Content Classifier

Classifies content types and filters irrelevant sources.
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)


class ContentClassifier:
    """
    Classifies content and filters spam/irrelevant sources.

    Responsibilities:
    - Detect PDFs vs web pages
    - Check content size
    - Filter spam domains
    - Filter irrelevant sources
    """

    # Known spam/low-quality domains
    SPAM_DOMAINS = {
        "pinterest.com",
        "facebook.com",
        "instagram.com",
        "twitter.com",
        "reddit.com",  # Often not primary sources
        "quora.com",   # Often not primary sources
    }

    # Maximum content size to process (characters)
    MAX_CONTENT_SIZE = 100_000  # 100K chars

    def __init__(self):
        """Initialize content classifier."""
        logger.info("Initialized ContentClassifier")

    def classify(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Classify a single content item.

        Args:
            item: Content item with 'url', 'title', 'snippet' fields

        Returns:
            Classification dict with 'type', 'should_process', 'reason'
            or None if should be filtered out
        """
        url = item.get("url", "")

        # Check if spam domain
        if self._is_spam_domain(url):
            logger.debug(f"Filtered spam domain: {url}")
            return None

        # Determine content type
        content_type = self._detect_content_type(url, item)

        # Check size (if available)
        if "size" in item and item["size"] > self.MAX_CONTENT_SIZE:
            logger.debug(f"Filtered oversized content: {url}")
            return None

        return {
            "url": url,
            "type": content_type,
            "should_process": True,
            "original_item": item,
        }

    def classify_batch(
        self, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Classify a batch of content items.

        Args:
            items: List of content items

        Returns:
            List of classified items (filtered items removed)
        """
        classified = []
        for item in items:
            result = self.classify(item)
            if result:
                classified.append(result)

        logger.info(
            f"Classified {len(classified)}/{len(items)} items "
            f"({len(items) - len(classified)} filtered)"
        )

        return classified

    def _is_spam_domain(self, url: str) -> bool:
        """
        Check if URL is from a spam/low-quality domain.

        Args:
            url: URL to check

        Returns:
            True if spam domain
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www prefix
            if domain.startswith("www."):
                domain = domain[4:]

            return domain in self.SPAM_DOMAINS
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {e}")
            return False

    def _detect_content_type(
        self, url: str, item: Dict[str, Any]
    ) -> str:
        """
        Detect content type (pdf, web, arxiv, github).

        Args:
            url: URL to check
            item: Content item

        Returns:
            Content type string
        """
        url_lower = url.lower()

        # Check for PDF
        if url_lower.endswith(".pdf") or ".pdf?" in url_lower:
            return "pdf"

        # Check for ArXiv
        if "arxiv.org" in url_lower:
            return "arxiv"

        # Check for GitHub
        if "github.com" in url_lower:
            return "github"

        # Default to web page
        return "web"

    def filter_by_relevance(
        self,
        items: List[Dict[str, Any]],
        query: str,
        min_score: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Filter items by basic relevance to query.

        Uses simple keyword matching. More sophisticated relevance
        scoring happens in the ranking stage.

        Args:
            items: Classified items
            query: User query
            min_score: Minimum relevance score to keep

        Returns:
            Filtered list of items
        """
        query_keywords = self._extract_keywords(query)

        filtered = []
        for item in items:
            # Calculate basic relevance
            relevance = self._calculate_basic_relevance(
                item, query_keywords
            )

            if relevance >= min_score:
                item["basic_relevance"] = relevance
                filtered.append(item)

        logger.info(
            f"Filtered {len(filtered)}/{len(items)} items by relevance "
            f"(threshold: {min_score})"
        )

        return filtered

    def _extract_keywords(self, text: str) -> set:
        """
        Extract keywords from text.

        Args:
            text: Text to extract from

        Returns:
            Set of lowercase keywords
        """
        # Remove punctuation and split
        words = re.findall(r'\w+', text.lower())

        # Filter out common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on",
            "at", "to", "for", "of", "with", "by", "from",
            "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "can",
        }

        return {w for w in words if w not in stop_words and len(w) > 2}

    def _calculate_basic_relevance(
        self, item: Dict[str, Any], query_keywords: set
    ) -> float:
        """
        Calculate basic relevance score.

        Args:
            item: Content item
            query_keywords: Set of query keywords

        Returns:
            Relevance score 0.0-1.0
        """
        original = item.get("original_item", {})

        # Combine title and snippet for matching
        title = original.get("title", "")
        snippet = original.get("snippet", "")
        text = f"{title} {snippet}".lower()

        # Extract keywords from content
        content_keywords = self._extract_keywords(text)

        # Calculate overlap
        if not query_keywords:
            return 0.5  # Neutral if no query keywords

        overlap = len(query_keywords.intersection(content_keywords))
        max_possible = len(query_keywords)

        return min(1.0, overlap / max_possible)
