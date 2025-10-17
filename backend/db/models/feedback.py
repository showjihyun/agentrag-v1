"""Feedback models for answer quality tracking."""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
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


class AnswerFeedback(Base):
    """Answer quality feedback model."""

    __tablename__ = "answer_feedback"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Query and Answer
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    # Quality Metrics
    overall_score = Column(Float, nullable=False, index=True)
    source_relevance = Column(Float)
    grounding_score = Column(Float)
    hallucination_risk = Column(Float)
    completeness_score = Column(Float)
    length_score = Column(Float)
    citation_score = Column(Float)

    # User Feedback
    user_rating = Column(
        Integer, nullable=True, index=True
    )  # 1=good, 0=neutral, -1=bad
    user_comment = Column(Text, nullable=True)

    # Context
    source_count = Column(Integer, default=0)
    mode = Column(String(50), nullable=True)  # fast, balanced, deep
    quality_level = Column(
        String(20), nullable=True, index=True
    )  # excellent, good, acceptable, poor, very_poor

    # Metadata
    suggestions = Column(JSON, default=list)
    extra_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    feedback_at = Column(DateTime, nullable=True)  # When user provided feedback

    # Relationships
    user = relationship("User", back_populates="answer_feedbacks")
    session = relationship("Session", back_populates="answer_feedbacks")
    message = relationship("Message", back_populates="feedback")

    # Indexes
    __table_args__ = (
        Index("ix_feedback_user_created", "user_id", "created_at"),
        Index("ix_feedback_quality_level", "quality_level", "created_at"),
        Index("ix_feedback_user_rating", "user_rating", "created_at"),
    )

    def __repr__(self):
        return f"<AnswerFeedback(id={self.id}, score={self.overall_score:.2f}, rating={self.user_rating})>"
