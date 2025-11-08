"""Notification database models."""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.db.database import Base


class NotificationType(str, enum.Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class Notification(Base):
    """Notification model for user notifications."""
    
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Notification content
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.INFO)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Action
    action_url = Column(String(500), nullable=True)
    action_label = Column(String(100), nullable=True)
    
    # Metadata (using extra_data to avoid SQLAlchemy reserved word)
    extra_data = Column(JSON, default=dict)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    # Note: back_populates commented out because User.notifications is commented out
    user = relationship("User")  # back_populates="notifications"
    
    # Indexes
    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_is_read", "is_read"),
        Index("idx_notifications_created_at", "created_at"),
        Index("idx_notifications_user_unread", "user_id", "is_read"),
    )
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, title={self.title})>"


class NotificationSettings(Base):
    """User notification settings."""
    
    __tablename__ = "notification_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Email notifications
    email_notifications = Column(Boolean, default=True)
    
    # Push notifications
    push_notifications = Column(Boolean, default=True)
    
    # Event-specific settings
    notify_on_share = Column(Boolean, default=True)
    notify_on_comment = Column(Boolean, default=True)
    notify_on_mention = Column(Boolean, default=True)
    notify_on_system_update = Column(Boolean, default=False)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), default="22:00")  # HH:MM format
    quiet_hours_end = Column(String(5), default="08:00")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # Note: back_populates commented out because User.notification_settings is commented out
    user = relationship("User")  # back_populates="notification_settings"
    
    # Indexes
    __table_args__ = (
        Index("idx_notification_settings_user_id", "user_id"),
    )
    
    def __repr__(self):
        return f"<NotificationSettings(user_id={self.user_id})>"
