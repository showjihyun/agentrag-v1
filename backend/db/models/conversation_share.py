"""Conversation share database models."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.db.database import Base


class ShareRole(str, enum.Enum):
    """Share roles."""
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class ConversationShare(Base):
    """Conversation share model."""
    
    __tablename__ = "conversation_shares"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Share details
    role = Column(Enum(ShareRole), nullable=False, default=ShareRole.VIEWER)
    shared_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="shares")
    user = relationship("User", foreign_keys=[user_id], back_populates="shared_conversations")
    shared_by_user = relationship("User", foreign_keys=[shared_by])
    
    # Indexes
    __table_args__ = (
        Index("idx_conversation_shares_conversation_id", "conversation_id"),
        Index("idx_conversation_shares_user_id", "user_id"),
        Index("idx_conversation_shares_conversation_user", "conversation_id", "user_id", unique=True),
    )
    
    def __repr__(self):
        return f"<ConversationShare(id={self.id}, conversation_id={self.conversation_id}, user_id={self.user_id}, role={self.role})>"
