"""
Workflows API v2

Enhanced workflow management with:
- Standardized responses
- Audit logging
- Rate limiting
- Better error handling
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models.user import User
from backend.core.auth_dependencies import get_current_user
from backend.core.api_response import (
    APIResponse,
    ResponseBuilder,
    ErrorCode,
    PaginationMeta,
    ResponseTimer,
)
from backend.core.rate_limiter_enhanced import rate_limit, RateLimitTier
from backend.core.audit_logger import get_audit_logger, AuditEventType
from backend.services.agent_builder.workflow_service import WorkflowService
from backend.models.agent_builder import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
)

logger = logging.getLogger(__name__)
audit = get_audit_logger()

router = APIRouter(prefix="/api/v2/workflows", tags=["v2-workflows"])


@router.get("")
@rate_limit(tier=RateLimitTier.FREE)
async def list_workflows(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List workflows with pagination and filtering.
    
    Returns standardized paginated response.
    """
    with ResponseTimer() as timer:
        try:
            workflow_service = WorkflowService(db)
            
            # Get workflows with pagination
            workflows, total = workflow_service.list_workflows_paginated(
                user_id=str(current_user.id),
                page=page,
                page_size=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # Convert to response format
            workflow_list = [
                {
                    "id": str(w.id),
                    "name": w.name,
                    "description": w.description,
                    "is_public": w.is_public,
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                    "updated_at": w.updated_at.isoformat() if w.updated_at else None,
                    "node_count": len(w.graph_definition.get("nodes", [])) if w.graph_definition else 0,
                }
                for w in workflows
            ]
            
            # Log access
            audit.log_resource_access(
                user_id=str(current_user.id),
                resource_type="workflow",
                resource_id="list",
                action=f"Listed workflows (page {page})",
                request=request
            )
            
            return ResponseBuilder.paginated(
                items=workflow_list,
                page=page,
                page_size=page_size,
                total_items=total,
                request_id=getattr(request.state, "request_id", None),
                duration_ms=timer.duration_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}", exc_info=True)
            return ResponseBuilder.error(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to list workflows",
                request_id=getattr(request.state, "request_id", None)
            )


@router.get("/{workflow_id}")
@rate_limit(tier=RateLimitTier.FREE)
async def get_workflow(
    request: Request,
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific workflow by ID.
    """
    with ResponseTimer() as timer:
        try:
            workflow_service = WorkflowService(db)
            workflow = workflow_service.get_workflow(
                workflow_id=workflow_id,
                user_id=str(current_user.id)
            )
            
            if not workflow:
                return ResponseBuilder.error(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"Workflow {workflow_id} not found",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Log access
            audit.log_resource_access(
                user_id=str(current_user.id),
                resource_type="workflow",
                resource_id=workflow_id,
                action="Retrieved workflow",
                request=request
            )
            
            return ResponseBuilder.success(
                data={
                    "id": str(workflow.id),
                    "user_id": str(workflow.user_id),
                    "name": workflow.name,
                    "description": workflow.description,
                    "graph_definition": workflow.graph_definition,
                    "is_public": workflow.is_public,
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
                },
                request_id=getattr(request.state, "request_id", None),
                duration_ms=timer.duration_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to get workflow: {e}", exc_info=True)
            return ResponseBuilder.error(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to get workflow",
                request_id=getattr(request.state, "request_id", None)
            )


@router.post("")
@rate_limit(tier=RateLimitTier.FREE, endpoint_key="/api/v2/workflows")
async def create_workflow(
    request: Request,
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new workflow.
    """
    with ResponseTimer() as timer:
        try:
            workflow_service = WorkflowService(db)
            workflow = workflow_service.create_workflow(
                user_id=str(current_user.id),
                workflow_data=workflow_data
            )
            
            # Log creation
            audit.log(
                event_type=AuditEventType.WORKFLOW_CREATED,
                action=f"Created workflow: {workflow.name}",
                request=request,
                user_id=str(current_user.id),
                resource_type="workflow",
                resource_id=str(workflow.id),
                details={"name": workflow.name}
            )
            
            return ResponseBuilder.success(
                data={
                    "id": str(workflow.id),
                    "user_id": str(workflow.user_id),
                    "name": workflow.name,
                    "description": workflow.description,
                    "graph_definition": workflow.graph_definition,
                    "is_public": workflow.is_public,
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
                },
                request_id=getattr(request.state, "request_id", None),
                duration_ms=timer.duration_ms
            )
            
        except ValueError as e:
            return ResponseBuilder.error(
                code=ErrorCode.VALIDATION_FAILED,
                message=str(e),
                request_id=getattr(request.state, "request_id", None)
            )
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}", exc_info=True)
            return ResponseBuilder.error(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to create workflow",
                request_id=getattr(request.state, "request_id", None)
            )


@router.put("/{workflow_id}")
@rate_limit(tier=RateLimitTier.FREE)
async def update_workflow(
    request: Request,
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing workflow.
    """
    with ResponseTimer() as timer:
        try:
            workflow_service = WorkflowService(db)
            workflow = workflow_service.update_workflow(
                workflow_id=workflow_id,
                user_id=str(current_user.id),
                workflow_data=workflow_data
            )
            
            if not workflow:
                return ResponseBuilder.error(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"Workflow {workflow_id} not found",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Log update
            audit.log(
                event_type=AuditEventType.WORKFLOW_UPDATED,
                action=f"Updated workflow: {workflow.name}",
                request=request,
                user_id=str(current_user.id),
                resource_type="workflow",
                resource_id=workflow_id
            )
            
            return ResponseBuilder.success(
                data={
                    "id": str(workflow.id),
                    "user_id": str(workflow.user_id),
                    "name": workflow.name,
                    "description": workflow.description,
                    "graph_definition": workflow.graph_definition,
                    "is_public": workflow.is_public,
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
                },
                request_id=getattr(request.state, "request_id", None),
                duration_ms=timer.duration_ms
            )
            
        except ValueError as e:
            return ResponseBuilder.error(
                code=ErrorCode.VALIDATION_FAILED,
                message=str(e),
                request_id=getattr(request.state, "request_id", None)
            )
        except Exception as e:
            logger.error(f"Failed to update workflow: {e}", exc_info=True)
            return ResponseBuilder.error(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to update workflow",
                request_id=getattr(request.state, "request_id", None)
            )


@router.delete("/{workflow_id}")
@rate_limit(tier=RateLimitTier.FREE)
async def delete_workflow(
    request: Request,
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a workflow.
    """
    with ResponseTimer() as timer:
        try:
            workflow_service = WorkflowService(db)
            
            # Get workflow name for logging
            workflow = workflow_service.get_workflow(workflow_id, str(current_user.id))
            if not workflow:
                return ResponseBuilder.error(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"Workflow {workflow_id} not found",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            workflow_name = workflow.name
            
            # Delete
            deleted = workflow_service.delete_workflow(
                workflow_id=workflow_id,
                user_id=str(current_user.id)
            )
            
            if not deleted:
                return ResponseBuilder.error(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"Workflow {workflow_id} not found",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Log deletion
            audit.log(
                event_type=AuditEventType.WORKFLOW_DELETED,
                action=f"Deleted workflow: {workflow_name}",
                request=request,
                user_id=str(current_user.id),
                resource_type="workflow",
                resource_id=workflow_id
            )
            
            return ResponseBuilder.success(
                data={"message": "Workflow deleted successfully"},
                request_id=getattr(request.state, "request_id", None),
                duration_ms=timer.duration_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}", exc_info=True)
            return ResponseBuilder.error(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to delete workflow",
                request_id=getattr(request.state, "request_id", None)
            )
