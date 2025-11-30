"""
Agent Versions API

Provides endpoints for agent version management:
- Version history
- Version comparison
- Rollback
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from backend.core.api_response import api_response
from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.agent_versioning import AgentVersioningService
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/api/agent-builder/agents",
    tags=["agent-builder-versions"],
)


# ============================================================================
# Request Models
# ============================================================================

class CreateVersionRequest(BaseModel):
    """Request to create a new version."""
    commit_message: str = Field("", description="Description of changes")


class RollbackRequest(BaseModel):
    """Request to rollback to a version."""
    target_version: int = Field(..., ge=1, description="Version number to rollback to")


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/{agent_id}/versions",
    summary="Get Version History",
    description="Get version history for an agent.",
)
async def get_version_history(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum versions to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get version history for an agent."""
    service = AgentVersioningService(db)
    
    try:
        versions = await service.get_version_history(agent_id, limit=limit)
        
        return api_response(
            data={
                "agent_id": agent_id,
                "versions": [v.to_dict() for v in versions],
                "total": len(versions),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{agent_id}/versions/{version_number}",
    summary="Get Specific Version",
    description="Get a specific version of an agent.",
)
async def get_version(
    agent_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific version."""
    service = AgentVersioningService(db)
    
    version = await service.get_version(agent_id, version_number)
    if not version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version_number} not found"
        )
    
    return api_response(data=version.to_dict())


@router.post(
    "/{agent_id}/versions",
    summary="Create Version",
    description="Create a new version snapshot of the agent.",
)
async def create_version(
    agent_id: str,
    request: CreateVersionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new version of an agent."""
    from backend.services.agent_builder.agent_service_refactored import AgentServiceRefactored
    
    # Get current agent
    agent_service = AgentServiceRefactored(db)
    agent = await agent_service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if str(agent.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Create version
    version_service = AgentVersioningService(db)
    version = await version_service.create_version(
        agent=agent,
        user_id=str(current_user.id),
        commit_message=request.commit_message,
        auto_version=False,
    )
    
    return api_response(
        data={
            "version": version.to_dict(),
            "message": f"Created version {version.version_number}",
        }
    )


@router.get(
    "/{agent_id}/versions/compare",
    summary="Compare Versions",
    description="Compare two versions and get diff.",
)
async def compare_versions(
    agent_id: str,
    from_version: int = Query(..., ge=1, description="Source version"),
    to_version: int = Query(..., ge=1, description="Target version"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare two versions."""
    service = AgentVersioningService(db)
    
    try:
        diff = await service.compare_versions(agent_id, from_version, to_version)
        return api_response(data=diff.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{agent_id}/versions/rollback",
    summary="Rollback to Version",
    description="Rollback agent to a previous version.",
)
async def rollback_version(
    agent_id: str,
    request: RollbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rollback to a previous version."""
    from backend.services.agent_builder.agent_service_refactored import AgentServiceRefactored
    
    # Verify ownership
    agent_service = AgentServiceRefactored(db)
    agent = await agent_service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if str(agent.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Perform rollback
    version_service = AgentVersioningService(db)
    
    try:
        result = await version_service.rollback(
            agent_id=agent_id,
            target_version=request.target_version,
            user_id=str(current_user.id),
        )
        
        return api_response(
            data={
                **result,
                "message": f"Prepared rollback to version {request.target_version}. Apply the configuration to complete.",
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{agent_id}/versions/{version_number}/publish",
    summary="Publish Version",
    description="Mark a version as published/stable.",
)
async def publish_version(
    agent_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a version."""
    service = AgentVersioningService(db)
    
    success = await service.publish_version(agent_id, version_number)
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return api_response(
        data={
            "agent_id": agent_id,
            "version_number": version_number,
            "is_published": True,
            "message": f"Version {version_number} published",
        }
    )
