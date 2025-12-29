"""Team Templates API endpoints for collaborative agent management."""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/team-templates",
    tags=["agent-builder-team-templates"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class TeamTemplateAgent(BaseModel):
    """Agent configuration within a team template."""
    id: str
    name: str
    role: str
    agent_id: Optional[str] = None


class TeamTemplateCreate(BaseModel):
    """Request model for creating a team template."""
    name: str
    description: str
    category: str
    orchestration_type: str
    agents: List[TeamTemplateAgent]
    tags: List[str] = []
    is_public: bool = False
    team_id: Optional[str] = None


class TeamTemplateUpdate(BaseModel):
    """Request model for updating a team template."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    orchestration_type: Optional[str] = None
    agents: Optional[List[TeamTemplateAgent]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class TeamTemplateResponse(BaseModel):
    """Response model for team template."""
    id: str
    name: str
    description: str
    category: str
    agents: List[TeamTemplateAgent]
    orchestration_type: str
    tags: List[str]
    is_public: bool
    is_favorite: bool
    created_by: dict
    created_at: datetime
    updated_at: datetime
    usage_count: int
    rating: float
    team_id: Optional[str] = None


class TeamTemplatesResponse(BaseModel):
    """Response model for team templates list."""
    templates: List[TeamTemplateResponse]
    total: int


class ToggleFavoriteRequest(BaseModel):
    """Request model for toggling favorite status."""
    is_favorite: bool


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "",
    response_model=TeamTemplatesResponse,
    summary="Get team templates",
    description="Get list of team templates with optional filtering.",
)
async def get_team_templates(
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get team templates with optional filtering.
    
    **Query Parameters:**
    - team_id: Filter by team ID
    - category: Filter by template category
    - search: Search in name and description
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    
    **Returns:**
    - List of team templates with metadata
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Getting team templates for user {current_user.id}")
        
        # Mock data for now - this would be implemented with a proper database
        mock_templates = [
            {
                "id": "template-1",
                "name": "고객 서비스 팀",
                "description": "고객 문의를 효율적으로 처리하는 에이전트 팀 구성",
                "category": "customer_service",
                "agents": [
                    {"id": "agent-1", "name": "문의 분류기", "role": "classifier"},
                    {"id": "agent-2", "name": "답변 생성기", "role": "responder"},
                    {"id": "agent-3", "name": "품질 검토자", "role": "reviewer"}
                ],
                "orchestration_type": "sequential",
                "tags": ["고객서비스", "자동화", "품질관리"],
                "is_public": True,
                "is_favorite": False,
                "created_by": {
                    "id": str(current_user.id),
                    "name": current_user.username or "User",
                    "avatar": None
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "usage_count": 15,
                "rating": 4.5,
                "team_id": team_id
            },
            {
                "id": "template-2",
                "name": "콘텐츠 제작 팀",
                "description": "다양한 콘텐츠를 생성하고 편집하는 전문 팀",
                "category": "content_creation",
                "agents": [
                    {"id": "agent-4", "name": "아이디어 생성기", "role": "ideator"},
                    {"id": "agent-5", "name": "콘텐츠 작성자", "role": "writer"},
                    {"id": "agent-6", "name": "편집자", "role": "editor"},
                    {"id": "agent-7", "name": "SEO 최적화기", "role": "optimizer"}
                ],
                "orchestration_type": "pipeline",
                "tags": ["콘텐츠", "창작", "SEO", "마케팅"],
                "is_public": True,
                "is_favorite": True,
                "created_by": {
                    "id": str(current_user.id),
                    "name": current_user.username or "User",
                    "avatar": None
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "usage_count": 23,
                "rating": 4.8,
                "team_id": team_id
            }
        ]
        
        # Apply filters
        filtered_templates = mock_templates
        
        if category:
            filtered_templates = [t for t in filtered_templates if t["category"] == category]
        
        if search:
            search_lower = search.lower()
            filtered_templates = [
                t for t in filtered_templates 
                if search_lower in t["name"].lower() or search_lower in t["description"].lower()
            ]
        
        # Apply pagination
        total = len(filtered_templates)
        paginated_templates = filtered_templates[skip:skip + limit]
        
        return TeamTemplatesResponse(
            templates=paginated_templates,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to get team templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team templates: {str(e)}"
        )


@router.post(
    "",
    response_model=TeamTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create team template",
    description="Create a new team template with agent configurations.",
)
async def create_team_template(
    template_data: TeamTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new team template.
    
    **Request Body:**
    - name: Template name (required)
    - description: Template description
    - category: Template category
    - orchestration_type: Orchestration type
    - agents: List of agent configurations
    - tags: List of tags
    - is_public: Whether template is public
    - team_id: Optional team ID
    
    **Returns:**
    - Created team template
    
    **Errors:**
    - 400: Invalid request data
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Creating team template for user {current_user.id}: {template_data.name}")
        
        # Mock creation - this would be implemented with proper database operations
        template_id = str(uuid.uuid4())
        
        created_template = TeamTemplateResponse(
            id=template_id,
            name=template_data.name,
            description=template_data.description,
            category=template_data.category,
            agents=template_data.agents,
            orchestration_type=template_data.orchestration_type,
            tags=template_data.tags,
            is_public=template_data.is_public,
            is_favorite=False,
            created_by={
                "id": str(current_user.id),
                "name": current_user.username or "User",
                "avatar": None
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            usage_count=0,
            rating=0.0,
            team_id=template_data.team_id
        )
        
        return created_template
        
    except Exception as e:
        logger.error(f"Failed to create team template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team template: {str(e)}"
        )


@router.put(
    "/{template_id}",
    response_model=TeamTemplateResponse,
    summary="Update team template",
    description="Update an existing team template.",
)
async def update_team_template(
    template_id: str,
    template_data: TeamTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing team template.
    
    **Path Parameters:**
    - template_id: ID of the template to update
    
    **Request Body:**
    - Fields to update (all optional)
    
    **Returns:**
    - Updated team template
    
    **Errors:**
    - 404: Template not found
    - 403: Permission denied
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Updating team template {template_id}")
        
        # Mock update - this would be implemented with proper database operations
        updated_template = TeamTemplateResponse(
            id=template_id,
            name=template_data.name or "Updated Template",
            description=template_data.description or "Updated description",
            category=template_data.category or "general",
            agents=template_data.agents or [],
            orchestration_type=template_data.orchestration_type or "sequential",
            tags=template_data.tags or [],
            is_public=template_data.is_public if template_data.is_public is not None else False,
            is_favorite=False,
            created_by={
                "id": str(current_user.id),
                "name": current_user.username or "User",
                "avatar": None
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            usage_count=0,
            rating=0.0,
            team_id=None
        )
        
        return updated_template
        
    except Exception as e:
        logger.error(f"Failed to update team template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team template: {str(e)}"
        )


@router.delete(
    "/{template_id}",
    summary="Delete team template",
    description="Delete a team template.",
)
async def delete_team_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a team template.
    
    **Path Parameters:**
    - template_id: ID of the template to delete
    
    **Returns:**
    - Success confirmation
    
    **Errors:**
    - 404: Template not found
    - 403: Permission denied
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Deleting team template {template_id}")
        
        # Mock deletion - this would be implemented with proper database operations
        return {"message": "Team template deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete team template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete team template: {str(e)}"
        )


@router.put(
    "/{template_id}/favorite",
    summary="Toggle template favorite status",
    description="Toggle favorite status for a team template.",
)
async def toggle_team_template_favorite(
    template_id: str,
    request: ToggleFavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Toggle favorite status for a team template.
    
    **Path Parameters:**
    - template_id: ID of the template
    
    **Request Body:**
    - is_favorite: New favorite status
    
    **Returns:**
    - Success confirmation
    
    **Errors:**
    - 404: Template not found
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Toggling favorite status for template {template_id}")
        
        # Mock toggle - this would be implemented with proper database operations
        return {"message": f"Template favorite status updated to {request.is_favorite}"}
        
    except Exception as e:
        logger.error(f"Failed to toggle template favorite: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle template favorite: {str(e)}"
        )