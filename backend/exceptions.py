"""Custom exceptions for the application."""

from typing import Optional, Dict, Any


class APIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class WorkflowPausedException(Exception):
    """Exception raised when workflow needs to pause for human approval."""
    
    def __init__(
        self,
        approval_id: str,
        message: str = "Workflow paused for human approval",
        node_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.approval_id = approval_id
        self.node_id = node_id
        self.data = data
        super().__init__(message)


class WorkflowValidationException(Exception):
    """Exception raised when workflow validation fails."""
    
    def __init__(self, errors: list, warnings: list = None):
        self.errors = errors
        self.warnings = warnings or []
        message = f"Workflow validation failed: {', '.join(errors)}"
        super().__init__(message)


class WorkflowNotFoundException(Exception):
    """Exception raised when workflow is not found."""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        super().__init__(f"Workflow not found: {workflow_id}")


class AgentNotFoundException(Exception):
    """Exception raised when agent is not found."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: {agent_id}")


class KnowledgebaseNotFoundException(Exception):
    """Exception raised when knowledgebase is not found."""
    
    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        super().__init__(f"Knowledgebase not found: {kb_id}")


class InsufficientPermissionsException(Exception):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, resource_type: str, resource_id: str, action: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        super().__init__(
            f"Insufficient permissions to {action} {resource_type}: {resource_id}"
        )
