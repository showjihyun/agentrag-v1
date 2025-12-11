"""
Event Bus Implementation

Simple in-memory event bus for domain events.
Can be extended to use Redis, RabbitMQ, etc.
"""

import logging
import asyncio
from typing import Dict, List, Callable, Any, Type
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """Base class for domain events."""
    event_type: str
    aggregate_id: str
    timestamp: datetime
    data: Dict[str, Any]


class EventBus:
    """
    Simple event bus for publishing and subscribing to domain events.
    
    Usage:
        bus = EventBus()
        bus.subscribe("WorkflowCreated", handler)
        await bus.publish(event)
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._async_handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")
    
    def subscribe_async(self, event_type: str, handler: Callable) -> None:
        """Subscribe async handler to an event type."""
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        self._async_handlers[event_type].append(handler)
        logger.debug(f"Subscribed async handler to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]
        if event_type in self._async_handlers:
            self._async_handlers[event_type] = [
                h for h in self._async_handlers[event_type] if h != handler
            ]
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribers."""
        event_type = event.event_type
        
        # Call sync handlers
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
        
        # Call async handlers
        for handler in self._async_handlers.get(event_type, []):
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in async event handler for {event_type}: {e}")
        
        logger.debug(f"Published event: {event_type}")
    
    def publish_sync(self, event: DomainEvent) -> None:
        """Publish event synchronously (only calls sync handlers)."""
        event_type = event.event_type
        
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")


# Global event bus instance
_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (for testing)."""
    global _event_bus
    _event_bus = None
