"""Rate limit configuration models."""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.db.database import Base


class RateLimitTier(str, enum.Enum):
    """Rate limit tier levels."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class RateLimitScope(str, enum.Enum):
    """Rate limit scope."""
    GLOBAL = "global"  # Default for all users
    ORGANIZATION = "organization"  # Per organization
    USER = "user"  # Per user
    API_KEY = "api_key"  # Per API key


class RateLimitConfig(Base):
    """
    Rate limit configuration table.
    
    Allows admins to configure rate limits for different scopes.
    """
    __tablename__ = "rate_limit_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Scope
    scope = Column(SQLEnum(RateLimitScope), nullable=False, default=RateLimitScope.GLOBAL)
    scope_id = Column(String(255), nullable=True)  # organization_id, user_id, or api_key_id
    
    # Tier
    tier = Column(SQLEnum(RateLimitTier), nullable=False, default=RateLimitTier.FREE)
    
    # Rate limits
    requests_per_minute = Column(Integer, nullable=False, default=60)
    requests_per_hour = Column(Integer, nullable=False, default=1000)
    requests_per_day = Column(Integer, nullable=False, default=10000)
    
    # Per-endpoint overrides (optional)
    endpoint_overrides = Column(JSONB, nullable=True)
    # Example: {"POST /api/v1/agents/execute": {"rpm": 10, "rph": 100, "rpd": 1000}}
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    name = Column(String(255), nullable=True)
    description = Column(String(500), nullable=True)
    
    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<RateLimitConfig {self.tier} - {self.scope}:{self.scope_id}>"


class RateLimitOverride(Base):
    """
    Temporary rate limit overrides.
    
    For special cases like events, testing, or temporary increases.
    """
    __tablename__ = "rate_limit_overrides"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Target
    scope = Column(SQLEnum(RateLimitScope), nullable=False)
    scope_id = Column(String(255), nullable=False)
    
    # Override limits
    requests_per_minute = Column(Integer, nullable=True)
    requests_per_hour = Column(Integer, nullable=True)
    requests_per_day = Column(Integer, nullable=True)
    
    # Time-based
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    reason = Column(String(500), nullable=True)
    
    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    
    def is_valid(self) -> bool:
        """Check if override is currently valid."""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.starts_at <= now <= self.expires_at
        )
    
    def __repr__(self):
        return f"<RateLimitOverride {self.scope}:{self.scope_id} until {self.expires_at}>"


class RateLimitUsage(Base):
    """
    Rate limit usage tracking.
    
    Stores usage statistics for monitoring and analytics.
    """
    __tablename__ = "rate_limit_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identifier
    identifier = Column(String(255), nullable=False, index=True)
    
    # Usage
    endpoint = Column(String(255), nullable=True)
    requests_count = Column(Integer, nullable=False, default=0)
    blocked_count = Column(Integer, nullable=False, default=0)
    
    # Time window
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False)
    window_type = Column(String(20), nullable=False)  # minute, hour, day
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RateLimitUsage {self.identifier} - {self.requests_count} requests>"
