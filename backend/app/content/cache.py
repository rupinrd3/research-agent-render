"""
Content Cache

Caches processed content for fast retrieval.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ContentCache:
    """
    In-memory content cache.

    Caches:
    - Extracted content
    - Summaries
    - Rankings

    Features:
    - TTL-based expiration
    - URL-based keys
    - Memory-efficient storage
    """

    def __init__(self, ttl_minutes: int = 15):
        """
        Initialize content cache.

        Args:
            ttl_minutes: Time to live in minutes (default: 15)
        """
        self.ttl = timedelta(minutes=ttl_minutes)
        self._cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Initialized ContentCache (TTL: {ttl_minutes} minutes)")

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached content for URL.

        Args:
            url: Content URL

        Returns:
            Cached content dict or None if not found/expired
        """
        normalized_url = self._normalize_url(url)

        if normalized_url not in self._cache:
            return None

        entry = self._cache[normalized_url]

        # Check if expired
        if self._is_expired(entry):
            del self._cache[normalized_url]
            logger.debug(f"Cache expired for {url}")
            return None

        logger.debug(f"Cache hit for {url}")
        return entry.get("data")

    def set(self, url: str, data: Dict[str, Any]) -> None:
        """
        Cache content for URL.

        Args:
            url: Content URL
            data: Content data to cache
        """
        normalized_url = self._normalize_url(url)

        self._cache[normalized_url] = {
            "data": data,
            "cached_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + self.ttl,
        }

        logger.debug(f"Cached content for {url}")

    def set_batch(self, items: List[Dict[str, Any]]) -> None:
        """
        Cache multiple items.

        Args:
            items: List of items with 'url' field
        """
        for item in items:
            url = item.get("url")
            if url:
                self.set(url, item)

        logger.info(f"Cached {len(items)} items")

    def has(self, url: str) -> bool:
        """
        Check if URL is in cache and not expired.

        Args:
            url: Content URL

        Returns:
            True if cached and not expired
        """
        return self.get(url) is not None

    def delete(self, url: str) -> None:
        """
        Delete cached entry for URL.

        Args:
            url: Content URL
        """
        normalized_url = self._normalize_url(url)

        if normalized_url in self._cache:
            del self._cache[normalized_url]
            logger.debug(f"Deleted cache entry for {url}")

    def clear(self) -> None:
        """Clear all cached content."""
        self._cache.clear()
        logger.info("Cleared all cache entries")

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired_urls = []

        for url, entry in self._cache.items():
            if self._is_expired(entry):
                expired_urls.append(url)

        for url in expired_urls:
            del self._cache[url]

        if expired_urls:
            logger.info(f"Cleaned up {len(expired_urls)} expired entries")

        return len(expired_urls)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        total_entries = len(self._cache)

        # Count expired
        expired_count = sum(
            1 for entry in self._cache.values() if self._is_expired(entry)
        )

        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_count,
            "expired_entries": expired_count,
            "ttl_minutes": self.ttl.total_seconds() / 60,
        }

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for consistent caching.

        Args:
            url: Original URL

        Returns:
            Normalized URL
        """
        # Remove trailing slash and query parameters
        normalized = url.split("?")[0].rstrip("/")
        return normalized.lower()

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """
        Check if cache entry is expired.

        Args:
            entry: Cache entry dict

        Returns:
            True if expired
        """
        expires_at = entry.get("expires_at")
        if not expires_at:
            return True

        return datetime.utcnow() > expires_at


class RedisContentCache(ContentCache):
    """
    Redis-based content cache (optional).

    Falls back to in-memory cache if Redis unavailable.
    """

    def __init__(self, redis_url: Optional[str] = None, ttl_minutes: int = 15):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (optional)
            ttl_minutes: Time to live in minutes
        """
        super().__init__(ttl_minutes=ttl_minutes)

        self.redis_client = None

        if redis_url:
            self._init_redis(redis_url)

    def _init_redis(self, redis_url: str) -> None:
        """
        Initialize Redis connection.

        Args:
            redis_url: Redis connection URL
        """
        try:
            import redis

            self.redis_client = redis.from_url(
                redis_url, decode_responses=True
            )

            # Test connection
            self.redis_client.ping()

            logger.info(f"Connected to Redis at {redis_url}")

        except ImportError:
            logger.warning(
                "redis-py not installed - using in-memory cache"
            )
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis: {e} - using in-memory cache"
            )

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """Get from Redis or fallback to in-memory."""
        if self.redis_client:
            try:
                normalized_url = self._normalize_url(url)
                cached_json = self.redis_client.get(f"content:{normalized_url}")

                if cached_json:
                    logger.debug(f"Redis cache hit for {url}")
                    return json.loads(cached_json)

            except Exception as e:
                logger.error(f"Redis get error: {e}")

        # Fallback to in-memory
        return super().get(url)

    def set(self, url: str, data: Dict[str, Any]) -> None:
        """Set in Redis and in-memory."""
        if self.redis_client:
            try:
                normalized_url = self._normalize_url(url)
                cached_json = json.dumps(data)

                self.redis_client.setex(
                    f"content:{normalized_url}",
                    int(self.ttl.total_seconds()),
                    cached_json,
                )

                logger.debug(f"Cached in Redis: {url}")

            except Exception as e:
                logger.error(f"Redis set error: {e}")

        # Also cache in-memory as fallback
        super().set(url, data)
