# Agent Builder API Migration Guide

## Overview

이 가이드는 기존 API 엔드포인트를 레거시 서비스에서 새로운 DDD 구조로 마이그레이션하는 방법을 설명합니다.

## Migration Strategy

### Phase 1: Facade 사용 (권장)
가장 간단한 마이그레이션 방법입니다.

### Phase 2: Application Services 직접 사용
더 세밀한 제어가 필요한 경우 사용합니다.

### Phase 3: CQRS 패턴 사용
읽기/쓰기 분리가 필요한 경우 사용합니다.

---

## Example 1: Workflow Creation

### Before (Legacy)

```python
from backend.services.agent_builder.workflow_service import WorkflowService
from backend.models.agent_builder import WorkflowCreate

@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = WorkflowService(db)
    workflow = service.create_workflow(
        user_id=str(current_user.id),
        workflow_data=workflow_data
    )
    return workflow
```

### After (Facade - Recommended)

```python
from backend.services.agent_builder.facade import AgentBuilderFacade

@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    facade = AgentBuilderFacade(db)
    workflow = facade.create_workflow(
        user_id=str(current_user.id),
        name=workflow_data.name,
        nodes=workflow_data.nodes,
        edges=workflow_data.edges,
        description=workflow_data.description,
    )
    return workflow
```

### After (Application Service)

```python
from backend.services.agent_builder.application import WorkflowApplicationService

@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = WorkflowApplicationService(db)
    workflow = service.create_workflow(
        user_id=str(current_user.id),
        name=workflow_data.name,
        nodes=workflow_data.nodes,
        edges=workflow_data.edges,
        description=workflow_data.description,
    )
    return workflow
```

### After (CQRS)

```python
from backend.services.agent_builder.application.commands import (
    WorkflowCommandHandler,
    CreateWorkflowCommand,
)

@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    handler = WorkflowCommandHandler(db)
    command = CreateWorkflowCommand(
        user_id=str(current_user.id),
        name=workflow_data.name,
        nodes=workflow_data.nodes,
        edges=workflow_data.edges,
        description=workflow_data.description,
    )
    workflow = handler.handle_create(command)
    return workflow
```

---

## Example 2: Workflow Execution

### Before (Legacy)

```python
from backend.services.agent_builder.workflow_executor import execute_workflow

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow_endpoint(
    workflow_id: str,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    result = await execute_workflow(workflow, db, input_data, str(current_user.id))
    return result
```

### After (Facade - Recommended)

```python
from backend.services.agent_builder.facade import AgentBuilderFacade

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow_endpoint(
    workflow_id: str,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    facade = AgentBuilderFacade(db)
    result = await facade.execute_workflow(
        workflow_id=workflow_id,
        input_data=input_data,
        user_id=str(current_user.id),
    )
    return result
```

### After (Application Service)

```python
from backend.services.agent_builder.application import WorkflowApplicationService

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow_endpoint(
    workflow_id: str,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = WorkflowApplicationService(db)
    result = await service.execute_workflow(
        workflow_id=workflow_id,
        input_data=input_data,
        user_id=str(current_user.id),
    )
    return result
```

---

## Example 3: Get Workflow (Query)

### Before (Legacy)

```python
from backend.services.agent_builder.workflow_service import WorkflowService

@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    return workflow
```

### After (Facade - Recommended)

```python
from backend.services.agent_builder.facade import AgentBuilderFacade

@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    facade = AgentBuilderFacade(db)
    workflow = facade.get_workflow(workflow_id)
    return workflow
```

### After (CQRS Query)

```python
from backend.services.agent_builder.application.queries import (
    WorkflowQueryHandler,
    GetWorkflowQuery,
)

@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    handler = WorkflowQueryHandler(db)
    query = GetWorkflowQuery(workflow_id=workflow_id)
    workflow = handler.handle_get(query)
    return workflow
```

---

## Example 4: Streaming Execution

### Before (Legacy)

```python
from backend.services.agent_builder.workflow_executor import execute_workflow_stream

@router.get("/workflows/{workflow_id}/execute/stream")
async def execute_workflow_stream_endpoint(
    workflow_id: str,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    async def event_generator():
        async for event in execute_workflow_stream(workflow, db, input_data, str(current_user.id)):
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### After (Facade - Recommended)

```python
from backend.services.agent_builder.facade import AgentBuilderFacade

@router.get("/workflows/{workflow_id}/execute/stream")
async def execute_workflow_stream_endpoint(
    workflow_id: str,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    facade = AgentBuilderFacade(db)
    
    async def event_generator():
        async for event in facade.execute_workflow_streaming(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=str(current_user.id),
        ):
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## Migration Checklist

### For Each Endpoint

- [ ] Identify the legacy service being used
- [ ] Choose migration approach (Facade, Application Service, or CQRS)
- [ ] Update imports
- [ ] Replace service instantiation
- [ ] Update method calls
- [ ] Test the endpoint
- [ ] Update API documentation

### Testing

```python
# Test the migrated endpoint
import pytest
from fastapi.testclient import TestClient

def test_create_workflow_with_facade(client: TestClient, db: Session):
    response = client.post(
        "/api/agent-builder/workflows",
        json={
            "name": "Test Workflow",
            "nodes": [],
            "edges": [],
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Workflow"
```

---

## Benefits of Migration

### 1. Separation of Concerns
- Business logic in Domain layer
- Use cases in Application layer
- Technical details in Infrastructure layer

### 2. Testability
- Domain logic can be tested without database
- Application services can use mocked repositories
- Infrastructure can be tested in isolation

### 3. Maintainability
- Clear boundaries between layers
- Easy to understand and modify
- Reduced coupling

### 4. Scalability
- Easy to add new features
- Can replace implementations without changing interfaces
- Support for multiple execution strategies

---

## Common Patterns

### Dependency Injection

```python
from backend.core.dependencies import get_agent_builder_facade

def get_agent_builder_facade(db: Session = Depends(get_db)) -> AgentBuilderFacade:
    """FastAPI dependency for AgentBuilderFacade."""
    return AgentBuilderFacade(db)

@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
    current_user: User = Depends(get_current_user),
):
    workflow = facade.create_workflow(...)
    return workflow
```

### Error Handling

```python
from backend.services.agent_builder.shared.errors import (
    NotFoundError,
    ValidationError,
    ExecutionError,
)

@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
):
    try:
        workflow = facade.get_workflow(workflow_id)
        return workflow
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Event Handling

```python
from backend.services.agent_builder.infrastructure.messaging import EventBus
from backend.services.agent_builder.domain.workflow.events import WorkflowCreated

# Subscribe to events
event_bus = EventBus()

@event_bus.subscribe(WorkflowCreated)
async def on_workflow_created(event: WorkflowCreated):
    # Send notification, update analytics, etc.
    logger.info(f"Workflow created: {event.workflow_name}")
```

---

## Priority Order for Migration

### High Priority (Core Functionality)
1. Workflow creation/update/delete
2. Workflow execution
3. Agent creation/update/delete

### Medium Priority (Features)
4. Workflow templates
5. Workflow versions
6. Execution monitoring

### Low Priority (Legacy Features)
7. Old executor compatibility
8. Deprecated endpoints

---

## Support

For questions or issues during migration:
1. Check `DDD_ARCHITECTURE.md` for architecture details
2. Review `DDD_VERIFICATION_REPORT.md` for verification results
3. Run `verify_ddd_architecture.py` to check implementation
4. Consult the team for complex cases
