"""OAuth authentication models."""

from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime

from backend.db.database import Base


class OAuthCredential(Base):
    """Model for storing OAuth credentials."""
    
    __tablename__ = "oauth_credentials"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    tool_id = Column(String, nullable=False, index=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String, default="Bearer")
    expires_at = Column(DateTime, nullable=True)
    scope = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<OAuthCredential(id={self.id}, user_id={self.user_id}, tool_id={self.tool_id})>"


class OAuthState(Base):
    """Model for storing OAuth state during authentication flow."""
    
    __tablename__ = "oauth_states"
    
    state = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    tool_id = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<OAuthState(state={self.state}, user_id={self.user_id}, tool_id={self.tool_id})>"
