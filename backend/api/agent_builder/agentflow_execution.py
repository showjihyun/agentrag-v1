"""
Agentflow Execution API

Endpoints for executing Agentflows with streaming support.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
# DDD Architecture
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.shared.errors import (
    NotFoundError,
    ValidationError,
    ExecutionError,
)
from backend.services.agent_builder.agentflow_executor import AgentflowExecutor

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/agentflows",
    tags=["agentflow-execution"],
)


class AgentflowExecuteRequest(BaseModel):
    """Request model for Agentflow execution."""
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the workflow")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variable overrides")


class AgentflowExecuteResponse(BaseModel):
    """Response model for Agentflow execution."""
    success: bool
    execution_id: str
    status: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    token_usage: Optional[list] = None


@router.post("/{workflow_id}/execute", response_model=AgentflowExecuteResponse)
async def execute_agentflow(
    workflow_id: str,
    request: AgentflowExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute an Agentflow.
    
    This endpoint executes an Agentflow workflow and returns the result.
    For streaming execution, use the /execute/stream endpoint.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow using Facade
        workflow = facade.get_workflow(workflow_id)
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Merge input data with variables
        input_data = {
            **request.input_data,
            **request.variables,
        }
        
        # Execute using Facade
        result = await facade.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=str(current_user.id),
        )
        
        return AgentflowExecuteResponse(
            success=result.get("status") == "completed",
            execution_id=result.get("execution_id", ""),
            status=result.get("status", "failed"),
            output=result.get("output"),
            error=result.get("message") if result.get("status") == "failed" else None,
        )
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except ExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentflow execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/execute/stream")
async def execute_agentflow_stream(
    workflow_id: str,
    request: AgentflowExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute an Agentflow with SSE streaming using DDD Facade.
    
    Returns Server-Sent Events with execution progress:
    - start: Execution started
    - status: Status update
    - node: Node execution completed
    - complete: Execution completed
    - error: Error occurred
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow using Facade
        workflow = facade.get_workflow(workflow_id)
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Merge input data with variables
        input_data = {
            **request.input_data,
            **request.variables,
        }
        
        # Execute with streaming using Facade
        return StreamingResponse(
            facade.execute_workflow_streaming(
                workflow_id=workflow_id,
                input_data=input_data,
                user_id=str(current_user.id),
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentflow streaming execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/executions")
async def list_agentflow_executions(
    workflow_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List executions for an Agentflow.
    """
    try:
        from backend.db.models.agent_builder import WorkflowExecution
        import uuid
        
        # Get workflow
        workflow_service = WorkflowService(db)
        workflow = workflow_service.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Query executions
        query = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == uuid.UUID(workflow_id)
        )
        
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        total = query.count()
        
        executions = query.order_by(
            WorkflowExecution.started_at.desc()
        ).limit(limit).offset(offset).all()
        
        return {
            "executions": [
                {
                    "id": str(e.id),
                    "workflow_id": str(e.workflow_id),
                    "status": e.status,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "duration_ms": int((e.completed_at - e.started_at).total_seconds() * 1000) if e.completed_at and e.started_at else None,
                    "error_message": e.error_message,
                }
                for e in executions
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/executions/{execution_id}")
async def get_agentflow_execution(
    workflow_id: str,
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get details of a specific Agentflow execution.
    """
    try:
        from backend.db.models.agent_builder import WorkflowExecution
        import uuid
        
        # Get execution
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == uuid.UUID(execution_id),
            WorkflowExecution.workflow_id == uuid.UUID(workflow_id),
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Check permissions
        if str(execution.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get token usage for this execution
        from backend.db.models.flows import TokenUsage
        
        token_usage = db.query(TokenUsage).filter(
            TokenUsage.flow_execution_id == uuid.UUID(execution_id)
        ).all()
        
        return {
            "id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_ms": int((execution.completed_at - execution.started_at).total_seconds() * 1000) if execution.completed_at and execution.started_at else None,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "error_message": execution.error_message,
            "execution_context": execution.execution_context,
            "token_usage": [
                {
                    "node_id": t.node_id,
                    "provider": t.provider,
                    "model": t.model,
                    "input_tokens": t.input_tokens,
                    "output_tokens": t.output_tokens,
                    "total_tokens": t.total_tokens,
                    "cost_usd": float(t.cost_usd),
                }
                for t in token_usage
            ],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
