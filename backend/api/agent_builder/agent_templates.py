"""
Agent Templates API

Provides endpoints for browsing and using agent templates.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from backend.core.api_response import api_response
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.agent_templates import (
    AgentTemplateService,
    AgentCategory,
    AgentComplexity,
)


router = APIRouter(
    prefix="/api/agent-builder/templates",
    tags=["agent-builder-templates"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateFromTemplateRequest(BaseModel):
    """Request to create agent from template."""
    template_id: str = Field(..., description="Template ID")
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: Optional[str] = Field(None, description="Custom description")
    llm_provider: Optional[str] = Field(None, description="Override LLM provider")
    llm_model: Optional[str] = Field(None, description="Override LLM model")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=32000, description="Max tokens")
    tool_configs: Optional[dict] = Field(None, description="Tool-specific configurations")


class TemplateResponse(BaseModel):
    """Template response model."""
    id: str
    name: str
    description: str
    category: str
    complexity: str
    icon: str
    recommended_provider: str
    recommended_model: str
    system_prompt: str
    tools: List[dict]
    requires_knowledgebase: bool
    tags: List[str]
    use_cases: List[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "",
    summary="List All Templates",
    description="Get all available agent templates.",
)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    complexity: Optional[str] = Query(None, description="Filter by complexity"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """
    List all available agent templates.
    
    Supports filtering by category, complexity, and search query.
    """
    service = AgentTemplateService()
    
    if search:
        templates = service.search_templates(search)
    elif category:
        try:
            cat = AgentCategory(category)
            templates = service.get_templates_by_category(cat)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}"
            )
    elif complexity:
        try:
            comp = AgentComplexity(complexity)
            templates = service.get_templates_by_complexity(comp)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid complexity: {complexity}"
            )
    else:
        templates = service.get_all_templates()
    
    return api_response(
        data={
            "templates": templates,
            "total": len(templates),
        }
    )


@router.get(
    "/categories",
    summary="List Categories",
    description="Get all available template categories.",
)
async def list_categories():
    """Get all template categories."""
    service = AgentTemplateService()
    categories = service.get_categories()
    
    return api_response(data={"categories": categories})


@router.get(
    "/complexity-levels",
    summary="List Complexity Levels",
    description="Get all complexity levels with descriptions.",
)
async def list_complexity_levels():
    """Get all complexity levels."""
    service = AgentTemplateService()
    levels = service.get_complexity_levels()
    
    return api_response(data={"levels": levels})


@router.get(
    "/{template_id}",
    summary="Get Template",
    description="Get a specific template by ID.",
)
async def get_template(template_id: str):
    """Get template details by ID."""
    service = AgentTemplateService()
    template = service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_id}"
        )
    
    return api_response(data=template.to_dict())


@router.post(
    "/{template_id}/create",
    summary="Create Agent from Template",
    description="Create a new agent based on a template.",
)
async def create_from_template(
    template_id: str,
    request: CreateFromTemplateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new agent from a template.
    
    Allows customization of various template settings.
    """
    service = AgentTemplateService()
    
    # Verify template exists
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_id}"
        )
    
    # Build customizations
    customizations = {}
    if request.description:
        customizations["description"] = request.description
    if request.llm_provider:
        customizations["llm_provider"] = request.llm_provider
    if request.llm_model:
        customizations["llm_model"] = request.llm_model
    if request.system_prompt:
        customizations["system_prompt"] = request.system_prompt
    if request.temperature is not None:
        customizations["temperature"] = request.temperature
    if request.max_tokens is not None:
        customizations["max_tokens"] = request.max_tokens
    if request.tool_configs:
        customizations["tool_configs"] = request.tool_configs
    
    try:
        agent_config = service.create_agent_from_template(
            template_id=template_id,
            name=request.name,
            user_id=str(current_user.id),
            customizations=customizations,
        )
        
        return api_response(
            data={
                "agent_config": agent_config,
                "message": f"Agent configuration created from template '{template.name}'",
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get(
    "/{template_id}/preview",
    summary="Preview Template",
    description="Preview what an agent would look like with this template.",
)
async def preview_template(
    template_id: str,
    name: str = Query("My Agent", description="Agent name for preview"),
):
    """Preview agent configuration from template."""
    service = AgentTemplateService()
    
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_id}"
        )
    
    # Generate preview config (without user_id)
    preview = {
        "name": name,
        "description": template.description,
        "template": template.name,
        "llm_provider": template.recommended_provider,
        "llm_model": template.recommended_model,
        "system_prompt": template.system_prompt[:500] + "..." if len(template.system_prompt) > 500 else template.system_prompt,
        "tools": [
            {"name": t.name, "description": t.description, "required": t.required}
            for t in template.tools
        ],
        "settings": {
            "temperature": template.temperature,
            "max_tokens": template.max_tokens,
            "enable_memory": template.enable_memory,
            "enable_streaming": template.enable_streaming,
        },
        "requires_knowledgebase": template.requires_knowledgebase,
        "knowledgebase_description": template.knowledgebase_description,
    }
    
    return api_response(data=preview)
