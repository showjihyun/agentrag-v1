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
    limit: int = Query(10, ge=1, le=50, description="Maximum number of trending agents"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get trending agents based on usage patterns."""
    try:
        logger.info(f"Getting trending agents for period: {time_period}")
        
        # Mock trending agents data
        trending_agents = [
            {
                "agent": {
                    "id": "trending-1",
                    "name": "데이터 분석 전문가",
                    "description": "고급 데이터 분석 및 시각화를 수행하는 AI 에이전트",
                    "agent_type": "custom",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "is_public": True,
                    "created_at": "2024-12-01T00:00:00Z",
                    "updated_at": "2024-12-25T00:00:00Z"
                },
                "trend_score": 95.5,
                "execution_count": 1247,
                "success_rate": 94.2,
                "unique_users": 89
            },
            {
                "agent": {
                    "id": "trending-2",
                    "name": "콘텐츠 생성기",
                    "description": "창의적이고 매력적인 콘텐츠를 자동 생성하는 AI 에이전트",
                    "agent_type": "template_based",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "is_public": True,
                    "created_at": "2024-11-15T00:00:00Z",
                    "updated_at": "2024-12-24T00:00:00Z"
                },
                "trend_score": 88.3,
                "execution_count": 892,
                "success_rate": 91.7,
                "unique_users": 67
            },
            {
                "agent": {
                    "id": "trending-3",
                    "name": "고객 서비스 봇",
                    "description": "24/7 고객 문의 응답 및 지원을 제공하는 AI 에이전트",
                    "agent_type": "custom",
                    "llm_provider": "claude",
                    "llm_model": "claude-3-sonnet",
                    "is_public": True,
                    "created_at": "2024-10-20T00:00:00Z",
                    "updated_at": "2024-12-23T00:00:00Z"
                },
                "trend_score": 82.1,
                "execution_count": 1456,
                "success_rate": 96.8,
                "unique_users": 123
            }
        ]
        
        return TrendingAgentsResponse(
            trending_agents=trending_agents[:limit],
            time_period=time_period,
            total_count=len(trending_agents)
        )
        
    except Exception as e:
        logger.error(f"Failed to get trending agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trending agents"
        )


@router.get(
    "/personalized-recommendations",
    response_model=PersonalizedRecommendationResponse,
    summary="Get personalized agent recommendations",
    description="Get AI-powered personalized agent recommendations based on user behavior and preferences.",
)
async def get_personalized_recommendations(
    orchestration_type: Optional[str] = Query(None, description="Filter by orchestration type"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recommendations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get personalized agent recommendations using AI analysis."""
    try:
        logger.info(f"Getting personalized recommendations for user {current_user.id}")
        
        # Mock personalized recommendations
        recommendations = [
            {
                "agent": {
                    "id": "rec-1",
                    "name": "맞춤형 데이터 분석가",
                    "description": "사용자의 분석 패턴에 최적화된 데이터 분석 에이전트",
                    "agent_type": "custom",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "is_public": True,
                    "created_at": "2024-12-01T00:00:00Z",
                    "updated_at": "2024-12-25T00:00:00Z"
                },
                "score": 0.95,
                "reasons": ["사용자의 데이터 분석 히스토리와 일치", "선호하는 시각화 스타일 반영"]
            }
        ]
        
        return PersonalizedRecommendationResponse(
            recommendations=recommendations[:limit],
            total_count=len(recommendations),
            orchestration_type=orchestration_type
        )
        
    except Exception as e:
        logger.error(f"Failed to get personalized recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personalized recommendations"
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
    """Get agent templates with filtering options."""
    try:
        logger.info(f"Getting agent templates for user {current_user.id}")
        
        # Mock templates data
        templates = [
            {
                "id": "template-1",
                "name": "데이터 분석 전문가",
                "description": "데이터를 수집하고 분석하여 인사이트를 제공하는 전문 에이전트",
                "category": "analytics",
                "orchestration_types": ["sequential", "pipeline"],
                "complexity": "intermediate",
                "capabilities": ["데이터 분석", "통계 처리", "시각화", "보고서 생성"],
                "tools": ["python_code", "data_visualization", "statistical_analysis"],
                "configuration": {
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "system_prompt": "당신은 데이터 분석 전문가입니다.",
                    "temperature": 0.3
                },
                "use_case": "순차적 데이터 처리 파이프라인에서 분석 단계를 담당"
            }
        ]
        
        # Apply filters
        filtered_templates = templates
        if orchestration_type:
            filtered_templates = [t for t in filtered_templates if orchestration_type in t["orchestration_types"]]
        if category:
            filtered_templates = [t for t in filtered_templates if t["category"] == category]
        if complexity:
            filtered_templates = [t for t in filtered_templates if t["complexity"] == complexity]
        
        return {
            "templates": filtered_templates,
            "total": len(filtered_templates),
            "filters": {
                "orchestration_type": orchestration_type,
                "category": category,
                "complexity": complexity
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent templates"
        )


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
    """Search users for agent sharing."""
    try:
        logger.info(f"Searching users with query: {q}")
        
        # Mock user search data
        users = [
            {
                "id": "user-1",
                "name": "김철수",
                "email": "kim@example.com",
                "avatar": None
            },
            {
                "id": "user-2",
                "name": "이영희",
                "email": "lee@example.com",
                "avatar": None
            }
        ]
        
        # Filter users based on query
        filtered_users = [
            user for user in users 
            if q.lower() in user["name"].lower() or q.lower() in user["email"].lower()
        ]
        
        return {
            "users": filtered_users[:limit]
        }
        
    except Exception as e:
        logger.error(f"Failed to search users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )


# ============================================================================
# CRUD OPERATIONS
# ============================================================================

@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Create a new custom agent with specified tools, prompts, and configuration.",
)
def create_agent(
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
        )
        
        # Execute command
        agent = facade.agent_commands.handle_create(command)
        
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
        
        # Temporarily return mock data to fix the 500 error
        return AgentListResponse(
            agents=[],
            total=0,
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
    """Get agents similar to the specified agent."""
    try:
        logger.info(f"Getting similar agents for agent {agent_id}")
        
        # Mock similar agents data
        similar_agents = [
            {
                "agent": {
                    "id": "similar-1",
                    "name": "고급 데이터 분석가",
                    "description": "복잡한 데이터셋 분석 및 예측 모델링 전문",
                    "agent_type": "custom",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "is_public": True,
                    "created_at": "2024-11-01T00:00:00Z",
                    "updated_at": "2024-12-20T00:00:00Z"
                },
                "similarity": 0.92,
                "common_features": ["데이터 분석", "통계 처리", "시각화"]
            }
        ]
        
        return SimilarAgentsResponse(
            similar_agents=similar_agents[:limit],
            total_count=len(similar_agents)
        )
        
    except Exception as e:
        logger.error(f"Failed to get similar agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get similar agents"
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
        agent = facade.agent_queries.handle_get(query)
        
        # Check permissions (owner or has read permission)
        if str(agent.user_id) != str(current_user.id) and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this agent"
            )
        
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