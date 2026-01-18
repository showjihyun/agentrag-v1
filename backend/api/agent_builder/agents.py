"""Agent Builder API endpoints for agent management."""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
# DDD Architecture - CQRS Pattern
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.application.commands import (
    CreateAgentCommand,
    UpdateAgentCommand,
)
from backend.services.agent_builder.application.queries import (
    GetAgentQuery,
    ListAgentsQuery,
)
from backend.services.agent_builder.shared.errors import (
    NotFoundError,
    ValidationError,
)
from backend.services.agent_builder.ai_recommendation_service import AIRecommendationService
from backend.exceptions.agent_builder import (
    AgentNotFoundException,
    AgentValidationException,
    AgentToolNotFoundException,
    AgentKnowledgebaseNotFoundException,
    AgentPermissionException
)
from backend.models.agent_builder import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    AgentExportResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/agents",
    tags=["agent-builder-agents"],
)


# ============================================================================
# Response Models
# ============================================================================

class OrchestrationRecommendationResponse(BaseModel):
    """Orchestration-based agent recommendation response."""
    orchestration_type: str
    recommended_agents: List[AgentResponse]
    compatibility_score: float
    reasoning: str
    alternative_types: List[str]


class PersonalizedRecommendationResponse(BaseModel):
    """Personalized agent recommendation response."""
    recommendations: List[dict]
    total_count: int
    orchestration_type: Optional[str] = None


class SimilarAgentsResponse(BaseModel):
    """Similar agents response."""
    similar_agents: List[dict]
    total_count: int


class TrendingAgentsResponse(BaseModel):
    """Trending agents response."""
    trending_agents: List[dict]
    time_period: str
    total_count: int


class WorkflowRecommendationResponse(BaseModel):
    """Workflow recommendation response."""
    recommended_workflows: List[dict]
    agent_ids: List[str]
    total_count: int


class AgentExecuteRequest(BaseModel):
    """Agent execution request."""
    input: str
    context: Optional[dict] = None


# ============================================================================
# SPECIFIC ROUTES (must come before /{agent_id} to avoid path conflicts)
# ============================================================================

