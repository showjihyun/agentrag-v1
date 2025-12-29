"""
Workflows API - DDD Implementation Example

This is a reference implementation showing how to use the new DDD architecture.
Can be used as a template for migrating other endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import json
import logging

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.models.agent_builder import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
)

# DDD Dependencies
from backend.services.agent_builder.dependencies import (
    get_agent_builder_facade,
    get_workflow_service,
    get_workflow_command_handler,
    get_workflow_query_handler,
)
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.application import WorkflowApplicationService
from backend.services.agent_builder.shared.errors import (
    NotFoundError,
    ValidationError,
    ExecutionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/workflows-ddd",
    tags=["workflows-ddd"],
)


# ============================================================================
# APPROACH 1: Using Facade (Recommended for most cases)
# ============================================================================

@router.post("/facade", response_model=WorkflowResponse, status_code=201)
async def create_workflow_with_facade(
    workflow_data: WorkflowCreate,
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new workflow using Facade pattern.
    
    This is the recommended approach for most use cases.
    Provides a simple, unified interface to the DDD architecture.
    """
    try:
        workflow = facade.create_workflow(
            user_id=str(current_user.id),
            name=workflow_data.name,
            nodes=workflow_data.nodes,
            edges=workflow_data.edges,
            description=workflow_data.description,
        )
        return workflow
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/facade/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_with_facade(
    workflow_id: str,
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
    current_user: User = Depends(get_current_user),
):
    """Get a workflow by ID using Facade pattern."""
    try:
        workflow = facade.get_workflow(workflow_id)
        
        # Check ownership
        if workflow.user_id != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return workflow
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.put("/facade/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow_with_facade(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
    current_user: User = Depends(get_current_user),
):
    """Update a workflow using Facade pattern."""
    try:
        # Check ownership
        existing = facade.get_workflow(workflow_id)
        if existing.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        workflow = facade.update_workflow(
            workflow_id=workflow_id,
            user_id=str(current_user.id),
            name=workflow_data.name,
            nodes=workflow_data.nodes,
            edges=workflow_data.edges,
            description=workflow_data.description,
        )
        return workflow
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/facade/{workflow_id}", status_code=204)
async def delete_workflow_with_facade(
    workflow_id: str,
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
    current_user: User = Depends(get_current_user),
):
    """Delete a workflow using Facade pattern."""
    try:
        # Check ownership
        existing = facade.get_workflow(workflow_id)
        if existing.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        facade.delete_workflow(workflow_id, str(current_user.id))
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/facade/{workflow_id}/execute")
async def execute_workflow_with_facade(
    workflow_id: str,
    input_data: Dict[str, Any],
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
    current_user: User = Depends(get_current_user),
):
    """Execute a workflow using Facade pattern."""
    try:
        result = await facade.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=str(current_user.id),
        )
        return result
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except ExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/facade/{workflow_id}/execute/stream")
async def execute_workflow_stream_with_facade(
    workflow_id: str,
    input_data: Dict[str, Any] = {},
    facade: AgentBuilderFacade = Depends(get_agent_builder_facade),
    current_user: User = Depends(get_current_user),
):
    """Execute a workflow with streaming using Facade pattern."""
    try:
        async def event_generator():
            async for event in facade.execute_workflow_streaming(
                workflow_id=workflow_id,
                input_data=input_data,
                user_id=str(current_user.id),
            ):
                yield f"data: {json.dumps(event)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")


# ============================================================================
# APPROACH 2: Using Application Service (For more control)
# ============================================================================

