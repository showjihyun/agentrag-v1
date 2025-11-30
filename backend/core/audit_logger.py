"""
Audit Logging System

Provides comprehensive audit logging for security and compliance:
- User actions (login, logout, password changes)
- Resource access (documents, workflows, agents)
- API calls
- Configuration changes
- Security events
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4

from fastapi import Request

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_PASSWORD_CHANGE = "auth.password.change"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    AUTH_2FA_ENABLED = "auth.2fa.enabled"
    AUTH_2FA_DISABLED = "auth.2fa.disabled"
    
    # User management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ROLE_CHANGED = "user.role.changed"
    
    # Resource access
    RESOURCE_CREATED = "resource.created"
    RESOURCE_READ = "resource.read"
    RESOURCE_UPDATED = "resource.updated"
    RESOURCE_DELETED = "resource.deleted"
    RESOURCE_SHARED = "resource.shared"
    RESOURCE_EXPORTED = "resource.exported"
    
    # Workflow events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_UPDATED = "workflow.updated"
    WORKFLOW_DELETED = "workflow.deleted"
    WORKFLOW_EXECUTED = "workflow.executed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # API events
    API_KEY_CREATED = "api_key.created"
    API_KEY_DELETED = "api_key.deleted"
    API_KEY_USED = "api_key.used"
    
    # Configuration events
    CONFIG_CHANGED = "config.changed"
    SETTINGS_UPDATED = "settings.updated"
    
    # Security events
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious"
    SECURITY_RATE_LIMIT_EXCEEDED = "security.rate_limit"
    SECURITY_PERMISSION_DENIED = "security.permission_denied"
    SECURITY_INVALID_TOKEN = "security.invalid_token"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents a single audit event."""
    id: str
    timestamp: str
    event_type: str
    severity: str
    user_id: Optional[str]
    user_email: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    request_id: Optional[str]
    session_id: Optional[str]
    success: bool
    error_message: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Centralized audit logging system.
    
    Supports multiple backends:
    - File logging
    - Database storage
    - External services (future: Elasticsearch, CloudWatch, etc.)
    """
    
    def __init__(
        self,
        db_session=None,
        redis_client=None,
        log_to_file: bool = True,
        log_to_db: bool = True,
        log_to_console: bool = False
    ):
        self.db = db_session
        self.redis = redis_client
        self.log_to_file = log_to_file
        self.log_to_db = log_to_db
        self.log_to_console = log_to_console
        
        # In-memory buffer for batch writes
        self._buffer: List[AuditEvent] = []
        self._buffer_size = 100
        
        # File logger
        if log_to_file:
            self._file_logger = logging.getLogger("audit")
            self._file_logger.setLevel(logging.INFO)
            
            # Create file handler if not exists
            if not self._file_logger.handlers:
                from logging.handlers import RotatingFileHandler
                import os
                
                log_dir = "logs"
                os.makedirs(log_dir, exist_ok=True)
                
                handler = RotatingFileHandler(
                    f"{log_dir}/audit.log",
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=10
                )
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(message)s'
                ))
                self._file_logger.addHandler(handler)
    
    def _create_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditEvent:
        """Create an audit event."""
        return AuditEvent(
            id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=event_type.value,
            severity=severity.value,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            request_id=request_id,
            session_id=session_id,
            success=success,
            error_message=error_message
        )
    
    def _extract_request_info(self, request: Optional[Request]) -> Dict[str, Optional[str]]:
        """Extract relevant info from FastAPI request."""
        if not request:
            return {
                "ip_address": None,
                "user_agent": None,
                "request_id": None
            }
        
        # Get IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else None
        
        return {
            "ip_address": ip,
            "user_agent": request.headers.get("User-Agent"),
            "request_id": getattr(request.state, "request_id", None)
        }
    
    def _write_event(self, event: AuditEvent):
        """Write event to configured backends."""
        # Console logging
        if self.log_to_console:
            logger.info(f"AUDIT: {event.to_json()}")
        
        # File logging
        if self.log_to_file and hasattr(self, "_file_logger"):
            self._file_logger.info(event.to_json())
        
        # Database logging
        if self.log_to_db and self.db:
            try:
                self._write_to_db(event)
            except Exception as e:
                logger.error(f"Failed to write audit event to DB: {e}")
        
        # Redis for real-time streaming (optional)
        if self.redis:
            try:
                self.redis.lpush("audit:events", event.to_json())
                self.redis.ltrim("audit:events", 0, 9999)  # Keep last 10000
            except Exception as e:
                logger.warning(f"Failed to write audit event to Redis: {e}")
    
    def _write_to_db(self, event: AuditEvent):
        """Write event to database."""
        # This would use SQLAlchemy model
        # For now, just log
        pass
    
    def log(
        self,
        event_type: AuditEventType,
        action: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log an audit event."""
        request_info = self._extract_request_info(request)
        
        event = self._create_event(
            event_type=event_type,
            severity=severity,
            action=action,
            user_id=user_id,
            user_email=user_email,
            ip_address=request_info["ip_address"],
            user_agent=request_info["user_agent"],
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request_id=request_info["request_id"],
            success=success,
            error_message=error_message
        )
        
        self._write_event(event)
    
    # Convenience methods for common events
    def log_login_success(
        self,
        user_id: str,
        user_email: str,
        request: Optional[Request] = None,
        details: Optional[Dict] = None
    ):
        """Log successful login."""
        self.log(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            action="User logged in successfully",
            request=request,
            user_id=user_id,
            user_email=user_email,
            details=details
        )
    
    def log_login_failed(
        self,
        user_email: str,
        request: Optional[Request] = None,
        reason: str = "Invalid credentials"
    ):
        """Log failed login attempt."""
        self.log(
            event_type=AuditEventType.AUTH_LOGIN_FAILED,
            action="Login attempt failed",
            severity=AuditSeverity.WARNING,
            request=request,
            user_email=user_email,
            success=False,
            error_message=reason,
            details={"reason": reason}
        )
    
    def log_resource_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        request: Optional[Request] = None,
        details: Optional[Dict] = None
    ):
        """Log resource access."""
        self.log(
            event_type=AuditEventType.RESOURCE_READ,
            action=action,
            request=request,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
    
    def log_workflow_execution(
        self,
        user_id: str,
        workflow_id: str,
        execution_id: str,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Log workflow execution."""
        event_type = AuditEventType.WORKFLOW_EXECUTED if success else AuditEventType.WORKFLOW_FAILED
        severity = AuditSeverity.INFO if success else AuditSeverity.ERROR
        
        self.log(
            event_type=event_type,
            action=f"Workflow {'executed successfully' if success else 'execution failed'}",
            severity=severity,
            request=request,
            user_id=user_id,
            resource_type="workflow",
            resource_id=workflow_id,
            success=success,
            error_message=error_message,
            details={**(details or {}), "execution_id": execution_id}
        )
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        description: str,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Log security-related event."""
        self.log(
            event_type=event_type,
            action=description,
            severity=AuditSeverity.WARNING,
            request=request,
            user_id=user_id,
            details=details,
            success=False
        )
    
    def log_config_change(
        self,
        user_id: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        request: Optional[Request] = None
    ):
        """Log configuration change."""
        self.log(
            event_type=AuditEventType.CONFIG_CHANGED,
            action=f"Configuration changed: {config_key}",
            request=request,
            user_id=user_id,
            resource_type="config",
            resource_id=config_key,
            details={
                "key": config_key,
                "old_value": str(old_value)[:100],  # Truncate for safety
                "new_value": str(new_value)[:100]
            }
        )


# Global instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(
    event_type: AuditEventType,
    action: str,
    **kwargs
):
    """Convenience function for audit logging."""
    get_audit_logger().log(event_type, action, **kwargs)
