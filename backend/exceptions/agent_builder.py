"""Agent Builder specific exceptions."""

from typing import Optional, Dict, Any, List


class AgentBuilderException(Exception):
    """Base exception for Agent Builder module."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Agent Builder exception.
        
        Args:
            message: Error message
            error_code: Error code for client handling
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API responses.
        
        Returns:
            Dictionary representation of exception
        """
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# AGENT EXCEPTIONS
# ============================================================================


class AgentNotFoundException(AgentBuilderException):
    """Agent not found exception."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent not found: {agent_id}",
            error_code="AGENT_NOT_FOUND",
            details={"agent_id": agent_id}
        )


class AgentValidationException(AgentBuilderException):
    """Agent validation failed exception."""
    
    def __init__(self, errors: List[str], agent_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Agent validation failed: {', '.join(errors)}",
            error_code="AGENT_VALIDATION_FAILED",
            details={"errors": errors, "agent_data": agent_data}
        )


class AgentPermissionException(AgentBuilderException):
    """Agent permission denied exception."""
    
    def __init__(self, agent_id: str, user_id: str, action: str):
        super().__init__(
            message=f"Permission denied for user {user_id} to {action} agent {agent_id}",
            error_code="AGENT_PERMISSION_DENIED",
            details={"agent_id": agent_id, "user_id": user_id, "action": action}
        )


class AgentExecutionException(AgentBuilderException):
    """Agent execution failed exception."""
    
    def __init__(self, agent_id: str, error: str, execution_id: Optional[str] = None):
        super().__init__(
            message=f"Agent execution failed: {error}",
            error_code="AGENT_EXECUTION_FAILED",
            details={"agent_id": agent_id, "error": error, "execution_id": execution_id}
        )


class AgentToolNotFoundException(AgentBuilderException):
    """Agent tool not found exception."""
    
    def __init__(self, tool_id: str):
        super().__init__(
            message=f"Tool not found: {tool_id}",
            error_code="TOOL_NOT_FOUND",
            details={"tool_id": tool_id}
        )


class AgentKnowledgebaseNotFoundException(AgentBuilderException):
    """Agent knowledgebase not found exception."""
    
    def __init__(self, knowledgebase_id: str):
        super().__init__(
            message=f"Knowledgebase not found: {knowledgebase_id}",
            error_code="KNOWLEDGEBASE_NOT_FOUND",
            details={"knowledgebase_id": knowledgebase_id}
        )


# ============================================================================
# WORKFLOW EXCEPTIONS
# ============================================================================


class WorkflowNotFoundException(AgentBuilderException):
    """Workflow not found exception."""
    
    def __init__(self, workflow_id: str):
        super().__init__(
            message=f"Workflow not found: {workflow_id}",
            error_code="WORKFLOW_NOT_FOUND",
            details={"workflow_id": workflow_id}
        )


class WorkflowValidationException(AgentBuilderException):
    """Workflow validation failed exception."""
    
    def __init__(self, errors: List[str], warnings: Optional[List[str]] = None):
        super().__init__(
            message=f"Workflow validation failed: {', '.join(errors)}",
            error_code="WORKFLOW_VALIDATION_FAILED",
            details={"errors": errors, "warnings": warnings or []}
        )


class WorkflowCycleException(AgentBuilderException):
    """Workflow contains cycle exception."""
    
    def __init__(self, cycle_path: List[str]):
        super().__init__(
            message=f"Workflow contains cycle: {' -> '.join(cycle_path)}",
            error_code="WORKFLOW_CYCLE_DETECTED",
            details={"cycle_path": cycle_path}
        )


class WorkflowExecutionException(AgentBuilderException):
    """Workflow execution failed exception."""
    
    def __init__(
        self,
        workflow_id: str,
        error: str,
        execution_id: Optional[str] = None,
        step: Optional[str] = None
    ):
        super().__init__(
            message=f"Workflow execution failed: {error}",
            error_code="WORKFLOW_EXECUTION_FAILED",
            details={
                "workflow_id": workflow_id,
                "error": error,
                "execution_id": execution_id,
                "step": step
            }
        )


class WorkflowTimeoutException(AgentBuilderException):
    """Workflow execution timeout exception."""
    
    def __init__(self, workflow_id: str, timeout_seconds: int, execution_id: Optional[str] = None):
        super().__init__(
            message=f"Workflow execution timed out after {timeout_seconds} seconds",
            error_code="WORKFLOW_TIMEOUT",
            details={
                "workflow_id": workflow_id,
                "timeout_seconds": timeout_seconds,
                "execution_id": execution_id
            }
        )


class WorkflowPermissionException(AgentBuilderException):
    """Workflow permission denied exception."""
    
    def __init__(self, workflow_id: str, user_id: str, action: str):
        super().__init__(
            message=f"Permission denied for user {user_id} to {action} workflow {workflow_id}",
            error_code="WORKFLOW_PERMISSION_DENIED",
            details={"workflow_id": workflow_id, "user_id": user_id, "action": action}
        )


# ============================================================================
# BLOCK EXCEPTIONS
# ============================================================================


class BlockNotFoundException(AgentBuilderException):
    """Block not found exception."""
    
    def __init__(self, block_id: str):
        super().__init__(
            message=f"Block not found: {block_id}",
            error_code="BLOCK_NOT_FOUND",
            details={"block_id": block_id}
        )


class BlockValidationException(AgentBuilderException):
    """Block validation failed exception."""
    
    def __init__(self, errors: List[str], block_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Block validation failed: {', '.join(errors)}",
            error_code="BLOCK_VALIDATION_FAILED",
            details={"errors": errors, "block_data": block_data}
        )


class BlockExecutionException(AgentBuilderException):
    """Block execution failed exception."""
    
    def __init__(self, block_id: str, error: str, input_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Block execution failed: {error}",
            error_code="BLOCK_EXECUTION_FAILED",
            details={"block_id": block_id, "error": error, "input_data": input_data}
        )


class BlockTypeException(AgentBuilderException):
    """Invalid block type exception."""
    
    def __init__(self, block_type: str, valid_types: List[str]):
        super().__init__(
            message=f"Invalid block type: {block_type}. Valid types: {', '.join(valid_types)}",
            error_code="INVALID_BLOCK_TYPE",
            details={"block_type": block_type, "valid_types": valid_types}
        )


class BlockDependencyException(AgentBuilderException):
    """Block dependency error exception."""
    
    def __init__(self, message: str, parent_block_id: str, child_block_id: str):
        super().__init__(
            message=message,
            error_code="BLOCK_DEPENDENCY_ERROR",
            details={"parent_block_id": parent_block_id, "child_block_id": child_block_id}
        )


class BlockTestException(AgentBuilderException):
    """Block test failed exception."""
    
    def __init__(
        self,
        block_id: str,
        test_case_id: str,
        error: str,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None
    ):
        super().__init__(
            message=f"Block test failed: {error}",
            error_code="BLOCK_TEST_FAILED",
            details={
                "block_id": block_id,
                "test_case_id": test_case_id,
                "error": error,
                "expected": expected,
                "actual": actual
            }
        )


# ============================================================================
# VARIABLE AND SECRET EXCEPTIONS
# ============================================================================


class VariableNotFoundException(AgentBuilderException):
    """Variable not found exception."""
    
    def __init__(self, variable_name: str, scope: Optional[str] = None):
        super().__init__(
            message=f"Variable not found: {variable_name}" + (f" in scope {scope}" if scope else ""),
            error_code="VARIABLE_NOT_FOUND",
            details={"variable_name": variable_name, "scope": scope}
        )


class VariableValidationException(AgentBuilderException):
    """Variable validation failed exception."""
    
    def __init__(self, errors: List[str], variable_name: str):
        super().__init__(
            message=f"Variable validation failed for {variable_name}: {', '.join(errors)}",
            error_code="VARIABLE_VALIDATION_FAILED",
            details={"errors": errors, "variable_name": variable_name}
        )


class SecretEncryptionException(AgentBuilderException):
    """Secret encryption failed exception."""
    
    def __init__(self, variable_id: str, error: str):
        super().__init__(
            message=f"Secret encryption failed: {error}",
            error_code="SECRET_ENCRYPTION_FAILED",
            details={"variable_id": variable_id, "error": error}
        )


class SecretDecryptionException(AgentBuilderException):
    """Secret decryption failed exception."""
    
    def __init__(self, variable_id: str, error: str):
        super().__init__(
            message=f"Secret decryption failed: {error}",
            error_code="SECRET_DECRYPTION_FAILED",
            details={"variable_id": variable_id, "error": error}
        )


# ============================================================================
# PERMISSION EXCEPTIONS
# ============================================================================


class PermissionDeniedException(AgentBuilderException):
    """Permission denied exception."""
    
    def __init__(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str
    ):
        super().__init__(
            message=f"Permission denied for user {user_id} to {action} {resource_type} {resource_id}",
            error_code="PERMISSION_DENIED",
            details={
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action
            }
        )


class ResourceShareException(AgentBuilderException):
    """Resource share error exception."""
    
    def __init__(self, message: str, resource_type: str, resource_id: str):
        super().__init__(
            message=message,
            error_code="RESOURCE_SHARE_ERROR",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


# ============================================================================
# QUOTA AND RATE LIMIT EXCEPTIONS
# ============================================================================


class QuotaExceededException(AgentBuilderException):
    """Quota exceeded exception."""
    
    def __init__(
        self,
        user_id: str,
        resource_type: str,
        current: int,
        limit: int
    ):
        super().__init__(
            message=f"Quota exceeded for {resource_type}: {current}/{limit}",
            error_code="QUOTA_EXCEEDED",
            details={
                "user_id": user_id,
                "resource_type": resource_type,
                "current": current,
                "limit": limit
            }
        )


class RateLimitExceededException(AgentBuilderException):
    """Rate limit exceeded exception."""
    
    def __init__(
        self,
        user_id: str,
        operation: str,
        retry_after: Optional[int] = None
    ):
        super().__init__(
            message=f"Rate limit exceeded for {operation}",
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "user_id": user_id,
                "operation": operation,
                "retry_after": retry_after
            }
        )


# ============================================================================
# COMPILATION AND RUNTIME EXCEPTIONS
# ============================================================================


class WorkflowCompilationException(AgentBuilderException):
    """Workflow compilation failed exception."""
    
    def __init__(self, workflow_id: str, error: str):
        super().__init__(
            message=f"Workflow compilation failed: {error}",
            error_code="WORKFLOW_COMPILATION_FAILED",
            details={"workflow_id": workflow_id, "error": error}
        )


class CodeExecutionException(AgentBuilderException):
    """Code execution failed exception."""
    
    def __init__(self, code_snippet: str, error: str, line_number: Optional[int] = None):
        super().__init__(
            message=f"Code execution failed: {error}",
            error_code="CODE_EXECUTION_FAILED",
            details={
                "code_snippet": code_snippet[:200],  # Truncate for safety
                "error": error,
                "line_number": line_number
            }
        )


class SandboxException(AgentBuilderException):
    """Sandbox execution error exception."""
    
    def __init__(self, error: str, sandbox_type: str):
        super().__init__(
            message=f"Sandbox execution failed: {error}",
            error_code="SANDBOX_EXECUTION_FAILED",
            details={"error": error, "sandbox_type": sandbox_type}
        )


# ============================================================================
# MEMORY EXCEPTIONS
# ============================================================================


class MemoryException(AgentBuilderException):
    """Base exception for memory operations."""
    pass


class MemoryNotFoundException(MemoryException):
    """Memory not found exception."""
    
    def __init__(self, memory_id: str):
        super().__init__(
            message=f"Memory {memory_id} not found",
            error_code="MEMORY_NOT_FOUND",
            details={"memory_id": memory_id}
        )


class MemoryQuotaExceededError(MemoryException):
    """Memory quota exceeded exception."""
    
    def __init__(self, current_mb: float, limit_mb: float):
        super().__init__(
            message=f"Memory quota exceeded: {current_mb:.2f}MB / {limit_mb:.2f}MB",
            error_code="MEMORY_QUOTA_EXCEEDED",
            details={
                "current_mb": current_mb,
                "limit_mb": limit_mb,
                "excess_mb": current_mb - limit_mb
            }
        )


class MemoryConsolidationError(MemoryException):
    """Memory consolidation failed exception."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Memory consolidation failed: {reason}",
            error_code="MEMORY_CONSOLIDATION_FAILED",
            details={"reason": reason}
        )


