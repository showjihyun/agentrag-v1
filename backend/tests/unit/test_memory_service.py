"""
Unit tests for Memory Service
"""

import pytest
from backend.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_memory_store_and_retrieve():
    """Test storing and retrieving memory."""
    memory = MemoryService("redis://localhost:6380")
    
    # Store
    result = await memory.store(
        namespace="test",
        key="test_key",
        value={"data": "test_value", "count": 42},
        memory_type="short_term",
        ttl=60,
    )
    
    assert result["success"] is True
    assert result["key"] == "test_key"
    
    # Retrieve
    retrieved = await memory.retrieve(
        namespace="test",
        key="test_key",
        memory_type="short_term",
    )
    
    assert retrieved is not None
    assert retrieved["value"]["data"] == "test_value"
    assert retrieved["value"]["count"] == 42
    
    # Cleanup
    await memory.delete("test", "test_key", "short_term")
    await memory.disconnect()


@pytest.mark.asyncio
async def test_memory_update():
    """Test updating memory."""
    memory = MemoryService("redis://localhost:6380")
    
    # Store initial
    await memory.store(
        namespace="test",
        key="update_test",
        value={"version": 1},
        memory_type="short_term",
    )
    
    # Update
    await memory.update(
        namespace="test",
        key="update_test",
        value={"version": 2},
        memory_type="short_term",
    )
    
    # Verify
    retrieved = await memory.retrieve(
        namespace="test",
        key="update_test",
        memory_type="short_term",
    )
    
    assert retrieved["value"]["version"] == 2
    assert "updated_at" in retrieved["metadata"]
    
    # Cleanup
    await memory.delete("test", "update_test", "short_term")
    await memory.disconnect()


@pytest.mark.asyncio
async def test_memory_ttl():
    """Test TTL functionality."""
    memory = MemoryService("redis://localhost:6380")
    
    # Store with TTL
    await memory.store(
        namespace="test",
        key="ttl_test",
        value={"data": "expires"},
        memory_type="short_term",
        ttl=5,  # 5 seconds
    )
    
    # Check TTL
    ttl = await memory.get_ttl("test", "ttl_test", "short_term")
    assert ttl is not None
    assert ttl <= 5
    
    # Cleanup
    await memory.delete("test", "ttl_test", "short_term")
    await memory.disconnect()
