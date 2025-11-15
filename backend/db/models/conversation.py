"""Conversation models."""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class Session(Base):
    """Conversation session model."""

    __tablename__ = "sessions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session Info
    title = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True,
    )
    last_message_at = Column(DateTime)

    # Metadata
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )
    answer_feedbacks = relationship(
        "AnswerFeedback", back_populates="session", cascade="all, delete-orphan"
    )

    # Composite Indexes and Constraints
    __table_args__ = (
        Index("ix_sessions_user_updated", "user_id", "updated_at"),
        CheckConstraint("message_count >= 0", name="check_message_count_positive"),
        CheckConstraint("total_tokens >= 0", name="check_total_tokens_positive"),
    )

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, title={self.title})>"


class Message(Base):
    """Message model for conversation history."""

    __tablename__ = "messages"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message Content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Query Metadata
    query_mode = Column(String(50))  # fast, balanced, deep
    processing_time_ms = Column(Integer)
    confidence_score = Column(Float)

    # Cache Information
    cache_hit = Column(Boolean, default=False)
    cache_match_type = Column(String(50))  # exact, semantic_high, semantic_medium
    cache_similarity = Column(Float)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Additional Metadata
    extra_metadata = Column(JSONB, default=dict)

    # Relationships
    session = relationship("Session", back_populates="messages")
    user = relationship("User", back_populates="messages")
    sources = relationship(
        "MessageSource", back_populates="message", cascade="all, delete-orphan"
    )
    feedback = relationship(
        "AnswerFeedback", back_populates="message", cascade="all, delete-orphan"
    )

    # Composite Indexes and Constraints
    __table_args__ = (
        Index("ix_messages_user_session", "user_id", "session_id"),
        Index("ix_messages_session_created", "session_id", "created_at"),
        Index("ix_messages_user_created", "user_id", "created_at"),
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')", name="check_role_valid"
        ),
        CheckConstraint(
            "processing_time_ms >= 0", name="check_processing_time_positive"
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="check_confidence_score_range",
        ),
    )

    def __repr__(self):
        return (
            f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"
        )


class MessageSource(Base):
    """Source document reference for messages."""

    __tablename__ = "message_sources"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source Information
    document_id = Column(String(255), nullable=False, index=True)
    document_name = Column(String(255), nullable=False)
    chunk_id = Column(String(255))
    score = Column(Float)

    # Content
    text = Column(Text)

    # Metadata
    extra_metadata = Column(JSONB, default=dict)

    # Relationships
    message = relationship("Message", back_populates="sources")

    def __repr__(self):
        return f"<MessageSource(id={self.id}, document_name={self.document_name})>"
