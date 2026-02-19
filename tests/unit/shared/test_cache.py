import asyncio

import pytest
import pytest_asyncio

from backend.shared.core.cache import RedisCache, cached, get_cache


@pytest_asyncio.fixture(autouse=True)
async def clear_global_cache():
    """Clear global cache before each test."""
    await get_cache().clear()
    yield
    await get_cache().clear()


@pytest.mark.asyncio
async def test_cache_set_and_get():
    cache = RedisCache()
    await cache.set("key1", "value1", ttl=60)
    hit, value = await cache.get("key1")
    assert hit is True
    assert value == "value1"


@pytest.mark.asyncio
async def test_cache_miss():
    cache = RedisCache()
    hit, value = await cache.get("nonexistent")
    assert hit is False
    assert value is None


@pytest.mark.asyncio
async def test_cache_ttl_expiry():
    cache = RedisCache()
    await cache.set("key1", "value1", ttl=0)
    # TTL of 0 means it expires immediately
    await asyncio.sleep(0.01)
    hit, _value = await cache.get("key1")
    assert hit is False


@pytest.mark.asyncio
async def test_cache_clear():
    cache = RedisCache()
    await cache.set("key1", "value1", ttl=60)
    await cache.set("key2", "value2", ttl=60)
    await cache.clear()
    hit1, _ = await cache.get("key1")
    hit2, _ = await cache.get("key2")
    assert hit1 is False
    assert hit2 is False


@pytest.mark.asyncio
async def test_cache_stats():
    cache = RedisCache()
    await cache.set("active", "val", ttl=60)
    await cache.set("expired", "val", ttl=0)
    await asyncio.sleep(0.01)
    stats = await cache.stats()
    # Test works with both redis and in-memory backends
    assert stats["backend"] in ["redis", "in-memory"]
    assert "total_keys" in stats or "keyspace_hits" in stats


@pytest.mark.asyncio
async def test_cached_decorator():
    call_count = 0

    @cached(ttl=60)
    async def my_func(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    result1 = await my_func(5)
    result2 = await my_func(5)
    result3 = await my_func(10)

    assert result1 == 10
    assert result2 == 10
    assert result3 == 20
    assert call_count == 2  # 5 cached, 10 is new


@pytest.mark.asyncio
async def test_cached_decorator_different_kwargs():
    call_count = 0

    @cached(ttl=60)
    async def my_func(x: int, multiplier: int = 2) -> int:
        nonlocal call_count
        call_count += 1
        return x * multiplier

    result1 = await my_func(5, multiplier=2)
    result2 = await my_func(5, multiplier=3)

    assert result1 == 10
    assert result2 == 15
    assert call_count == 2


@pytest.mark.asyncio
async def test_cached_skip_self():
    call_count = 0

    class MyService:
        @cached(ttl=60, skip_self=True)
        async def get_data(self, key: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"data_{key}"

    svc1 = MyService()
    svc2 = MyService()

    result1 = await svc1.get_data("a")
    result2 = await svc2.get_data("a")  # different self, same key

    assert result1 == "data_a"
    assert result2 == "data_a"
    assert call_count == 1  # Should be cached across instances


@pytest.mark.asyncio
async def test_concurrent_cache_access():
    call_count = 0

    @cached(ttl=60)
    async def slow_func(x: int) -> int:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)
        return x * 2

    # First call populates cache
    await slow_func(5)
    # Concurrent reads from cache
    results = await asyncio.gather(*[slow_func(5) for _ in range(10)])
    assert all(r == 10 for r in results)
    assert call_count == 1
