"""
Audit Logging Service for Agent Builder.

Logs all user actions, security events, and system operations
to the AuditLog model for compliance and debugging.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from backend.db.models.agent_builder import AuditLog

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for logging audit events."""
    
    def __init__(self, db: Session):
        """
        Initialize Audit Logger.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            user_id: User performing the action
            action: Action performed (e.g., "create_agent", "execute_workflow")
            resource_type: Type of resource (e.g., "agent", "workflow")
            resource_id: ID of the resource
            details: Additional details about the action
            ip_address: IP address of the user
            user_agent: User agent string
            success: Whether the action succeeded
            error_message: Error message if action failed
            
        Returns:
            Created AuditLog entry
        """
        try:
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details={
                    **(details or {}),
                    "success": success,
                    "error_message": error_message
                },
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            logger.info(
                f"Audit log created: user={user_id}, action={action}, "
                f"resource={resource_type}:{resource_id}, success={success}"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            self.db.rollback()
            # Don't raise exception - audit logging should not break main flow
            return None
    
    def log_from_request(
        self,
        request: Request,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event from a FastAPI request.
        
        Extracts IP address and user agent from request headers.
        
        Args:
            request: FastAPI Request object
            user_id: User performing the action
            action: Action performed
            resource_type: Type of resource
            resource_id: ID of the resource
            details: Additional details
            success: Whether the action succeeded
            error_message: Error message if action failed
            
        Returns:
            Created AuditLog entry
        """
        # Extract IP address
        ip_address = self._get_client_ip(request)
        
        # Extract user agent
        user_agent = request.headers.get("user-agent", "Unknown")
        
        return self.log_action(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Handles X-Forwarded-For header for proxied requests.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (for proxied requests)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "Unknown"
    
    def log_agent_create(
        self,
        request: Request,
        user_id: str,
        agent_id: str,
        agent_name: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log agent creation."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="create_agent",
            resource_type="agent",
            resource_id=agent_id,
            details={"agent_name": agent_name},
            success=success,
            error_message=error_message
        )
    
    def log_agent_update(
        self,
        request: Request,
        user_id: str,
        agent_id: str,
        changes: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log agent update."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="update_agent",
            resource_type="agent",
            resource_id=agent_id,
            details={"changes": changes},
            success=success,
            error_message=error_message
        )
    
    def log_agent_delete(
        self,
        request: Request,
        user_id: str,
        agent_id: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log agent deletion."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="delete_agent",
            resource_type="agent",
            resource_id=agent_id,
            success=success,
            error_message=error_message
        )
    
    def log_agent_execute(
        self,
        request: Request,
        user_id: str,
        agent_id: str,
        execution_id: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log agent execution."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="execute_agent",
            resource_type="agent",
            resource_id=agent_id,
            details={"execution_id": execution_id},
            success=success,
            error_message=error_message
        )
    
    def log_workflow_create(
        self,
        request: Request,
        user_id: str,
        workflow_id: str,
        workflow_name: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log workflow creation."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="create_workflow",
            resource_type="workflow",
            resource_id=workflow_id,
            details={"workflow_name": workflow_name},
            success=success,
            error_message=error_message
        )
    
    def log_workflow_execute(
        self,
        request: Request,
        user_id: str,
        workflow_id: str,
        execution_id: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log workflow execution."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="execute_workflow",
            resource_type="workflow",
            resource_id=workflow_id,
            details={"execution_id": execution_id},
            success=success,
            error_message=error_message
        )
    
    def log_block_create(
        self,
        request: Request,
        user_id: str,
        block_id: str,
        block_name: str,
        block_type: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log block creation."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="create_block",
            resource_type="block",
            resource_id=block_id,
            details={"block_name": block_name, "block_type": block_type},
            success=success,
            error_message=error_message
        )
    
    def log_knowledgebase_create(
        self,
        request: Request,
        user_id: str,
        kb_id: str,
        kb_name: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log knowledgebase creation."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="create_knowledgebase",
            resource_type="knowledgebase",
            resource_id=kb_id,
            details={"knowledgebase_name": kb_name},
            success=success,
            error_message=error_message
        )
    
    def log_permission_grant(
        self,
        request: Request,
        user_id: str,
        target_user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log permission grant."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action="grant_permission",
            resource_type=resource_type,
            resource_id=resource_id,
            details={
                "target_user_id": target_user_id,
                "permission_action": action
            },
            success=success,
            error_message=error_message
        )
    
    def log_security_event(
        self,
        request: Request,
        user_id: str,
        event_type: str,
        details: Dict[str, Any],
        success: bool = True
    ) -> AuditLog:
        """Log security event."""
        return self.log_from_request(
            request=request,
            user_id=user_id,
            action=f"security_{event_type}",
            details=details,
            success=success
        )


def get_audit_logger(db: Session) -> AuditLogger:
    """
    Get AuditLogger instance.
    
    Args:
        db: Database session
        
    Returns:
        AuditLogger instance
    """
    return AuditLogger(db)
