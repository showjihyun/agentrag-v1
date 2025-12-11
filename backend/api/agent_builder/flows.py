# Flows API - Unified endpoint for Agentflow and Chatflow

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.db.models.flows import Agentflow, Chatflow

router = APIRouter(prefix="/api/agent-builder/flows", tags=["Flows"])


# ============================================================================
# Request/Response Models
# ============================================================================

class FlowListResponse(BaseModel):
    """Response model for flow list."""
    flows: List[dict]
    total: int
    page: int
    page_size: int


class FlowExecutionRequest(BaseModel):
    """Request model for flow execution."""
    input_data: dict


class FlowExecutionResponse(BaseModel):
    """Response model for flow execution."""
    id: str
    flow_id: str
    flow_type: str
    status: str
    started_at: str
    input_data: Optional[dict] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=FlowListResponse)
async def get_flows(
    flow_type: Optional[str] = Query(None, description="Filter by flow type: agentflow or chatflow"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of flows (both Agentflow and Chatflow).
    
    Supports filtering, searching, pagination, and sorting.
    """
    try:
        flows = []
        
        # Get Agentflows if not filtering for chatflow only
        if not flow_type or flow_type == "agentflow":
            agentflow_query = db.query(Agentflow).filter(
                Agentflow.user_id == current_user.id,
                Agentflow.deleted_at.is_(None)
            )
            
            # Apply filters for agentflows
            if search:
                search_pattern = f"%{search.lower()}%"
                agentflow_query = agentflow_query.filter(
                    (Agentflow.name.ilike(search_pattern)) |
                    (Agentflow.description.ilike(search_pattern))
                )
            
            if category:
                agentflow_query = agentflow_query.filter(Agentflow.category == category)
            
            if is_active is not None:
                agentflow_query = agentflow_query.filter(Agentflow.is_active == is_active)
            
            agentflows = agentflow_query.all()
            
            for flow in agentflows:
                # Apply tag filter
                if tags and not any(tag in (flow.tags or []) for tag in tags):
                    continue
                    
                flows.append({
                    "id": str(flow.id),
                    "name": flow.name,
                    "description": flow.description,
                    "flow_type": "agentflow",
                    "orchestration_type": flow.orchestration_type,
                    "supervisor_config": flow.supervisor_config,
                    "tags": flow.tags,
                    "category": flow.category,
                    "is_active": flow.is_active,
                    "execution_count": flow.execution_count,
                    "last_execution_status": flow.last_execution_status,
                    "last_execution_at": flow.last_execution_at.isoformat() if flow.last_execution_at else None,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                })
        
        # Get Chatflows if not filtering for agentflow only
        if not flow_type or flow_type == "chatflow":
            chatflow_query = db.query(Chatflow).filter(
                Chatflow.user_id == current_user.id,
                Chatflow.deleted_at.is_(None)
            )
            
            # Apply filters for chatflows
            if search:
                search_pattern = f"%{search.lower()}%"
                chatflow_query = chatflow_query.filter(
                    (Chatflow.name.ilike(search_pattern)) |
                    (Chatflow.description.ilike(search_pattern))
                )
            
            if category:
                chatflow_query = chatflow_query.filter(Chatflow.category == category)
            
            if is_active is not None:
                chatflow_query = chatflow_query.filter(Chatflow.is_active == is_active)
            
            chatflows = chatflow_query.all()
            
            for flow in chatflows:
                # Apply tag filter
                if tags and not any(tag in (flow.tags or []) for tag in tags):
                    continue
                    
                flows.append({
                    "id": str(flow.id),
                    "name": flow.name,
                    "description": flow.description,
                    "flow_type": "chatflow",
                    "chat_config": flow.chat_config,
                    "memory_config": flow.memory_config,
                    "rag_config": flow.rag_config,
                    "tags": flow.tags,
                    "category": flow.category,
                    "is_active": flow.is_active,
                    "execution_count": flow.execution_count,
                    "last_execution_status": flow.last_execution_status,
                    "last_execution_at": flow.last_execution_at.isoformat() if flow.last_execution_at else None,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                })
        
        # Sort flows
        if sort_by == "name":
            flows.sort(key=lambda x: x["name"], reverse=(sort_order == "desc"))
        elif sort_by == "created_at":
            flows.sort(key=lambda x: x["created_at"], reverse=(sort_order == "desc"))
        elif sort_by == "updated_at":
            flows.sort(key=lambda x: x["updated_at"], reverse=(sort_order == "desc"))
        elif sort_by == "execution_count":
            flows.sort(key=lambda x: x["execution_count"] or 0, reverse=(sort_order == "desc"))
        
        # Apply pagination
        total = len(flows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_flows = flows[start_idx:end_idx]
        
        return FlowListResponse(
            flows=paginated_flows,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{flow_id}")
async def get_flow(
    flow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific flow by ID.
    
    Automatically detects flow type (Agentflow or Chatflow).
    """
    try:
        # Try to find as Agentflow first
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == flow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if agentflow:
            return {
                "id": str(agentflow.id),
                "name": agentflow.name,
                "description": agentflow.description,
                "flow_type": "agentflow",
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
        
        # Try to find as Chatflow
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == flow_id,
            Chatflow.user_id == current_user.id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if chatflow:
            return {
                "id": str(chatflow.id),
                "name": chatflow.name,
                "description": chatflow.description,
                "flow_type": "chatflow",
                "chat_config": chatflow.chat_config,
                "memory_config": chatflow.memory_config,
                "rag_config": chatflow.rag_config,
                "graph_definition": chatflow.graph_definition,
                "tags": chatflow.tags,
                "category": chatflow.category,
                "is_active": chatflow.is_active,
                "execution_count": chatflow.execution_count,
                "last_execution_status": chatflow.last_execution_status,
                "last_execution_at": chatflow.last_execution_at.isoformat() if chatflow.last_execution_at else None,
                "created_at": chatflow.created_at.isoformat(),
                "updated_at": chatflow.updated_at.isoformat(),
                "tools": [
                    {
                        "id": str(tool.id),
                        "tool_id": tool.tool_id,
                        "name": tool.name,
                        "description": tool.description,
                        "enabled": tool.enabled,
                        "configuration": tool.configuration,
                    }
                    for tool in chatflow.tools
                ]
            }
        
        raise HTTPException(status_code=404, detail="Flow not found")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flow ID")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{flow_id}")
async def update_flow(
    flow_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a flow.
    
    Supports partial updates for both Agentflow and Chatflow.
    """
    try:
        # Try to find as Agentflow first
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == flow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if agentflow:
            # Update Agentflow
            if 'name' in data:
                agentflow.name = data['name']
            if 'description' in data:
                agentflow.description = data['description']
            if 'orchestration_type' in data:
                agentflow.orchestration_type = data['orchestration_type']
            if 'supervisor_config' in data:
                agentflow.supervisor_config = data['supervisor_config']
            if 'graph_definition' in data:
                agentflow.graph_definition = data['graph_definition']
            if 'tags' in data:
                agentflow.tags = data['tags']
            if 'category' in data:
                agentflow.category = data['category']
            if 'is_active' in data:
                agentflow.is_active = data['is_active']
            
            # Handle agents update
            if 'agents' in data and data['agents']:
                # Clear existing agents
                from backend.db.models.flows import AgentflowAgent
                db.query(AgentflowAgent).filter(
                    AgentflowAgent.agentflow_id == agentflow.id
                ).delete()
                
                # Add new agents
                for agent_data in data['agents']:
                    agent = AgentflowAgent(
                        agentflow_id=agentflow.id,
                        agent_id=agent_data.get('agent_id'),
                        name=agent_data.get('name', ''),
                        role=agent_data.get('role', ''),
                        description=agent_data.get('description', ''),
                        priority=agent_data.get('priority', 1),
                        max_retries=agent_data.get('max_retries', 3),
                        timeout_seconds=agent_data.get('timeout_seconds', 60),
                        capabilities=agent_data.get('capabilities', []),
                        dependencies=agent_data.get('dependencies', [])
                    )
                    db.add(agent)
            
            agentflow.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(agentflow)
            
            return {
                "id": str(agentflow.id),
                "name": agentflow.name,
                "description": agentflow.description,
                "flow_type": "agentflow",
                "orchestration_type": agentflow.orchestration_type,
                "supervisor_config": agentflow.supervisor_config,
                "tags": agentflow.tags,
                "category": agentflow.category,
                "is_active": agentflow.is_active,
                "updated_at": agentflow.updated_at.isoformat(),
            }
        
        # Try to find as Chatflow
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == flow_id,
            Chatflow.user_id == current_user.id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if chatflow:
            # Update Chatflow
            if 'name' in data:
                chatflow.name = data['name']
            if 'description' in data:
                chatflow.description = data['description']
            if 'chat_config' in data:
                chatflow.chat_config = data['chat_config']
            if 'memory_config' in data:
                chatflow.memory_config = data['memory_config']
            if 'rag_config' in data:
                chatflow.rag_config = data['rag_config']
            if 'graph_definition' in data:
                chatflow.graph_definition = data['graph_definition']
            if 'tags' in data:
                chatflow.tags = data['tags']
            if 'category' in data:
                chatflow.category = data['category']
            if 'is_active' in data:
                chatflow.is_active = data['is_active']
            
            # Handle tools update
            if 'tools' in data and data['tools']:
                # Clear existing tools
                from backend.db.models.flows import ChatflowTool
                db.query(ChatflowTool).filter(
                    ChatflowTool.chatflow_id == chatflow.id
                ).delete()
                
                # Add new tools
                for tool_data in data['tools']:
                    tool = ChatflowTool(
                        chatflow_id=chatflow.id,
                        tool_id=tool_data.get('tool_id', ''),
                        name=tool_data.get('name', ''),
                        description=tool_data.get('description', ''),
                        enabled=tool_data.get('enabled', True),
                        configuration=tool_data.get('configuration', {})
                    )
                    db.add(tool)
            
            chatflow.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(chatflow)
            
            return {
                "id": str(chatflow.id),
                "name": chatflow.name,
                "description": chatflow.description,
                "flow_type": "chatflow",
                "chat_config": chatflow.chat_config,
                "memory_config": chatflow.memory_config,
                "rag_config": chatflow.rag_config,
                "tags": chatflow.tags,
                "category": chatflow.category,
                "is_active": chatflow.is_active,
                "updated_at": chatflow.updated_at.isoformat(),
            }
        
        raise HTTPException(status_code=404, detail="Flow not found")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flow ID")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{flow_id}")
async def delete_flow(
    flow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a flow (soft delete).
    
    Supports both Agentflow and Chatflow.
    """
    try:
        # Try to find as Agentflow first
        agentflow = db.query(Agentflow).filter(
            Agentflow.id == flow_id,
            Agentflow.user_id == current_user.id,
            Agentflow.deleted_at.is_(None)
        ).first()
        
        if agentflow:
            # Soft delete Agentflow
            agentflow.deleted_at = datetime.utcnow()
            agentflow.is_active = False
            db.commit()
            
            return {"message": "Agentflow deleted successfully"}
        
        # Try to find as Chatflow
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == flow_id,
            Chatflow.user_id == current_user.id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if chatflow:
            # Soft delete Chatflow
            chatflow.deleted_at = datetime.utcnow()
            chatflow.is_active = False
            db.commit()
            
            return {"message": "Chatflow deleted successfully"}
        
        raise HTTPException(status_code=404, detail="Flow not found")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flow ID")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{flow_id}/execute", response_model=FlowExecutionResponse)
async def execute_flow(
    flow_id: str,
    request: FlowExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a flow with input data.
    
    Returns execution ID for tracking.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Execute workflow
        execution = facade.execute_workflow(
            workflow_id=int(flow_id),
            user_id=current_user.id,
            input_data=request.input_data
        )
        
        if not execution:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        return FlowExecutionResponse(
            id=str(execution.get('id')),
            flow_id=flow_id,
            flow_type=execution.get('flow_type', 'workflow'),
            status=execution.get('status', 'pending'),
            started_at=execution.get('started_at', ''),
            input_data=request.input_data
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flow ID")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{flow_id}/executions")
async def get_flow_executions(
    flow_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution history for a flow.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get executions
        executions = facade.list_executions(
            workflow_id=int(flow_id),
            user_id=current_user.id,
            skip=offset,
            limit=limit
        )
        
        return {
            "executions": executions,
            "total": len(executions)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flow ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
