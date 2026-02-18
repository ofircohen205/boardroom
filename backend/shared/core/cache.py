# backend/cache.py
"""Redis-based caching with in-memory fallback."""

import asyncio
import functools
import hashlib
import json
from typing import Any, Optional

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from backend.shared.core.logging import get_logger
from backend.shared.core.settings import settings

logger = get_logger(__name__)


def _serialize(value: Any) -> bytes:
    """Serialize value to JSON bytes."""
    return json.dumps(value, default=str).encode("utf-8")


def _deserialize(data: bytes) -> Any:
    """Deserialize JSON bytes to value."""
    return json.loads(data.decode("utf-8"))


class RedisCache:
    """Redis-based cache with automatic fallback to in-memory cache."""

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._fallback_store: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
        self._connected = False

    async def _ensure_connection(self):
        """Ensure Redis connection is established, fallback to in-memory if failed."""
        if self._connected:
            return

        try:
            self._pool = ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=False,
                max_connections=10,
            )
            self._redis = Redis(connection_pool=self._pool)
            await self._redis.ping()
            self._connected = True
            logger.info("✅ Redis cache connected")
        except (RedisError, Exception) as e:
            logger.warning(f"⚠️  Redis connection failed, using in-memory cache: {e}")
            self._redis = None
            self._connected = False

    async def get(self, key: str) -> tuple[bool, Any]:
        """Get a value from cache. Returns (hit, value)."""
        await self._ensure_connection()

        if self._redis:
            try:
                value = await self._redis.get(key)
                if value is None:
                    return False, None
                # Deserialize from JSON
                return True, _deserialize(value)
            except (RedisError, Exception) as e:
                logger.warning(f"Redis get error, falling back to in-memory: {e}")
                # Fall through to in-memory

        # In-memory fallback
        async with self._lock:
            if key not in self._fallback_store:
                return False, None
            value, expires_at = self._fallback_store[key]
            import time

            if time.time() > expires_at:
                del self._fallback_store[key]
                return False, None
            return True, value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Set a value in cache with TTL (seconds)."""
        await self._ensure_connection()

        if self._redis:
            try:
                # Serialize to JSON
                serialized = _serialize(value)
                await self._redis.setex(key, ttl, serialized)
                return
            except (RedisError, Exception) as e:
                logger.warning(f"Redis set error, falling back to in-memory: {e}")
                # Fall through to in-memory

        # In-memory fallback
        import time

        async with self._lock:
            self._fallback_store[key] = (value, time.time() + ttl)

    async def clear(self) -> None:
        """Clear all cache entries."""
        await self._ensure_connection()

        if self._redis:
            try:
                await self._redis.flushdb()
                logger.info("Redis cache cleared")
                return
            except (RedisError, Exception) as e:
                logger.warning(f"Redis clear error, falling back to in-memory: {e}")
                # Fall through to in-memory

        # In-memory fallback
        async with self._lock:
            self._fallback_store.clear()
            logger.info("In-memory cache cleared")

    async def stats(self) -> dict:
        """Get cache statistics."""
        await self._ensure_connection()

        if self._redis:
            try:
                info = await self._redis.info("stats")
                keyspace = await self._redis.info("keyspace")
                db_keys = keyspace.get("db0", {}).get("keys", 0)
                return {
                    "backend": "redis",
                    "connected": True,
                    "total_keys": db_keys,
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            except (RedisError, Exception) as e:
                logger.warning(f"Redis stats error: {e}")
                # Fall through to in-memory

        # In-memory fallback
        import time

        async with self._lock:
            now = time.time()
            active = sum(1 for _, exp in self._fallback_store.values() if now <= exp)
            return {
                "backend": "in-memory",
                "connected": False,
                "total_keys": len(self._fallback_store),
                "active_keys": active,
            }

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
        self._connected = False
        logger.info("Cache connection closed")


# Global cache instance
_cache = RedisCache()


def get_cache() -> RedisCache:
    """Get the global cache instance."""
    return _cache


def cached(ttl: int = 300, skip_self: bool = False):
    """
    Decorator that caches async function results with a TTL (in seconds).

    Args:
        ttl: Cache time-to-live in seconds.
        skip_self: If True, skip the first positional arg (self) for key generation.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_args = args[1:] if skip_self else args
            key_parts = [func.__module__, func.__qualname__]
            key_parts.extend(str(a) for a in cache_args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            raw_key = ":".join(key_parts)
            key = f"boardroom:{hashlib.md5(raw_key.encode()).hexdigest()}"

            # Try to get from cache
            hit, value = await _cache.get(key)
            if hit:
                return value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await _cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator
