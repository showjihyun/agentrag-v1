# Event Store for Event Sourcing
# Stores all domain events for audit logging and time-travel debugging

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class DomainEvent:
    """Base class for all domain events."""
    
    def __init__(
        self,
        aggregate_id: str,
        aggregate_type: str,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.event_type = event_type
        self.event_data = event_data
        self.user_id = user_id
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.version = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create event from dictionary."""
        event = cls(
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            event_type=data["event_type"],
            event_data=data["event_data"],
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {})
        )
        event.timestamp = datetime.fromisoformat(data["timestamp"])
        event.version = data.get("version", 1)
        return event


class EventStore:
    """
    Event Store for storing and retrieving domain events.
    
    Features:
    - Store all domain events
    - Retrieve events by aggregate
    - Replay events for time-travel debugging
    - Audit logging
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def append(
        self,
        event: DomainEvent
    ) -> int:
        """
        Append a new event to the store.
        
        Args:
            event: Domain event to store
            
        Returns:
            Event ID
        """
        from backend.db.models.event_store import EventStoreModel
        
        try:
            # Create event record
            event_record = EventStoreModel(
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                event_type=event.event_type,
                event_data=event.event_data,
                user_id=event.user_id,
                metadata=event.metadata,
                timestamp=event.timestamp,
                version=event.version
            )
            
            self.db.add(event_record)
            self.db.commit()
            self.db.refresh(event_record)
            
            logger.info(
                "Event stored",
                extra={
                    "event_id": event_record.id,
                    "aggregate_id": event.aggregate_id,
                    "event_type": event.event_type
                }
            )
            
            return event_record.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to store event: {e}", exc_info=True)
            raise
    
    async def get_events(
        self,
        aggregate_id: str,
        aggregate_type: Optional[str] = None,
        from_version: int = 0
    ) -> List[DomainEvent]:
        """
        Get all events for an aggregate.
        
        Args:
            aggregate_id: Aggregate identifier
            aggregate_type: Optional aggregate type filter
            from_version: Start from this version
            
        Returns:
            List of domain events
        """
        from backend.db.models.event_store import EventStoreModel
        
        try:
            query = self.db.query(EventStoreModel).filter(
                EventStoreModel.aggregate_id == aggregate_id,
                EventStoreModel.version >= from_version
            )
            
            if aggregate_type:
                query = query.filter(EventStoreModel.aggregate_type == aggregate_type)
            
            query = query.order_by(EventStoreModel.version.asc())
            
            records = query.all()
            
            events = [
                DomainEvent(
                    aggregate_id=record.aggregate_id,
                    aggregate_type=record.aggregate_type,
                    event_type=record.event_type,
                    event_data=record.event_data,
                    user_id=record.user_id,
                    metadata=record.metadata
                )
                for record in records
            ]
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events: {e}", exc_info=True)
            raise
    
    async def replay(
        self,
        aggregate_id: str,
        aggregate_type: str,
        to_version: Optional[int] = None
    ) -> List[DomainEvent]:
        """
        Replay events up to a specific version (time-travel debugging).
        
        Args:
            aggregate_id: Aggregate identifier
            aggregate_type: Aggregate type
            to_version: Replay up to this version (None = all)
            
        Returns:
            List of events up to version
        """
        from backend.db.models.event_store import EventStoreModel
        
        try:
            query = self.db.query(EventStoreModel).filter(
                EventStoreModel.aggregate_id == aggregate_id,
                EventStoreModel.aggregate_type == aggregate_type
            )
            
            if to_version is not None:
                query = query.filter(EventStoreModel.version <= to_version)
            
            query = query.order_by(EventStoreModel.version.asc())
            
            records = query.all()
            
            events = [
                DomainEvent(
                    aggregate_id=record.aggregate_id,
                    aggregate_type=record.aggregate_type,
                    event_type=record.event_type,
                    event_data=record.event_data,
                    user_id=record.user_id,
                    metadata=record.metadata
                )
                for record in records
            ]
            
            logger.info(
                "Events replayed",
                extra={
                    "aggregate_id": aggregate_id,
                    "event_count": len(events),
                    "to_version": to_version
                }
            )
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to replay events: {e}", exc_info=True)
            raise
    
    async def get_audit_log(
        self,
        user_id: Optional[int] = None,
        aggregate_type: Optional[str] = None,
        event_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[DomainEvent]:
        """
        Get audit log with filters.
        
        Args:
            user_id: Filter by user
            aggregate_type: Filter by aggregate type
            event_type: Filter by event type
            from_date: Start date
            to_date: End date
            limit: Maximum number of events
            
        Returns:
            List of events matching filters
        """
        from backend.db.models.event_store import EventStoreModel
        
        try:
            query = self.db.query(EventStoreModel)
            
            if user_id:
                query = query.filter(EventStoreModel.user_id == user_id)
            
            if aggregate_type:
                query = query.filter(EventStoreModel.aggregate_type == aggregate_type)
            
            if event_type:
                query = query.filter(EventStoreModel.event_type == event_type)
            
            if from_date:
                query = query.filter(EventStoreModel.timestamp >= from_date)
            
            if to_date:
                query = query.filter(EventStoreModel.timestamp <= to_date)
            
            query = query.order_by(EventStoreModel.timestamp.desc()).limit(limit)
            
            records = query.all()
            
            events = [
                DomainEvent(
                    aggregate_id=record.aggregate_id,
                    aggregate_type=record.aggregate_type,
                    event_type=record.event_type,
                    event_data=record.event_data,
                    user_id=record.user_id,
                    metadata=record.metadata
                )
                for record in records
            ]
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get audit log: {e}", exc_info=True)
            raise


# Singleton instance
_event_store: Optional[EventStore] = None


def get_event_store(db: Session) -> EventStore:
    """Get or create event store instance."""
    return EventStore(db)
