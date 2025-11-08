"""
Unit tests for Multi-Level Cache
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.core.advanced_cache import (
    LRUCache,
    MultiLevelCache,
    cache_key
)


@pytest.mark.asyncio
async def test_lru_cache_basic():
    """Test basic LRU cache operations"""
    cache = LRUCache(max_size=3)
    
    # Set values
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")
    
    # Get values
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"
    
    # Size check
    assert cache.size() == 3


@pytest.mark.asyncio
async def test_lru_cache_eviction():
    """Test LRU cache eviction"""
    cache = LRUCache(max_size=2)
    
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")  # Should evict key1
    
    assert await cache.get("key1") is None
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"


@pytest.mark.asyncio
async def test_lru_cache_ttl():
    """Test LRU cache TTL"""
    cache = LRUCache(max_size=10)
    
    await cache.set("key1", "value1", ttl=1)
    
    # Should exist immediately
    assert await cache.get("key1") == "value1"
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    
    # Should be expired
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_multi_level_cache_l1_hit():
    """Test L1 cache hit"""
    redis_mock = AsyncMock()
    cache = MultiLevelCache(redis_client=redis_mock)
    
    # Set in L1
    await cache.l1_cache.set("key1", "value1")
    
    # Get should hit L1
    value = await cache.get("key1")
    
    assert value == "value1"
    assert cache.stats["l1_hits"] == 1
    assert cache.stats["l1_misses"] == 0


@pytest.mark.asyncio
async def test_multi_level_cache_l2_hit():
    """Test L2 cache hit with promotion to L1"""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = '{"data": "value2"}'
    
    cache = MultiLevelCache(redis_client=redis_mock)
    
    # Get should hit L2 and promote to L1
    value = await cache.get("key2")
    
    assert value == {"data": "value2"}
    assert cache.stats["l1_misses"] == 1
    assert cache.stats["l2_hits"] == 1
    
    # Second get should hit L1
    value = await cache.get("key2")
    assert cache.stats["l1_hits"] == 1


@pytest.mark.asyncio
async def test_multi_level_cache_write_through():
    """Test write-through to all levels"""
    redis_mock = AsyncMock()
    cache = MultiLevelCache(redis_client=redis_mock)
    
    # Set value
    await cache.set("key1", "value1", ttl=3600)
    
    # Should be in L1
    assert await cache.l1_cache.get("key1") == "value1"
    
    # Should be written to L2
    redis_mock.setex.assert_called_once()


@pytest.mark.asyncio
async def test_multi_level_cache_get_or_set():
    """Test get_or_set pattern"""
    redis_mock = AsyncMock()
    cache = MultiLevelCache(redis_client=redis_mock)
    
    call_count = 0
    
    async def factory():
        nonlocal call_count
        call_count += 1
        return f"computed_value_{call_count}"
    
    # First call should compute
    value1 = await cache.get_or_set("key1", factory)
    assert value1 == "computed_value_1"
    assert call_count == 1
    
    # Second call should use cache
    value2 = await cache.get_or_set("key1", factory)
    assert value2 == "computed_value_1"
    assert call_count == 1  # Not called again


@pytest.mark.asyncio
async def test_cache_key_generation():
    """Test cache key generation"""
    
    # Simple key
    key1 = cache_key("user", "123")
    assert key1 == "user:123"
    
    # With kwargs
    key2 = cache_key("user", user_id=123, include_profile=True)
    assert "user_id=123" in key2
    assert "include_profile=True" in key2
    
    # Long key should be hashed
    long_key = cache_key("x" * 300)
    assert long_key.startswith("hash:")
    assert len(long_key) < 50


@pytest.mark.asyncio
async def test_cache_statistics():
    """Test cache statistics tracking"""
    redis_mock = AsyncMock()
    cache = MultiLevelCache(redis_client=redis_mock)
    
    # Set some values
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    
    # Get values (L1 hits)
    await cache.get("key1")
    await cache.get("key2")
    
    # Get non-existent (misses)
    await cache.get("key3", fetch_from_db=False)
    
    stats = cache.get_stats()
    
    assert stats["l1_hits"] == 2
    assert stats["l1_misses"] == 1
    assert stats["hit_rate"] > 0
