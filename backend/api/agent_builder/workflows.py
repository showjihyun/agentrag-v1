"""Agent Builder API endpoints for workflow management - Phase 2 Enhanced."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.transaction import transactional
# DDD Architecture
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.shared.errors import (
    NotFoundError,
    ValidationError,
    ExecutionError,
)
from backend.models.agent_builder import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowValidationResult,
    WorkflowCompileResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/workflows",
    tags=["agent-builder-workflows"],
)


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow",
    description="Create a new agent workflow with nodes and edges.",
)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new workflow using DDD Facade pattern."""
    try:
        logger.info(f"Creating workflow for user {current_user.id}: {workflow_data.name}")
        
        facade = AgentBuilderFacade(db)
        workflow = facade.create_workflow(
            user_id=str(current_user.id),
            name=workflow_data.name,
            nodes=workflow_data.nodes,
            edges=workflow_data.edges,
            description=workflow_data.description,
        )
        
        logger.info(f"Workflow created successfully: {workflow.id}")
        
        # Convert UUID fields to strings for response
        return WorkflowResponse(
            id=str(workflow.workflow.id),
            user_id=str(workflow.workflow.user_id),
            name=workflow.workflow.name,
            description=workflow.workflow.description,
            graph_definition=workflow.workflow.to_graph_definition(),
            is_public=workflow.workflow.is_public,
            created_at=workflow.workflow.created_at,
            updated_at=workflow.workflow.updated_at
        )
        
    except ValidationError as e:
        logger.warning(f"Invalid workflow data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow"
        )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow by ID",
    description="Retrieve a specific workflow by ID.",
)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get workflow by ID using DDD Facade pattern."""
    try:
        logger.info(f"Fetching workflow {workflow_id} for user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        workflow = facade.get_workflow(workflow_id)
        
        # Check permissions (owner or public)
        if str(workflow.workflow.user_id) != str(current_user.id) and not workflow.workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this workflow"
            )
        
        # Convert UUID fields to strings for response
        return WorkflowResponse(
            id=str(workflow.workflow.id),
            user_id=str(workflow.workflow.user_id),
            name=workflow.workflow.name,
            description=workflow.workflow.description,
            graph_definition=workflow.workflow.to_graph_definition(),
            is_public=workflow.workflow.is_public,
            created_at=workflow.workflow.created_at,
            updated_at=workflow.workflow.updated_at
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow"
        )


@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Update workflow",
    description="Update an existing workflow. Requires ownership.",
)
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update workflow using DDD Facade pattern."""
    try:
        logger.info(f"Updating workflow {workflow_id} for user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        
        # Check ownership
        existing_workflow = facade.get_workflow(workflow_id)
        if str(existing_workflow.workflow.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this workflow"
            )
        
        # Update workflow
        updated_workflow = facade.update_workflow(
            workflow_id=workflow_id,
            user_id=str(current_user.id),
            name=workflow_data.name,
            nodes=workflow_data.nodes,
            edges=workflow_data.edges,
            description=workflow_data.description,
        )
        
        logger.info(f"Workflow updated successfully: {workflow_id}")
        
        # Convert UUID fields to strings for response
        return WorkflowResponse(
            id=str(updated_workflow.workflow.id),
            user_id=str(updated_workflow.workflow.user_id),
            name=updated_workflow.workflow.name,
            description=updated_workflow.workflow.description,
            graph_definition=updated_workflow.workflow.to_graph_definition(),
            is_public=updated_workflow.workflow.is_public,
            created_at=updated_workflow.workflow.created_at,
            updated_at=updated_workflow.workflow.updated_at
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    except ValidationError as e:
        logger.warning(f"Invalid workflow data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workflow"
        )


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workflow",
    description="Delete a workflow. Requires ownership.",
)
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete workflow using DDD Facade pattern."""
    try:
        logger.info(f"Deleting workflow {workflow_id} for user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        
        # Check ownership
        existing_workflow = facade.get_workflow(workflow_id)
        if str(existing_workflow.workflow.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this workflow"
            )
        
        # Delete workflow
        facade.delete_workflow(workflow_id, str(current_user.id))
        
        logger.info(f"Workflow deleted successfully: {workflow_id}")
        return None
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workflow"
        )


@router.get(
    "",
    response_model=WorkflowListResponse,
    summary="List workflows",
    description="List workflows with advanced filtering and search (Phase 2).",
)
async def list_workflows(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    include_public: bool = Query(True, description="Include public workflows"),
    node_types: Optional[str] = Query(None, description="Filter by node types (comma-separated: agent,control,tool)"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    status_filter: Optional[str] = Query(None, description="Filter by status (draft,active,archived)"),
    sort_by: Optional[str] = Query("updated_at", description="Sort field (name,created_at,updated_at)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc,desc)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List workflows with advanced filtering using DDD Facade pattern."""
    try:
        logger.info(f"Listing workflows for user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        
        # Get workflows based on filters (fetch more for filtering)
        if include_public:
            workflows = facade.list_workflows(
                user_id=None,
                offset=0,
                limit=limit * 3,  # Get more for filtering
            )
            # Convert UUID to string for comparison
            workflows = [w for w in workflows if str(w.user_id) == str(current_user.id) or w.is_public]
        else:
            workflows = facade.list_workflows(
                user_id=str(current_user.id),
                offset=0,
                limit=limit * 3,
            )
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            workflows = [
                w for w in workflows 
                if search_lower in w.name.lower() or 
                (w.description and search_lower in w.description.lower())
            ]
        
        # Apply node type filter (Phase 2)
        if node_types:
            node_type_list = [nt.strip() for nt in node_types.split(",")]
            filtered_workflows = []
            for w in workflows:
                graph_def = w.graph_definition or {}
                nodes = graph_def.get("nodes", [])
                workflow_node_types = {node.get("node_type") for node in nodes if node.get("node_type")}
                if any(nt in workflow_node_types for nt in node_type_list):
                    filtered_workflows.append(w)
            workflows = filtered_workflows
        
        # Apply tags filter (Phase 2)
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            filtered_workflows = []
            for w in workflows:
                graph_def = w.graph_definition or {}
                nodes = graph_def.get("nodes", [])
                workflow_tags = set()
                for node in nodes:
                    node_tags = node.get("data", {}).get("tags", [])
                    if isinstance(node_tags, list):
                        workflow_tags.update(node_tags)
                if any(tag in workflow_tags for tag in tag_list):
                    filtered_workflows.append(w)
            workflows = filtered_workflows
        
        # Apply status filter (Phase 2)
        if status_filter:
            workflows = [w for w in workflows if w.graph_definition.get("status") == status_filter]
        
        # Apply sorting (Phase 2)
        if sort_by == "name":
            workflows.sort(key=lambda w: w.name.lower(), reverse=(sort_order == "desc"))
        elif sort_by == "created_at":
            workflows.sort(key=lambda w: w.created_at, reverse=(sort_order == "desc"))
        else:  # updated_at (default)
            workflows.sort(key=lambda w: w.updated_at, reverse=(sort_order == "desc"))
        
        total = len(workflows)
        
        # Apply pagination after filtering
        workflows = workflows[skip:skip + limit]
        
        # Convert UUID fields to strings for response
        workflow_responses = [
            WorkflowResponse(
                id=str(w.id),
                user_id=str(w.user_id),
                name=w.name,
                description=w.description,
                graph_definition=w.to_graph_definition(),
                is_public=w.is_public,
                created_at=w.created_at,
                updated_at=w.updated_at
            )
            for w in workflows
        ]
        
        return WorkflowListResponse(
            workflows=workflow_responses,
            total=total,
            offset=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list workflows"
        )


@router.get(
    "/{workflow_id}/executions",
    summary="Get workflow execution history",
    description="Retrieve execution history for a specific workflow.",
)
async def get_workflow_executions(
    workflow_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    status_filter: Optional[str] = Query(None, description="Filter by status (success, failed, running)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get workflow execution history."""
    try:
        logger.info(f"Fetching executions for workflow {workflow_id}")
        
        facade = AgentBuilderFacade(db)
        workflow = facade.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check permissions
        if str(workflow.workflow.user_id) != str(current_user.id) and not workflow.workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this workflow"
            )
        
        # Get executions from database
        from backend.db.models.agent_builder import WorkflowExecution
        
        # Build base query
        base_query = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        )
        
        # Apply status filter if provided
        if status_filter:
            base_query = base_query.filter(WorkflowExecution.status == status_filter)
        
        # Get total count before pagination
        total_count = base_query.count()
        
        # Apply pagination and ordering
        executions = base_query.order_by(
            WorkflowExecution.started_at.desc()
        ).limit(limit).offset(offset).all()
        
        # Format response
        execution_list = []
        for exec in executions:
            duration = None
            if exec.completed_at and exec.started_at:
                duration = (exec.completed_at - exec.started_at).total_seconds()
            
            execution_list.append({
                "id": str(exec.id),
                "workflow_id": str(exec.workflow_id),
                "status": exec.status,
                "duration": duration,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                "error_message": exec.error_message,
                "input_data": exec.input_data,
                "output_data": exec.output_data,
            })
        
        return {
            "executions": execution_list,
            "total": total_count,
            "offset": offset,
            "limit": limit,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow executions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow executions"
        )


@router.get(
    "/{workflow_id}/executions/{execution_id}",
    summary="Get workflow execution detail",
    description="Retrieve detailed information about a specific workflow execution.",
)
async def get_workflow_execution(
    workflow_id: str,
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get workflow execution detail."""
    try:
        logger.info(f"Fetching execution {execution_id} for workflow {workflow_id}")
        
        from backend.db.models.agent_builder import WorkflowExecution
        import uuid
        
        # Get execution
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == uuid.UUID(execution_id),
            WorkflowExecution.workflow_id == uuid.UUID(workflow_id)
        ).first()
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found"
            )
        
        # Check permissions
        if str(execution.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this execution"
            )
        
        # Get workflow for name
        facade = AgentBuilderFacade(db)
        workflow = facade.get_workflow(workflow_id)
        
        # Calculate duration
        duration = None
        if execution.completed_at and execution.started_at:
            duration = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
        
        # Extract node executions from execution_context
        node_executions = []
        if execution.execution_context:
            # First try to get detailed node_executions
            node_executions_data = execution.execution_context.get("node_executions", [])
            if node_executions_data:
                node_executions = node_executions_data
            else:
                # Fallback to node_results for backward compatibility
                node_results = execution.execution_context.get("node_results", {})
                for node_id, result in node_results.items():
                    node_executions.append({
                        "node_id": node_id,
                        "node_name": node_id,
                        "status": "completed",
                        "input": execution.input_data,
                        "output": result,
                        "started_at": execution.started_at.isoformat() if execution.started_at else None,
                        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                    })
        
        return {
            "id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "workflow_name": workflow.workflow.name if workflow else "Unknown",
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration": duration,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "error_message": execution.error_message,
            "node_executions": node_executions,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow execution"
        )


@router.post(
    "/{workflow_id}/execute",
    summary="Execute workflow",
    description="Execute a workflow with optional input data using DDD Application Service.",
)
async def execute_workflow(
    workflow_id: str,
    input_data: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a workflow using DDD Application Service."""
    try:
        logger.info(f"[WORKFLOW EXECUTE] Starting execution for workflow {workflow_id}, user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        
        # Check permissions
        workflow = facade.get_workflow(workflow_id)
        if str(workflow.workflow.user_id) != str(current_user.id) and not workflow.workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to execute this workflow"
            )
        
        # Execute workflow using Application Service
        result = await facade.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=str(current_user.id),
        )
        
        logger.info(f"Workflow executed: {result.get('execution_id')} - Status: {result.get('status')}")
        
        return result
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    except ExecutionError as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow"
        )


@router.post(
    "/{workflow_id}/duplicate",
    response_model=WorkflowResponse,
    summary="Duplicate workflow",
    description="Create a copy of an existing workflow.",
)
async def duplicate_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Duplicate a workflow."""
    try:
        logger.info(f"Duplicating workflow {workflow_id} for user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        
        # Get original workflow
        original = facade.get_workflow(workflow_id)
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check permission (can duplicate own workflows or public workflows)
        if str(original.workflow.user_id) != str(current_user.id) and not original.workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to duplicate this workflow"
            )
        
        # Create duplicate
        from backend.models.agent_builder import WorkflowNodeCreate, WorkflowEdgeCreate
        import uuid
        
        # Create ID mapping for nodes
        old_to_new_id = {}
        nodes = []
        
        for node in original.workflow.nodes:
            new_id = str(uuid.uuid4())
            old_to_new_id[node.id] = new_id
            
            nodes.append(WorkflowNodeCreate(
                id=new_id,
                node_type=node.node_type.value,
                node_ref_id=node.node_ref_id,
                position_x=node.position.x,
                position_y=node.position.y,
                configuration=node.config.to_dict()
            ))
        
        # Convert edges with new node IDs
        edges = []
        for edge in original.workflow.edges:
            edges.append(WorkflowEdgeCreate(
                id=str(uuid.uuid4()),
                source_node_id=old_to_new_id.get(edge.source_node_id, edge.source_node_id),
                target_node_id=old_to_new_id.get(edge.target_node_id, edge.target_node_id),
                edge_type=edge.edge_type.value,
                condition=edge.condition.to_dict() if edge.condition else None
            ))
        
        # Get entry point with new ID
        entry_point = None
        if original.workflow.entry_point:
            entry_point = old_to_new_id.get(original.workflow.entry_point, nodes[0].id if nodes else None)
        elif nodes:
            entry_point = nodes[0].id
        
        # Create new workflow
        workflow_data = WorkflowCreate(
            name=f"{original.workflow.name} (Copy)",
            description=original.workflow.description,
            nodes=nodes,
            edges=edges,
            entry_point=entry_point,
            is_public=False  # Duplicates are private by default
        )
        
        new_workflow = workflow_service.create_workflow(
            user_id=str(current_user.id),
            workflow_data=workflow_data
        )
        
        logger.info(f"Workflow duplicated successfully: {new_workflow.id}")
        
        return WorkflowResponse(
            id=str(new_workflow.workflow.id),
            user_id=str(new_workflow.workflow.user_id),
            name=new_workflow.workflow.name,
            description=new_workflow.workflow.description,
            graph_definition=new_workflow.workflow.to_graph_definition(),
            is_public=new_workflow.workflow.is_public,
            created_at=new_workflow.workflow.created_at,
            updated_at=new_workflow.workflow.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate workflow"
        )


# ============================================================================
# Phase 2 Enhancements
# ============================================================================


@router.get(
    "/{workflow_id}/execute/stream",
    summary="Execute workflow with streaming",
    description="Execute workflow with Server-Sent Events streaming for real-time progress (Phase 2).",
)
async def execute_workflow_stream(
    workflow_id: str,
    input_data: str = Query("{}", description="JSON string of input data"),
    token: Optional[str] = Query(None, description="Auth token for SSE"),
    db: Session = Depends(get_db),
):
    """
    Execute workflow with Server-Sent Events streaming (Phase 2).
    
    Streams real-time execution progress for ExecutionTimeline component.
    
    Events:
    - start: Execution started
    - node_start: Node execution started
    - node_complete: Node execution completed
    - node_error: Node execution failed
    - complete: Workflow execution completed
    - error: Workflow execution failed
    """
    async def event_generator():
        try:
            # Authenticate user
            if not token or token == 'null':
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Authentication required'}})}\n\n"
                return
            
            from backend.services.auth_service import AuthService
            payload = AuthService.decode_token(token)
            if not payload:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Invalid token'}})}\n\n"
                return
            
            user_id = payload.get("sub")
            
            # Get workflow
            facade = AgentBuilderFacade(db)
            workflow = facade.get_workflow(workflow_id)
            
            if not workflow:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Workflow not found'}})}\n\n"
                return
            
            # Check permissions
            if str(workflow.workflow.user_id) != str(user_id) and not workflow.workflow.is_public:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Access denied'}})}\n\n"
                return
            
            # Parse input data
            try:
                input_dict = json.loads(input_data)
            except:
                input_dict = {}
            
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'data': {'workflow_id': workflow_id, 'timestamp': datetime.utcnow().isoformat()}})}\n\n"
            
            # Execute workflow with streaming
            from backend.services.agent_builder.workflow_executor import execute_workflow_stream
            
            async for event in execute_workflow_stream(workflow, db, input_dict, user_id):
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming
            
        except Exception as e:
            logger.error(f"SSE stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.patch(
    "/{workflow_id}/autosave",
    summary="Autosave workflow",
    description="Autosave workflow changes (optimized for Phase 2 debouncing).",
)
async def autosave_workflow(
    workflow_id: str,
    nodes: Optional[List[Any]] = None,
    edges: Optional[List[Any]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Autosave workflow changes (Phase 2 optimization).
    
    Only updates graph_definition without full validation.
    Use PUT /workflows/{id} for full updates with validation.
    """
    try:
        facade = AgentBuilderFacade(db)
        workflow = facade.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check ownership
        if str(workflow.workflow.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update only if provided
        if nodes is not None or edges is not None:
            # Get the database model directly for fast autosave
            from backend.db.models.agent_builder import Workflow
            db_workflow = db.query(Workflow).filter(
                Workflow.id == workflow_id,
                Workflow.deleted_at.is_(None)
            ).first()
            
            if not db_workflow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workflow {workflow_id} not found"
                )
            
            graph_def = db_workflow.graph_definition or {}
            
            if nodes is not None:
                graph_def["nodes"] = nodes
            
            if edges is not None:
                graph_def["edges"] = edges
            
            db_workflow.graph_definition = graph_def
            db_workflow.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_workflow)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "updated_at": db_workflow.updated_at.isoformat() if 'db_workflow' in locals() else datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to autosave workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to autosave workflow"
        )


