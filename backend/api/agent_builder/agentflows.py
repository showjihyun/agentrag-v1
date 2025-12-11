# Agentflow-specific API endpoints

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.db.models.flows import Agentflow, AgentflowAgent as AgentflowAgentModel

router = APIRouter(prefix="/api/agent-builder/agentflows", tags=["Agentflows"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SupervisorConfig(BaseModel):
    """Supervisor configuration for Agentflow."""
    enabled: bool
    llm_provider: str
    llm_model: str
    max_iterations: int = 10
    decision_strategy: str = "llm_based"
    fallback_agent_id: Optional[str] = None


class AgentflowAgentRequest(BaseModel):
    """Agent configuration in Agentflow."""
    agent_id: str
    name: str
    role: str
    description: Optional[str] = None
    capabilities: List[str] = []
    priority: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    dependencies: List[str] = []


class CreateAgentflowRequest(BaseModel):
    """Request model for creating Agentflow."""
    name: str
    description: Optional[str] = None
    orchestration_type: str = "sequential"  # sequential, parallel, hierarchical, adaptive
    supervisor_config: Optional[SupervisorConfig] = None
    graph_definition: Optional[dict] = None
    tags: List[str] = []


class UpdateAgentflowRequest(BaseModel):
    """Request model for updating Agentflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    orchestration_type: Optional[str] = None
    supervisor_config: Optional[SupervisorConfig] = None
    graph_definition: Optional[dict] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("")
async def create_agentflow(
    request: CreateAgentflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Agentflow.
    
    Agentflow is a multi-agent system with orchestration.
    """
    try:
        # Create Agentflow directly using the flows model
        agentflow = Agentflow(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            orchestration_type=request.orchestration_type,
            supervisor_config=request.supervisor_config.dict() if request.supervisor_config else {},
            graph_definition=request.graph_definition or {},
            tags=request.tags,
        )
        
        db.add(agentflow)
        db.flush()
        
        # Return as dict for consistency
        result = {
            "id": str(agentflow.id),
            "name": agentflow.name,
            "description": agentflow.description,
            "orchestration_type": agentflow.orchestration_type,
            "supervisor_config": agentflow.supervisor_config,
            "graph_definition": agentflow.graph_definition,
            "tags": agentflow.tags,
            "is_active": agentflow.is_active,
            "created_at": agentflow.created_at.isoformat(),
            "updated_at": agentflow.updated_at.isoformat(),
        }
        
        db.commit()
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_agentflows(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of Agentflows.
    """
    try:
        # Query Agentflows directly
        query = db.query(Agentflow).filter(
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        )
        
        # Apply filters
        if search:
            search_lower = f"%{search.lower()}%"
            query = query.filter(
                (Agentflow.name.ilike(search_lower)) |
                (Agentflow.description.ilike(search_lower))
            )
        
        if category:
            query = query.filter(Agentflow.category == category)
        
        if is_active is not None:
            query = query.filter(Agentflow.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and get results
        agentflows = query.order_by(Agentflow.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # Convert to dict format
        flows = []
        for flow in agentflows:
            flow_dict = {
                "id": str(flow.id),
                "name": flow.name,
                "description": flow.description,
                "orchestration_type": flow.orchestration_type,
                "supervisor_config": flow.supervisor_config,
                "graph_definition": flow.graph_definition,
                "tags": flow.tags,
                "category": flow.category,
                "is_active": flow.is_active,
                "execution_count": flow.execution_count,
                "last_execution_status": flow.last_execution_status,
                "last_execution_at": flow.last_execution_at.isoformat() if flow.last_execution_at else None,
                "created_at": flow.created_at.isoformat(),
                "updated_at": flow.updated_at.isoformat(),
                "agents": [
                    {
                        "id": str(agent.id),
                        "name": agent.name,
                        "role": agent.role,
                        "description": agent.description,
                        "priority": agent.priority,
                    }
                    for agent in flow.agents
                ]
            }
            
            # Apply tag filter if specified
            if tags:
                if any(tag in flow_dict.get('tags', []) for tag in tags):
                    flows.append(flow_dict)
            else:
                flows.append(flow_dict)
        
        return {
            "flows": flows,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agentflow_id}")
async def get_agentflow(
    agentflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific Agentflow by ID.
    """
    try:
        # Query Agentflow directly
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == agentflow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if not agentflow:
            raise HTTPException(status_code=404, detail="Agentflow not found")
        
        # Convert to dict format
        result = {
            "id": str(agentflow.id),
            "name": agentflow.name,
            "description": agentflow.description,
            "orchestration_type": agentflow.orchestration_type,
            "supervisor_config": agentflow.supervisor_config,
            "graph_definition": agentflow.graph_definition,
            "tags": agentflow.tags,
            "category": agentflow.category,
            "is_active": agentflow.is_active,
            "execution_count": agentflow.execution_count,
            "last_execution_status": agentflow.last_execution_status,
            "last_execution_at": agentflow.last_execution_at.isoformat() if agentflow.last_execution_at else None,
            "created_at": agentflow.created_at.isoformat(),
            "updated_at": agentflow.updated_at.isoformat(),
            "agents": [
                {
                    "id": str(agent.id),
                    "agent_id": str(agent.agent_id) if agent.agent_id else None,
                    "name": agent.name,
                    "role": agent.role,
                    "description": agent.description,
                    "capabilities": agent.capabilities,
                    "priority": agent.priority,
                    "max_retries": agent.max_retries,
                    "timeout_seconds": agent.timeout_seconds,
                    "dependencies": agent.dependencies,
                }
                for agent in agentflow.agents
            ]
        }
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agentflow ID")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agentflow_id}")
async def update_agentflow(
    agentflow_id: str,
    request: UpdateAgentflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an Agentflow.
    """
    try:
        # Get existing Agentflow
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == agentflow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if not agentflow:
            raise HTTPException(status_code=404, detail="Agentflow not found")
        
        # Update fields
        if request.name is not None:
            agentflow.name = request.name
        if request.description is not None:
            agentflow.description = request.description
        if request.orchestration_type is not None:
            agentflow.orchestration_type = request.orchestration_type
        if request.supervisor_config is not None:
            agentflow.supervisor_config = request.supervisor_config.dict()
        if request.graph_definition is not None:
            agentflow.graph_definition = request.graph_definition
        if request.is_active is not None:
            agentflow.is_active = request.is_active
        if request.tags is not None:
            agentflow.tags = request.tags
        
        # Update timestamp
        from datetime import datetime
        agentflow.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(agentflow)
        
        # Return updated data
        result = {
            "id": str(agentflow.id),
            "name": agentflow.name,
            "description": agentflow.description,
            "orchestration_type": agentflow.orchestration_type,
            "supervisor_config": agentflow.supervisor_config,
            "graph_definition": agentflow.graph_definition,
            "tags": agentflow.tags,
            "category": agentflow.category,
            "is_active": agentflow.is_active,
            "execution_count": agentflow.execution_count,
            "last_execution_status": agentflow.last_execution_status,
            "last_execution_at": agentflow.last_execution_at.isoformat() if agentflow.last_execution_at else None,
            "created_at": agentflow.created_at.isoformat(),
            "updated_at": agentflow.updated_at.isoformat(),
        }
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agentflow ID")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agentflow_id}")
async def delete_agentflow(
    agentflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an Agentflow.
    """
    try:
        # Get existing Agentflow
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == agentflow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if not agentflow:
            raise HTTPException(status_code=404, detail="Agentflow not found")
        
        # Soft delete
        from datetime import datetime
        agentflow.deleted_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Agentflow deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agentflow ID")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
