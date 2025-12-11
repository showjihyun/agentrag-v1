"""
Infrastructure Layer

Contains implementations of domain interfaces and external service integrations.
"""

from backend.services.agent_builder.infrastructure.execution.executor import UnifiedExecutor
from backend.services.agent_builder.infrastructure.execution.node_handler_registry import NodeHandlerRegistry
from backend.services.agent_builder.infrastructure.execution.legacy_adapter import (
    LegacyExecutorAdapter,
    get_executor,
)
from backend.services.agent_builder.infrastructure.persistence import (
    AgentRepositoryImpl,
    WorkflowRepositoryImpl,
    ExecutionRepositoryImpl,
)
from backend.services.agent_builder.infrastructure.messaging import (
    EventBus,
    get_event_bus,
)

__all__ = [
    # Execution
    "UnifiedExecutor",
    "NodeHandlerRegistry",
    "LegacyExecutorAdapter",
    "get_executor",
    # Persistence
    "AgentRepositoryImpl",
    "WorkflowRepositoryImpl",
    "ExecutionRepositoryImpl",
    # Messaging
    "EventBus",
    "get_event_bus",
]
