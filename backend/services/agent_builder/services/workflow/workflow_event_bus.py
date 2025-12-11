"""
Workflow Event Bus

Event-driven architecture for workflow execution with pub/sub pattern.
Enables loose coupling between components and real-time notifications.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
import uuid

logger = logging.getLogger(__name__)


class WorkflowEventType(str, Enum):
    """Types of workflow events."""
    # Lifecycle events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_UPDATED = "workflow.updated"
    WORKFLOW_DELETED = "workflow.deleted"
    
    # Execution events
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_PAUSED = "execution.paused"
    EXECUTION_RESUMED = "execution.resumed"
    EXECUTION_CANCELLED = "execution.cancelled"
    EXECUTION_TIMEOUT = "execution.timeout"
    
    # Node events
    NODE_STARTED = "node.started"
    NODE_COMPLETED = "node.completed"
    NODE_FAILED = "node.failed"
    NODE_SKIPPED = "node.skipped"
    NODE_RETRYING = "node.retrying"
    
    # Approval events
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
    APPROVAL_TIMEOUT = "approval.timeout"
    
    # System events
    DLQ_ENTRY_ADDED = "dlq.entry_added"
    DLQ_ENTRY_RESOLVED = "dlq.entry_resolved"
    CIRCUIT_BREAKER_OPENED = "circuit_breaker.opened"
    CIRCUIT_BREAKER_CLOSED = "circuit_breaker.closed"


@dataclass
class WorkflowEvent:
    """Represents a workflow event."""
    event_type: WorkflowEventType
    workflow_id: str
    execution_id: Optional[str] = None
    node_id: Optional[str] = None
    user_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["event_type"] = self.event_type.value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowEvent":
        """Create from dictionary."""
        data["event_type"] = WorkflowEventType(data["event_type"])
        return cls(**data)


# Type alias for event handlers
EventHandler = Callable[[WorkflowEvent], Awaitable[None]]


class WorkflowEventBus:
    """
    Event bus for workflow system.
    
    Features:
    - Pub/sub pattern for loose coupling
    - Async event handling
    - Event persistence (optional)
    - Dead letter handling for failed handlers
    - Event replay capability
    """
    
    def __init__(self, redis_client=None, persist_events: bool = True):
        """
        Initialize event bus.
        
        Args:
            redis_client: Optional Redis client for distributed pub/sub
            persist_events: Whether to persist events for replay
        """
        self.redis = redis_client
        self.persist_events = persist_events
        
        # Local subscribers
        self._subscribers: Dict[WorkflowEventType, List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []
        
        # Event history (in-memory, limited)
        self._event_history: List[WorkflowEvent] = []
        self._max_history = 1000
        
        # Failed handler tracking
        self._failed_handlers: List[Dict[str, Any]] = []
    
    def subscribe(
        self,
        event_type: WorkflowEventType,
        handler: EventHandler,
    ) -> Callable[[], None]:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Async handler function
            
        Returns:
            Unsubscribe function
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type.value}: {handler.__name__}")
        
        def unsubscribe():
            self._subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed from {event_type.value}: {handler.__name__}")
        
        return unsubscribe
    
    def subscribe_all(self, handler: EventHandler) -> Callable[[], None]:
        """
        Subscribe to all events.
        
        Args:
            handler: Async handler function
            
        Returns:
            Unsubscribe function
        """
        self._global_subscribers.append(handler)
        logger.debug(f"Subscribed to all events: {handler.__name__}")
        
        def unsubscribe():
            self._global_subscribers.remove(handler)
        
        return unsubscribe
    
    async def publish(self, event: WorkflowEvent) -> None:
        """
        Publish an event.
        
        Args:
            event: Event to publish
        """
        logger.info(f"Publishing event: {event.event_type.value} for workflow {event.workflow_id}")
        
        # Persist event
        if self.persist_events:
            await self._persist_event(event)
        
        # Get handlers
        handlers = list(self._global_subscribers)
        if event.event_type in self._subscribers:
            handlers.extend(self._subscribers[event.event_type])
        
        # Execute handlers concurrently
        if handlers:
            results = await asyncio.gather(
                *[self._safe_handle(handler, event) for handler in handlers],
                return_exceptions=True,
            )
            
            # Log any failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Handler failed: {handlers[i].__name__} - {result}")
        
        # Publish to Redis for distributed subscribers
        if self.redis:
            try:
                await self.redis.publish(
                    f"workflow:events:{event.event_type.value}",
                    event.to_json(),
                )
            except Exception as e:
                logger.warning(f"Redis publish failed: {e}")
    
    async def _safe_handle(
        self,
        handler: EventHandler,
        event: WorkflowEvent,
    ) -> None:
        """Safely execute handler with error tracking."""
        try:
            await handler(event)
        except Exception as e:
            self._failed_handlers.append({
                "handler": handler.__name__,
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            raise
    
    async def _persist_event(self, event: WorkflowEvent) -> None:
        """Persist event for replay."""
        # Add to local history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Persist to Redis
        if self.redis:
            try:
                key = f"workflow:events:history:{event.workflow_id}"
                await self.redis.lpush(key, event.to_json())
                await self.redis.ltrim(key, 0, 99)  # Keep last 100 events per workflow
                await self.redis.expire(key, 86400 * 7)  # 7 days TTL
            except Exception as e:
                logger.warning(f"Event persistence failed: {e}")
    
    async def get_events(
        self,
        workflow_id: Optional[str] = None,
        event_type: Optional[WorkflowEventType] = None,
        execution_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[WorkflowEvent]:
        """
        Get historical events.
        
        Args:
            workflow_id: Filter by workflow
            event_type: Filter by event type
            execution_id: Filter by execution
            limit: Max events to return
            
        Returns:
            List of events
        """
        events = self._event_history.copy()
        
        # Try to get from Redis first
        if self.redis and workflow_id:
            try:
                key = f"workflow:events:history:{workflow_id}"
                data = await self.redis.lrange(key, 0, limit - 1)
                events = [WorkflowEvent.from_dict(json.loads(d)) for d in data]
            except Exception as e:
                logger.warning(f"Redis event fetch failed: {e}")
        
        # Apply filters
        if workflow_id:
            events = [e for e in events if e.workflow_id == workflow_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if execution_id:
            events = [e for e in events if e.execution_id == execution_id]
        
        return events[:limit]
    
    async def replay_events(
        self,
        workflow_id: str,
        from_event_id: Optional[str] = None,
        handler: Optional[EventHandler] = None,
    ) -> int:
        """
        Replay events for a workflow.
        
        Args:
            workflow_id: Workflow ID
            from_event_id: Start from this event (exclusive)
            handler: Optional specific handler to replay to
            
        Returns:
            Number of events replayed
        """
        events = await self.get_events(workflow_id=workflow_id, limit=1000)
        
        # Find starting point
        start_idx = 0
        if from_event_id:
            for i, event in enumerate(events):
                if event.event_id == from_event_id:
                    start_idx = i + 1
                    break
        
        events_to_replay = events[start_idx:]
        
        for event in events_to_replay:
            if handler:
                await self._safe_handle(handler, event)
            else:
                await self.publish(event)
        
        logger.info(f"Replayed {len(events_to_replay)} events for workflow {workflow_id}")
        return len(events_to_replay)


# Global event bus instance
_event_bus: Optional[WorkflowEventBus] = None


def get_event_bus(redis_client=None) -> WorkflowEventBus:
    """Get or create global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = WorkflowEventBus(redis_client)
    return _event_bus


