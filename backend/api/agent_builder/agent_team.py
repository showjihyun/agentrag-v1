"""Agent Builder API endpoints for Agent Team (Multi-Agent Collaboration)."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.agent_team_orchestrator import (
    AgentTeamOrchestrator,
    AgentTeamConfig,
    AgentConfig,
    TaskConfig,
    AgentRole,
    ExecutionMode,
    AGENT_TEMPLATES,
    create_team_from_template,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/agent-team",
    tags=["agent-builder-agent-team"],
)


# Request/Response Models
class AgentCreateRequest(BaseModel):
    """Request to create an agent."""
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., description="Agent role (researcher, writer, etc.)")
    goal: str = Field(..., min_length=1)
    backstory: str = Field(..., min_length=1)
    tools: List[str] = Field(default_factory=list)
    llm_model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7, ge=0, le=2)
    allow_delegation: bool = Field(default=False)
    delegate_to: List[str] = Field(default_factory=list)


class TaskCreateRequest(BaseModel):
    """Request to create a task."""
    description: str = Field(..., min_length=1)
    agent_id: str = Field(..., description="ID of agent to execute task")
    expected_output: str = Field(..., min_length=1)
    context_from: List[str] = Field(default_factory=list, description="Task IDs for context")
    tools: List[str] = Field(default_factory=list)
    async_execution: bool = Field(default=False)
    human_input: bool = Field(default=False)


class AgentTeamCreateRequest(BaseModel):
    """Request to create an agent team."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    agents: List[AgentCreateRequest]
    tasks: List[TaskCreateRequest]
    execution_mode: str = Field(default="sequential", description="sequential, parallel, hierarchical")
    manager_agent_id: Optional[str] = Field(default=None)
    verbose: bool = Field(default=False)


class AgentTeamFromTemplateRequest(BaseModel):
    """Request to create agent team from template."""
    template_name: str = Field(..., description="research_team, content_team, dev_team")
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    tasks: List[Dict[str, Any]] = Field(..., description="List of task definitions")


class AgentTeamExecuteRequest(BaseModel):
    """Request to execute an agent team."""
    inputs: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Agent response model."""
    id: str
    name: str
    role: str
    goal: str
    backstory: str
    tools: List[str]
    llm_model: str
    allow_delegation: bool
    delegate_to: List[str]


class TaskResponse(BaseModel):
    """Task response model."""
    id: str
    description: str
    agent_id: str
    expected_output: str
    context_from: List[str]
    status: Optional[str] = None
    output: Optional[Any] = None


class AgentTeamResponse(BaseModel):
    """Agent team response model."""
    id: str
    name: str
    description: str
    agents: List[AgentResponse]
    tasks: List[TaskResponse]
    execution_mode: str
    manager_agent_id: Optional[str]
    created_at: Optional[str] = None


# In-memory storage (replace with DB in production)
_agent_teams: Dict[str, Dict[str, Any]] = {}


@router.get("/templates")
async def get_agent_templates(
    current_user: User = Depends(get_current_user),
):
    """
    Get available agent templates.
    
    Returns predefined agent configurations for common roles.
    """
    templates = {}
    for key, agent in AGENT_TEMPLATES.items():
        templates[key] = {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value,
            "goal": agent.goal,
            "backstory": agent.backstory[:200] + "..." if len(agent.backstory) > 200 else agent.backstory,
            "tools": agent.tools,
            "allow_delegation": agent.allow_delegation,
        }
    
    return {
        "templates": templates,
        "team_templates": ["research_team", "content_team", "dev_team"],
    }


@router.get("/roles")
async def get_agent_roles(
    current_user: User = Depends(get_current_user),
):
    """Get available agent roles."""
    return {
        "roles": [
            {"value": role.value, "label": role.value.title()}
            for role in AgentRole
        ]
    }


@router.post("", response_model=AgentTeamResponse)
async def create_agent_team(
    request: AgentTeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new agent team with agents and tasks.
    
    An agent team is a group of AI agents that collaborate to complete tasks.
    """
    try:
        import uuid
        
        team_id = str(uuid.uuid4())
        
        # Build agent configs
        agents = []
        for i, agent_req in enumerate(request.agents):
            agent_id = f"agent_{i}_{uuid.uuid4().hex[:8]}"
            agents.append(AgentConfig(
                id=agent_id,
                name=agent_req.name,
                role=AgentRole(agent_req.role) if agent_req.role in [r.value for r in AgentRole] else AgentRole.CUSTOM,
                goal=agent_req.goal,
                backstory=agent_req.backstory,
                tools=agent_req.tools,
                llm_model=agent_req.llm_model,
                temperature=agent_req.temperature,
                allow_delegation=agent_req.allow_delegation,
                delegate_to=agent_req.delegate_to,
            ))
        
        agent_id_map = {f"agent_{i}": agents[i].id for i in range(len(agents))}
        
        # Build task configs
        tasks = []
        for i, task_req in enumerate(request.tasks):
            task_id = f"task_{i}_{uuid.uuid4().hex[:8]}"
            agent_id = task_req.agent_id
            if agent_id in agent_id_map:
                agent_id = agent_id_map[agent_id]
            elif not any(a.id == agent_id for a in agents):
                agent_id = agents[i % len(agents)].id
            
            tasks.append(TaskConfig(
                id=task_id,
                description=task_req.description,
                agent_id=agent_id,
                expected_output=task_req.expected_output,
                context_from=task_req.context_from,
                tools=task_req.tools,
                async_execution=task_req.async_execution,
                human_input=task_req.human_input,
            ))
        
        # Create team config
        team_config = AgentTeamConfig(
            id=team_id,
            name=request.name,
            description=request.description,
            agents=agents,
            tasks=tasks,
            execution_mode=ExecutionMode(request.execution_mode),
            manager_agent_id=request.manager_agent_id,
            verbose=request.verbose,
        )
        
        # Store team
        _agent_teams[team_id] = {
            "config": team_config,
            "user_id": str(current_user.id),
            "created_at": datetime.utcnow().isoformat(),
            "executions": [],
        }
        
        logger.info(f"Created agent team {team_id} with {len(agents)} agents and {len(tasks)} tasks")
        
        return AgentTeamResponse(
            id=team_id,
            name=team_config.name,
            description=team_config.description,
            agents=[AgentResponse(
                id=a.id,
                name=a.name,
                role=a.role.value,
                goal=a.goal,
                backstory=a.backstory,
                tools=a.tools,
                llm_model=a.llm_model,
                allow_delegation=a.allow_delegation,
                delegate_to=a.delegate_to,
            ) for a in agents],
            tasks=[TaskResponse(
                id=t.id,
                description=t.description,
                agent_id=t.agent_id,
                expected_output=t.expected_output,
                context_from=t.context_from,
            ) for t in tasks],
            execution_mode=team_config.execution_mode.value,
            manager_agent_id=team_config.manager_agent_id,
            created_at=_agent_teams[team_id]["created_at"],
        )
        
    except Exception as e:
        logger.error(f"Failed to create agent team: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent team: {str(e)}"
        )


