"""
Event Sourcing Implementation

Stores all changes as a sequence of events, enabling:
- Complete audit trail
- Time travel (replay to any point)
- Event replay for debugging
- CQRS pattern support
"""

import logging
import json
import uuid
from typing import List, Optional, Dict, Any, Type
from datetime import datetime
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import redis.asyncio as redis
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """Base class for domain events."""
    
    id: str
    aggregate_id: str
    aggregate_type: str
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    version: int
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create from dictionary."""
        return cls(**data)


class Aggregate(ABC):
    """
    Base class for aggregates in event sourcing.
    
    An aggregate is a cluster of domain objects that can be treated
    as a single unit for data changes.
    """
    
    def __init__(self, aggregate_id: str):
        """
        Initialize aggregate.
        
        Args:
            aggregate_id: Unique aggregate identifier
        """
        self.id = aggregate_id
        self.version = 0
        self.uncommitted_events: List[DomainEvent] = []
    
    @abstractmethod
    def apply_event(self, event: DomainEvent):
        """
        Apply an event to update aggregate state.
        
        Args:
            event: Domain event to apply
        """
        pass
    
    def raise_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Raise a new domain event.
        
        Args:
            event_type: Type of event
            data: Event data
            user_id: User who triggered the event
            correlation_id: Correlation ID for tracking
        """
        event = DomainEvent(
            id=str(uuid.uuid4()),
            aggregate_id=self.id,
            aggregate_type=self.__class__.__name__,
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            version=self.version + 1,
            user_id=user_id,
            correlation_id=correlation_id
        )
        
        self.uncommitted_events.append(event)
        self.apply_event(event)
        self.version += 1
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get uncommitted events."""
        return self.uncommitted_events.copy()
    
    def mark_events_as_committed(self):
        """Mark all uncommitted events as committed."""
        self.uncommitted_events.clear()
    
    def load_from_history(self, events: List[DomainEvent]):
        """
        Rebuild aggregate state from event history.
        
        Args:
            events: Historical events
        """
        for event in events:
            self.apply_event(event)
            self.version = event.version


class EventStore:
    """
    Event Store for persisting domain events.
    
    Stores events in both PostgreSQL (for querying) and Redis (for caching).
    """
    
    def __init__(
        self,
        db: Session,
        redis_client: redis.Redis
    ):
        """
        Initialize Event Store.
        
        Args:
            db: Database session
            redis_client: Redis client
        """
        self.db = db
        self.redis = redis_client
    
    async def save_events(
        self,
        aggregate_id: str,
        events: List[DomainEvent],
        expected_version: int
    ):
        """
        Save events to the event store.
        
        Args:
            aggregate_id: Aggregate ID
            events: Events to save
            expected_version: Expected current version (for optimistic locking)
            
        Raises:
            ConcurrencyError: If version mismatch detected
        """
        if not events:
            return
        
        # Check version for optimistic locking
        current_version = await self._get_current_version(aggregate_id)
        
        if current_version != expected_version:
            raise ConcurrencyError(
                f"Version mismatch: expected {expected_version}, "
                f"got {current_version}"
            )
        
        # Save to database
        from backend.db.models.event_store import EventStoreModel
        
        for event in events:
            event_model = EventStoreModel(
                id=event.id,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                event_type=event.event_type,
                data=event.data,
                timestamp=datetime.fromisoformat(event.timestamp),
                version=event.version,
                user_id=event.user_id,
                correlation_id=event.correlation_id
            )
            self.db.add(event_model)
        
        self.db.commit()
        
        # Cache in Redis
        await self._cache_events(aggregate_id, events)
        
        logger.info(
            f"Saved {len(events)} events for aggregate {aggregate_id}",
            extra={
                "aggregate_id": aggregate_id,
                "event_count": len(events),
                "version": events[-1].version
            }
        )
    
    async def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0
    ) -> List[DomainEvent]:
        """
        Get events for an aggregate.
        
        Args:
            aggregate_id: Aggregate ID
            from_version: Start from this version (default: 0)
            
        Returns:
            List of domain events
        """
        # Try cache first
        cached_events = await self._get_cached_events(aggregate_id, from_version)
        if cached_events:
            return cached_events
        
        # Load from database
        from backend.db.models.event_store import EventStoreModel
        
        query = self.db.query(EventStoreModel).filter(
            EventStoreModel.aggregate_id == aggregate_id,
            EventStoreModel.version > from_version
        ).order_by(EventStoreModel.version)
        
        event_models = query.all()
        
        events = [
            DomainEvent(
                id=model.id,
                aggregate_id=model.aggregate_id,
                aggregate_type=model.aggregate_type,
                event_type=model.event_type,
                data=model.data,
                timestamp=model.timestamp.isoformat(),
                version=model.version,
                user_id=model.user_id,
                correlation_id=model.correlation_id
            )
            for model in event_models
        ]
        
        # Cache for future use
        if events:
            await self._cache_events(aggregate_id, events)
        
        return events
    
    async def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100
    ) -> List[DomainEvent]:
        """
        Get events by type.
        
        Args:
            event_type: Event type
            limit: Maximum number of events
            
        Returns:
            List of domain events
        """
        from backend.db.models.event_store import EventStoreModel
        
        query = self.db.query(EventStoreModel).filter(
            EventStoreModel.event_type == event_type
        ).order_by(EventStoreModel.timestamp.desc()).limit(limit)
        
        event_models = query.all()
        
        return [
            DomainEvent(
                id=model.id,
                aggregate_id=model.aggregate_id,
                aggregate_type=model.aggregate_type,
                event_type=model.event_type,
                data=model.data,
                timestamp=model.timestamp.isoformat(),
                version=model.version,
                user_id=model.user_id,
                correlation_id=model.correlation_id
            )
            for model in event_models
        ]
    
    async def _get_current_version(self, aggregate_id: str) -> int:
        """Get current version of aggregate."""
        from backend.db.models.event_store import EventStoreModel
        
        result = self.db.query(EventStoreModel.version).filter(
            EventStoreModel.aggregate_id == aggregate_id
        ).order_by(EventStoreModel.version.desc()).first()
        
        return result[0] if result else 0
    
    async def _cache_events(self, aggregate_id: str, events: List[DomainEvent]):
        """Cache events in Redis."""
        key = f"events:{aggregate_id}"
        
        for event in events:
            await self.redis.zadd(
                key,
                {json.dumps(event.to_dict()): event.version}
            )
        
        # Set expiration (1 hour)
        await self.redis.expire(key, 3600)
    
    async def _get_cached_events(
        self,
        aggregate_id: str,
        from_version: int
    ) -> Optional[List[DomainEvent]]:
        """Get cached events from Redis."""
        key = f"events:{aggregate_id}"
        
        # Get events with version > from_version
        cached = await self.redis.zrangebyscore(
            key,
            min=from_version + 1,
            max="+inf"
        )
        
        if not cached:
            return None
        
        return [
            DomainEvent.from_dict(json.loads(event))
            for event in cached
        ]


class ConcurrencyError(Exception):
    """Raised when optimistic locking detects a version mismatch."""
    pass


class Repository:
    """
    Repository for loading and saving aggregates.
    
    Implements the Repository pattern with event sourcing.
    """
    
    def __init__(self, event_store: EventStore):
        """
        Initialize Repository.
        
        Args:
            event_store: Event store instance
        """
        self.event_store = event_store
    
    async def load(
        self,
        aggregate_type: Type[Aggregate],
        aggregate_id: str
    ) -> Optional[Aggregate]:
        """
        Load an aggregate from event history.
        
        Args:
            aggregate_type: Aggregate class
            aggregate_id: Aggregate ID
            
        Returns:
            Aggregate instance or None if not found
        """
        events = await self.event_store.get_events(aggregate_id)
        
        if not events:
            return None
        
        # Create aggregate and replay events
        aggregate = aggregate_type(aggregate_id)
        aggregate.load_from_history(events)
        
        return aggregate
    
    async def save(self, aggregate: Aggregate):
        """
        Save an aggregate by persisting its uncommitted events.
        
        Args:
            aggregate: Aggregate to save
        """
        events = aggregate.get_uncommitted_events()
        
        if not events:
            return
        
        # Save events
        await self.event_store.save_events(
            aggregate_id=aggregate.id,
            events=events,
            expected_version=aggregate.version - len(events)
        )
        
        # Mark as committed
        aggregate.mark_events_as_committed()
