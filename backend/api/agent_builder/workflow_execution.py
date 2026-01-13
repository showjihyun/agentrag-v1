"""
Workflow Execution API
워크플로우 실행 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime

from backend.models.user import User
from backend.core.dependencies import get_current_user
from backend.core.security.orchestration_security import OrchestrationSecurity
from backend.core.cache.orchestration_cache import OrchestrationCache
from backend.services.agent_builder.workflow_execution_service import (
    WorkflowExecutionService,
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    WorkflowNodeType,
    WorkflowExecutionStatus,
    workflow_execution_service
)
from backend.core.error_handling.plugin_errors import (
    PluginException,
    PluginErrorCode,
    handle_plugin_errors
)

router = APIRouter(prefix="/workflow-execution", tags=["Workflow Execution"])


@router.post("/execute")
@handle_plugin_errors(attempt_recovery=True, max_retries=2)
async def execute_workflow(
    workflow_data: Dict[str, Any],
    input_data: Dict[str, Any] = None,
    execution_mode: str = "async",
    timeout_seconds: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a workflow
    
    Args:
        workflow_data: Workflow definition (nodes and edges)
        input_data: Input data for the workflow
        execution_mode: "sync", "async", or "streaming"
        timeout_seconds: Execution timeout in seconds
        current_user: Current authenticated user
    
    Returns:
        Execution result or streaming response
    """
    try:
        # Security validation
        security_result = await OrchestrationSecurity.validate_execution_request(
            workflow_data, input_data or {}, current_user
        )
        
        if not security_result.allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Execution not allowed: {security_result.reason}"
            )
        
        # Parse workflow definition
        workflow = _parse_workflow_definition(workflow_data)
        
        # Cache key for similar executions
        cache_key = f"workflow_execution:{workflow.id}:{hash(str(input_data))}"
        
        # Check cache for recent similar executions (if not streaming)
        if execution_mode != "streaming":
            cached_result = await OrchestrationCache.get(cache_key)
            if cached_result:
                return {
                    "cached": True,
                    "result": cached_result,
                    "message": "Result retrieved from cache"
                }
        
        # Execute workflow
        result = await workflow_execution_service.execute_workflow(
            workflow=workflow,
            input_data=input_data or {},
            user_id=current_user.id,
            execution_mode=execution_mode,
            timeout_seconds=timeout_seconds
        )
        
        # Handle streaming response
        if execution_mode == "streaming":
            async def stream_generator():
                async for update in result:
                    yield f"data: {json.dumps(update.__dict__, default=str)}\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        
        # Cache successful results
        if result.status == WorkflowExecutionStatus.COMPLETED:
            await OrchestrationCache.set(
                cache_key, 
                result.__dict__, 
                ttl_seconds=3600  # 1 hour
            )
        
        return {
            "success": True,
            "result": result.__dict__,
            "execution_id": result.execution_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/execute-async")
async def execute_workflow_async(
    workflow_data: Dict[str, Any],
    input_data: Dict[str, Any] = None,
    timeout_seconds: Optional[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user)
):
    """
    Execute workflow asynchronously in background
    
    Returns execution ID immediately, actual execution runs in background
    """
    try:
        # Security validation
        security_result = await OrchestrationSecurity.validate_execution_request(
            workflow_data, input_data or {}, current_user
        )
        
        if not security_result.allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Execution not allowed: {security_result.reason}"
            )
        
        # Parse workflow
        workflow = _parse_workflow_definition(workflow_data)
        
        # Generate execution ID
        execution_id = f"async_workflow_{workflow.id}_{int(datetime.now().timestamp())}"
        
        # Add background task
        background_tasks.add_task(
            _execute_workflow_background,
            workflow,
            input_data or {},
            current_user.id,
            execution_id,
            timeout_seconds
        )
        
        return {
            "success": True,
            "execution_id": execution_id,
            "message": "Workflow execution started in background",
            "status_endpoint": f"/workflow-execution/status/{execution_id}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start async execution: {str(e)}"
        )


