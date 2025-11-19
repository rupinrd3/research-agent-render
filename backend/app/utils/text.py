"""
Text Processing Utilities

Common text processing and manipulation functions.
"""

import re
from typing import Optional
from urllib.parse import urlparse


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(suffix)
    return text[:truncate_at].rstrip() + suffix


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.

    Args:
        url: Full URL

    Returns:
        Domain name (e.g., 'example.com')

    Examples:
        >>> extract_domain('https://www.example.com/path')
        'www.example.com'
        >>> extract_domain('invalid-url')
        'unknown'
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        return domain if domain else "unknown"
    except Exception:
        return "unknown"


def clean_text(text: str, remove_extra_whitespace: bool = True) -> str:
    """
    Clean and normalize text.

    Args:
        text: Text to clean
        remove_extra_whitespace: Remove extra spaces and newlines

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove control characters
    text = "".join(char for char in text if char.isprintable() or char in "\n\t")

    # Remove extra whitespace if requested
    if remove_extra_whitespace:
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        # Replace multiple newlines with double newline
        text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def count_words(text: str) -> int:
    """
    Count words in text.

    Args:
        text: Text to count words in

    Returns:
        Number of words
    """
    if not text:
        return 0

    # Split on whitespace and count non-empty strings
    words = text.split()
    return len([w for w in words if w])


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    """
    Extract keywords from text (simple implementation).

    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords

    Returns:
        List of keywords
    """
    if not text:
        return []

    # Simple extraction: lowercase words, remove common words
    stop_words = {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "but",
        "in", "with", "to", "for", "of", "as", "by", "from", "this", "that"
    }

    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 3]

    # Get unique keywords maintaining order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    return unique_keywords[:max_keywords]


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    if not text:
        return []

    # Simple sentence splitting (improved regex)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text to single spaces.

    Args:
        text: Text to normalize

    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""

    # Replace all whitespace (including newlines) with single space
    return " ".join(text.split())