@router.post("/service", response_model=WorkflowResponse, status_code=201)
async def create_workflow_with_service(
    workflow_data: WorkflowCreate,
    service: WorkflowApplicationService = Depends(get_workflow_service),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new workflow using Application Service.
    
    Use this approach when you need more control over the workflow creation process.
    """
    try:
        workflow = service.create_workflow(
            user_id=str(current_user.id),
            name=workflow_data.name,
            nodes=workflow_data.nodes,
            edges=workflow_data.edges,
            description=workflow_data.description,
        )
        return workflow
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/service", response_model=List[WorkflowResponse])
async def list_workflows_with_service(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: WorkflowApplicationService = Depends(get_workflow_service),
    current_user: User = Depends(get_current_user),
):
    """List workflows using Application Service."""
    workflows = service.list_workflows(
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
    )
    return workflows


# ============================================================================
# APPROACH 3: Using CQRS (For explicit read/write separation)
# ============================================================================

@router.post("/cqrs", response_model=WorkflowResponse, status_code=201)
async def create_workflow_with_cqrs(
    workflow_data: WorkflowCreate,
    handler = Depends(get_workflow_command_handler),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new workflow using CQRS Command pattern.
    
    Use this approach when you want explicit separation between reads and writes.
    """
    from backend.services.agent_builder.application.commands import CreateWorkflowCommand
    
    try:
        command = CreateWorkflowCommand(
            user_id=str(current_user.id),
            name=workflow_data.name,
            nodes=workflow_data.nodes,
            edges=workflow_data.edges,
            description=workflow_data.description,
        )
        workflow = handler.handle_create(command)
        return workflow
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cqrs/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_with_cqrs(
    workflow_id: str,
    handler = Depends(get_workflow_query_handler),
    current_user: User = Depends(get_current_user),
):
    """Get a workflow using CQRS Query pattern."""
    from backend.services.agent_builder.application.queries import GetWorkflowQuery
    
    try:
        query = GetWorkflowQuery(workflow_id=workflow_id)
        workflow = handler.handle_get(query)
        
        # Check ownership
        if workflow.user_id != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return workflow
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.get("/cqrs", response_model=List[WorkflowResponse])
async def list_workflows_with_cqrs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    handler = Depends(get_workflow_query_handler),
    current_user: User = Depends(get_current_user),
):
    """List workflows using CQRS Query pattern."""
    from backend.services.agent_builder.application.queries import ListWorkflowsQuery
    
    query = ListWorkflowsQuery(
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
    )
    workflows = handler.handle_list(query)
    return workflows


# ============================================================================
# COMPARISON ENDPOINT (For testing)
# ============================================================================

@router.get("/comparison")
async def compare_approaches(
    current_user: User = Depends(get_current_user),
):
    """
    Compare different approaches for accessing DDD architecture.
    
    Returns information about each approach and when to use them.
    """
    return {
        "approaches": [
            {
                "name": "Facade",
                "endpoint_prefix": "/facade",
                "description": "Unified interface to DDD architecture",
                "pros": [
                    "Simple and easy to use",
                    "Hides complexity",
                    "Good for most use cases",
                ],
                "cons": [
                    "Less control over internal operations",
                ],
                "use_when": [
                    "Building new features",
                    "Need simple API",
                    "Don't need fine-grained control",
                ],
            },
            {
                "name": "Application Service",
                "endpoint_prefix": "/service",
                "description": "Direct access to application layer",
                "pros": [
                    "More control",
                    "Access to all service methods",
                    "Better for complex operations",
                ],
                "cons": [
                    "More verbose",
                    "Need to understand application layer",
                ],
                "use_when": [
                    "Need fine-grained control",
                    "Complex business logic",
                    "Custom workflows",
                ],
            },
            {
                "name": "CQRS",
                "endpoint_prefix": "/cqrs",
                "description": "Explicit read/write separation",
                "pros": [
                    "Clear separation of concerns",
                    "Optimized for reads and writes separately",
                    "Better for complex domains",
                ],
                "cons": [
                    "More boilerplate",
                    "Steeper learning curve",
                ],
                "use_when": [
                    "Need read/write optimization",
                    "Complex query requirements",
                    "Event sourcing",
                ],
            },
        ],
        "recommendation": "Start with Facade, move to Application Service or CQRS as needed",
    }
