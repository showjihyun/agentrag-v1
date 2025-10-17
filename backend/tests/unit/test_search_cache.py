"""
Unit tests for SearchCacheManager.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from backend.services.search_cache import SearchCacheManager


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock()
    redis_mock.setex = Mock()
    redis_mock.incr = Mock(return_value=1)
    redis_mock.zincrby = Mock(return_value=1)
    redis_mock.zrevrange = Mock(return_value=[])
    redis_mock.exists = Mock(return_value=False)
    return redis_mock


@pytest.fixture
def cache_manager(mock_redis):
    """Create SearchCacheManager instance."""
    return SearchCacheManager(
        redis_client=mock_redis, l1_ttl=3600, l2_threshold=3, max_l2_size=1000
    )


class TestSearchCacheManager:
    """Test SearchCacheManager functionality."""

    def test_initialization(self, cache_manager):
        """Test cache manager initialization."""
        assert cache_manager.l1_ttl == 3600
        assert cache_manager.l2_threshold == 3
        assert cache_manager.max_l2_size == 1000

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_manager, mock_redis):
        """Test cache miss scenario."""
        mock_redis.get.return_value = None

        result = await cache_manager.get_cached_results(query="test query", top_k=10)

        assert result is None

    @pytest.mark.asyncio
    async def test_l1_cache_hit(self, cache_manager, mock_redis):
        """Test L1 cache hit."""
        cached_data = [{"id": "1", "text": "test"}]
        mock_redis.get.return_value = json.dumps(cached_data)

        result = await cache_manager.get_cached_results(query="test query", top_k=10)

        assert result == cached_data

    @pytest.mark.asyncio
    async def test_cache_results(self, cache_manager, mock_redis):
        """Test caching results."""
        results = [{"id": "1", "text": "test"}]

        await cache_manager.cache_results(
            query="test query",
            top_k=10,
            filters=None,
            search_mode="hybrid",
            results=results,
        )

        # Verify setex was called for L1 cache
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_embedding_cache(self, cache_manager, mock_redis):
        """Test embedding caching."""
        text = "test text"
        embedding = [0.1, 0.2, 0.3]

        # Cache embedding
        await cache_manager.cache_embedding(text, embedding)
        assert mock_redis.set.called

        # Get cached embedding
        mock_redis.get.return_value = json.dumps(embedding)
        result = await cache_manager.get_embedding_cache(text)
        assert result == embedding

    @pytest.mark.asyncio
    async def test_popular_queries(self, cache_manager, mock_redis):
        """Test popular queries retrieval."""
        mock_redis.zrevrange.return_value = [(b"hash1", 10.0), (b"hash2", 5.0)]
        mock_redis.get.side_effect = [b"query1", b"query2"]

        popular = await cache_manager.get_popular_queries(top_n=2)

        assert len(popular) == 2
        assert popular[0]["query"] == "query1"
        assert popular[0]["frequency"] == 10

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_manager, mock_redis):
        """Test cache statistics."""
        mock_redis.get.side_effect = ["100", "50", "25", "1000"]

        stats = await cache_manager.get_cache_stats()

        assert "l1_hits" in stats
        assert "l2_hits" in stats
        assert "hit_rate_percent" in stats
        assert "l2_cache_size" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
