"""
Tests for Cache Invalidation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.core.cache_invalidation import CacheDependencyGraph


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis = MagicMock()
    redis.sadd = AsyncMock()
    redis.smembers = AsyncMock(return_value=set())
    redis.delete = AsyncMock()
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


@pytest.fixture
def cache_deps(mock_redis):
    """Create cache dependency graph"""
    return CacheDependencyGraph(mock_redis)


class TestDependencyTracking:
    """Test dependency tracking"""
    
    @pytest.mark.asyncio
    async def test_add_dependency(self, cache_deps, mock_redis):
        """Test adding dependencies"""
        await cache_deps.add_dependency(
            key="workflow:123",
            depends_on=["user:456", "workflow_list:456"]
        )
        
        # Verify Redis calls
        assert mock_redis.sadd.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_dependents(self, cache_deps, mock_redis):
        """Test getting dependent keys"""
        mock_redis.smembers.return_value = {b"workflow:123", b"workflow:456"}
        
        dependents = await cache_deps.get_dependents("user:123")
        
        assert len(dependents) == 2
        assert "workflow:123" in dependents
        assert "workflow:456" in dependents


class TestCacheInvalidation:
    """Test cache invalidation"""
    
    @pytest.mark.asyncio
    async def test_invalidate_single_key(self, cache_deps, mock_redis):
        """Test invalidating single key without cascade"""
        await cache_deps.invalidate("workflow:123", cascade=False)
        
        # Should delete only the key
        mock_redis.delete.assert_called_once_with("workflow:123")
    
    @pytest.mark.asyncio
    async def test_invalidate_with_cascade(self, cache_deps, mock_redis):
        """Test invalidating key with cascade"""
        # Setup dependency chain
        async def mock_smembers(key):
            if key == "cache_deps:user:123":
                return {b"workflow_list:123"}
            elif key == "cache_deps:workflow_list:123":
                return {b"workflow:456"}
            return set()
        
        mock_redis.smembers = mock_smembers
        
        await cache_deps.invalidate("user:123", cascade=True)
        
        # Should delete all dependent keys
        mock_redis.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache_deps, mock_redis):
        """Test invalidating keys by pattern"""
        # Mock scan to return keys
        mock_redis.scan.return_value = (0, [b"workflow:123", b"workflow:456"])
        
        await cache_deps.invalidate_pattern("workflow:*")
        
        # Should delete matched keys
        mock_redis.delete.assert_called_with(b"workflow:123", b"workflow:456")


class TestDependencyGraph:
    """Test dependency graph operations"""
    
    @pytest.mark.asyncio
    async def test_clear_dependencies(self, cache_deps, mock_redis):
        """Test clearing dependencies"""
        await cache_deps.clear_dependencies("workflow:123")
        
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_circular_dependency_handling(self, cache_deps, mock_redis):
        """Test handling of circular dependencies"""
        # Setup circular dependency
        async def mock_smembers(key):
            if key == "cache_deps:a":
                return {b"b"}
            elif key == "cache_deps:b":
                return {b"a"}  # Circular!
            return set()
        
        mock_redis.smembers = mock_smembers
        
        # Should not infinite loop
        await cache_deps.invalidate("a", cascade=True)
        
        # Should handle gracefully
        assert mock_redis.delete.called


class TestCacheUsagePatterns:
    """Test common cache usage patterns"""
    
    @pytest.mark.asyncio
    async def test_workflow_user_dependency(self, cache_deps, mock_redis):
        """Test workflow depending on user"""
        # Cache workflow with user dependency
        await cache_deps.add_dependency(
            key="workflow:123",
            depends_on=["user:456"]
        )
        
        # Invalidate user should invalidate workflow
        mock_redis.smembers.return_value = {b"workflow:123"}
        await cache_deps.invalidate("user:456", cascade=True)
        
        # Workflow should be deleted
        assert mock_redis.delete.called
    
    @pytest.mark.asyncio
    async def test_multi_level_dependency(self, cache_deps, mock_redis):
        """Test multi-level dependency chain"""
        # Setup: execution -> workflow -> user
        async def mock_smembers(key):
            if key == "cache_deps:user:123":
                return {b"workflow:456"}
            elif key == "cache_deps:workflow:456":
                return {b"execution:789"}
            return set()
        
        mock_redis.smembers = mock_smembers
        
        # Invalidate user
        await cache_deps.invalidate("user:123", cascade=True)
        
        # All levels should be invalidated
        assert mock_redis.delete.called
