# Agentflow-specific API endpoints

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.db.models.flows import Agentflow, AgentflowAgent as AgentflowAgentModel, FlowExecution
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/agent-builder/agentflows", tags=["Agentflows"])


# ============================================================================
# Request/Response Models
# ============================================================================

# Valid orchestration types
VALID_ORCHESTRATION_TYPES = {
    # Core patterns
    "sequential", "parallel", "hierarchical", "adaptive",
    # 2025 Trends
    "consensus_building", "dynamic_routing", "swarm_intelligence", "event_driven", "reflection",
    # 2026 Trends  
    "neuromorphic", "quantum_enhanced", "bio_inspired", "self_evolving", "federated", "emotional_ai", "predictive"
}


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
    orchestration_type: str = "sequential"  # All 17 types supported: sequential, parallel, hierarchical, adaptive, consensus_building, dynamic_routing, swarm_intelligence, event_driven, reflection, neuromorphic, quantum_enhanced, bio_inspired, self_evolving, federated, emotional_ai, predictive
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
        # Validate orchestration type
        if request.orchestration_type not in VALID_ORCHESTRATION_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid orchestration type '{request.orchestration_type}'. "
                       f"Valid types: {', '.join(sorted(VALID_ORCHESTRATION_TYPES))}"
            )
        
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


@router.post("/{agentflow_id}/agents")
async def add_agent_to_agentflow(
    agentflow_id: str,
    request: AgentflowAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add an agent to an existing Agentflow."""
    try:
        from backend.services.agent_builder.integration_service import AgentWorkflowIntegrationService
        
        integration_service = AgentWorkflowIntegrationService(db)
        
        # Verify agentflow exists and user has permission
        agentflow = db.query(Agentflow).filter(
            and_(Agentflow.id == uuid.UUID(agentflow_id), Agentflow.user_id == current_user.id)
        ).first()
        
        if not agentflow:
            raise HTTPException(status_code=404, detail="Agentflow not found")
        
        # Verify agent exists
        agent = db.query(Agent).filter(Agent.id == uuid.UUID(request.agent_id)).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Create AgentflowAgent
        agentflow_agent = AgentflowAgent(
            agentflow_id=agentflow.id,
            agent_id=agent.id,
            name=request.name,
            role=request.role,
            description=request.description,
            capabilities=request.capabilities,
            priority=request.priority,
            max_retries=request.max_retries,
            timeout_seconds=request.timeout_seconds,
            dependencies=request.dependencies,
        )
        
        db.add(agentflow_agent)
        db.commit()
        
        return {
            "id": str(agentflow_agent.id),
            "agent_id": str(agentflow_agent.agent_id),
            "name": agentflow_agent.name,
            "role": agentflow_agent.role,
            "message": "Agent added to agentflow successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agentflow_id}/execution-plan")
async def get_agentflow_execution_plan(
    agentflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the execution plan for an Agentflow."""
    try:
        from backend.services.agent_builder.integration_service import AgentWorkflowIntegrationService
        
        integration_service = AgentWorkflowIntegrationService(db)
        execution_plan = integration_service.get_agentflow_execution_plan(agentflow_id)
        
        return execution_plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agentflow_id}/validate")
