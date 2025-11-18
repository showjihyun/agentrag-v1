"""Agent Builder API endpoints for agent management."""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.agent_service_refactored import AgentServiceRefactored
from backend.core.dependencies import get_agent_service
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


# Pagination parameters
class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    skip: int = Query(0, ge=0, description="Number of records to skip")
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return")


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Create a new custom agent with specified tools, prompts, and configuration. Requires authentication.",
)
def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    agent_service: AgentServiceRefactored = Depends(get_agent_service),
):
    """
    Create a new agent with Refactored Service (Repository Pattern, Transaction Management).
    
    **Requirements:** 1.1, 1.4
    
    **Request Body:**
    - name: Agent name (required)
    - description: Agent description
    - agent_type: Type of agent (custom, template_based)
    - template_id: Template ID if using template
    - llm_provider: LLM provider (ollama, openai, claude)
    - llm_model: LLM model name
    - prompt_template_id: Prompt template ID
    - configuration: Agent-specific configuration
    - tool_ids: List of tool IDs to attach
    - knowledgebase_ids: List of knowledgebase IDs to attach
    
    **Returns:**
    - Agent object with ID and metadata
    
    **Errors:**
    - 400: Invalid request data or validation failed
    - 404: Tool or knowledgebase not found
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Creating agent for user {current_user.id}: {agent_data.name}")
        
        agent = agent_service.create_agent(
            user_id=str(current_user.id),
            agent_data=agent_data
        )
        
        logger.info(f"Agent created successfully: {agent.id}")
        
        # Convert Agent ORM object to AgentResponse
        return AgentResponse(
            id=str(agent.id),
            user_id=str(agent.user_id),
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type,
            template_id=str(agent.template_id) if agent.template_id else None,
            llm_provider=agent.llm_provider,
            llm_model=agent.llm_model,
            prompt_template_id=str(agent.prompt_template_id) if agent.prompt_template_id else None,
            configuration=agent.configuration or {},
            is_public=agent.is_public,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            deleted_at=agent.deleted_at,
            tools=[
                {
                    "tool_id": str(at.tool_id),
                    "order": at.order,
                    "configuration": at.configuration or {}
                }
                for at in agent.tools
            ] if agent.tools else [],
            knowledgebases=[
                {
                    "knowledgebase_id": str(ak.knowledgebase_id),
                    "order": ak.order
                }
                for ak in agent.knowledgebases
            ] if agent.knowledgebases else [],
            version_count=0
        )
        
    except AgentValidationException as e:
        logger.warning(f"Agent validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    except AgentToolNotFoundException as e:
        logger.warning(f"Tool not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict()
        )
    except AgentKnowledgebaseNotFoundException as e:
        logger.warning(f"Knowledgebase not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
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
    agent_service: AgentServiceRefactored = Depends(get_agent_service),
):
    """
    Get agent by ID.
    
    **Requirements:** 1.1, 1.4
    
    **Path Parameters:**
    - agent_id: Agent UUID
    
    **Returns:**
    - Agent object with full details
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access)
    - 404: Agent not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Fetching agent {agent_id} for user {current_user.id}")
        
        agent = await agent_service.get_agent(agent_id)
        
        # Check permissions (owner or has read permission)
        # Convert both to UUID for comparison
        if str(agent.user_id) != str(current_user.id) and not agent.is_public:
            raise AgentPermissionException(agent_id, str(current_user.id), "read")
        
        # Convert Agent ORM object to AgentResponse
        return AgentResponse(
            id=str(agent.id),
            user_id=str(agent.user_id),
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type,
            template_id=str(agent.template_id) if agent.template_id else None,
            llm_provider=agent.llm_provider,
            llm_model=agent.llm_model,
            prompt_template_id=str(agent.prompt_template_id) if agent.prompt_template_id else None,
            configuration=agent.configuration or {},
            is_public=agent.is_public,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            deleted_at=agent.deleted_at,
            tools=[
                {
                    "tool_id": str(at.tool_id),
                    "order": at.order,
                    "configuration": at.configuration or {}
                }
                for at in agent.tools
            ] if agent.tools else [],
            knowledgebases=[
                {
                    "knowledgebase_id": str(ak.knowledgebase_id),
                    "order": ak.order
                }
                for ak in agent.knowledgebases
            ] if agent.knowledgebases else [],
            version_count=0
        )
        
    except AgentNotFoundException as e:
        logger.warning(f"Agent not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict()
        )
    except AgentPermissionException as e:
        logger.warning(f"Permission denied: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.to_dict()
        )
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
    description="Update an existing agent. Requires ownership.",
)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    agent_service: AgentServiceRefactored = Depends(get_agent_service),
):
    """
    Update agent.
    
    **Requirements:** 1.1, 1.4
    
    **Path Parameters:**
    - agent_id: Agent UUID
    
    **Request Body:**
    - Fields to update (all optional)
    
    **Returns:**
    - Updated agent object
    
    **Errors:**
    - 400: Invalid request data
    - 401: Unauthorized
    - 403: Forbidden (not owner)
    - 404: Agent not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Updating agent {agent_id} for user {current_user.id}")
        
        # Check ownership
        existing_agent = await agent_service.get_agent(agent_id)
        if not existing_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        if str(existing_agent.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this agent"
            )
        
        # Update agent
        updated_agent = await agent_service.update_agent(
            agent_id=agent_id,
            agent_data=agent_data,
            user_id=str(current_user.id)
        )
        
        logger.info(f"Agent updated successfully: {agent_id}")
        return updated_agent
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid agent data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent",
    description="Soft delete an agent. Requires ownership.",
)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft delete agent.
    
    **Requirements:** 1.4, 6.4
    
    **Path Parameters:**
    - agent_id: Agent UUID
    
    **Returns:**
    - 204 No Content on success
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (not owner)
    - 404: Agent not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Deleting agent {agent_id} for user {current_user.id}")
        
        agent_service = AgentServiceRefactored(db)
        
        # Check ownership
        existing_agent = await agent_service.get_agent(agent_id)
        if not existing_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        if str(existing_agent.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this agent"
            )
        
        # Soft delete
        await agent_service.delete_agent(agent_id)
        
        logger.info(f"Agent deleted successfully: {agent_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
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
    """
    List user's agents with pagination.
    
    **Requirements:** 1.1, 9.3
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 50, max: 100)
    - agent_type: Filter by agent type (custom, template_based)
    - search: Search in name and description
    
    **Returns:**
    - List of agents with pagination metadata
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Listing agents for user {current_user.id}")
        
        agent_service = AgentServiceRefactored(db)
        
        # Get agents with proper parameters
        agents = agent_service.list_agents(
            user_id=str(current_user.id),
            agent_type=agent_type,
            limit=limit,
            offset=skip
        )
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            agents = [
                a for a in agents
                if search_lower in a.name.lower() or
                (a.description and search_lower in a.description.lower())
            ]
        
        total = len(agents)
        
        # Convert Agent ORM objects to AgentResponse objects
        agent_responses = []
        for agent in agents:
            agent_responses.append(AgentResponse(
                id=str(agent.id),
                user_id=str(agent.user_id),
                name=agent.name,
                description=agent.description,
                agent_type=agent.agent_type,
                template_id=str(agent.template_id) if agent.template_id else None,
                llm_provider=agent.llm_provider,
                llm_model=agent.llm_model,
                prompt_template_id=str(agent.prompt_template_id) if agent.prompt_template_id else None,
                configuration=agent.configuration or {},
                is_public=agent.is_public,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
                deleted_at=agent.deleted_at,
                tools=[
                    {
                        "tool_id": str(at.tool_id),
                        "order": at.order,
                        "configuration": at.configuration or {}
                    }
                    for at in agent.tools
                ] if agent.tools else [],
                knowledgebases=[
                    {
                        "knowledgebase_id": str(ak.knowledgebase_id),
                        "order": ak.order
                    }
                    for ak in agent.knowledgebases
                ] if agent.knowledgebases else [],
                version_count=0
            ))
        
        return AgentListResponse(
            agents=agent_responses,
            total=total,
            limit=limit,
            offset=skip
        )
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents"
        )


