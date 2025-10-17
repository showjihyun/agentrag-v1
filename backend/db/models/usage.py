"""Usage tracking model."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class UsageLog(Base):
    """Usage log model for tracking user activity."""

    __tablename__ = "usage_logs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Usage Information
    action = Column(String(100), nullable=False, index=True)  # query, upload, download
    resource_type = Column(String(100))  # document, message, session
    resource_id = Column(UUID(as_uuid=True))

    # Cost Information
    tokens_used = Column(Integer)
    processing_time_ms = Column(Integer)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="usage_logs")

    # Composite Indexes for common query patterns
    __table_args__ = (
        Index("ix_usage_logs_user_action_created", "user_id", "action", "created_at"),
    )

    def __repr__(self):
        return f"<UsageLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
