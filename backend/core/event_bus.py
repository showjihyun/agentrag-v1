"""
Event Bus Implementation using Redis Streams

Provides publish-subscribe pattern for event-driven architecture.
"""

import asyncio
import json
import logging
import uuid
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

import redis.asyncio as redis


logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event data structure."""
    
    id: str
    type: str
    data: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create from dictionary."""
        return cls(**data)


class EventBus:
    """
    Event Bus using Redis Streams.
    
    Provides publish-subscribe pattern for event-driven architecture.
    Supports event persistence, replay, and guaranteed delivery.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        consumer_group: str = "agent_builder",
        max_stream_length: int = 10000
    ):
        """
        Initialize Event Bus.
        
        Args:
            redis_client: Redis client
            consumer_group: Consumer group name
            max_stream_length: Maximum events to keep in stream
        """
        self.redis = redis_client
        self.consumer_group = consumer_group
        self.max_stream_length = max_stream_length
        self.handlers: Dict[str, List[Callable]] = {}
        self.running = False
        self._consumer_tasks: List[asyncio.Task] = []
    
    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish an event to the event bus.
        
        Args:
            event_type: Type of event (e.g., "agent.created")
            data: Event data
            correlation_id: Correlation ID for tracking related events
            causation_id: ID of event that caused this event
            metadata: Additional metadata
            
        Returns:
            Event ID
        """
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id,
            causation_id=causation_id,
            metadata=metadata or {}
        )
        
        # Serialize event
        event_dict = event.to_dict()
        event_json = {
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in event_dict.items()
        }
        
        # Publish to Redis Stream
        stream_key = f"events:{event_type}"
        
        try:
            await self.redis.xadd(
                stream_key,
                event_json,
                maxlen=self.max_stream_length
            )
            
            logger.info(
                f"Event published: {event_type}",
                extra={
                    "event_id": event.id,
                    "event_type": event_type,
                    "correlation_id": correlation_id
                }
            )
            
            # Trigger local handlers immediately
            await self._trigger_local_handlers(event)
            
            return event.id
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}", exc_info=True)
            raise
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any]
    ):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Async function to handle event
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        
        logger.info(
            f"Handler subscribed to event: {event_type}",
            extra={"handler": handler.__name__}
        )
    
    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any]
    ):
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self.handlers:
            self.handlers[event_type].remove(handler)
            
            logger.info(
                f"Handler unsubscribed from event: {event_type}",
                extra={"handler": handler.__name__}
            )
    
    async def start_consuming(self):
        """Start consuming events from Redis Streams."""
        if self.running:
            logger.warning("Event bus already running")
            return
        
        self.running = True
        
        # Create consumer group for each event type
        for event_type in self.handlers.keys():
            stream_key = f"events:{event_type}"
            
            try:
                # Create consumer group if not exists
                await self.redis.xgroup_create(
                    stream_key,
                    self.consumer_group,
                    id="0",
                    mkstream=True
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    logger.error(f"Failed to create consumer group: {e}")
            
            # Start consumer task
            task = asyncio.create_task(
                self._consume_stream(stream_key, event_type)
            )
            self._consumer_tasks.append(task)
        
        logger.info("Event bus started consuming")
    
    async def stop_consuming(self):
        """Stop consuming events."""
        self.running = False
        
        # Cancel all consumer tasks
        for task in self._consumer_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._consumer_tasks, return_exceptions=True)
        
        self._consumer_tasks.clear()
        
        logger.info("Event bus stopped consuming")
    
    async def _consume_stream(self, stream_key: str, event_type: str):
        """
        Consume events from a Redis Stream.
        
        Args:
            stream_key: Redis stream key
            event_type: Event type
        """
        consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
        
        while self.running:
            try:
                # Read from stream
                messages = await self.redis.xreadgroup(
                    self.consumer_group,
                    consumer_name,
                    {stream_key: ">"},
                    count=10,
                    block=1000  # 1 second timeout
                )
                
                if not messages:
                    continue
                
                # Process messages
                for stream, message_list in messages:
                    for message_id, message_data in message_list:
                        await self._process_message(
                            stream_key,
                            message_id,
                            message_data,
                            event_type
                        )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Error consuming stream {stream_key}: {e}",
                    exc_info=True
                )
                await asyncio.sleep(1)
    
    async def _process_message(
        self,
        stream_key: str,
        message_id: bytes,
        message_data: Dict[bytes, bytes],
        event_type: str
    ):
        """
        Process a message from Redis Stream.
        
        Args:
            stream_key: Stream key
            message_id: Message ID
            message_data: Message data
            event_type: Event type
        """
        try:
            # Deserialize event
            event_dict = {
                k.decode(): v.decode() for k, v in message_data.items()
            }
            
            # Parse JSON fields
            for key in ["data", "metadata"]:
                if key in event_dict and event_dict[key]:
                    event_dict[key] = json.loads(event_dict[key])
            
            event = Event.from_dict(event_dict)
            
            # Trigger handlers
            await self._trigger_local_handlers(event)
            
            # Acknowledge message
            await self.redis.xack(
                stream_key,
                self.consumer_group,
                message_id
            )
            
        except Exception as e:
            logger.error(
                f"Failed to process message {message_id}: {e}",
                exc_info=True
            )
    
    async def _trigger_local_handlers(self, event: Event):
        """
        Trigger local event handlers.
        
        Args:
            event: Event to process
        """
        if event.type not in self.handlers:
            return
        
        handlers = self.handlers[event.type]
        
        # Execute handlers concurrently
        results = await asyncio.gather(
            *[self._execute_handler(handler, event) for handler in handlers],
            return_exceptions=True
        )
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler {handlers[i].__name__} failed: {result}",
                    exc_info=result
                )
    
    async def _execute_handler(self, handler: Callable, event: Event):
        """
        Execute a single handler.
        
        Args:
            handler: Handler function
            event: Event to process
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(
                f"Handler {handler.__name__} raised exception: {e}",
                exc_info=True
            )
            raise
    
    async def get_event_history(
        self,
        event_type: str,
        start: str = "-",
        end: str = "+",
        count: int = 100
    ) -> List[Event]:
        """
        Get event history from stream.
        
        Args:
            event_type: Event type
            start: Start ID (default: oldest)
            end: End ID (default: newest)
            count: Maximum number of events
            
        Returns:
            List of events
        """
        stream_key = f"events:{event_type}"
        
        try:
            messages = await self.redis.xrange(
                stream_key,
                min=start,
                max=end,
                count=count
            )
            
            events = []
            for message_id, message_data in messages:
                event_dict = {
                    k.decode(): v.decode() for k, v in message_data.items()
                }
                
                # Parse JSON fields
                for key in ["data", "metadata"]:
                    if key in event_dict and event_dict[key]:
                        event_dict[key] = json.loads(event_dict[key])
                
                events.append(Event.from_dict(event_dict))
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get event history: {e}", exc_info=True)
            return []
    
    async def replay_events(
        self,
        event_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ):
        """
        Replay events within a time range.
        
        Args:
            event_type: Event type to replay
            start_time: Start time (optional)
            end_time: End time (optional)
        """
        events = await self.get_event_history(event_type)
        
        # Filter by time if specified
        if start_time or end_time:
            filtered_events = []
            for event in events:
                event_time = datetime.fromisoformat(event.timestamp)
                
                if start_time and event_time < start_time:
                    continue
                if end_time and event_time > end_time:
                    continue
                
                filtered_events.append(event)
            
            events = filtered_events
        
        # Replay events
        logger.info(f"Replaying {len(events)} events of type {event_type}")
        
        for event in events:
            await self._trigger_local_handlers(event)


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _event_bus
    if _event_bus is None:
        raise RuntimeError("Event bus not initialized")
    return _event_bus


async def initialize_event_bus(redis_client: redis.Redis) -> EventBus:
    """
    Initialize global event bus.
    
    Args:
        redis_client: Redis client
        
    Returns:
        Event bus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(redis_client)
    return _event_bus


async def cleanup_event_bus():
    """Cleanup global event bus."""
    global _event_bus
    if _event_bus is not None:
        await _event_bus.stop_consuming()
        _event_bus = None