@router.post(
    "/{agent_id}/clone",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone agent",
    description="Create a copy of an existing agent with a new ID.",
)
async def clone_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clone an agent.
    
    **Requirements:** 6.4, 9.3
    
    **Path Parameters:**
    - agent_id: Agent UUID to clone
    
    **Returns:**
    - New agent object with cloned configuration
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access source agent)
    - 404: Agent not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Cloning agent {agent_id} for user {current_user.id}")
        
        agent_service = AgentServiceRefactored(db)
        
        # Check if agent exists and user has access
        source_agent = await agent_service.get_agent(agent_id)
        if not source_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Check permissions (owner or public)
        if str(source_agent.user_id) != str(current_user.id) and not source_agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to clone this agent"
            )
        
        # Clone agent
        cloned_agent = await agent_service.clone_agent(
            agent_id=agent_id,
            user_id=str(current_user.id)
        )
        
        logger.info(f"Agent cloned successfully: {cloned_agent.id}")
        return cloned_agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clone agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone agent"
        )


@router.get(
    "/{agent_id}/export",
    response_model=AgentExportResponse,
    summary="Export agent as JSON",
    description="Export agent configuration including version history as JSON.",
)
async def export_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export agent as JSON.
    
    **Requirements:** 6.5
    
    **Path Parameters:**
    - agent_id: Agent UUID to export
    
    **Returns:**
    - Complete agent configuration as JSON
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access)
    - 404: Agent not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Exporting agent {agent_id} for user {current_user.id}")
        
        agent_service = AgentServiceRefactored(db)
        
        # Check if agent exists and user has access
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Check permissions
        if str(agent.user_id) != str(current_user.id) and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to export this agent"
            )
        
        # Export agent
        export_data = agent_service.export_agent(agent_id)
        
        logger.info(f"Agent exported successfully: {agent_id}")
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export agent"
        )


