"""
Unit tests for Event Bus
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from backend.core.event_bus import EventBus, Event


@pytest.fixture
async def redis_mock():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.xadd = AsyncMock(return_value=b"1234567890-0")
    mock.xgroup_create = AsyncMock()
    mock.xreadgroup = AsyncMock(return_value=[])
    mock.xack = AsyncMock()
    mock.xrange = AsyncMock(return_value=[])
    return mock


@pytest.fixture
async def event_bus(redis_mock):
    """Create event bus instance."""
    return EventBus(redis_mock)


@pytest.mark.asyncio
async def test_publish_event(event_bus, redis_mock):
    """Test publishing an event."""
    event_id = await event_bus.publish(
        event_type="test.event",
        data={"key": "value"},
        correlation_id="corr-123"
    )
    
    assert event_id is not None
    assert redis_mock.xadd.called


@pytest.mark.asyncio
async def test_subscribe_handler(event_bus):
    """Test subscribing to events."""
    handler = AsyncMock()
    
    event_bus.subscribe("test.event", handler)
    
    assert "test.event" in event_bus.handlers
    assert handler in event_bus.handlers["test.event"]


@pytest.mark.asyncio
async def test_trigger_local_handlers(event_bus):
    """Test triggering local handlers."""
    handler = AsyncMock()
    event_bus.subscribe("test.event", handler)
    
    await event_bus.publish(
        event_type="test.event",
        data={"key": "value"}
    )
    
    # Wait for handler to be called
    await asyncio.sleep(0.1)
    
    assert handler.called


@pytest.mark.asyncio
async def test_unsubscribe_handler(event_bus):
    """Test unsubscribing from events."""
    handler = AsyncMock()
    
    event_bus.subscribe("test.event", handler)
    event_bus.unsubscribe("test.event", handler)
    
    assert handler not in event_bus.handlers.get("test.event", [])


@pytest.mark.asyncio
async def test_event_serialization():
    """Test event serialization."""
    event = Event(
        id="event-123",
        type="test.event",
        data={"key": "value"},
        timestamp="2025-11-05T12:00:00",
        correlation_id="corr-123"
    )
    
    event_dict = event.to_dict()
    
    assert event_dict["id"] == "event-123"
    assert event_dict["type"] == "test.event"
    assert event_dict["data"] == {"key": "value"}
    
    # Test deserialization
    event2 = Event.from_dict(event_dict)
    assert event2.id == event.id
    assert event2.type == event.type


@pytest.mark.asyncio
async def test_get_event_history(event_bus, redis_mock):
    """Test getting event history."""
    redis_mock.xrange.return_value = [
        (b"1234567890-0", {
            b"id": b"event-1",
            b"type": b"test.event",
            b"data": b'{"key": "value"}',
            b"timestamp": b"2025-11-05T12:00:00"
        })
    ]
    
    events = await event_bus.get_event_history("test.event")
    
    assert len(events) == 1
    assert events[0].id == "event-1"
    assert events[0].type == "test.event"
