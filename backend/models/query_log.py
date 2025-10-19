"""
Query Log Model
Stores query execution logs for monitoring and analytics
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from backend.db.database import Base


class QueryLog(Base):
    """Query execution log for monitoring and analytics"""
    
    __tablename__ = "query_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_mode = Column(String(50))  # fast, balanced, deep
    
    # Performance metrics
    response_time_ms = Column(Float)
    confidence_score = Column(Float)
    
    # Query metadata (JSON field for flexible data)
    # Note: Using 'query_metadata' instead of 'metadata' to avoid SQLAlchemy reserved word
    query_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<QueryLog(id={self.id}, mode={self.query_mode}, time={self.response_time_ms}ms)>"
