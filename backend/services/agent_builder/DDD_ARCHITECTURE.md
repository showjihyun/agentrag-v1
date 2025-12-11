# Agent Builder DDD Architecture

## Overview

The Agent Builder module follows Domain-Driven Design (DDD) principles with a clean layered architecture.

## Directory Structure

```
backend/services/agent_builder/
├── domain/                    # Core business logic
│   ├── agent/                 # Agent aggregate
│   │   ├── aggregate.py       # AgentAggregate root
│   │   ├── entities.py        # AgentEntity, AgentVersionEntity
│   │   ├── value_objects.py   # AgentType, AgentConfig, ModelConfig
│   │   ├── events.py          # AgentCreated, AgentUpdated, etc.
│   │   └── repository.py      # AgentRepositoryInterface
│   ├── workflow/              # Workflow aggregate
│   │   ├── aggregate.py       # WorkflowAggregate root
│   │   ├── entities.py        # WorkflowEntity, NodeEntity, EdgeEntity
│   │   ├── value_objects.py   # NodeType, EdgeType, ExecutionContext
│   │   ├── events.py          # WorkflowCreated, WorkflowExecuted, etc.
│   │   └── repository.py      # WorkflowRepositoryInterface
│   ├── execution/             # Execution aggregate
│   │   ├── aggregate.py       # ExecutionAggregate root
│   │   ├── entities.py        # ExecutionEntity, ExecutionStepEntity
│   │   ├── value_objects.py   # ExecutionStatus, StepType
│   │   ├── events.py          # ExecutionStarted, ExecutionCompleted
│   │   └── repository.py      # ExecutionRepositoryInterface
│   └── block/                 # Block aggregate
│       ├── aggregate.py       # BlockAggregate root
│       ├── entities.py        # BlockEntity
│       └── value_objects.py   # BlockType, BlockConfig
│
├── application/               # Use cases and orchestration
│   ├── workflow_application_service.py
│   ├── agent_application_service.py
│   ├── execution_application_service.py
│   ├── commands/              # Command handlers (CQRS)
│   └── queries/               # Query handlers (CQRS)
│
├── infrastructure/            # External concerns
│   ├── execution/             # Workflow execution engine
│   │   ├── executor.py        # UnifiedExecutor
│   │   ├── base_handler.py    # BaseNodeHandler
│   │   ├── node_handler_registry.py
│   │   └── node_handlers/     # Handler implementations
│   │       ├── agent_handler.py
│   │       ├── tool_handler.py
│   │       ├── llm_handler.py
│   │       ├── condition_handler.py
│   │       ├── code_handler.py
│   │       ├── http_handler.py
│   │       └── start_end_handler.py
│   ├── persistence/           # Repository implementations
│   │   ├── workflow_repository.py
│   │   ├── agent_repository.py
│   │   └── execution_repository.py
│   ├── messaging/             # Event bus
│   │   └── event_bus.py
│   └── monitoring/            # Metrics and tracing
│
├── shared/                    # Cross-cutting concerns
│   ├── errors.py              # Domain exceptions
│   ├── validators.py          # Validation utilities
│   └── utils.py               # Common utilities
│
└── facade.py                  # Unified API facade
```

## Key Concepts

### Aggregates

Each aggregate is a consistency boundary:

- **AgentAggregate**: Manages agent lifecycle, tools, and configuration
- **WorkflowAggregate**: Manages workflow graph (nodes, edges), validation
- **ExecutionAggregate**: Tracks execution state, steps, metrics
- **BlockAggregate**: Manages reusable workflow blocks

### Application Services

Orchestrate domain operations:

```python
from backend.services.agent_builder.application import WorkflowApplicationService

service = WorkflowApplicationService(db)
workflow = service.create_workflow(user_id, name, nodes, edges)
result = await service.execute_workflow(workflow_id, input_data, user_id)
```

### Facade Pattern

Simplified API for common operations:

```python
from backend.services.agent_builder import AgentBuilderFacade

facade = AgentBuilderFacade(db)
workflow = facade.create_workflow(user_id, name, nodes, edges)
result = await facade.execute_workflow(workflow_id, input_data, user_id)
```

## Execution Flow

1. **API Layer** receives request
2. **Application Service** orchestrates the operation
3. **Domain Aggregate** enforces business rules
4. **Infrastructure** handles persistence and execution
5. **Events** are published for side effects

## Node Handlers

The execution engine uses pluggable handlers:

```python
from backend.services.agent_builder.infrastructure.execution import NodeHandlerRegistry

registry = NodeHandlerRegistry()
registry.register("llm", LLMNodeHandler())
registry.register("tool", ToolNodeHandler())
```

## Migration from Legacy

Legacy services are still available for backward compatibility:

```python
# Legacy (still works)
from backend.services.agent_builder import WorkflowService
service = WorkflowService(db)

# New DDD approach (recommended)
from backend.services.agent_builder import AgentBuilderFacade
facade = AgentBuilderFacade(db)
```

## CQRS Pattern

Commands (write) and Queries (read) are separated:

### Commands

```python
from backend.services.agent_builder.application.commands import (
    CreateWorkflowCommand,
    WorkflowCommandHandler,
)

handler = WorkflowCommandHandler(db)
command = CreateWorkflowCommand(
    user_id="user-123",
    name="My Workflow",
    nodes=[...],
    edges=[...],
)
workflow = handler.handle_create(command)
```

### Queries

```python
from backend.services.agent_builder.application.queries import (
    GetWorkflowQuery,
    WorkflowQueryHandler,
)

handler = WorkflowQueryHandler(db)
query = GetWorkflowQuery(workflow_id="workflow-123")
result = handler.handle_get(query)
```

## Legacy Executor Adapter

For gradual migration from existing executors:

```python
from backend.services.agent_builder.infrastructure import get_executor

# Use new UnifiedExecutor (default)
executor = get_executor(db, use_unified=True)
result = await executor.execute(workflow, input_data, user_id)

# Fallback to legacy executor
executor = get_executor(db, use_unified=False)
result = await executor.execute(workflow, input_data, user_id)
```

## Testing

Each layer can be tested independently:

- **Domain**: Pure unit tests (no dependencies)
- **Application**: Integration tests with mocked repositories
- **Infrastructure**: Integration tests with real database
