"""
Formatting Utilities

Functions for formatting various data types for display.
"""

from datetime import datetime, timedelta
from typing import Optional


def format_timestamp(
    timestamp: datetime | str | None = None, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format timestamp for display.

    Args:
        timestamp: Timestamp to format (datetime object, ISO string, or None for now)
        format_str: Format string for strftime

    Returns:
        Formatted timestamp string

    Examples:
        >>> format_timestamp()
        '2025-01-15 14:30:00'
        >>> format_timestamp('2025-01-15T14:30:00')
        '2025-01-15 14:30:00'
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    elif isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return timestamp  # Return as-is if can't parse

    return timestamp.strftime(format_str)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string

    Examples:
        >>> format_duration(45)
        '45s'
        >>> format_duration(125)
        '2m 5s'
        >>> format_duration(3665)
        '1h 1m 5s'
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    delta = timedelta(seconds=int(seconds))
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    secs = delta.seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:  # Always show seconds if no other unit
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_cost(cost: float, currency: str = "$") -> str:
    """
    Format cost in USD.

    Args:
        cost: Cost value
        currency: Currency symbol

    Returns:
        Formatted cost string

    Examples:
        >>> format_cost(0.00123)
        '$0.0012'
        >>> format_cost(1.5)
        '$1.50'
    """
    if cost < 0.01:
        return f"{currency}{cost:.4f}"
    return f"{currency}{cost:.2f}"


def format_token_count(tokens: int) -> str:
    """
    Format token count with K/M suffix for large numbers.

    Args:
        tokens: Number of tokens

    Returns:
        Formatted token count

    Examples:
        >>> format_token_count(500)
        '500'
        >>> format_token_count(1500)
        '1.5K'
        >>> format_token_count(1500000)
        '1.5M'
    """
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1_000_000:
        return f"{tokens / 1000:.1f}K"
    else:
        return f"{tokens / 1_000_000:.1f}M"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """
    Format decimal as percentage.

    Args:
        value: Value between 0 and 1 (or 0 and 100)
        decimal_places: Number of decimal places

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(0.75)
        '75.0%'
        >>> format_percentage(0.8567, 2)
        '85.67%'
    """
    # Handle both 0-1 and 0-100 ranges
    if value <= 1:
        value *= 100

    return f"{value:.{decimal_places}f}%"


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in bytes to human-readable string.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string

    Examples:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_size)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


def format_list(items: list, max_items: int = 5, separator: str = ", ") -> str:
    """
    Format list with truncation for display.

    Args:
        items: List of items to format
        max_items: Maximum items to show before truncating
        separator: Separator between items

    Returns:
        Formatted list string

    Examples:
        >>> format_list(['a', 'b', 'c'])
        'a, b, c'
        >>> format_list(['a', 'b', 'c', 'd', 'e', 'f'], 3)
        'a, b, c... (3 more)'
    """
    if not items:
        return ""

    if len(items) <= max_items:
        return separator.join(str(item) for item in items)

    shown = separator.join(str(item) for item in items[:max_items])
    remaining = len(items) - max_items
    return f"{shown}... ({remaining} more)"
