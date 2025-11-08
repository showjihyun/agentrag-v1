"""
Event Store Database Model

Stores domain events for event sourcing.
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from backend.db.database import Base


class EventStoreModel(Base):
    """Event Store table for persisting domain events."""
    
    __tablename__ = "event_store"
    
    # Primary key
    id = Column(String(36), primary_key=True)
    
    # Aggregate information
    aggregate_id = Column(String(36), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False, index=True)
    
    # Event information
    event_type = Column(String(100), nullable=False, index=True)
    data = Column(JSON, nullable=False)
    
    # Versioning
    version = Column(Integer, nullable=False)
    
    # Metadata
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    correlation_id = Column(String(36), nullable=True, index=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_aggregate_version", "aggregate_id", "version", unique=True),
        Index("idx_event_type_timestamp", "event_type", "timestamp"),
        Index("idx_correlation", "correlation_id"),
    )
    
    def __repr__(self):
        return (
            f"<EventStoreModel(id={self.id}, "
            f"aggregate_id={self.aggregate_id}, "
            f"event_type={self.event_type}, "
            f"version={self.version})>"
        )
