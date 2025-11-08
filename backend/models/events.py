"""
Event Types for Event-Driven Architecture

Defines all event types used in the system.
"""

from enum import Enum
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""
    
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    aggregate_id: str
    aggregate_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentEvent(str, Enum):
    """Agent-related events."""
    
    CREATED = "agent.created"
    UPDATED = "agent.updated"
    DELETED = "agent.deleted"
    CLONED = "agent.cloned"
    PUBLISHED = "agent.published"
    UNPUBLISHED = "agent.unpublished"
    
    # Execution events
    EXECUTION_STARTED = "agent.execution.started"
    EXECUTION_COMPLETED = "agent.execution.completed"
    EXECUTION_FAILED = "agent.execution.failed"
    EXECUTION_CANCELLED = "agent.execution.cancelled"
    
    # Version events
    VERSION_CREATED = "agent.version.created"
    VERSION_RESTORED = "agent.version.restored"


class WorkflowEvent(str, Enum):
    """Workflow-related events."""
    
    CREATED = "workflow.created"
    UPDATED = "workflow.updated"
    DELETED = "workflow.deleted"
    COMPILED = "workflow.compiled"
    
    # Execution events
    EXECUTION_STARTED = "workflow.execution.started"
    EXECUTION_COMPLETED = "workflow.execution.completed"
    EXECUTION_FAILED = "workflow.execution.failed"
    
    # Node events
    NODE_ADDED = "workflow.node.added"
    NODE_UPDATED = "workflow.node.updated"
    NODE_DELETED = "workflow.node.deleted"
    NODE_EXECUTED = "workflow.node.executed"
    
    # Edge events
    EDGE_ADDED = "workflow.edge.added"
    EDGE_DELETED = "workflow.edge.deleted"


class BlockEvent(str, Enum):
    """Block-related events."""
    
    CREATED = "block.created"
    UPDATED = "block.updated"
    DELETED = "block.deleted"
    EXECUTED = "block.executed"


class KnowledgebaseEvent(str, Enum):
    """Knowledgebase-related events."""
    
    CREATED = "knowledgebase.created"
    UPDATED = "knowledgebase.updated"
    DELETED = "knowledgebase.deleted"
    
    # Document events
    DOCUMENT_ADDED = "knowledgebase.document.added"
    DOCUMENT_REMOVED = "knowledgebase.document.removed"
    DOCUMENT_INDEXED = "knowledgebase.document.indexed"
    
    # Query events
    QUERIED = "knowledgebase.queried"


class VariableEvent(str, Enum):
    """Variable-related events."""
    
    CREATED = "variable.created"
    UPDATED = "variable.updated"
    DELETED = "variable.deleted"
    VALUE_CHANGED = "variable.value.changed"


class ExecutionEvent(str, Enum):
    """Execution-related events."""
    
    STARTED = "execution.started"
    STEP_STARTED = "execution.step.started"
    STEP_COMPLETED = "execution.step.completed"
    STEP_FAILED = "execution.step.failed"
    COMPLETED = "execution.completed"
    FAILED = "execution.failed"
    CANCELLED = "execution.cancelled"
    
    # Resource events
    RESOURCE_ALLOCATED = "execution.resource.allocated"
    RESOURCE_RELEASED = "execution.resource.released"


class PermissionEvent(str, Enum):
    """Permission-related events."""
    
    GRANTED = "permission.granted"
    REVOKED = "permission.revoked"
    ROLE_ASSIGNED = "permission.role.assigned"
    ROLE_REMOVED = "permission.role.removed"


class AuditEvent(str, Enum):
    """Audit-related events."""
    
    USER_LOGIN = "audit.user.login"
    USER_LOGOUT = "audit.user.logout"
    RESOURCE_ACCESSED = "audit.resource.accessed"
    RESOURCE_MODIFIED = "audit.resource.modified"
    PERMISSION_CHANGED = "audit.permission.changed"
    SECURITY_VIOLATION = "audit.security.violation"


class SystemEvent(str, Enum):
    """System-related events."""
    
    STARTED = "system.started"
    STOPPED = "system.stopped"
    HEALTH_CHECK_FAILED = "system.health.failed"
    HEALTH_CHECK_RECOVERED = "system.health.recovered"
    
    # Resource events
    RESOURCE_THRESHOLD_EXCEEDED = "system.resource.threshold.exceeded"
    RESOURCE_THRESHOLD_NORMAL = "system.resource.threshold.normal"
    
    # Cache events
    CACHE_CLEARED = "system.cache.cleared"
    CACHE_WARMED = "system.cache.warmed"


# Event type groups for easier filtering
EVENT_GROUPS = {
    "agent": [e.value for e in AgentEvent],
    "workflow": [e.value for e in WorkflowEvent],
    "block": [e.value for e in BlockEvent],
    "knowledgebase": [e.value for e in KnowledgebaseEvent],
    "variable": [e.value for e in VariableEvent],
    "execution": [e.value for e in ExecutionEvent],
    "permission": [e.value for e in PermissionEvent],
    "audit": [e.value for e in AuditEvent],
    "system": [e.value for e in SystemEvent],
}