class InvalidMemoryTypeError(MemoryException):
    """Invalid memory type exception."""
    
    def __init__(self, memory_type: str):
        valid_types = ['short_term', 'long_term', 'episodic', 'semantic']
        super().__init__(
            message=f"Invalid memory type: {memory_type}. Must be one of {valid_types}",
            error_code="INVALID_MEMORY_TYPE",
            details={
                "provided_type": memory_type,
                "valid_types": valid_types
            }
        )


# ============================================================================
# COST EXCEPTIONS
# ============================================================================


class CostException(AgentBuilderException):
    """Base exception for cost operations."""
    pass


class BudgetExceededError(CostException):
    """Budget exceeded exception."""
    
    def __init__(self, current_cost: float, budget: float):
        super().__init__(
            message=f"Budget exceeded: ${current_cost:.2f} / ${budget:.2f}",
            error_code="BUDGET_EXCEEDED",
            details={
                "current_cost": current_cost,
                "budget": budget,
                "excess": current_cost - budget,
                "percentage": (current_cost / budget) * 100 if budget > 0 else 0
            }
        )


class CostRecordNotFoundError(CostException):
    """Cost record not found exception."""
    
    def __init__(self, record_id: str):
        super().__init__(
            message=f"Cost record {record_id} not found",
            error_code="COST_RECORD_NOT_FOUND",
            details={"record_id": record_id}
        )


