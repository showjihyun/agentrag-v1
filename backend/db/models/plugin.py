"""
SQLAlchemy database models for the plugin system.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

from backend.db.base import Base


class PluginRegistry(Base):
    """Plugin registry table for storing plugin metadata"""
    __tablename__ = "plugin_registry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text)
    author = Column(String(255))
    category = Column(String(50))
    status = Column(String(50), default='registered')
    manifest = Column(JSON, nullable=False)
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64))
    signature = Column(Text)
    installed_at = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    configurations = relationship("PluginConfiguration", back_populates="plugin", cascade="all, delete-orphan")
    metrics = relationship("PluginMetric", back_populates="plugin", cascade="all, delete-orphan")
    dependencies = relationship("PluginDependency", back_populates="plugin", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_plugin_name_version'),
        Index('idx_plugin_registry_name', 'name'),
        Index('idx_plugin_registry_category', 'category'),
        Index('idx_plugin_registry_status', 'status'),
    )


class PluginConfiguration(Base):
    """Plugin configurations table for user-specific settings"""
    __tablename__ = "plugin_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_id = Column(UUID(as_uuid=True), ForeignKey('plugin_registry.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True))  # Reference to user table
    environment = Column(String(50), default='production')
    settings = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    plugin = relationship("PluginRegistry", back_populates="configurations")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('plugin_id', 'user_id', 'environment', name='uq_plugin_config_user_env'),
        Index('idx_plugin_configurations_plugin_user', 'plugin_id', 'user_id'),
    )


class PluginMetric(Base):
    """Plugin metrics table for performance and usage tracking"""
    __tablename__ = "plugin_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_id = Column(UUID(as_uuid=True), ForeignKey('plugin_registry.id', ondelete='CASCADE'), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(String(255))  # Store as string for flexibility
    metric_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    plugin = relationship("PluginRegistry", back_populates="metrics")
    
    # Constraints
    __table_args__ = (
        Index('idx_plugin_metrics_plugin_time', 'plugin_id', 'recorded_at'),
        Index('idx_plugin_metrics_name', 'metric_name'),
    )


class PluginDependency(Base):
    """Plugin dependencies table for dependency management"""
    __tablename__ = "plugin_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_id = Column(UUID(as_uuid=True), ForeignKey('plugin_registry.id', ondelete='CASCADE'), nullable=False)
    dependency_name = Column(String(255), nullable=False)
    version_constraint = Column(String(100))
    optional = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    plugin = relationship("PluginRegistry", back_populates="dependencies")
    
    # Constraints
    __table_args__ = (
        Index('idx_plugin_dependencies_plugin', 'plugin_id'),
        Index('idx_plugin_dependencies_name', 'dependency_name'),
    )


class PluginAuditLog(Base):
    """Plugin audit log for security and compliance tracking"""
    __tablename__ = "plugin_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_id = Column(UUID(as_uuid=True), ForeignKey('plugin_registry.id', ondelete='CASCADE'))
    user_id = Column(UUID(as_uuid=True))  # Reference to user table
    action = Column(String(100), nullable=False)  # install, activate, configure, etc.
    details = Column(JSON)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        Index('idx_plugin_audit_plugin', 'plugin_id'),
        Index('idx_plugin_audit_user', 'user_id'),
        Index('idx_plugin_audit_timestamp', 'timestamp'),
        Index('idx_plugin_audit_action', 'action'),
    )


class PluginSecurityScan(Base):
    """Plugin security scan results"""
    __tablename__ = "plugin_security_scans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_id = Column(UUID(as_uuid=True), ForeignKey('plugin_registry.id', ondelete='CASCADE'), nullable=False)
    scan_type = Column(String(50), nullable=False)  # static_analysis, malware_scan, etc.
    scan_result = Column(String(20), nullable=False)  # passed, failed, warning
    findings = Column(JSON)  # Detailed scan findings
    scan_version = Column(String(20))  # Scanner version
    scanned_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        Index('idx_plugin_security_plugin', 'plugin_id'),
        Index('idx_plugin_security_result', 'scan_result'),
        Index('idx_plugin_security_timestamp', 'scanned_at'),
    )