"""
Unit tests for Phase 2 performance improvements.

Tests:
1. LLM response caching
2. Background task management
3. Connection pooling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from backend.core.llm_cache import LLMResponseCache, get_or_generate
from backend.core.background_tasks import BackgroundTaskManager, TaskStatus
from backend.core.connection_pool import RedisConnectionPool


class TestLLMResponseCache:
    """Test LLM response caching."""

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        mock_redis = AsyncMock()
        cache = LLMResponseCache(mock_redis)

        messages = [{"role": "user", "content": "test"}]

        key1 = cache._generate_cache_key(messages, 0.7, None, "model1")
        key2 = cache._generate_cache_key(messages, 0.7, None, "model1")

        # Same inputs should generate same key
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_cache_key_different_for_different_inputs(self):
        """Test cache keys differ for different inputs."""
        mock_redis = AsyncMock()
        cache = LLMResponseCache(mock_redis)

        messages1 = [{"role": "user", "content": "test1"}]
        messages2 = [{"role": "user", "content": "test2"}]

        key1 = cache._generate_cache_key(messages1, 0.7, None, "model1")
        key2 = cache._generate_cache_key(messages2, 0.7, None, "model1")

        # Different inputs should generate different keys
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache hit returns cached response."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(
            return_value='{"response": "cached response", "cached_at": "2024-01-01"}'
        )

        cache = LLMResponseCache(mock_redis)

        messages = [{"role": "user", "content": "test"}]
        response = await cache.get(messages)

        assert response == "cached response"
        assert cache.hits == 1
        assert cache.misses == 0

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss returns None."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        cache = LLMResponseCache(mock_redis)

        messages = [{"role": "user", "content": "test"}]
        response = await cache.get(messages)

        assert response is None
        assert cache.hits == 0
        assert cache.misses == 1

    @pytest.mark.asyncio
    async def test_cache_set(self):
        """Test caching a response."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)

        cache = LLMResponseCache(mock_redis, default_ttl=3600)

        messages = [{"role": "user", "content": "test"}]
        success = await cache.set(messages, "test response")

        assert success is True
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_generate_cache_hit(self):
        """Test get_or_generate with cache hit."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(
            return_value='{"response": "cached", "cached_at": "2024-01-01"}'
        )

        cache = LLMResponseCache(mock_redis)

        mock_llm = Mock()
        mock_llm.model = "test-model"
        mock_llm.generate = AsyncMock(return_value="new response")

        messages = [{"role": "user", "content": "test"}]
        response = await get_or_generate(cache, mock_llm, messages)

        # Should return cached response without calling LLM
        assert response == "cached"
        mock_llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_generate_cache_miss(self):
        """Test get_or_generate with cache miss."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)

        cache = LLMResponseCache(mock_redis)

        mock_llm = Mock()
        mock_llm.model = "test-model"
        mock_llm.generate = AsyncMock(return_value="new response")

        messages = [{"role": "user", "content": "test"}]
        response = await get_or_generate(cache, mock_llm, messages)

        # Should generate new response and cache it
        assert response == "new response"
        mock_llm.generate.assert_called_once()
        mock_redis.setex.assert_called_once()

    def test_cache_stats(self):
        """Test cache statistics."""
        mock_redis = Mock()
        cache = LLMResponseCache(mock_redis)

        cache.hits = 7
        cache.misses = 3

        stats = cache.get_stats()

        assert stats["hits"] == 7
        assert stats["misses"] == 3
        assert stats["total_requests"] == 10
        assert stats["hit_rate"] == 70.0


class TestBackgroundTaskManager:
    """Test background task management."""

    def test_create_task(self):
        """Test task creation."""
        manager = BackgroundTaskManager()

        async def dummy_func():
            return "result"

        task_id = manager.create_task("test_task", dummy_func)

        assert task_id.startswith("test_task_")
        assert task_id in manager.tasks

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test successful task execution."""
        manager = BackgroundTaskManager()

        async def dummy_func():
            await asyncio.sleep(0.1)
            return "success"

        task_id = manager.create_task("test_task", dummy_func)

        await manager.execute_task(task_id)

        task = manager.tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "success"

    @pytest.mark.asyncio
    async def test_execute_task_failure(self):
        """Test task execution failure."""
        manager = BackgroundTaskManager()

        async def failing_func():
            raise ValueError("Test error")

        task_id = manager.create_task("test_task", failing_func)

        await manager.execute_task(task_id)

        task = manager.tasks[task_id]
        assert task.status == TaskStatus.FAILED
        assert "Test error" in task.error

    def test_get_task_status(self):
        """Test getting task status."""
        manager = BackgroundTaskManager()

        async def dummy_func():
            return "result"

        task_id = manager.create_task("test_task", dummy_func)

        status = manager.get_task_status(task_id)

        assert status is not None
        assert status["task_id"] == task_id
        assert status["status"] == "pending"

    def test_get_stats(self):
        """Test task manager statistics."""
        manager = BackgroundTaskManager()

        async def dummy_func():
            return "result"

        # Create some tasks
        manager.create_task("test1", dummy_func)
        manager.create_task("test2", dummy_func)

        stats = manager.get_stats()

        assert stats["total_tasks"] == 2
        assert stats["by_status"]["pending"] == 2


class TestRedisConnectionPool:
    """Test Redis connection pooling."""

    def test_pool_initialization(self):
        """Test connection pool initialization."""
        pool = RedisConnectionPool(host="localhost", port=6379, max_connections=50)

        assert pool.host == "localhost"
        assert pool.port == 6379
        assert pool.max_connections == 50

    def test_get_client(self):
        """Test getting Redis client from pool."""
        pool = RedisConnectionPool()

        client = pool.get_client()

        assert client is not None

        # Getting client again should return same instance
        client2 = pool.get_client()
        assert client is client2

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test connection health check."""
        # This would require actual Redis connection
        # Placeholder for integration test
        pass


# Performance benchmarks
class TestPhase2Performance:
    """Performance benchmarks for Phase 2 improvements."""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Benchmark cache performance."""
        # Requires actual Redis connection
        pass

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_background_task_throughput(self):
        """Benchmark background task throughput."""
        manager = BackgroundTaskManager(max_concurrent_tasks=10)

        async def quick_task():
            await asyncio.sleep(0.01)
            return "done"

        # Submit many tasks
        task_ids = []
        for i in range(100):
            task_id = manager.submit_task("benchmark", quick_task)
            task_ids.append(task_id)

        # Wait for completion
        # (In real test, would wait for all tasks)
        await asyncio.sleep(2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