class InvalidTimeRangeError(CostException):
    """Invalid time range exception."""
    
    def __init__(self, time_range: str):
        valid_ranges = ['24h', '7d', '30d', '90d', 'all']
        super().__init__(
            message=f"Invalid time range: {time_range}. Must be one of {valid_ranges}",
            error_code="INVALID_TIME_RANGE",
            details={
                "provided_range": time_range,
                "valid_ranges": valid_ranges
            }
        )


class OptimizationNotFoundError(CostException):
    """Optimization not found exception."""
    
    def __init__(self, optimization_id: str):
        super().__init__(
            message=f"Optimization {optimization_id} not found",
            error_code="OPTIMIZATION_NOT_FOUND",
            details={"optimization_id": optimization_id}
        )


# ============================================================================
# BRANCH EXCEPTIONS
# ============================================================================


class BranchException(AgentBuilderException):
    """Base exception for branch operations."""
    pass


class BranchNotFoundException(BranchException):
    """Branch not found exception."""
    
    def __init__(self, branch_id: str):
        super().__init__(
            message=f"Branch {branch_id} not found",
            error_code="BRANCH_NOT_FOUND",
            details={"branch_id": branch_id}
        )


class BranchAlreadyExistsError(BranchException):
    """Branch already exists exception."""
    
    def __init__(self, branch_name: str, workflow_id: str):
        super().__init__(
            message=f"Branch '{branch_name}' already exists for workflow {workflow_id}",
            error_code="BRANCH_ALREADY_EXISTS",
            details={
                "branch_name": branch_name,
                "workflow_id": workflow_id
            }
        )


