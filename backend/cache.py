import asyncio
import functools
import hashlib
import time
from typing import Any


class CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, expires_at: float):
        self.value = value
        self.expires_at = expires_at


class TTLCache:
    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> tuple[bool, Any]:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False, None
            if time.time() > entry.expires_at:
                del self._store[key]
                return False, None
            return True, entry.value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        async with self._lock:
            self._store[key] = CacheEntry(value, time.time() + ttl)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def stats(self) -> dict:
        async with self._lock:
            now = time.time()
            total = len(self._store)
            expired = sum(1 for e in self._store.values() if now > e.expires_at)
            return {"total_entries": total, "active_entries": total - expired, "expired_entries": expired}


# Global cache instance
_cache = TTLCache()


def get_cache() -> TTLCache:
    return _cache


def cached(ttl: int = 300, skip_self: bool = False):
    """Decorator that caches async function results with a TTL (in seconds).

    Args:
        ttl: Cache time-to-live in seconds.
        skip_self: If True, skip the first positional arg (self) for key generation.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_args = args[1:] if skip_self else args
            key_parts = [func.__module__, func.__qualname__]
            key_parts.extend(str(a) for a in cache_args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            raw_key = ":".join(key_parts)
            key = hashlib.md5(raw_key.encode()).hexdigest()

            hit, value = await _cache.get(key)
            if hit:
                return value

            result = await func(*args, **kwargs)
            await _cache.set(key, result, ttl)
            return result

        return wrapper
    return decorator