@router.post("/from-template", response_model=AgentTeamResponse)
async def create_agent_team_from_template(
    request: AgentTeamFromTemplateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create an agent team from a predefined template.
    
    Available templates:
    - research_team: Researcher, Analyst, Writer
    - content_team: Researcher, Writer, Editor
    - dev_team: Coder, Reviewer
    """
    try:
        team_config = create_team_from_template(
            template_name=request.template_name,
            tasks=request.tasks,
            name=request.name,
            description=request.description,
        )
        
        _agent_teams[team_config.id] = {
            "config": team_config,
            "user_id": str(current_user.id),
            "created_at": datetime.utcnow().isoformat(),
            "executions": [],
        }
        
        return AgentTeamResponse(
            id=team_config.id,
            name=team_config.name,
            description=team_config.description,
            agents=[AgentResponse(
                id=a.id,
                name=a.name,
                role=a.role.value,
                goal=a.goal,
                backstory=a.backstory,
                tools=a.tools,
                llm_model=a.llm_model,
                allow_delegation=a.allow_delegation,
                delegate_to=a.delegate_to,
            ) for a in team_config.agents],
            tasks=[TaskResponse(
                id=t.id,
                description=t.description,
                agent_id=t.agent_id,
                expected_output=t.expected_output,
                context_from=t.context_from,
            ) for t in team_config.tasks],
            execution_mode=team_config.execution_mode.value,
            manager_agent_id=team_config.manager_agent_id,
            created_at=_agent_teams[team_config.id]["created_at"],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create agent team from template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{team_id}", response_model=AgentTeamResponse)
async def get_agent_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get agent team by ID."""
    team_data = _agent_teams.get(team_id)
    if not team_data:
        raise HTTPException(status_code=404, detail="Agent team not found")
    
    if team_data["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    config = team_data["config"]
    
    return AgentTeamResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        agents=[AgentResponse(
            id=a.id,
            name=a.name,
            role=a.role.value,
            goal=a.goal,
            backstory=a.backstory,
            tools=a.tools,
            llm_model=a.llm_model,
            allow_delegation=a.allow_delegation,
            delegate_to=a.delegate_to,
        ) for a in config.agents],
        tasks=[TaskResponse(
            id=t.id,
            description=t.description,
            agent_id=t.agent_id,
            expected_output=t.expected_output,
            context_from=t.context_from,
        ) for t in config.tasks],
        execution_mode=config.execution_mode.value,
        manager_agent_id=config.manager_agent_id,
        created_at=team_data["created_at"],
    )


@router.get("")
async def list_agent_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """List user's agent teams."""
    user_id = str(current_user.id)
    user_teams = [
        {
            "id": team_id,
            "name": data["config"].name,
            "description": data["config"].description,
            "agent_count": len(data["config"].agents),
            "task_count": len(data["config"].tasks),
            "execution_mode": data["config"].execution_mode.value,
            "created_at": data["created_at"],
            "execution_count": len(data["executions"]),
        }
        for team_id, data in _agent_teams.items()
        if data["user_id"] == user_id
    ]
    
    return {
        "teams": user_teams[skip:skip + limit],
        "total": len(user_teams),
    }


@router.post("/{team_id}/execute")
async def execute_agent_team(
    team_id: str,
    request: AgentTeamExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Execute an agent team with all its tasks.
    
    Returns execution results with outputs from all tasks.
    """
    team_data = _agent_teams.get(team_id)
    if not team_data:
        raise HTTPException(status_code=404, detail="Agent team not found")
    
    if team_data["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        orchestrator = AgentTeamOrchestrator(team_data["config"])
        result = await orchestrator.execute(request.inputs)
        
        import uuid
        execution_id = str(uuid.uuid4())
        team_data["executions"].append({
            "id": execution_id,
            "inputs": request.inputs,
            "result": result,
            "executed_at": datetime.utcnow().isoformat(),
        })
        
        return {
            "execution_id": execution_id,
            **result,
        }
        
    except Exception as e:
        logger.error(f"Agent team execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{team_id}")
async def delete_agent_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete an agent team."""
    team_data = _agent_teams.get(team_id)
    if not team_data:
        raise HTTPException(status_code=404, detail="Agent team not found")
    
    if team_data["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    del _agent_teams[team_id]
    
    return {"message": "Agent team deleted", "id": team_id}
