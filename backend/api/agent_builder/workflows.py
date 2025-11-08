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
        return workflow
        
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
        if workflow.user_id != str(current_user.id) and not workflow.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this workflow"
            )
        
        return workflow
        
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
        
        if existing_workflow.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this workflow"
            )
        
        # Update workflow
        updated_workflow = workflow_service.update_workflow(workflow_id, workflow_data)
        
        logger.info(f"Workflow updated successfully: {workflow_id}")
        return updated_workflow
        
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
        
        if existing_workflow.user_id != str(current_user.id):
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
            workflows = [w for w in workflows if w.user_id == str(current_user.id) or w.is_public]
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
        
        return WorkflowListResponse(
            workflows=workflows,
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
