"""
Validation Utilities

Functions for validating and sanitizing various inputs.
"""

import re
from typing import Optional
from urllib.parse import urlparse
from pathlib import Path


def validate_url(url: str, allowed_schemes: Optional[list[str]] = None) -> bool:
    """
    Validate if string is a valid URL.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])

    Returns:
        True if valid URL, False otherwise

    Examples:
        >>> validate_url('https://example.com')
        True
        >>> validate_url('not-a-url')
        False
        >>> validate_url('ftp://example.com', ['ftp'])
        True
    """
    if not url or not isinstance(url, str):
        return False

    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in allowed_schemes
            and bool(parsed.netloc)
        )
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """
    Validate if string is a valid email address.

    Args:
        email: Email address to validate

    Returns:
        True if valid email, False otherwise

    Examples:
        >>> validate_email('user@example.com')
        True
        >>> validate_email('invalid-email')
        False
    """
    if not email or not isinstance(email, str):
        return False

    # Simple but robust email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(
    filename: str,
    replacement: str = "_",
    max_length: int = 255
) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.

    Args:
        filename: Filename to sanitize
        replacement: Character to replace invalid chars with
        max_length: Maximum filename length

    Returns:
        Sanitized filename

    Examples:
        >>> sanitize_filename('my file?.txt')
        'my_file_.txt'
        >>> sanitize_filename('a' * 300)
        'aaa...aaa'  # truncated to 255 chars
    """
    if not filename:
        return "unnamed"

    # Remove invalid filename characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, replacement, filename)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Truncate if too long
    if len(sanitized) > max_length:
        # Keep extension if present
        stem = Path(sanitized).stem
        suffix = Path(sanitized).suffix
        available = max_length - len(suffix)
        sanitized = stem[:available] + suffix

    return sanitized if sanitized else "unnamed"


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format.

    Args:
        session_id: Session ID to validate

    Returns:
        True if valid format, False otherwise

    Examples:
        >>> validate_session_id('550e8400-e29b-41d4-a716-446655440000')
        True
        >>> validate_session_id('invalid')
        False
    """
    if not session_id or not isinstance(session_id, str):
        return False

    # UUID format (8-4-4-4-12)
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, session_id, re.IGNORECASE))


def validate_api_key(api_key: str, min_length: int = 20) -> bool:
    """
    Validate API key format (basic check).

    Args:
        api_key: API key to validate
        min_length: Minimum required length

    Returns:
        True if valid format, False otherwise

    Examples:
        >>> validate_api_key('sk-1234567890abcdefghij')
        True
        >>> validate_api_key('short')
        False
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # Basic checks: alphanumeric + common chars, minimum length
    return len(api_key) >= min_length and bool(re.match(r'^[A-Za-z0-9_-]+$', api_key))


def sanitize_query(query: str, max_length: int = 1000) -> str:
    """
    Sanitize user search query.

    Args:
        query: Query string to sanitize
        max_length: Maximum query length

    Returns:
        Sanitized query

    Examples:
        >>> sanitize_query('  what is AI?  ')
        'what is AI?'
        >>> sanitize_query('<script>alert("xss")</script>')
        'scriptalert("xss")/script'
    """
    if not query:
        return ""

    # Remove HTML tags
    query = re.sub(r'<[^>]+>', '', query)

    # Clean whitespace
    query = " ".join(query.split())

    # Truncate if too long
    if len(query) > max_length:
        query = query[:max_length].rstrip()

    return query


def validate_port(port: int | str) -> bool:
    """
    Validate port number.

    Args:
        port: Port number to validate

    Returns:
        True if valid port, False otherwise

    Examples:
        >>> validate_port(8000)
        True
        >>> validate_port('8000')
        True
        >>> validate_port(99999)
        False
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False