@router.post(
    "/import",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import agent from JSON",
    description="Import an agent configuration from JSON file.",
)
async def import_agent(
    file: UploadFile = File(..., description="JSON file containing agent configuration"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Import agent from JSON.
    
    **Requirements:** 6.5
    
    **Request:**
    - file: JSON file with agent configuration
    
    **Returns:**
    - Imported agent object
    
    **Errors:**
    - 400: Invalid JSON or agent data
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Importing agent for user {current_user.id}")
        
        # Read and parse JSON
        content = await file.read()
        try:
            import json
            agent_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON: {str(e)}"
            )
        
        agent_service = AgentServiceRefactored(db)
        
        # Import agent
        imported_agent = agent_service.import_agent(
            user_id=str(current_user.id),
            agent_data=agent_data
        )
        
        logger.info(f"Agent imported successfully: {imported_agent.id}")
        return imported_agent
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid agent data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to import agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import agent"
        )



class AgentExecuteRequest(BaseModel):
    """Agent execution request."""
    input: str
    context: Optional[dict] = None


@router.post(
    "/{agent_id}/execute",
    summary="Execute agent",
    description="Execute an agent with given input.",
)
async def execute_agent(
    agent_id: str,
    request: AgentExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute agent with input.
    
    **Request:**
    - input: Input text for the agent
    - context: Optional context data
    
    **Returns:**
    - Execution result with output
    
    **Errors:**
    - 404: Agent not found
    - 403: Permission denied
    - 500: Execution failed
    """
    try:
        logger.info(f"Executing agent {agent_id} for user {current_user.id}")
        
        agent_service = AgentServiceRefactored(db)
        
        # Get agent and verify permissions
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if str(agent.user_id) != str(current_user.id) and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to execute this agent"
            )
        
        # Import executor
        from backend.services.agent_builder.agent_executor import AgentExecutor
        
        # Execute agent with actual executor
        executor = AgentExecutor(db)
        execution = await executor.execute_agent(
            agent_id=agent_id,
            user_id=str(current_user.id),
            input_data={"input": request.input, **(request.context or {})},
            session_id=None,
            variables=request.context
        )
        
        # Return execution result
        result = {
            "success": execution.status == "completed",
            "execution_id": str(execution.id),
            "output": execution.output_data.get("output", "") if execution.output_data else "",
            "status": execution.status,
            "error": execution.error_message,
            "result": {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "input": request.input,
                "timestamp": execution.started_at.isoformat(),
                "duration_ms": execution.duration_ms,
                "tokens_used": execution.output_data.get("tokens_used", 0) if execution.output_data else 0
            }
        }
        
        logger.info(f"Agent executed successfully: {execution.id}")
        return result
        
    except HTTPException:
        raise
    except AgentNotFoundException as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AgentPermissionException as e:
        logger.warning(f"Permission denied for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to execute agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute agent: {str(e)}"
        )



class AgentStatsResponse(BaseModel):
    """Agent statistics response."""
    agent_id: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    avg_duration_ms: Optional[float]
    last_run_at: Optional[datetime]


@router.get(
    "/{agent_id}/statistics",
    response_model=AgentStatsResponse,
    summary="Get agent statistics",
    description="Get execution statistics for an agent.",
)
async def get_agent_stats(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get agent execution statistics.
    
    **Returns:**
    - Execution statistics including runs, success rate, and average duration
    
    **Errors:**
    - 404: Agent not found
    - 403: Permission denied
    """
    try:
        logger.info(f"Getting stats for agent {agent_id}")
        
        agent_service = AgentServiceRefactored(db)
        
        # Get agent and verify permissions
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if str(agent.user_id) != str(current_user.id) and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this agent's statistics"
            )
        
        # Get execution statistics from agent_executions table
        from backend.db.models.agent_builder import AgentExecution
        
        executions = db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id
        ).all()
        
        total_runs = len(executions)
        successful_runs = sum(1 for e in executions if e.status == 'completed')
        failed_runs = sum(1 for e in executions if e.status == 'failed')
        
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0.0
        
        # Calculate average duration
        completed_executions = [e for e in executions if e.status == 'completed' and e.started_at and e.completed_at]
        if completed_executions:
            durations = [(e.completed_at - e.started_at).total_seconds() * 1000 for e in completed_executions]
            avg_duration_ms = sum(durations) / len(durations)
        else:
            avg_duration_ms = None
        
        # Get last run time
        last_run_at = max([e.started_at for e in executions], default=None) if executions else None
        
        return AgentStatsResponse(
            agent_id=agent_id,
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            success_rate=round(success_rate, 1),
            avg_duration_ms=round(avg_duration_ms, 1) if avg_duration_ms else None,
            last_run_at=last_run_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent statistics: {str(e)}"
        )



@router.get(
    "/{agent_id}/stats",
    response_model=AgentStatsResponse,
    summary="Get agent statistics (alias)",
    description="Get execution statistics for an agent. Alias for /statistics endpoint.",
)
async def get_agent_stats_alias(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get agent execution statistics (alias endpoint).
    
    This is an alias for the /statistics endpoint for backward compatibility.
    """
    return await get_agent_stats(agent_id, current_user, db)
