"""User model."""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    BigInteger,
    DateTime,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255))

    # Authorization
    role = Column(String(50), default="user")  # user, premium, admin
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login_at = Column(DateTime)

    # Usage Tracking
    query_count = Column(Integer, default=0)
    storage_used_bytes = Column(BigInteger, default=0)

    # Preferences
    preferences = Column(JSONB, default=dict)

    # Relationships
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message", back_populates="user", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )
    batch_uploads = relationship(
        "BatchUpload", back_populates="user", cascade="all, delete-orphan"
    )
    answer_feedbacks = relationship(
        "AnswerFeedback", back_populates="user", cascade="all, delete-orphan"
    )
    usage_logs = relationship(
        "UsageLog", back_populates="user", cascade="all, delete-orphan"
    )
    # notifications = relationship(
    #     "Notification", back_populates="user", cascade="all, delete-orphan"
    # )
    # notification_settings = relationship(
    #     "NotificationSettings", back_populates="user", cascade="all, delete-orphan", uselist=False
    # )
    bookmarks = relationship(
        "Bookmark", back_populates="user", cascade="all, delete-orphan"
    )
    shared_sessions = relationship(
        "ConversationShare",
        foreign_keys="ConversationShare.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )

    # Database Constraints for data integrity
    __table_args__ = (
        CheckConstraint("query_count >= 0", name="check_query_count_positive"),
        CheckConstraint("storage_used_bytes >= 0", name="check_storage_positive"),
        CheckConstraint(
            "role IN ('user', 'premium', 'admin')", name="check_role_valid"
        ),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
