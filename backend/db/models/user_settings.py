"""
User Settings Database Model

Stores user preferences in the database for persistence.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class UserSettings(Base):
    """User settings stored in database."""
    
    __tablename__ = "user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Notification settings
    notification_settings = Column(JSON, default=dict)
    
    # Security settings
    security_settings = Column(JSON, default=dict)
    
    # Appearance settings
    appearance_settings = Column(JSON, default=dict)
    
    # LLM settings
    llm_settings = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "notification_settings": self.notification_settings or {},
            "security_settings": self.security_settings or {},
            "appearance_settings": self.appearance_settings or {},
            "llm_settings": self.llm_settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EnvironmentVariable(Base):
    """User environment variables stored in database."""
    
    __tablename__ = "environment_variables"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)  # Encrypted in production
    description = Column(String(500), default="")
    is_secret = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on user_id + key
    __table_args__ = (
        {"extend_existing": True},
    )
    
    def __repr__(self):
        return f"<EnvironmentVariable(user_id={self.user_id}, key={self.key})>"
    
    def to_dict(self, mask_secret: bool = True):
        return {
            "id": str(self.id),
            "key": self.key,
            "value": "***" if (self.is_secret and mask_secret) else self.value,
            "description": self.description,
            "is_secret": self.is_secret,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AuditLog(Base):
    """Audit log entries stored in database."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event info
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), default="info")
    action = Column(String(500), nullable=False)
    
    # User info
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    
    # Request info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    
    # Resource info
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    
    # Details
    details = Column(JSON, default=dict)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog(event_type={self.event_type}, user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "severity": self.severity,
            "action": self.action,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_email": self.user_email,
            "ip_address": self.ip_address,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
