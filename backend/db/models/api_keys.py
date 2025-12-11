"""
API Keys Database Model
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class APIKey(Base):
    """API Key model for secure authentication"""
    
    __tablename__ = "api_keys"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Key Information
    name = Column(String(255), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_prefix = Column(String(12), nullable=False)  # For display (e.g., "agr_abc...")
    
    # Permissions
    scopes = Column(JSONB, default=list)  # List of allowed scopes
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Usage Tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Rotation
    rotated_at = Column(DateTime, nullable=True)
    rotated_to_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Revocation
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if key is expired"""
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.utcnow()
    
    @property
    def is_valid(self) -> bool:
        """Check if key is valid (active and not expired)"""
        return self.is_active and not self.is_expired
