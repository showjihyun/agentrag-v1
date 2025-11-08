"""Bookmark database models."""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ARRAY, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class Bookmark(Base):
    """Bookmark model for saving conversations and documents."""
    
    __tablename__ = "bookmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Bookmark type and reference
    type = Column(String(50), nullable=False)  # 'conversation' or 'document'
    item_id = Column(String(255), nullable=False)  # ID of the bookmarked item
    
    # Metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=list)
    
    # Status
    is_favorite = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="bookmarks")
    
    # Indexes
    __table_args__ = (
        Index("idx_bookmarks_user_id", "user_id"),
        Index("idx_bookmarks_type", "type"),
        Index("idx_bookmarks_item_id", "item_id"),
        Index("idx_bookmarks_user_type", "user_id", "type"),
        Index("idx_bookmarks_is_favorite", "is_favorite"),
        Index("idx_bookmarks_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<Bookmark(id={self.id}, user_id={self.user_id}, type={self.type}, title={self.title})>"
