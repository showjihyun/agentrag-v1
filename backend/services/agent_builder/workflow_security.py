"""
Workflow Security Manager

Security utilities for workflow execution including input validation,
output sanitization, and audit logging.
"""

import logging
import re
import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security levels for workflows."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CODE_INJECTION = "code_injection"
    PATH_TRAVERSAL = "path_traversal"
    SSRF = "ssrf"
    SENSITIVE_DATA = "sensitive_data"
    RATE_LIMIT = "rate_limit"


@dataclass
class SecurityScanResult:
    """Result of security scan."""
    is_safe: bool
    threats: List[Dict[str, Any]]
    sanitized_data: Optional[Dict[str, Any]]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "threat_count": len(self.threats),
            "threats": self.threats,
            "recommendations": self.recommendations,
        }


@dataclass
class AuditLogEntry:
    """Audit log entry."""
    timestamp: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }


class WorkflowSecurityManager:
    """
    Security manager for workflow system.
    
    Features:
    - Input validation and sanitization
    - SQL injection detection
    - XSS prevention
    - Code injection detection
    - Sensitive data masking
    - Audit logging
    - Webhook signature verification
    """
    
    # Patterns for threat detection
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
    ]
    
    CODE_INJECTION_PATTERNS = [
        r"(__import__|eval|exec|compile)\s*\(",
        r"(os\.system|subprocess|popen)\s*\(",
        r"(\bimport\s+os\b|\bfrom\s+os\b)",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",
    ]
    
    SENSITIVE_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b\d{16}\b",  # Credit card
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"(password|secret|api_key|token)\s*[:=]\s*['\"]?[\w-]+",  # Credentials
    ]
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._audit_buffer: List[AuditLogEntry] = []
        self._audit_buffer_size = 100
    
    def scan_input(
        self,
        data: Dict[str, Any],
        security_level: SecurityLevel = SecurityLevel.MEDIUM,
    ) -> SecurityScanResult:
        """
        Scan input data for security threats.
        
        Args:
            data: Input data to scan
            security_level: Security level for scanning
            
        Returns:
            SecurityScanResult
        """
        threats = []
        recommendations = []
        
        # Convert to string for pattern matching
        data_str = str(data)
        
        # SQL Injection check
        if security_level in [SecurityLevel.MEDIUM, SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            for pattern in self.SQL_INJECTION_PATTERNS:
                if re.search(pattern, data_str, re.IGNORECASE):
                    threats.append({
                        "type": ThreatType.SQL_INJECTION.value,
                        "pattern": pattern,
                        "severity": "high",
                    })
        
        # XSS check
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                threats.append({
                    "type": ThreatType.XSS.value,
                    "pattern": pattern,
                    "severity": "medium",
                })
        
        # Code injection check
        if security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            for pattern in self.CODE_INJECTION_PATTERNS:
                if re.search(pattern, data_str, re.IGNORECASE):
                    threats.append({
                        "type": ThreatType.CODE_INJECTION.value,
                        "pattern": pattern,
                        "severity": "critical",
                    })
        
        # Path traversal check
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                threats.append({
                    "type": ThreatType.PATH_TRAVERSAL.value,
                    "pattern": pattern,
                    "severity": "high",
                })
        
        # Sensitive data check
        if security_level == SecurityLevel.CRITICAL:
            for pattern in self.SENSITIVE_PATTERNS:
                if re.search(pattern, data_str, re.IGNORECASE):
                    threats.append({
                        "type": ThreatType.SENSITIVE_DATA.value,
                        "pattern": pattern,
                        "severity": "medium",
                    })
                    recommendations.append("Consider masking sensitive data before processing")
        
        # Generate recommendations
        if threats:
            if any(t["type"] == ThreatType.SQL_INJECTION.value for t in threats):
                recommendations.append("Use parameterized queries instead of string concatenation")
            if any(t["type"] == ThreatType.XSS.value for t in threats):
                recommendations.append("Sanitize HTML content before rendering")
            if any(t["type"] == ThreatType.CODE_INJECTION.value for t in threats):
                recommendations.append("Avoid executing user-provided code")
        
        # Sanitize data if threats found
        sanitized = self.sanitize_input(data) if threats else data
        
        return SecurityScanResult(
            is_safe=len(threats) == 0,
            threats=threats,
            sanitized_data=sanitized,
            recommendations=recommendations,
        )
    
    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize input data by removing/escaping dangerous content.
        
        Args:
            data: Input data
            
        Returns:
            Sanitized data
        """
        def sanitize_value(value: Any) -> Any:
            if isinstance(value, str):
                # Remove script tags
                value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
                # Escape HTML
                value = value.replace("<", "&lt;").replace(">", "&gt;")
                # Remove SQL comments
                value = re.sub(r"(--|\/\*|\*\/)", "", value)
                return value
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(v) for v in value]
            return value
        
        return sanitize_value(data)
    
    def mask_sensitive_data(
        self,
        data: Dict[str, Any],
        fields_to_mask: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """
        Mask sensitive data in output.
        
        Args:
            data: Data to mask
            fields_to_mask: Specific fields to mask
            
        Returns:
            Masked data
        """
        default_sensitive_fields = {
            "password", "secret", "api_key", "token", "authorization",
            "credit_card", "ssn", "private_key", "access_token", "refresh_token",
        }
        
        fields = fields_to_mask or default_sensitive_fields
        
        def mask_value(key: str, value: Any) -> Any:
            if isinstance(value, dict):
                return {k: mask_value(k, v) for k, v in value.items()}
            elif isinstance(value, list):
                return [mask_value(key, v) for v in value]
            elif isinstance(value, str) and key.lower() in fields:
                if len(value) > 4:
                    return value[:2] + "*" * (len(value) - 4) + value[-2:]
                return "****"
            return value
        
        return {k: mask_value(k, v) for k, v in data.items()}
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        algorithm: str = "sha256",
    ) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Request payload
            signature: Provided signature
            secret: Webhook secret
            algorithm: Hash algorithm
            
        Returns:
            True if valid
        """
        if algorithm == "sha256":
            expected = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()
        elif algorithm == "sha1":
            expected = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha1,
            ).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected, signature)
    
    def generate_webhook_secret(self, length: int = 32) -> str:
        """Generate secure webhook secret."""
        return secrets.token_urlsafe(length)
    
    def audit_log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Log security audit event.
        
        Args:
            user_id: User performing action
            action: Action type (create, read, update, delete, execute)
            resource_type: Type of resource
            resource_id: Resource ID
            details: Additional details
            ip_address: Client IP
            user_agent: Client user agent
        """
        entry = AuditLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self._audit_buffer.append(entry)
        
        # Flush if buffer is full
        if len(self._audit_buffer) >= self._audit_buffer_size:
            self._flush_audit_log()
        
        logger.info(f"Audit: {action} on {resource_type}/{resource_id} by {user_id}")
    
    def _flush_audit_log(self):
        """Flush audit log buffer to storage."""
        if not self._audit_buffer:
            return
        
        if self.db:
            try:
                # Would insert to audit_logs table
                # For now, just log
                for entry in self._audit_buffer:
                    logger.debug(f"Audit entry: {entry.to_dict()}")
            except Exception as e:
                logger.error(f"Failed to flush audit log: {e}")
        
        self._audit_buffer.clear()
    
    def check_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
    ) -> bool:
        """
        Check if user has permission for action.
        
        Args:
            user_id: User ID
            resource_type: Resource type
            resource_id: Resource ID
            action: Action to perform
            
        Returns:
            True if permitted
        """
        # Basic implementation - would integrate with permission system
        if resource_type == "workflow":
            from backend.db.models.agent_builder import Workflow
            
            if self.db:
                workflow = self.db.query(Workflow).filter(
                    Workflow.id == resource_id
                ).first()
                
                if not workflow:
                    return False
                
                # Owner has all permissions
                if str(workflow.user_id) == user_id:
                    return True
                
                # Public workflows allow read
                if workflow.is_public and action == "read":
                    return True
                
                return False
        
        return False


# Global security manager
_security_manager: Optional[WorkflowSecurityManager] = None


def get_security_manager(db_session=None) -> WorkflowSecurityManager:
    """Get or create global security manager."""
    global _security_manager
    if _security_manager is None:
        _security_manager = WorkflowSecurityManager(db_session)
    return _security_manager
