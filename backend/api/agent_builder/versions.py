"""API endpoints for workflow versioning."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.workflow_version_service import WorkflowVersionService
from backend.models.agent_builder import WorkflowResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/workflows/{workflow_id}/versions", tags=["workflow-versions"])


class VersionResponse(BaseModel):
    """Schema for version response."""
    id: str
    workflow_id: str
    version_number: int
    version_tag: Optional[str]
    snapshot: dict
    change_description: Optional[str]
    created_by: str
    created_at: str


class VersionListResponse(BaseModel):
    """Schema for version list response."""
    versions: List[VersionResponse]
    total: int


class CreateVersionRequest(BaseModel):
    """Schema for creating a version."""
    change_description: Optional[str] = None
    version_tag: Optional[str] = None


class RollbackRequest(BaseModel):
    """Schema for rollback request."""
    version_number: int


class CompareVersionsResponse(BaseModel):
    """Schema for version comparison response."""
    workflow_changes: dict
    blocks_added: List[str]
    blocks_removed: List[str]
    blocks_modified: List[str]
    edges_added: List[tuple]
    edges_removed: List[tuple]


@router.post("", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    workflow_id: str,
    request: CreateVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new version of a workflow.
    
    Captures the current state of the workflow as a version snapshot.
    """
    try:
        from uuid import UUID
        
        service = WorkflowVersionService(db)
        
        version = service.create_version(
            workflow_id=UUID(workflow_id),
            user_id=current_user.id,
            change_description=request.change_description,
            version_tag=request.version_tag
        )
        
        logger.info(f"Created version {version.version_number} for workflow {workflow_id}")
        
        return VersionResponse(**version.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create version"
        )


@router.get("", response_model=VersionListResponse)
async def list_versions(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all versions of a workflow.
    
    Returns versions in descending order (newest first).
    """
    try:
        from uuid import UUID
        
        service = WorkflowVersionService(db)
        versions = service.list_versions(UUID(workflow_id))
        
        version_responses = [
            VersionResponse(**version.to_dict())
            for version in versions
        ]
        
        return VersionListResponse(
            versions=version_responses,
            total=len(version_responses)
        )
        
    except Exception as e:
        logger.error(f"Error listing versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list versions"
        )


@router.get("/{version_number}", response_model=VersionResponse)
async def get_version(
    workflow_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific version of a workflow.
    """
    try:
        from uuid import UUID
        
        service = WorkflowVersionService(db)
        version = service.get_version(UUID(workflow_id), version_number)
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        return VersionResponse(**version.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get version"
        )


@router.post("/rollback", response_model=WorkflowResponse)
async def rollback_to_version(
    workflow_id: str,
    request: RollbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rollback workflow to a specific version.
    
    Creates a new version before rolling back, so the rollback can be undone.
    """
    try:
        from uuid import UUID
        
        service = WorkflowVersionService(db)
        
        workflow = service.rollback_to_version(
            workflow_id=UUID(workflow_id),
            version_number=request.version_number,
            user_id=current_user.id
        )
        
        logger.info(f"Rolled back workflow {workflow_id} to version {request.version_number}")
        
        return WorkflowResponse(
            id=str(workflow.id),
            user_id=str(workflow.user_id),
            name=workflow.name,
            description=workflow.description,
            graph_definition=workflow.graph_definition,
            is_public=workflow.is_public,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rolling back workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rollback workflow"
        )


@router.get("/compare", response_model=CompareVersionsResponse)
async def compare_versions(
    workflow_id: str,
    version1: int,
    version2: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compare two versions of a workflow.
    
    Returns the differences between the two versions.
    """
    try:
        from uuid import UUID
        
        service = WorkflowVersionService(db)
        
        differences = service.compare_versions(
            workflow_id=UUID(workflow_id),
            version1=version1,
            version2=version2
        )
        
        return CompareVersionsResponse(**differences)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error comparing versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare versions"
        )