class BranchConflictError(BranchException):
    """Branch merge conflict exception."""
    
    def __init__(self, conflicts: List[Dict[str, Any]]):
        super().__init__(
            message=f"Merge conflicts detected: {len(conflicts)} conflicts",
            error_code="BRANCH_CONFLICT",
            details={
                "conflict_count": len(conflicts),
                "conflicts": conflicts
            }
        )


class CannotDeleteMainBranchError(BranchException):
    """Cannot delete main branch exception."""
    
    def __init__(self, branch_id: str):
        super().__init__(
            message="Cannot delete main branch",
            error_code="CANNOT_DELETE_MAIN_BRANCH",
            details={"branch_id": branch_id}
        )


class CannotDeleteActiveBranchError(BranchException):
    """Cannot delete active branch exception."""
    
    def __init__(self, branch_id: str):
        super().__init__(
            message="Cannot delete active branch. Switch to another branch first.",
            error_code="CANNOT_DELETE_ACTIVE_BRANCH",
            details={"branch_id": branch_id}
        )


# ============================================================================
# COLLABORATION EXCEPTIONS
# ============================================================================


class CollaborationException(AgentBuilderException):
    """Base exception for collaboration operations."""
    pass


class ResourceLockedException(CollaborationException):
    """Resource is locked by another user exception."""
    
    def __init__(self, resource_type: str, resource_id: str, locked_by: str):
        super().__init__(
            message=f"Resource {resource_type}:{resource_id} is locked by {locked_by}",
            error_code="RESOURCE_LOCKED",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "locked_by": locked_by
            }
        )


class LockNotOwnedError(CollaborationException):
    """User doesn't own the lock exception."""
    
    def __init__(self, resource_type: str, resource_id: str, user_id: str):
        super().__init__(
            message=f"User {user_id} doesn't own lock on {resource_type}:{resource_id}",
            error_code="LOCK_NOT_OWNED",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": user_id
            }
        )


class SessionExpiredError(CollaborationException):
    """Collaboration session expired exception."""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Collaboration session {session_id} has expired",
            error_code="SESSION_EXPIRED",
            details={"session_id": session_id}
        )


class TooManyActiveUsersError(CollaborationException):
    """Too many active users exception."""
    
    def __init__(self, current_count: int, max_count: int):
        super().__init__(
            message=f"Too many active users: {current_count}/{max_count}",
            error_code="TOO_MANY_ACTIVE_USERS",
            details={
                "current_count": current_count,
                "max_count": max_count
            }
        )
