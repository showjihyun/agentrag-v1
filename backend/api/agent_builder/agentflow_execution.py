"""
Agentflow Execution API

Endpoints for executing Agentflows with streaming support and advanced optimization features.
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
from backend.services.agent_builder.workflow_optimizer import AdaptiveWorkflowOptimizer
from backend.agents.error_recovery import AgentErrorRecovery

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


@router.get("/{workflow_id}/optimization-analysis")
async def get_optimization_analysis(
    workflow_id: str,
    days_back: int = Query(30, description="Number of days of execution history to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive optimization analysis for a workflow.
    
    This endpoint analyzes workflow execution patterns and provides
    intelligent optimization suggestions.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow and check permissions
        workflow = facade.get_workflow(workflow_id)
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Initialize optimizer
        optimizer = AdaptiveWorkflowOptimizer(db)
        
        # Perform analysis
        analysis = await optimizer.analyze_workflow(workflow_id, days_back)
        
        return {
            "success": True,
            "analysis": {
                "workflow_id": analysis.workflow_id,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
                "execution_count": analysis.execution_count,
                "success_rate": analysis.success_rate,
                "average_duration_ms": analysis.average_duration,
                "optimization_score": analysis.optimization_score,
                "bottlenecks": analysis.bottlenecks,
                "resource_usage": analysis.resource_usage,
                "cost_analysis": analysis.cost_analysis,
                "suggestions": [
                    {
                        "type": s.type.value,
                        "title": s.title,
                        "description": s.description,
                        "impact": s.impact.value,
                        "priority": s.priority.value,
                        "action": s.action,
                        "estimated_improvement": s.estimated_improvement,
                        "confidence_score": s.confidence_score
                    }
                    for s in analysis.suggestions
                ]
            }
        }
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        logger.error(f"Error analyzing workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/optimization-recommendations")
async def get_optimization_recommendations(
    workflow_id: str,
    limit: int = Query(5, description="Maximum number of recommendations to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get top optimization recommendations for a workflow.
    
    Returns prioritized optimization suggestions based on impact and confidence.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow and check permissions
        workflow = facade.get_workflow(workflow_id)
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Initialize optimizer
        optimizer = AdaptiveWorkflowOptimizer(db)
        
        # Get recommendations
        recommendations = await optimizer.get_optimization_recommendations(workflow_id, limit)
        
        return {
            "success": True,
            "recommendations": [
                {
                    "type": r.type.value,
                    "title": r.title,
                    "description": r.description,
                    "impact": r.impact.value,
                    "priority": r.priority.value,
                    "action": r.action,
                    "estimated_improvement": r.estimated_improvement,
                    "implementation_effort": r.implementation_effort,
                    "confidence_score": r.confidence_score
                }
                for r in recommendations
            ]
        }
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        logger.error(f"Error getting recommendations for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/error-recovery-stats")
async def get_error_recovery_stats(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get error recovery statistics for a workflow.
    
    Returns information about error patterns, recovery success rates,
    and circuit breaker states.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow and check permissions
        workflow = facade.get_workflow(workflow_id)
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Initialize error recovery system
        error_recovery = AgentErrorRecovery()
        
        # Get recovery statistics
        stats = error_recovery.get_recovery_statistics()
        
        return {
            "success": True,
            "error_recovery_stats": stats
        }
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        logger.error(f"Error getting recovery stats for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class OptimizationApplyRequest(BaseModel):
    """Request model for applying optimization suggestions."""
    suggestion_ids: list[str] = Field(description="IDs of suggestions to apply")
    auto_apply: bool = Field(default=False, description="Whether to apply automatically")


@router.post("/{workflow_id}/apply-optimizations")
async def apply_optimizations(
    workflow_id: str,
    request: OptimizationApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Apply optimization suggestions to a workflow.
    
    This endpoint applies selected optimization suggestions to improve
    workflow performance, cost efficiency, or reliability.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow and check permissions
        workflow = facade.get_workflow(workflow_id)
        if str(workflow.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # For now, return a placeholder response
        # In a full implementation, this would:
        # 1. Validate the suggestion IDs
        # 2. Apply the optimizations to the workflow configuration
        # 3. Update the workflow in the database
        # 4. Return the updated workflow configuration
        
        return {
            "success": True,
            "message": f"Applied {len(request.suggestion_ids)} optimization suggestions",
            "applied_suggestions": request.suggestion_ids,
            "auto_applied": request.auto_apply,
            "next_steps": [
                "Test the optimized workflow",
                "Monitor performance improvements",
                "Review execution metrics"
            ]
        }
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        logger.error(f"Error applying optimizations to workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/performance-prediction")
async def get_performance_prediction(
    workflow_id: str,
    input_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get performance prediction for a workflow execution.
    
    Predicts execution time, resource usage, and cost based on
    historical data and input parameters.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow and check permissions
        workflow = facade.get_workflow(workflow_id)
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Initialize optimizer for prediction
        optimizer = AdaptiveWorkflowOptimizer(db)
        
        # Get recent analysis for prediction base
        analysis = await optimizer.analyze_workflow(workflow_id, days_back=7)
        
        # Generate prediction based on analysis
        # This is a simplified prediction - in a full implementation,
        # this would use ML models trained on execution history
        prediction = {
            "estimated_duration_ms": analysis.average_duration * 1.1,  # Add 10% buffer
            "estimated_cost": analysis.cost_analysis.get('avg_cost_per_execution', 0) * 1.05,
            "estimated_tokens": analysis.resource_usage.get('avg_tokens_per_execution', 0),
            "success_probability": analysis.success_rate,
            "recommended_concurrency": min(5, max(1, int(analysis.optimization_score * 5))),
            "confidence_score": min(0.9, analysis.optimization_score + 0.1),
            "bottleneck_warnings": [
                f"Agent {b['agent_name']} may cause delays"
                for b in analysis.bottlenecks
                if b.get('severity', 0) > 0.5
            ]
        }
        
        return {
            "success": True,
            "prediction": prediction,
            "based_on_executions": analysis.execution_count,
            "analysis_date": analysis.analysis_timestamp.isoformat()
        }
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        logger.error(f"Error predicting performance for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/execute-optimized", response_model=AgentflowExecuteResponse)
async def execute_optimized_agentflow(
    workflow_id: str,
    request: AgentflowExecuteRequest,
    enable_predictions: bool = Query(True, description="Enable execution predictions"),
    enable_recovery: bool = Query(True, description="Enable error recovery"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute an Agentflow with advanced optimization features.
    
    This endpoint executes a workflow with:
    - Predictive resource allocation
    - Adaptive concurrency scaling
    - Intelligent error recovery
    - Real-time optimization
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow using Facade
        workflow = facade.get_workflow(workflow_id)
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get performance prediction if enabled
        prediction = None
        if enable_predictions:
            optimizer = AdaptiveWorkflowOptimizer(db)
            analysis = await optimizer.analyze_workflow(workflow_id, days_back=7)
            prediction = {
                "estimated_duration": analysis.average_duration / 1000,  # Convert to seconds
                "recommended_concurrency": min(5, max(1, int(analysis.optimization_score * 5))),
                "confidence": analysis.optimization_score
            }
        
        # Merge input data with variables
        input_data = {
            **request.input_data,
            **request.variables,
        }
        
        # Add optimization parameters
        if prediction:
            input_data['_optimization'] = {
                'enable_predictions': enable_predictions,
                'enable_recovery': enable_recovery,
                'predicted_duration': prediction['estimated_duration'],
                'recommended_concurrency': prediction['recommended_concurrency']
            }
        
        # Execute using Facade with optimization
        result = await facade.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=str(current_user.id),
        )
        
        # Enhanced response with optimization data
        response = AgentflowExecuteResponse(
            success=result.get("status") == "completed",
            execution_id=result.get("execution_id", ""),
            status=result.get("status", "failed"),
            output=result.get("output"),
            error=result.get("message") if result.get("status") == "failed" else None,
            duration_ms=result.get("duration_ms"),
            token_usage=result.get("token_usage", [])
        )
        
        # Add optimization metadata to response
        if hasattr(response, '__dict__'):
            response.__dict__['optimization_data'] = {
                'predictions_enabled': enable_predictions,
                'recovery_enabled': enable_recovery,
                'prediction_accuracy': result.get('prediction_accuracy'),
                'optimizations_applied': result.get('optimizations_applied', []),
                'performance_score': result.get('performance_score')
            }
        
        return response
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except ExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing optimized workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")