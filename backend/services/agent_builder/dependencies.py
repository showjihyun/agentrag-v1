"""
FastAPI Dependencies for Agent Builder

Provides dependency injection for DDD services.
"""

from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends

from backend.db.database import get_db
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.application import (
    WorkflowApplicationService,
    AgentApplicationService,
    ExecutionApplicationService,
)
from backend.services.agent_builder.infrastructure.execution import UnifiedExecutor
from backend.services.agent_builder.infrastructure.messaging import EventBus


# ============================================================================
# FACADE (Recommended for most use cases)
# ============================================================================

def get_agent_builder_facade(
    db: Session = Depends(get_db)
) -> AgentBuilderFacade:
    """
    Get AgentBuilderFacade instance.
    
    Usage:
        @router.post("/workflows")
        async def create_workflow(
            facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
        ):
            workflow = facade.create_workflow(...)
            return workflow
    """
    return AgentBuilderFacade(db)


# ============================================================================
# APPLICATION SERVICES (For more control)
# ============================================================================

def get_workflow_service(
    db: Session = Depends(get_db)
) -> WorkflowApplicationService:
    """
    Get WorkflowApplicationService instance.
    
    Usage:
        @router.post("/workflows")
        async def create_workflow(
            service: WorkflowApplicationService = Depends(get_workflow_service),
        ):
            workflow = service.create_workflow(...)
            return workflow
    """
    return WorkflowApplicationService(db)


def get_agent_service(
    db: Session = Depends(get_db)
) -> AgentApplicationService:
    """
    Get AgentApplicationService instance.
    
    Usage:
        @router.post("/agents")
        async def create_agent(
            service: AgentApplicationService = Depends(get_agent_service),
        ):
            agent = service.create_agent(...)
            return agent
    """
    return AgentApplicationService(db)


def get_execution_service(
    db: Session = Depends(get_db)
) -> ExecutionApplicationService:
    """
    Get ExecutionApplicationService instance.
    
    Usage:
        @router.get("/executions/{execution_id}")
        async def get_execution(
            execution_id: str,
            service: ExecutionApplicationService = Depends(get_execution_service),
        ):
            execution = service.get_execution(execution_id)
            return execution
    """
    return ExecutionApplicationService(db)


# ============================================================================
# INFRASTRUCTURE (For advanced use cases)
# ============================================================================

def get_unified_executor(
    db: Session = Depends(get_db)
) -> UnifiedExecutor:
    """
    Get UnifiedExecutor instance.
    
    Usage:
        @router.post("/workflows/{workflow_id}/execute")
        async def execute_workflow(
            workflow_id: str,
            executor: UnifiedExecutor = Depends(get_unified_executor),
        ):
            result = await executor.execute(workflow, input_data, user_id)
            return result
    """
    return UnifiedExecutor(db)


def get_event_bus() -> EventBus:
    """
    Get EventBus singleton instance.
    
    Usage:
        @router.post("/workflows")
        async def create_workflow(
            event_bus: EventBus = Depends(get_event_bus),
        ):
            # Subscribe to events
            @event_bus.subscribe(WorkflowCreated)
            async def on_created(event):
                logger.info(f"Workflow created: {event.workflow_name}")
    """
    return EventBus.get_instance()


# ============================================================================
# CQRS HANDLERS (For explicit read/write separation)
# ============================================================================

def get_workflow_command_handler(
    db: Session = Depends(get_db)
):
    """
    Get WorkflowCommandHandler for write operations.
    
    Usage:
        from backend.services.agent_builder.application.commands import CreateWorkflowCommand
        
        @router.post("/workflows")
        async def create_workflow(
            handler = Depends(get_workflow_command_handler),
        ):
            command = CreateWorkflowCommand(...)
            workflow = handler.handle_create(command)
            return workflow
    """
    from backend.services.agent_builder.application.commands import WorkflowCommandHandler
    return WorkflowCommandHandler(db)


def get_workflow_query_handler(
    db: Session = Depends(get_db)
):
    """
    Get WorkflowQueryHandler for read operations.
    
    Usage:
        from backend.services.agent_builder.application.queries import GetWorkflowQuery
        
        @router.get("/workflows/{workflow_id}")
        async def get_workflow(
            workflow_id: str,
            handler = Depends(get_workflow_query_handler),
        ):
            query = GetWorkflowQuery(workflow_id=workflow_id)
            workflow = handler.handle_get(query)
            return workflow
    """
    from backend.services.agent_builder.application.queries import WorkflowQueryHandler
    return WorkflowQueryHandler(db)


def get_agent_command_handler(
    db: Session = Depends(get_db)
):
    """Get AgentCommandHandler for write operations."""
    from backend.services.agent_builder.application.commands import AgentCommandHandler
    return AgentCommandHandler(db)


def get_agent_query_handler(
    db: Session = Depends(get_db)
):
    """Get AgentQueryHandler for read operations."""
    from backend.services.agent_builder.application.queries import AgentQueryHandler
    return AgentQueryHandler(db)


def get_execution_query_handler(
    db: Session = Depends(get_db)
):
    """Get ExecutionQueryHandler for read operations."""
    from backend.services.agent_builder.application.queries import ExecutionQueryHandler
    return ExecutionQueryHandler(db)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Using Facade (Recommended)
--------------------------------------

from backend.services.agent_builder.dependencies import get_agent_builder_facade

@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
    current_user: User = Depends(get_current_user),
):
    workflow = facade.create_workflow(
        user_id=str(current_user.id),
        name=workflow_data.name,
        nodes=workflow_data.nodes,
        edges=workflow_data.edges,
    )
    return workflow


Example 2: Using Application Service
-------------------------------------

from backend.services.agent_builder.dependencies import get_workflow_service

@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    service: WorkflowApplicationService = Depends(get_workflow_service),
    current_user: User = Depends(get_current_user),
):
    workflow = service.create_workflow(
        user_id=str(current_user.id),
        name=workflow_data.name,
        nodes=workflow_data.nodes,
        edges=workflow_data.edges,
    )
    return workflow


Example 3: Using CQRS
---------------------

from backend.services.agent_builder.dependencies import (
    get_workflow_command_handler,
    get_workflow_query_handler,
)
from backend.services.agent_builder.application.commands import CreateWorkflowCommand
from backend.services.agent_builder.application.queries import GetWorkflowQuery

@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    handler = Depends(get_workflow_command_handler),
    current_user: User = Depends(get_current_user),
):
    command = CreateWorkflowCommand(
        user_id=str(current_user.id),
        name=workflow_data.name,
        nodes=workflow_data.nodes,
        edges=workflow_data.edges,
    )
    workflow = handler.handle_create(command)
    return workflow

@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    handler = Depends(get_workflow_query_handler),
):
    query = GetWorkflowQuery(workflow_id=workflow_id)
    workflow = handler.handle_get(query)
    return workflow


Example 4: Using Executor Directly
-----------------------------------

from backend.services.agent_builder.dependencies import get_unified_executor

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    input_data: Dict[str, Any],
    executor: UnifiedExecutor = Depends(get_unified_executor),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Load workflow
    workflow_entity = load_workflow(db, workflow_id)
    
    # Execute
    result = await executor.execute(
        workflow=workflow_entity,
        input_data=input_data,
        user_id=str(current_user.id),
    )
    return result
"""