@router.get("/status/{execution_id}")
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get workflow execution status"""
    try:
        status = workflow_execution_service.get_execution_status(execution_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found"
            )
        
        # Check if user has access to this execution
        if status.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this execution"
            )
        
        return {
            "success": True,
            "execution_id": execution_id,
            "status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution status: {str(e)}"
        )


@router.post("/cancel/{execution_id}")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel workflow execution"""
    try:
        # Check if user has access to this execution
        status = workflow_execution_service.get_execution_status(execution_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found"
            )
        
        if status.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this execution"
            )
        
        # Cancel execution
        success = await workflow_execution_service.cancel_workflow_execution(execution_id)
        
        if success:
            return {
                "success": True,
                "message": f"Execution {execution_id} cancelled successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to cancel execution {execution_id}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel execution: {str(e)}"
        )


@router.get("/validate")
async def validate_workflow(
    workflow_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Validate workflow definition"""
    try:
        # Parse workflow
        workflow = _parse_workflow_definition(workflow_data)
        
        # Basic validation
        validation_errors = []
        validation_warnings = []
        validation_suggestions = []
        
        # Check for required nodes
        input_nodes = [n for n in workflow.nodes if n.type == WorkflowNodeType.INPUT]
        output_nodes = [n for n in workflow.nodes if n.type == WorkflowNodeType.OUTPUT]
        
        if not input_nodes:
            validation_warnings.append("No input node found. Consider adding an input node.")
        
        if not output_nodes:
            validation_warnings.append("No output node found. Consider adding an output node.")
        
        # Check for disconnected nodes
        connected_nodes = set()
        for edge in workflow.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        disconnected_nodes = [n.id for n in workflow.nodes if n.id not in connected_nodes]
        if disconnected_nodes:
            validation_warnings.append(f"Disconnected nodes found: {', '.join(disconnected_nodes)}")
        
        # Check for circular dependencies
        try:
            workflow_execution_service._topological_sort(
                workflow_execution_service._build_execution_graph(workflow)
            )
        except ValueError as e:
            validation_errors.append(str(e))
        
        # Performance analysis
        estimated_time = len(workflow.nodes) * 2.0  # Rough estimate
        performance_level = "excellent" if estimated_time < 10 else "good" if estimated_time < 30 else "fair"
        
        # Security check
        security_risk = "low"
        security_warnings = []
        
        # Check for potentially risky nodes
        risky_nodes = [n for n in workflow.nodes if n.type in [WorkflowNodeType.TOOL, WorkflowNodeType.AGENT]]
        if len(risky_nodes) > 5:
            security_risk = "medium"
            security_warnings.append("Many external tool/agent nodes detected. Review permissions carefully.")
        
        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": validation_warnings,
            "suggestions": validation_suggestions,
            "security": {
                "risk_level": security_risk,
                "warnings": security_warnings
            },
            "performance": {
                "estimated_execution_time": estimated_time,
                "performance_level": performance_level,
                "resource_usage": "moderate",
                "optimization_suggestions": [
                    "Consider parallel execution for independent nodes",
                    "Cache results of expensive operations"
                ] if estimated_time > 20 else []
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow validation failed: {str(e)}"
        )


@router.get("/statistics")
async def get_execution_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get workflow execution statistics"""
    try:
        stats = workflow_execution_service.get_execution_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/templates")
async def get_workflow_templates():
    """Get predefined workflow templates"""
    templates = [
        {
            "id": "simple_llm_chain",
            "name": "Simple LLM Chain",
            "description": "Basic workflow with input -> LLM -> output",
            "category": "Basic",
            "nodes": [
                {
                    "id": "input_1",
                    "type": "input",
                    "position": {"x": 100, "y": 100},
                    "data": {"label": "Input"}
                },
                {
                    "id": "llm_1",
                    "type": "llm",
                    "position": {"x": 300, "y": 100},
                    "data": {
                        "label": "LLM",
                        "model": "gpt-3.5-turbo",
                        "prompt": "Process this input: {input}"
                    }
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "position": {"x": 500, "y": 100},
                    "data": {"label": "Output"}
                }
            ],
            "edges": [
                {
                    "id": "edge_1",
                    "source": "input_1",
                    "target": "llm_1"
                },
                {
                    "id": "edge_2",
                    "source": "llm_1",
                    "target": "output_1"
                }
            ]
        },
        {
            "id": "search_and_summarize",
            "name": "Search and Summarize",
            "description": "Search web and summarize results with LLM",
            "category": "Research",
            "nodes": [
                {
                    "id": "input_1",
                    "type": "input",
                    "position": {"x": 100, "y": 100},
                    "data": {"label": "Search Query"}
                },
                {
                    "id": "search_1",
                    "type": "tool",
                    "position": {"x": 300, "y": 100},
                    "data": {
                        "label": "Web Search",
                        "toolType": "web_search"
                    }
                },
                {
                    "id": "llm_1",
                    "type": "llm",
                    "position": {"x": 500, "y": 100},
                    "data": {
                        "label": "Summarizer",
                        "model": "gpt-3.5-turbo",
                        "prompt": "Summarize these search results: {search_results}"
                    }
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "position": {"x": 700, "y": 100},
                    "data": {"label": "Summary"}
                }
            ],
            "edges": [
                {
                    "id": "edge_1",
                    "source": "input_1",
                    "target": "search_1"
                },
                {
                    "id": "edge_2",
                    "source": "search_1",
                    "target": "llm_1"
                },
                {
                    "id": "edge_3",
                    "source": "llm_1",
                    "target": "output_1"
                }
            ]
        }
    ]
    
    return {
        "success": True,
        "templates": templates
    }


# Helper functions
def _parse_workflow_definition(workflow_data: Dict[str, Any]) -> WorkflowDefinition:
    """Parse workflow definition from request data"""
    try:
        nodes = []
        for node_data in workflow_data.get("nodes", []):
            node = WorkflowNode(
                id=node_data["id"],
                type=WorkflowNodeType(node_data["type"]),
                position=node_data.get("position", {"x": 0, "y": 0}),
                data=node_data.get("data", {})
            )
            nodes.append(node)
        
        edges = []
        for edge_data in workflow_data.get("edges", []):
            edge = WorkflowEdge(
                id=edge_data["id"],
                source=edge_data["source"],
                target=edge_data["target"],
                source_handle=edge_data.get("sourceHandle"),
                target_handle=edge_data.get("targetHandle"),
                data=edge_data.get("data", {})
            )
            edges.append(edge)
        
        return WorkflowDefinition(
            id=workflow_data.get("id", f"workflow_{int(datetime.now().timestamp())}"),
            name=workflow_data.get("name", "Untitled Workflow"),
            description=workflow_data.get("description", ""),
            nodes=nodes,
            edges=edges,
            metadata=workflow_data.get("metadata", {})
        )
        
    except Exception as e:
        raise ValueError(f"Invalid workflow definition: {str(e)}")


async def _execute_workflow_background(
    workflow: WorkflowDefinition,
    input_data: Dict[str, Any],
    user_id: str,
    execution_id: str,
    timeout_seconds: Optional[int]
):
    """Execute workflow in background task"""
    try:
        result = await workflow_execution_service.execute_workflow(
            workflow=workflow,
            input_data=input_data,
            user_id=user_id,
            execution_mode="async",
            timeout_seconds=timeout_seconds
        )
        
        # Store result for later retrieval
        # In a real implementation, you'd store this in a database
        print(f"Background execution {execution_id} completed: {result.status}")
        
    except Exception as e:
        print(f"Background execution {execution_id} failed: {str(e)}")