"""Custom Tools database models."""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class CustomTool(Base):
    """User-created custom tools."""

    __tablename__ = "custom_tools"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, default="custom")
    icon = Column(String(50), default="🔧")
    
    # Configuration
    method = Column(String(10), nullable=False, default="GET")  # GET, POST, PUT, DELETE
    url = Column(Text, nullable=False)
    headers = Column(JSON, default=dict)  # {"Authorization": "Bearer {{api_key}}"}
    query_params = Column(JSON, default=dict)
    body_template = Column(JSON, default=dict)
    
    # Parameters (input)
    parameters = Column(JSON, default=list)  # [{"name": "query", "type": "string", "required": true}]
    
    # Outputs (response mapping)
    outputs = Column(JSON, default=list)  # [{"name": "result", "path": "data.result"}]
    
    # Authentication
    requires_auth = Column(Boolean, default=False)
    auth_type = Column(String(20))  # api_key, oauth2, basic
    auth_config = Column(JSON, default=dict)
    
    # Sharing
    is_public = Column(Boolean, default=False)
    is_marketplace = Column(Boolean, default=False)
    
    # Testing
    test_data = Column(JSON, default=dict)  # Sample test parameters
    last_test_result = Column(JSON)
    last_test_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage stats
    usage_count = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index("idx_custom_tools_user_id", "user_id"),
        Index("idx_custom_tools_category", "category"),
        Index("idx_custom_tools_public", "is_public"),
        Index("idx_custom_tools_marketplace", "is_marketplace"),
    )


class CustomToolUsage(Base):
    """Track custom tool usage."""

    __tablename__ = "custom_tool_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    tool_id = Column(
        UUID(as_uuid=True),
        ForeignKey("custom_tools.id", ondelete="CASCADE"),
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
    )
    
    # Execution details
    input_data = Column(JSON)
    output_data = Column(JSON)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    duration_ms = Column(Integer)
    
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index("idx_custom_tool_usage_tool_id", "tool_id"),
        Index("idx_custom_tool_usage_user_id", "user_id"),
        Index("idx_custom_tool_usage_executed_at", "executed_at"),
    )


class CustomToolRating(Base):
    """User ratings for marketplace tools."""

    __tablename__ = "custom_tool_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    tool_id = Column(
        UUID(as_uuid=True),
        ForeignKey("custom_tools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    rating = Column(Integer, nullable=False)  # 1-5
    review = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_custom_tool_ratings_tool_id", "tool_id"),
        Index("idx_custom_tool_ratings_user_id", "user_id"),
    )
