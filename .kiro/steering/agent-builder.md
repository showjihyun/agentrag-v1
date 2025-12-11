---
inclusion: fileMatch
fileMatchPattern: "**/agent_builder/**,**/agent-builder/**"
---

# Agent Builder Guidelines

## Overview

Agent Builder is a visual workflow designer for creating AI agents and chatbots. It follows Domain-Driven Design (DDD) principles with clear separation of concerns.

## Architecture

### Domain Layer (`services/agent_builder/domain/`)
- **Aggregates**: Root entities that ensure consistency
- **Entities**: Domain objects with identity
- **Value Objects**: Immutable domain concepts
- **Events**: Domain events for state changes
- **Repository Interfaces**: Abstract data access

### Application Layer (`services/agent_builder/application/`)
- **Commands**: Write operations (create, update, delete)
- **Queries**: Read operations
- **Application Services**: Orchestrate use cases

### Infrastructure Layer (`services/agent_builder/infrastructure/`)
- **Repositories**: Concrete data access implementations
- **Execution Engine**: Workflow execution with node handlers
- **Event Bus**: Event publishing and subscription
- **Legacy Adapter**: Backward compatibility

## Key Concepts

### Flows
- **Chatflow**: Conversational AI with memory
- **Agentflow**: Task-oriented with tool execution

### Blocks/Nodes
- **Start/End**: Flow control
- **LLM**: Language model invocation
- **HTTP**: External API calls
- **Code**: Python/JavaScript execution
- **Condition**: Branching logic
- **Loop**: Iteration
- **Tool**: External tool integration
- **Agent**: Nested agent execution

### Execution
- Node handlers process each block type
- Context passed between nodes
- Real-time status streaming via SSE

## Code Patterns

### Creating a new node handler
```python
# infrastructure/execution/node_handlers/my_handler.py
from backend.services.agent_builder.infrastructure.execution.base_handler import BaseNodeHandler

class MyNodeHandler(BaseNodeHandler):
    async def execute(self, node: dict, context: dict) -> dict:
        # Process node
        result = await self._process(node, context)
        return {"output": result}
```

### Domain events
```python
# domain/workflow/events.py
@dataclass
class WorkflowExecuted(DomainEvent):
    workflow_id: str
    execution_id: str
    status: str
```

### Application commands
```python
# application/commands/workflow_commands.py
@dataclass
class ExecuteWorkflowCommand:
    workflow_id: str
    input_data: dict
    user_id: str
```

## Frontend Components

### Key Components
- `WorkflowCanvas`: React Flow based canvas
- `BlockEditor`: Node configuration panel
- `ExecutionMonitor`: Real-time execution view
- `ToolConfigField`: Dynamic tool configuration

### State Management
- Zustand for workflow state
- React Query for server data
- Local state for UI interactions

## API Endpoints

### Flows
- `GET /api/agent-builder/flows` - List flows
- `POST /api/agent-builder/flows` - Create flow
- `GET /api/agent-builder/flows/{id}` - Get flow
- `PUT /api/agent-builder/flows/{id}` - Update flow
- `DELETE /api/agent-builder/flows/{id}` - Delete flow

### Execution
- `POST /api/agent-builder/flows/{id}/execute` - Execute flow
- `GET /api/agent-builder/executions/{id}` - Get execution status
- `GET /api/agent-builder/executions/{id}/stream` - Stream execution (SSE)

### Chat
- `POST /api/agent-builder/chatflows/{id}/chat` - Send message
- `GET /api/agent-builder/chatflows/{id}/history` - Get chat history

## Testing

### Unit Tests
```python
# tests/unit/test_workflow_execution.py
async def test_execute_workflow():
    executor = WorkflowExecutor(...)
    result = await executor.execute(workflow, input_data)
    assert result.status == "completed"
```

### Integration Tests
```python
# tests/integration/test_agent_builder_api.py
async def test_create_and_execute_flow(client):
    # Create flow
    response = await client.post("/api/agent-builder/flows", json=flow_data)
    flow_id = response.json()["id"]
    
    # Execute
    response = await client.post(f"/api/agent-builder/flows/{flow_id}/execute")
    assert response.status_code == 200
```

## Best Practices

1. **Domain Logic**: Keep business rules in domain layer
2. **Immutability**: Use value objects for immutable concepts
3. **Events**: Emit domain events for state changes
4. **Validation**: Validate at domain boundaries
5. **Testing**: Test domain logic independently