@router.get(
    "/{workflow_id}/statistics",
    summary="Get workflow statistics",
    description="Get workflow execution statistics and performance metrics (Phase 2).",
)
async def get_workflow_statistics(
    workflow_id: str,
    time_range: Optional[str] = Query("7d", description="Time range (1d, 7d, 30d, all)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get workflow execution statistics (Phase 2).
    
    Returns:
    - Total executions
    - Success/failure rates
    - Average execution time
    - Node performance metrics
    - Execution timeline
    """
    try:
        facade = AgentBuilderFacade(db)
        workflow = facade.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check permissions
        if str(workflow.workflow.user_id) != str(current_user.id) and not workflow.workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get executions
        from backend.db.models.agent_builder import WorkflowExecution
        
        # Calculate time range
        now = datetime.utcnow()
        if time_range == "1d":
            start_time = now - timedelta(days=1)
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
        elif time_range == "30d":
            start_time = now - timedelta(days=30)
        else:  # all
            start_time = datetime.min
        
        # Query executions
        executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id,
            WorkflowExecution.started_at >= start_time
        ).all()
        
        # Calculate statistics
        total = len(executions)
        completed = sum(1 for e in executions if e.status == "completed")
        failed = sum(1 for e in executions if e.status == "failed")
        running = sum(1 for e in executions if e.status == "running")
        
        # Calculate average duration
        completed_execs = [e for e in executions if e.status == "completed" and e.completed_at and e.started_at]
        avg_duration = sum((e.completed_at - e.started_at).total_seconds() for e in completed_execs) / len(completed_execs) if completed_execs else 0
        
        # Node performance metrics
        node_stats = {}
        for exec in completed_execs:
            context = exec.execution_context or {}
            node_timings = context.get("node_timings", {})
            for node_id, timing in node_timings.items():
                if node_id not in node_stats:
                    node_stats[node_id] = {
                        "executions": 0,
                        "total_time": 0,
                        "failures": 0
                    }
                node_stats[node_id]["executions"] += 1
                node_stats[node_id]["total_time"] += timing.get("duration", 0)
                if timing.get("status") == "failed":
                    node_stats[node_id]["failures"] += 1
        
        # Calculate averages
        for node_id, stats in node_stats.items():
            stats["avg_time"] = stats["total_time"] / stats["executions"] if stats["executions"] > 0 else 0
            stats["failure_rate"] = stats["failures"] / stats["executions"] if stats["executions"] > 0 else 0
        
        # Execution timeline (last 10)
        recent_executions = sorted(executions, key=lambda e: e.started_at, reverse=True)[:10]
        timeline = [
            {
                "id": str(e.id),
                "status": e.status,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "duration": (e.completed_at - e.started_at).total_seconds() if e.completed_at and e.started_at else None,
                "error": e.error_message
            }
            for e in recent_executions
        ]
        
        return {
            "workflow_id": workflow_id,
            "time_range": time_range,
            "statistics": {
                "total_executions": total,
                "completed": completed,
                "failed": failed,
                "running": running,
                "success_rate": round((completed / total * 100) if total > 0 else 0, 1),
                "avg_duration_seconds": round(avg_duration, 2),
            },
            "node_performance": node_stats,
            "recent_executions": timeline
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow statistics"
        )



@router.post(
    "/{workflow_id}/nodes/agent",
    summary="Add agent to workflow",
    description="Add an agent as a node to the workflow for agent orchestration.",
)
async def add_agent_to_workflow(
    workflow_id: str,
    agent_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add an agent as a node to a workflow.
    
    Request body:
    {
        "agent_id": "uuid",
        "position_x": 100,
        "position_y": 200,
        "role": "worker",  # optional
        "max_retries": 3,  # optional
        "timeout_seconds": 60,  # optional
        "auto_convert": true  # optional, convert to block
    }
    """
    try:
        from backend.services.agent_builder.integration_service import AgentWorkflowIntegrationService
        
        # Validate workflow exists and user has access
        facade = AgentBuilderFacade(db)
        workflow = facade.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check permissions
        if str(workflow.workflow.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this workflow"
            )
        
        # Extract parameters
        agent_id = agent_data.get("agent_id")
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="agent_id is required"
            )
        
        position_x = agent_data.get("position_x", 0)
        position_y = agent_data.get("position_y", 0)
        role = agent_data.get("role", "worker")
        max_retries = agent_data.get("max_retries", 3)
        timeout_seconds = agent_data.get("timeout_seconds", 60)
        auto_convert = agent_data.get("auto_convert", True)
        
        # Add agent to workflow
        integration_service = AgentWorkflowIntegrationService(db)
        
        node = integration_service.add_agent_block_to_workflow(
            workflow_id=workflow_id,
            agent_id=agent_id,
            position_x=position_x,
            position_y=position_y,
            auto_convert=auto_convert,
            role=role,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
        )
        
        db.commit()
        
        logger.info(f"Added agent {agent_id} to workflow {workflow_id}")
        
        return {
            "node_id": str(node.id),
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "node_type": node.node_type,
            "name": node.name,
            "position": {
                "x": node.position_x,
                "y": node.position_y,
            },
            "configuration": node.configuration,
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add agent to workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add agent to workflow"
        )


@router.get(
    "/{workflow_id}/agents",
    summary="Get agents in workflow",
    description="Get all agent nodes in the workflow.",
)
async def get_workflow_agents(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all agent nodes in a workflow."""
    try:
        from backend.db.models.agent_builder import WorkflowNode, Agent
        
        # Validate workflow exists and user has access
        facade = AgentBuilderFacade(db)
        workflow = facade.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check permissions
        if str(workflow.workflow.user_id) != str(current_user.id) and not workflow.workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get agent nodes
        agent_nodes = db.query(WorkflowNode).filter(
            WorkflowNode.workflow_id == workflow_id,
            WorkflowNode.node_type == "agent"
        ).all()
        
        # Enrich with agent details
        result = []
        for node in agent_nodes:
            agent_id = node.configuration.get("agent_id")
            if agent_id:
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    result.append({
                        "node_id": str(node.id),
                        "agent_id": str(agent.id),
                        "name": node.name,
                        "description": node.description,
                        "position": {
                            "x": node.position_x,
                            "y": node.position_y,
                        },
                        "configuration": node.configuration,
                        "agent_details": {
                            "llm_provider": agent.llm_provider,
                            "llm_model": agent.llm_model,
                            "agent_type": agent.agent_type,
                        }
                    })
        
        return {
            "workflow_id": workflow_id,
            "agents": result,
            "total": len(result),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow agents"
        )
