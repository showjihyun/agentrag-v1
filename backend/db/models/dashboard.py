"""
Dashboard Database Models

Stores user dashboard layouts and widget configurations.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.db.session import Base


class DashboardLayout(Base):
    """User dashboard layout configuration."""
    
    __tablename__ = "dashboard_layouts"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), default="Default Dashboard")
    theme = Column(String(50), default="default")
    columns = Column(Integer, default=12)
    row_height = Column(Integer, default=100)
    is_default = Column(Integer, default=1)  # SQLite compatible boolean
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    widgets = relationship("DashboardWidget", back_populates="layout", cascade="all, delete-orphan")


class DashboardWidget(Base):
    """Dashboard widget configuration."""
    
    __tablename__ = "dashboard_widgets"
    
    id = Column(String(36), primary_key=True)
    layout_id = Column(String(36), ForeignKey("dashboard_layouts.id"), nullable=False, index=True)
    widget_type = Column(String(50), nullable=False)  # workflow_stats, recent_executions, etc.
    title = Column(String(100), nullable=False)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    width = Column(Integer, default=6)
    height = Column(Integer, default=2)
    config = Column(JSON, default=dict)  # Widget-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    layout = relationship("DashboardLayout", back_populates="widgets")
