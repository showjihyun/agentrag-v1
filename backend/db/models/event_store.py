# Database model for Event Store

from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.sql import func
from backend.db.database import Base


class EventStoreModel(Base):
    """Event Store table for storing all domain events."""
    
    __tablename__ = "event_store"
    
    id = Column(Integer, primary_key=True, index=True)
    aggregate_id = Column(String, nullable=False, index=True)
    aggregate_type = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    user_id = Column(Integer, nullable=True, index=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_aggregate_version', 'aggregate_id', 'version'),
        Index('idx_aggregate_type_timestamp', 'aggregate_type', 'timestamp'),
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )
