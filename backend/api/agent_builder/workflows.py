"""Agent Builder API endpoints for workflow management - FIXED VERSION."""

import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.workflow_service import WorkflowService
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
    """Create a new workflow."""
    try:
        logger.info(f"Creating workflow for user {current_user.id}: {workflow_data.name}")
        
        workflow_service = WorkflowService(db)
        workflow = workflow_service.create_workflow(
            user_id=str(current_user.id),
            workflow_data=workflow_data
        )
        
        logger.info(f"Workflow created successfully: {workflow.id}")
        
        # Convert UUID fields to strings for response
        return WorkflowResponse(
            id=str(workflow.id),
            user_id=str(workflow.user_id),
            name=workflow.name,
            description=workflow.description,
            graph_definition=workflow.graph_definition,
            is_public=workflow.is_public,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
        
    except ValueError as e:
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
    """Get workflow by ID."""
    try:
        logger.info(f"Fetching workflow {workflow_id} for user {current_user.id}")
        
        workflow_service = WorkflowService(db)
        workflow = workflow_service.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check permissions (owner or public)
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this workflow"
            )
        
        # Convert UUID fields to strings for response
        return WorkflowResponse(
            id=str(workflow.id),
            user_id=str(workflow.user_id),
            name=workflow.name,
            description=workflow.description,
            graph_definition=workflow.graph_definition,
            is_public=workflow.is_public,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
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
    """Update workflow."""
    try:
        logger.info(f"Updating workflow {workflow_id} for user {current_user.id}")
        
        workflow_service = WorkflowService(db)
        
        # Check ownership
        existing_workflow = workflow_service.get_workflow(workflow_id)
        if not existing_workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        if str(existing_workflow.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this workflow"
            )
        
        # Update workflow
        updated_workflow = workflow_service.update_workflow(workflow_id, workflow_data)
        
        logger.info(f"Workflow updated successfully: {workflow_id}")
        
        # Convert UUID fields to strings for response
        return WorkflowResponse(
            id=str(updated_workflow.id),
            user_id=str(updated_workflow.user_id),
            name=updated_workflow.name,
            description=updated_workflow.description,
            graph_definition=updated_workflow.graph_definition,
            is_public=updated_workflow.is_public,
            created_at=updated_workflow.created_at,
            updated_at=updated_workflow.updated_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid workflow data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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
    """Delete workflow."""
    try:
        logger.info(f"Deleting workflow {workflow_id} for user {current_user.id}")
        
        workflow_service = WorkflowService(db)
        
        # Check ownership
        existing_workflow = workflow_service.get_workflow(workflow_id)
        if not existing_workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        if str(existing_workflow.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this workflow"
            )
        
        # Delete workflow
        workflow_service.delete_workflow(workflow_id)
        
        logger.info(f"Workflow deleted successfully: {workflow_id}")
        return None
        
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
    description="List workflows with filtering and search.",
)
async def list_workflows(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    include_public: bool = Query(True, description="Include public workflows"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List workflows with filtering."""
    try:
        logger.info(f"Listing workflows for user {current_user.id}")
        
        workflow_service = WorkflowService(db)
        
        # Get workflows based on filters
        if include_public:
            workflows = workflow_service.list_workflows(
                user_id=None,
                is_public=None,
                limit=limit,
                offset=skip
            )
            # Convert UUID to string for comparison
            workflows = [w for w in workflows if str(w.user_id) == str(current_user.id) or w.is_public]
        else:
            workflows = workflow_service.list_workflows(
                user_id=str(current_user.id),
                is_public=None,
                limit=limit,
                offset=skip
            )
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            workflows = [
                w for w in workflows 
                if search_lower in w.name.lower() or 
                (w.description and search_lower in w.description.lower())
            ]
        
        total = len(workflows)
        
        # Convert UUID fields to strings for response
        workflow_responses = [
            WorkflowResponse(
                id=str(w.id),
                user_id=str(w.user_id),
                name=w.name,
                description=w.description,
                graph_definition=w.graph_definition,
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
        
        workflow_service = WorkflowService(db)
        workflow = workflow_service.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
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
                "id": exec.id,
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


@router.post(
    "/{workflow_id}/execute",
    summary="Execute workflow",
    description="Execute a workflow with optional input data.",
)
async def execute_workflow(
    workflow_id: str,
    input_data: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a workflow."""
    try:
        logger.info(f"Executing workflow {workflow_id} for user {current_user.id}")
        
        workflow_service = WorkflowService(db)
        workflow = workflow_service.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check permissions (compare UUIDs properly)
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to execute this workflow"
            )
        
        # Create execution record
        from backend.db.models.agent_builder import WorkflowExecution
        from datetime import datetime
        import uuid
        
        execution = WorkflowExecution(
            id=uuid.uuid4(),
            workflow_id=uuid.UUID(workflow_id),
            user_id=uuid.UUID(str(current_user.id)),
            input_data=input_data,
            execution_context={},
            status="running",
            started_at=datetime.utcnow(),
        )
        
        try:
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # Execute workflow using the execution engine
            from backend.services.agent_builder.workflow_executor import execute_workflow
            import asyncio
            
            try:
                # Run async execution (use await since we're already in async context)
                # Pass user_id for API key retrieval
                input_data_with_user = {
                    **input_data,
                    "_user_id": str(current_user.id)  # Internal field for user context
                }
                result = await execute_workflow(workflow, db, input_data_with_user)
                
                if result.get("success"):
                    execution.status = "completed"
                    execution.output_data = result.get("output", {})
                    execution.execution_context = result.get("execution_context", {})
                else:
                    execution.status = "failed"
                    execution.error_message = result.get("error", "Unknown error")
                    execution.execution_context = result.get("execution_context", {})
                
                execution.completed_at = datetime.utcnow()
                
                try:
                    db.commit()
                except Exception as commit_error:
                    # If commit fails, rollback and try again with fresh session
                    logger.error(f"Commit failed: {commit_error}")
                    db.rollback()
                    
                    # Refresh execution object and try again
                    db.refresh(execution)
                    execution.status = "failed"
                    execution.error_message = f"Execution completed but failed to save: {str(commit_error)}"
                    execution.completed_at = datetime.utcnow()
                    db.commit()
                
                logger.info(f"Workflow executed: {execution.id} - Status: {execution.status}")
                
                return {
                    "execution_id": str(execution.id),
                    "status": execution.status,
                    "message": "Workflow execution completed" if result.get("success") else f"Workflow execution failed: {result.get('error')}",
                    "output": result.get("output"),
                }
                
            except Exception as exec_error:
                # Execution failed - rollback and update status
                logger.error(f"Workflow execution error: {exec_error}")
                db.rollback()
                
                # Refresh and update execution status
                try:
                    db.refresh(execution)
                    execution.status = "failed"
                    execution.completed_at = datetime.utcnow()
                    execution.error_message = str(exec_error)
                    db.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update execution status: {update_error}")
                
                return {
                    "execution_id": str(execution.id),
                    "status": "failed",
                    "message": f"Workflow execution failed: {str(exec_error)}",
                }
            
        except Exception as exec_error:
            # Rollback on error
            logger.error(f"Failed to create execution record: {exec_error}")
            db.rollback()
            raise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow"
        )