# Convenience functions for publishing common events
async def emit_execution_started(
    workflow_id: str,
    execution_id: str,
    input_data: Dict[str, Any],
    user_id: Optional[str] = None,
) -> None:
    """Emit execution started event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.EXECUTION_STARTED,
        workflow_id=workflow_id,
        execution_id=execution_id,
        user_id=user_id,
        data={"input_data": input_data},
    )
    await get_event_bus().publish(event)


async def emit_execution_completed(
    workflow_id: str,
    execution_id: str,
    output_data: Any,
    duration_ms: float,
) -> None:
    """Emit execution completed event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.EXECUTION_COMPLETED,
        workflow_id=workflow_id,
        execution_id=execution_id,
        data={
            "output_data": output_data,
            "duration_ms": duration_ms,
        },
    )
    await get_event_bus().publish(event)


async def emit_execution_failed(
    workflow_id: str,
    execution_id: str,
    error: str,
    error_type: str,
    node_id: Optional[str] = None,
) -> None:
    """Emit execution failed event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.EXECUTION_FAILED,
        workflow_id=workflow_id,
        execution_id=execution_id,
        node_id=node_id,
        data={
            "error": error,
            "error_type": error_type,
        },
    )
    await get_event_bus().publish(event)


async def emit_node_started(
    workflow_id: str,
    execution_id: str,
    node_id: str,
    node_type: str,
) -> None:
    """Emit node started event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.NODE_STARTED,
        workflow_id=workflow_id,
        execution_id=execution_id,
        node_id=node_id,
        data={"node_type": node_type},
    )
    await get_event_bus().publish(event)


async def emit_node_completed(
    workflow_id: str,
    execution_id: str,
    node_id: str,
    node_type: str,
    duration_ms: float,
    output: Any = None,
) -> None:
    """Emit node completed event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.NODE_COMPLETED,
        workflow_id=workflow_id,
        execution_id=execution_id,
        node_id=node_id,
        data={
            "node_type": node_type,
            "duration_ms": duration_ms,
            "output_preview": str(output)[:200] if output else None,
        },
    )
    await get_event_bus().publish(event)