async def validate_agentflow_integrity(
    agentflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate the integrity of an Agentflow."""
    try:
        from backend.services.agent_builder.integration_service import AgentWorkflowIntegrationService
        
        integration_service = AgentWorkflowIntegrationService(db)
        validation_report = integration_service.validate_agentflow_integrity(agentflow_id)
        
        return validation_report
        
    except Exception as e:
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
            # Validate orchestration type
            if request.orchestration_type not in VALID_ORCHESTRATION_TYPES:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid orchestration type '{request.orchestration_type}'. "
                           f"Valid types: {', '.join(sorted(VALID_ORCHESTRATION_TYPES))}"
                )
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


@router.post("/{agentflow_id}/execute")
async def execute_agentflow(
    agentflow_id: str,
    input_data: dict = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute an Agentflow with detailed error handling and real-time monitoring.
    """
    execution_id = None
    
    try:
        # 1. Validate AgentFlow exists and is accessible
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == agentflow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if not agentflow:
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "AgentFlow not found",
                    "message": f"AgentFlow with ID {agentflow_id} was not found or you don't have access to it.",
                    "code": "AGENTFLOW_NOT_FOUND"
                }
            )
        
        if not agentflow.is_active:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "AgentFlow is inactive",
                    "message": f"AgentFlow '{agentflow.name}' is currently inactive and cannot be executed.",
                    "code": "AGENTFLOW_INACTIVE"
                }
            )
        
        # 2. Validate graph definition
        if not agentflow.graph_definition or not agentflow.graph_definition.get("nodes"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid workflow configuration",
                    "message": "AgentFlow has no nodes defined. Please configure the workflow before executing.",
                    "code": "EMPTY_WORKFLOW"
                }
            )
        
        # 3. Create execution record with detailed tracking
        execution_id = str(uuid.uuid4())
        
        flow_execution = FlowExecution(
            id=execution_id,
            agentflow_id=agentflow.id,
            user_id=current_user.id,
            flow_type="agentflow",
            flow_name=agentflow.name,
            input_data=input_data or {},
            status="initializing",
            started_at=datetime.utcnow(),
            metrics={
                "total_nodes": len(agentflow.graph_definition.get("nodes", [])),
                "completed_nodes": 0,
                "failed_nodes": 0,
                "execution_path": [],
                "error_details": []
            }
        )
        
        db.add(flow_execution)
        db.commit()
        
        logger.info(
            "AgentFlow execution started",
            execution_id=execution_id,
            agentflow_id=agentflow_id,
            user_id=str(current_user.id)
        )
        
        # 4. Execute AgentFlow using the executor
        try:
            from backend.services.agent_builder.execution.agentflow_executor import AgentFlowExecutor
            from backend.core.cache_manager import CacheManager
            
            cache_manager = CacheManager()
            executor = AgentFlowExecutor(db, cache_manager)
            
            # Execute asynchronously with detailed error tracking
            execution_result = await executor.execute_agentflow(
                agentflow_id=agentflow_id,
                user=current_user,
                input_data=input_data or {}
            )
            
            return {
                "execution_id": execution_result["execution_id"],
                "status": execution_result["status"],
                "started_at": execution_result["started_at"],
                "message": f"AgentFlow '{agentflow.name}' executed successfully",
                "stream_url": f"/api/agent-builder/executions/{execution_result['execution_id']}/stream",
                "details_url": f"/api/agent-builder/executions/{execution_result['execution_id']}"
            }
            
        except Exception as execution_error:
            # Update execution record with detailed error information
            flow_execution.status = "failed"
            flow_execution.completed_at = datetime.utcnow()
            flow_execution.error_message = str(execution_error)
            
            if flow_execution.started_at:
                flow_execution.duration_ms = int(
                    (flow_execution.completed_at - flow_execution.started_at).total_seconds() * 1000
                )
            
            # Add detailed error information to metrics
            error_details = {
                "error_type": type(execution_error).__name__,
                "error_message": str(execution_error),
                "error_location": "execution_engine",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if flow_execution.metrics:
                flow_execution.metrics["error_details"].append(error_details)
            else:
                flow_execution.metrics = {"error_details": [error_details]}
            
            db.commit()
            
            logger.error(
                "AgentFlow execution failed",
                execution_id=execution_id,
                agentflow_id=agentflow_id,
                error=str(execution_error),
                error_type=type(execution_error).__name__
            )
            
            # Return detailed error response
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Execution failed",
                    "message": f"AgentFlow execution failed: {str(execution_error)}",
                    "code": "EXECUTION_FAILED",
                    "execution_id": execution_id,
                    "error_type": type(execution_error).__name__,
                    "details": {
                        "agentflow_name": agentflow.name,
                        "error_location": "execution_engine",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        # Handle unexpected errors
        error_details = {
            "error": "Unexpected error",
            "message": f"An unexpected error occurred: {str(e)}",
            "code": "UNEXPECTED_ERROR",
            "error_type": type(e).__name__,
            "execution_id": execution_id
        }
        
        logger.error(
            "Unexpected error in AgentFlow execution",
            execution_id=execution_id,
            agentflow_id=agentflow_id,
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Update execution record if it exists
        if execution_id:
            try:
                flow_execution = db.query(FlowExecution).filter(
                    FlowExecution.id == execution_id
                ).first()
                
                if flow_execution:
                    flow_execution.status = "failed"
                    flow_execution.completed_at = datetime.utcnow()
                    flow_execution.error_message = str(e)
                    
                    if flow_execution.started_at:
                        flow_execution.duration_ms = int(
                            (flow_execution.completed_at - flow_execution.started_at).total_seconds() * 1000
                        )
                    
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update execution record: {str(db_error)}")
        
        raise HTTPException(status_code=500, detail=error_details)


@router.get("/available-agents")
async def get_available_agents(
    search: Optional[str] = Query(None),
    agent_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available agents that can be added to AgentFlows.
    
    Returns agents created in Building Blocks that can be used in AgentFlow teams.
    """
    try:
        from backend.db.models.agent_builder import Agent
        
        # Query available agents
        query = db.query(Agent).filter(
            Agent.user_id == current_user.id,
            Agent.deleted_at.is_(None)
        )
        
        # Apply filters
        if search:
            search_lower = f"%{search.lower()}%"
            query = query.filter(
                (Agent.name.ilike(search_lower)) |
                (Agent.description.ilike(search_lower))
            )
        
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and get results
        agents = query.order_by(Agent.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # Convert to response format
        available_agents = []
        for agent in agents:
            agent_dict = {
                "id": str(agent.id),
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model,
                "configuration": agent.configuration,
                "is_public": agent.is_public,
                "created_at": agent.created_at.isoformat(),
                "updated_at": agent.updated_at.isoformat(),
                # Include tools and capabilities for better selection
                "tools": [
                    {
                        "tool_id": tool.tool_id,
                        "configuration": tool.configuration
                    }
                    for tool in agent.tools
                ],
                "capabilities": agent.configuration.get("capabilities", []) if agent.configuration else []
            }
            available_agents.append(agent_dict)
        
        return {
            "agents": available_agents,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        logger.error(f"Error fetching available agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agentflow_id}/agents")
async def add_agent_to_agentflow(
    agentflow_id: str,
    request: AgentflowAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add an agent to an AgentFlow team.
    """
    try:
        from backend.db.models.agent_builder import Agent
        
        # Validate AgentFlow exists and is accessible
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == agentflow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if not agentflow:
            raise HTTPException(status_code=404, detail="AgentFlow not found")
        
        # Validate agent exists and is accessible
        agent = db.query(Agent).filter(
            Agent.id == request.agent_id,
            Agent.user_id == current_user.id,
            Agent.deleted_at.is_(None)
        ).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent is already in the AgentFlow
        existing_agent = db.query(AgentflowAgentModel).filter(
            AgentflowAgentModel.agentflow_id == agentflow_id,
            AgentflowAgentModel.agent_id == request.agent_id
        ).first()
        
        if existing_agent:
            raise HTTPException(status_code=400, detail="Agent is already part of this AgentFlow")
        
        # Create AgentFlow agent association
        agentflow_agent = AgentflowAgentModel(
            agentflow_id=agentflow.id,
            agent_id=agent.id,
            name=request.name,
            role=request.role,
            description=request.description,
            capabilities=request.capabilities,
            priority=request.priority,
            max_retries=request.max_retries,
            timeout_seconds=request.timeout_seconds,
            dependencies=request.dependencies
        )
        
        db.add(agentflow_agent)
        
        # Update AgentFlow timestamp
        agentflow.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(agentflow_agent)
        
        # Return the created agent association
        result = {
            "id": str(agentflow_agent.id),
            "agent_id": str(agentflow_agent.agent_id),
            "name": agentflow_agent.name,
            "role": agentflow_agent.role,
            "description": agentflow_agent.description,
            "capabilities": agentflow_agent.capabilities,
            "priority": agentflow_agent.priority,
            "max_retries": agentflow_agent.max_retries,
            "timeout_seconds": agentflow_agent.timeout_seconds,
            "dependencies": agentflow_agent.dependencies,
            "created_at": agentflow_agent.created_at.isoformat(),
            # Include agent details for convenience
            "agent_details": {
                "name": agent.name,
                "description": agent.description,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model,
                "agent_type": agent.agent_type
            }
        }
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding agent to AgentFlow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agentflow_id}/agents/{agent_association_id}")
async def update_agentflow_agent(
    agentflow_id: str,
    agent_association_id: str,
    request: AgentflowAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an agent's configuration in an AgentFlow.
    """
    try:
        # Validate AgentFlow exists and is accessible
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == agentflow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if not agentflow:
            raise HTTPException(status_code=404, detail="AgentFlow not found")
        
        # Get the agent association
        agentflow_agent = db.query(AgentflowAgentModel).filter(
            AgentflowAgentModel.id == agent_association_id,
            AgentflowAgentModel.agentflow_id == agentflow_id
        ).first()
        
        if not agentflow_agent:
            raise HTTPException(status_code=404, detail="Agent association not found")
        
        # Update agent configuration
        agentflow_agent.name = request.name
        agentflow_agent.role = request.role
        agentflow_agent.description = request.description
        agentflow_agent.capabilities = request.capabilities
        agentflow_agent.priority = request.priority
        agentflow_agent.max_retries = request.max_retries
        agentflow_agent.timeout_seconds = request.timeout_seconds
        agentflow_agent.dependencies = request.dependencies
        
        # Update AgentFlow timestamp
        agentflow.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(agentflow_agent)
        
        # Return updated association
        result = {
            "id": str(agentflow_agent.id),
            "agent_id": str(agentflow_agent.agent_id),
            "name": agentflow_agent.name,
            "role": agentflow_agent.role,
            "description": agentflow_agent.description,
            "capabilities": agentflow_agent.capabilities,
            "priority": agentflow_agent.priority,
            "max_retries": agentflow_agent.max_retries,
            "timeout_seconds": agentflow_agent.timeout_seconds,
            "dependencies": agentflow_agent.dependencies,
            "created_at": agentflow_agent.created_at.isoformat()
        }
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating AgentFlow agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agentflow_id}/agents/{agent_association_id}")
async def remove_agent_from_agentflow(
    agentflow_id: str,
    agent_association_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove an agent from an AgentFlow team.
    """
    try:
        # Validate AgentFlow exists and is accessible
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == agentflow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if not agentflow:
            raise HTTPException(status_code=404, detail="AgentFlow not found")
        
        # Get the agent association
        agentflow_agent = db.query(AgentflowAgentModel).filter(
            AgentflowAgentModel.id == agent_association_id,
            AgentflowAgentModel.agentflow_id == agentflow_id
        ).first()
        
        if not agentflow_agent:
            raise HTTPException(status_code=404, detail="Agent association not found")
        
        # Remove the association
        db.delete(agentflow_agent)
        
        # Update AgentFlow timestamp
        agentflow.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Agent removed from AgentFlow successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing agent from AgentFlow: {str(e)}")
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
