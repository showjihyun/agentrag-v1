"""Tool-related database models."""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class ToolCredential(Base):
    """Tool credential model for storing encrypted credentials."""

    __tablename__ = "tool_credentials"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_id = Column(
        String(100),
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Credential Information
    name = Column(String(255), nullable=False)
    credentials = Column(Text, nullable=False)  # Encrypted JSON

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    tool_executions = relationship(
        "ToolExecution",
        back_populates="credential",
        cascade="all, delete-orphan"
    )

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_tool_credentials_user_tool", "user_id", "tool_id"),
        Index("idx_tool_credentials_user_active", "user_id", "is_active"),
        UniqueConstraint("user_id", "tool_id", "name", name="uq_tool_credential"),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<ToolCredential(id={self.id}, user_id={self.user_id}, tool_id={self.tool_id})>"


class ToolExecution(Base):
    """Tool execution tracking model."""

    __tablename__ = "tool_executions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    tool_id = Column(
        String(100),
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    credential_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tool_credentials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Execution Information
    parameters = Column(JSONB)  # Input parameters
    result = Column(JSONB)  # Execution result

    # Status
    status = Column(String(50), nullable=False, index=True)
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # Relationships
    credential = relationship("ToolCredential", back_populates="tool_executions")

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_tool_executions_tool_started_desc", "tool_id", "started_at"),
        Index("idx_tool_executions_user_started_desc", "user_id", "started_at"),
        Index("idx_tool_executions_status_started", "status", "started_at"),
        Index("idx_tool_executions_agent_started", "agent_id", "started_at"),
        CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'timeout', 'cancelled')",
            name="check_tool_execution_status_valid",
        ),
        CheckConstraint("duration_ms >= 0", name="check_tool_duration_positive"),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<ToolExecution(id={self.id}, tool_id={self.tool_id}, status={self.status})>"
