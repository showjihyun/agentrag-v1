"""API endpoints for workflow templates."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.workflow_template_service import WorkflowTemplateService
from backend.models.agent_builder import WorkflowResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/templates", tags=["workflow-templates"])


class TemplateResponse(BaseModel):
    """Schema for template response."""
    id: str
    name: str
    description: str
    category: str
    blocks: List[dict]
    edges: List[dict]
    variables: List[dict]
    metadata: dict
    created_at: str
    updated_at: str


class TemplateListResponse(BaseModel):
    """Schema for template list response."""
    templates: List[TemplateResponse]
    total: int


class CreateFromTemplateRequest(BaseModel):
    """Schema for creating workflow from template."""
    workflow_name: Optional[str] = None
    variable_values: Optional[dict] = None


class SaveAsTemplateRequest(BaseModel):
    """Schema for saving workflow as template."""
    template_name: str
    template_description: str
    category: str


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List available workflow templates.
    
    Templates can be filtered by category.
    """
    try:
        service = WorkflowTemplateService(db)
        templates = service.list_templates(category=category)
        
        template_responses = [
            TemplateResponse(**template.to_dict())
            for template in templates
        ]
        
        return TemplateListResponse(
            templates=template_responses,
            total=len(template_responses)
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates"
        )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific workflow template.
    """
    try:
        service = WorkflowTemplateService(db)
        template = service.get_template(template_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return TemplateResponse(**template.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get template"
        )


@router.post("/{template_id}/instantiate", response_model=WorkflowResponse)
async def create_workflow_from_template(
    template_id: str,
    request: CreateFromTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new workflow from a template.
    
    Optionally provide variable values to substitute in the template.
    """
    try:
        service = WorkflowTemplateService(db)
        
        workflow = service.create_workflow_from_template(
            template_id=template_id,
            user_id=current_user.id,
            workflow_name=request.workflow_name,
            variable_values=request.variable_values
        )
        
        logger.info(f"Created workflow from template '{template_id}': {workflow.id}")
        
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
        logger.error(f"Error creating workflow from template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow from template"
        )


@router.post("/from-workflow/{workflow_id}", response_model=TemplateResponse)
async def save_workflow_as_template(
    workflow_id: str,
    request: SaveAsTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Save an existing workflow as a template.
    
    This allows users to create reusable templates from their workflows.
    """
    try:
        from uuid import UUID
        
        service = WorkflowTemplateService(db)
        
        template = service.save_workflow_as_template(
            workflow_id=UUID(workflow_id),
            template_name=request.template_name,
            template_description=request.template_description,
            category=request.category
        )
        
        logger.info(f"Saved workflow {workflow_id} as template '{template.id}'")
        
        return TemplateResponse(**template.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error saving workflow as template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save workflow as template"
        )