@router.get(
    "/trending",
    response_model=TrendingAgentsResponse,
    summary="Get trending agents",
    description="Get trending agents based on usage patterns and popularity.",
)
async def get_trending_agents(
    time_period: str = Query("7d", description="Time period for trending analysis (1d, 7d, 30d)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of trending agents to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get trending agents - returns empty list for now."""
    return TrendingAgentsResponse(
        trending_agents=[],
        time_period=time_period,
        total_count=0
    )
    limit: int = Query(10, ge=1, le=50, description="Maximum number of trending agents"),
@router.get(
    "/personalized-recommendations",
    response_model=PersonalizedRecommendationResponse,
    summary="Get personalized agent recommendations",
    description="Get AI-powered personalized agent recommendations based on user behavior and preferences.",
)
async def get_personalized_recommendations(
    orchestration_type: Optional[str] = Query(None, description="Filter by orchestration type"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get personalized recommendations - returns empty list for now."""
    return PersonalizedRecommendationResponse(
        recommendations=[],
        total_count=0
    )


@router.get(
    "/templates",
    summary="Get agent templates",
    description="Get available agent templates filtered by orchestration type and other criteria.",
)
async def get_agent_templates(
    orchestration_type: Optional[str] = Query(None, description="Filter by orchestration type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    complexity: Optional[str] = Query(None, description="Filter by complexity level"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get agent templates - returns empty list for now."""
    return {"templates": [], "total_count": 0}


@router.get(
    "/search-users",
    summary="Search users for sharing",
    description="Search users by name or email for agent sharing.",
)
async def search_users(
    q: str = Query(..., min_length=3, description="Search query (name or email)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search users for agent sharing - returns empty list for now."""
    return {"users": [], "total_count": 0}
@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Create a new custom agent with specified tools, prompts, and configuration.",
)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new agent using DDD CQRS Command pattern."""
    try:
        logger.info(f"Creating agent for user {current_user.id}: {agent_data.name}")
        
        facade = AgentBuilderFacade(db)
        
        # Create command
        command = CreateAgentCommand(
            user_id=str(current_user.id),
            name=agent_data.name,
            description=agent_data.description,
            agent_type=agent_data.agent_type,
            template_id=agent_data.template_id,
            llm_provider=agent_data.llm_provider,
            llm_model=agent_data.llm_model,
            prompt_template_id=agent_data.prompt_template_id,
            configuration=agent_data.configuration,
            tool_ids=agent_data.tool_ids,
            knowledgebase_ids=agent_data.knowledgebase_ids,
            context_items=[item.dict() for item in agent_data.context_items] if agent_data.context_items else [],
            mcp_servers=[server.dict() for server in agent_data.mcp_servers] if agent_data.mcp_servers else [],
        )
        
        # Execute command
        aggregate = facade.agent_commands.handle_create(command)
        
        logger.info(f"Agent created successfully: {aggregate.id}")
        
        # Get the agent entity from the aggregate
        agent = aggregate.agent
        
        # Convert AgentAggregate to AgentResponse
        configuration = agent.config.to_dict() if agent.config else {}
        
        return AgentResponse(
            id=str(agent.id),
            user_id=str(agent.user_id),
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type.value if hasattr(agent.agent_type, 'value') else str(agent.agent_type),
            template_id=agent.template_id,
            llm_provider=agent.llm_provider,
            llm_model=agent.llm_model,
            prompt_template_id=None,  # Not directly available in domain model
            configuration=configuration,
            context_items=configuration.get("context_items", []),
            mcp_servers=configuration.get("mcp_servers", []),
            is_public=agent.is_public,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            deleted_at=agent.deleted_at,
            tools=[
                {
                    "tool_id": tool.tool_id,
                    "order": tool.order,
                    "configuration": tool.configuration or {}
                }
                for tool in agent.tools
            ],
            knowledgebases=[
                {
                    "knowledgebase_id": kb.knowledgebase_id,
                    "order": kb.priority if hasattr(kb, 'priority') else 0
                }
                for kb in agent.knowledgebases
            ],
            version_count=0
        )
        
    except ValidationError as e:
        logger.warning(f"Agent validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        logger.warning(f"Resource not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List user's agents",
    description="List all agents owned by the current user with pagination and filtering.",
)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's agents with pagination using DDD CQRS Query pattern."""
    try:
        logger.info(f"Listing agents for user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        
        # Create query
        query = ListAgentsQuery(
            user_id=str(current_user.id),
            limit=limit,
            offset=skip
        )
        
        # Execute query
        agent_dicts = facade.agent_queries.handle_list(query)
        
        # Convert to AgentResponse objects
        from datetime import datetime
        agents = []
        for agent_dict in agent_dicts:
            # Parse datetime strings
            created_at = datetime.fromisoformat(agent_dict["created_at"]) if agent_dict.get("created_at") else None
            updated_at = datetime.fromisoformat(agent_dict["updated_at"]) if agent_dict.get("updated_at") else None
            
            configuration = agent_dict.get("configuration", {})
            
            agents.append(AgentResponse(
                id=agent_dict["id"],
                user_id=agent_dict["user_id"],
                name=agent_dict["name"],
                description=agent_dict.get("description"),
                agent_type=agent_dict["agent_type"],
                template_id=agent_dict.get("template_id"),
                llm_provider=agent_dict.get("llm_provider", "openai"),
                llm_model=agent_dict.get("llm_model", "gpt-3.5-turbo"),
                prompt_template_id=None,
                configuration=configuration,
                context_items=configuration.get("context_items", []),
                mcp_servers=configuration.get("mcp_servers", []),
                is_public=agent_dict.get("is_public", False),
                created_at=created_at,
                updated_at=updated_at,
                deleted_at=None,
                tools=[
                    {
                        "tool_id": tool["tool_id"],
                        "order": tool.get("order", 0),
                        "configuration": tool.get("configuration", {})
                    }
                    for tool in agent_dict.get("tools", [])
                ],
                knowledgebases=[
                    {
                        "knowledgebase_id": kb["knowledgebase_id"],
                        "order": kb.get("priority", 0)
                    }
                    for kb in agent_dict.get("knowledgebases", [])
                ],
                version_count=0
            ))
        
        return AgentListResponse(
            agents=agents,
            total=len(agents),
            limit=limit,
            offset=skip
        )
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents"
        )


# ============================================================================
# AGENT ID ROUTES (must come after specific routes)
# ============================================================================

@router.get(
    "/{agent_id}/similar",
    response_model=SimilarAgentsResponse,
    summary="Get similar agents",
    description="Find agents similar to the specified agent based on characteristics and usage patterns.",
)
async def get_similar_agents(
    agent_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of similar agents"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get agents similar to the specified agent - returns empty list for now."""
    return SimilarAgentsResponse(
        similar_agents=[],
        total_count=0
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent by ID",
    description="Retrieve a specific agent by ID. Checks user permissions.",
)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get agent by ID using DDD CQRS Query pattern."""
    try:
        logger.info(f"Fetching agent {agent_id} for user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        
        # Create query
        query = GetAgentQuery(agent_id=agent_id)
        
        # Execute query
        agent_dict = facade.agent_queries.handle_get(query)
        
        if not agent_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Check permissions (owner or has read permission)
        if str(agent_dict["user_id"]) != str(current_user.id) and not agent_dict.get("is_public", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this agent"
            )
        
        # Convert query result to AgentResponse
        configuration = agent_dict.get("configuration", {})
        
        # Parse datetime strings
        from datetime import datetime
        created_at = datetime.fromisoformat(agent_dict["created_at"]) if agent_dict.get("created_at") else None
        updated_at = datetime.fromisoformat(agent_dict["updated_at"]) if agent_dict.get("updated_at") else None
        
        return AgentResponse(
            id=agent_dict["id"],
            user_id=agent_dict["user_id"],
            name=agent_dict["name"],
            description=agent_dict.get("description"),
            agent_type=agent_dict["agent_type"],
            template_id=agent_dict.get("template_id"),
            llm_provider=agent_dict.get("llm_provider", "openai"),
            llm_model=agent_dict.get("llm_model", "gpt-3.5-turbo"),
            prompt_template_id=None,  # Not in query result
            configuration=configuration,
            context_items=configuration.get("context_items", []),
            mcp_servers=configuration.get("mcp_servers", []),
            is_public=agent_dict.get("is_public", False),
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=None,
            tools=[
                {
                    "tool_id": tool["tool_id"],
                    "order": tool.get("order", 0),
                    "configuration": tool.get("configuration", {})
                }
                for tool in agent_dict.get("tools", [])
            ],
            knowledgebases=[
                {
                    "knowledgebase_id": kb["knowledgebase_id"],
                    "order": kb.get("priority", 0)
                }
                for kb in agent_dict.get("knowledgebases", [])
            ],
            version_count=0
        )
        
    except ValueError as e:
        logger.warning(f"Invalid agent ID format: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent ID format: {agent_id}"
        )
    except NotFoundError as e:
        logger.warning(f"Agent not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update agent",
    description="Update an existing agent. Only the owner can update the agent.",
)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update agent using DDD CQRS Command pattern."""
    try:
        logger.info(f"Updating agent {agent_id} for user {current_user.id}")
        
        facade = AgentBuilderFacade(db)
        
        # First check if agent exists and user has permission
        query = GetAgentQuery(agent_id=agent_id)
        agent_dict = facade.agent_queries.handle_get(query)
        
        if str(agent_dict["user_id"]) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this agent"
            )
        
        # Create update command
        command = UpdateAgentCommand(
            agent_id=agent_id,
            name=agent_data.name,
            description=agent_data.description,
            llm_provider=agent_data.llm_provider,
            llm_model=agent_data.llm_model,
            prompt_template_id=agent_data.prompt_template_id,
            configuration=agent_data.configuration,
            tool_ids=agent_data.tool_ids,
            knowledgebase_ids=agent_data.knowledgebase_ids,
            context_items=[item.dict() for item in agent_data.context_items] if agent_data.context_items else None,
            mcp_servers=[server.dict() for server in agent_data.mcp_servers] if agent_data.mcp_servers else None,
            is_public=agent_data.is_public,
        )
        
        # Execute command
        updated_aggregate = facade.agent_commands.handle_update(command)
        
        logger.info(f"Agent updated successfully: {agent_id}")
        
        # Get the agent entity from the aggregate
        updated_agent = updated_aggregate.agent
        
        # Convert to response
        configuration = updated_agent.config.to_dict() if updated_agent.config else {}
        
        return AgentResponse(
            id=str(updated_agent.id),
            user_id=str(updated_agent.user_id),
            name=updated_agent.name,
            description=updated_agent.description,
            agent_type=updated_agent.agent_type.value if hasattr(updated_agent.agent_type, 'value') else str(updated_agent.agent_type),
            template_id=updated_agent.template_id,
            llm_provider=updated_agent.llm_provider,
            llm_model=updated_agent.llm_model,
            prompt_template_id=None,  # Not directly available in domain model
            configuration=configuration,
            context_items=configuration.get("context_items", []),
            mcp_servers=configuration.get("mcp_servers", []),
            is_public=updated_agent.is_public,
            created_at=updated_agent.created_at,
            updated_at=updated_agent.updated_at,
            deleted_at=updated_agent.deleted_at,
            tools=[
                {
                    "tool_id": tool.tool_id,
                    "order": tool.order,
                    "configuration": tool.configuration or {}
                }
                for tool in updated_agent.tools
            ],
            knowledgebases=[
                {
                    "knowledgebase_id": kb.knowledgebase_id,
                    "order": kb.priority if hasattr(kb, 'priority') else 0
                }
                for kb in updated_agent.knowledgebases
            ],
            version_count=0
        )
        
    except ValueError as e:
        logger.warning(f"Invalid agent ID format: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent ID format: {agent_id}"
        )
    except NotFoundError as e:
        logger.warning(f"Agent not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Agent validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# AGENT TOOLS MANAGEMENT
# ============================================================================

class ToolItem(BaseModel):
    """Tool item for updating agent tools."""
    tool_id: str
    configuration: dict = Field(default_factory=dict)
    order: int = 0


class UpdateToolsRequest(BaseModel):
    """Request model for updating agent tools."""
    tools: List[ToolItem] = Field(default_factory=list, description="List of tools to attach to the agent")


@router.put(
    "/{agent_id}/tools",
    response_model=AgentResponse,
    summary="Update agent tools",
    description="Update the tools attached to an agent.",
)
async def update_agent_tools(
    agent_id: str,
    request: UpdateToolsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update agent tools using DDD aggregate pattern."""
    try:
        from uuid import UUID
        
        logger.info(f"Updating tools for agent {agent_id}")
        
        # Get the agent
        facade = AgentBuilderFacade(db)
        query = GetAgentQuery(agent_id=agent_id)
        agent_dict = facade.agent_queries.handle_get(query)
        
        if not agent_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Check permissions
        if str(agent_dict["user_id"]) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this agent"
            )
        
        # Get the aggregate
        from backend.services.agent_builder.infrastructure.persistence.agent_repository import AgentRepositoryImpl
        repository = AgentRepositoryImpl(db)
        aggregate = repository.find_by_id(UUID(agent_id))
        
        if not aggregate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Get current tool IDs
        current_tool_ids = {tool.tool_id for tool in aggregate.agent.tools}
        new_tool_ids = {tool.tool_id for tool in request.tools}
        
        # Detach removed tools
        for tool_id in current_tool_ids - new_tool_ids:
            aggregate.detach_tool(tool_id, UUID(str(current_user.id)))
        
        # Attach new tools
        for tool_item in request.tools:
            if tool_item.tool_id not in current_tool_ids:
                aggregate.attach_tool(
                    tool_item.tool_id, 
                    UUID(str(current_user.id)), 
                    configuration=tool_item.configuration,
                    order=tool_item.order
                )
        
        # Save the aggregate
        repository.save(aggregate)
        
        # Return updated agent
        agent = aggregate.agent
        configuration = agent.config.to_dict() if agent.config else {}
        
        return AgentResponse(
            id=str(agent.id),
            user_id=str(agent.user_id),
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type.value if hasattr(agent.agent_type, 'value') else str(agent.agent_type),
            template_id=agent.template_id,
            llm_provider=agent.llm_provider,
            llm_model=agent.llm_model,
            prompt_template_id=None,
            configuration=configuration,
            context_items=configuration.get("context_items", []),
            mcp_servers=configuration.get("mcp_servers", []),
            is_public=agent.is_public,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            deleted_at=agent.deleted_at,
            tools=[
                {
                    "tool_id": tool.tool_id,
                    "order": tool.order,
                    "configuration": tool.configuration or {}
                }
                for tool in agent.tools
            ],
            knowledgebases=[
                {
                    "knowledgebase_id": kb.knowledgebase_id,
                    "order": kb.priority if hasattr(kb, 'priority') else 0
                }
                for kb in agent.knowledgebases
            ],
            version_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent tools: {str(e)}"
        )


# ============================================================================
# AGENT EXECUTION
# ============================================================================

class AgentExecuteRequest(BaseModel):
    """Request model for agent execution."""
    input: Optional[str] = Field(None, description="Input text for the agent")
    input_data: Optional[dict] = Field(None, description="Input data for the agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    workflow_id: Optional[str] = Field(None, description="Workflow ID if part of a workflow")
    
    def get_input_data(self) -> dict:
        """Get input data from either field."""
        if self.input_data:
            return self.input_data
        elif self.input:
            # If input is a string, wrap it in a dict
            return {"input": self.input}
        else:
            return {}


class AgentExecuteResponse(BaseModel):
    """Response model for agent execution."""
    output: dict = Field(..., description="Agent execution output")
    execution_id: Optional[str] = Field(None, description="Execution ID for tracking")
    status: str = Field(..., description="Execution status")


@router.post(
    "/{agent_id}/execute",
    response_model=AgentExecuteResponse,
    summary="Execute agent",
    description="Execute an agent with the provided input data.",
)
async def execute_agent(
    agent_id: str,
    request: AgentExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute an agent using the agent plugin manager."""
    try:
        from backend.services.plugins.agents.agent_plugin_manager import AgentPluginManager
        
        logger.info(f"Executing agent {agent_id} for user {current_user.id}")
        
        # Get the agent plugin manager
        manager = AgentPluginManager(db)
        
        # Execute the agent
        result = await manager.execute_custom_agent(
            agent_id=agent_id,
            input_data=request.get_input_data(),
            user_id=str(current_user.id),
            session_id=request.session_id,
            workflow_id=request.workflow_id
        )
        
        return AgentExecuteResponse(
            output=result.get("output", {}),
            execution_id=result.get("execution_id"),
            status=result.get("status", "completed")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute agent: {str(e)}"
        )
