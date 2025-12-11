"""
Application Layer

Contains use cases and application services.
Orchestrates domain objects and infrastructure.

CQRS Pattern:
- Commands: Write operations (create, update, delete)
- Queries: Read operations (get, list, stats)
"""

from backend.services.agent_builder.application.agent_application_service import AgentApplicationService
from backend.services.agent_builder.application.workflow_application_service import WorkflowApplicationService
from backend.services.agent_builder.application.execution_application_service import ExecutionApplicationService

# CQRS Commands
from backend.services.agent_builder.application.commands import (
    CreateWorkflowCommand,
    UpdateWorkflowCommand,
    DeleteWorkflowCommand,
    ExecuteWorkflowCommand,
    WorkflowCommandHandler,
    CreateAgentCommand,
    UpdateAgentCommand,
    DeleteAgentCommand,
    AgentCommandHandler,
)

# CQRS Queries
from backend.services.agent_builder.application.queries import (
    GetWorkflowQuery,
    ListWorkflowsQuery,
    WorkflowQueryHandler,
    GetAgentQuery,
    ListAgentsQuery,
    AgentQueryHandler,
    GetExecutionQuery,
    ListExecutionsQuery,
    ExecutionQueryHandler,
)

__all__ = [
    # Application Services
    "AgentApplicationService",
    "WorkflowApplicationService",
    "ExecutionApplicationService",
    # Commands
    "CreateWorkflowCommand",
    "UpdateWorkflowCommand",
    "DeleteWorkflowCommand",
    "ExecuteWorkflowCommand",
    "WorkflowCommandHandler",
    "CreateAgentCommand",
    "UpdateAgentCommand",
    "DeleteAgentCommand",
    "AgentCommandHandler",
    # Queries
    "GetWorkflowQuery",
    "ListWorkflowsQuery",
    "WorkflowQueryHandler",
    "GetAgentQuery",
    "ListAgentsQuery",
    "AgentQueryHandler",
    "GetExecutionQuery",
    "ListExecutionsQuery",
    "ExecutionQueryHandler",
]
