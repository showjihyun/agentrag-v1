"""
Workflow Debug API Endpoints

Provides REST API for workflow debugging features:
- Breakpoint management
- Debug session control
- Performance metrics
- Execution history
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.services.agent_builder.workflow_debugger import (
    WorkflowDebugger,
    ExecutionStatus,
    Breakpoint as DebuggerBreakpoint,
)

router = APIRouter(prefix="/debug", tags=["workflow-debug"])

# In-memory debugger instances (in production, use Redis or database)
debugger_sessions: Dict[str, WorkflowDebugger] = {}


# Pydantic Models
class BreakpointCreate(BaseModel):
    node_id: str = Field(..., description="Node ID to set breakpoint")
    condition: Optional[str] = Field(None, description="Optional condition expression")


class BreakpointResponse(BaseModel):
    node_id: str
    enabled: bool
    condition: Optional[str]
    hit_count: int


class ExecutionStateResponse(BaseModel):
    node_id: str
    timestamp: datetime
    status: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str]
    duration_ms: Optional[float]
    memory_mb: Optional[float]
    cpu_percent: Optional[float]


class NodeMetricsResponse(BaseModel):
    node_id: str
    node_name: str
    executions: int
    avg_duration_ms: float
    success_rate: float
    error_rate: float
    avg_memory_mb: float
    avg_cpu_percent: float


class PerformanceMetricsResponse(BaseModel):
    total_duration_ms: float
    avg_duration_ms: float
    success_rate: float
    error_rate: float
    node_metrics: Dict[str, NodeMetricsResponse]


class BottleneckResponse(BaseModel):
    node_id: str
    node_name: str
    percentage: float
    avg_duration_ms: float
    executions: int


class RecommendationResponse(BaseModel):
    type: str
    severity: str
    title: str
    description: str


class DebugSessionResponse(BaseModel):
    is_debugging: bool
    is_paused: bool
    current_node_id: Optional[str]
    breakpoints: List[BreakpointResponse]
    execution_history: List[ExecutionStateResponse]
    performance_metrics: PerformanceMetricsResponse
    bottlenecks: List[BottleneckResponse]
    recommendations: List[RecommendationResponse]


def get_debugger(workflow_id: str) -> WorkflowDebugger:
    """Get or create debugger instance for workflow"""
    if workflow_id not in debugger_sessions:
        debugger_sessions[workflow_id] = WorkflowDebugger()
    return debugger_sessions[workflow_id]


@router.post("/{workflow_id}/start")
async def start_debug_session(
    workflow_id: str
):
    """Start a debug session for workflow"""
    debugger = get_debugger(workflow_id)
    debugger.start_debugging()
    
    return {
        "message": "Debug session started",
        "workflow_id": workflow_id,
        "is_debugging": debugger.is_debugging
    }


@router.post("/{workflow_id}/stop")
async def stop_debug_session(
    workflow_id: str
):
    """Stop debug session"""
    debugger = get_debugger(workflow_id)
    debugger.stop_debugging()
    
    return {
        "message": "Debug session stopped",
        "workflow_id": workflow_id,
        "is_debugging": debugger.is_debugging
    }


@router.post("/{workflow_id}/breakpoints")
async def add_breakpoint(
    workflow_id: str,
    breakpoint: BreakpointCreate
) -> BreakpointResponse:
    """Add a breakpoint"""
    debugger = get_debugger(workflow_id)
    bp = debugger.add_breakpoint(
        node_id=breakpoint.node_id,
        condition=breakpoint.condition
    )
    
    return BreakpointResponse(
        node_id=bp.node_id,
        enabled=bp.enabled,
        condition=bp.condition,
        hit_count=bp.hit_count
    )


@router.delete("/{workflow_id}/breakpoints/{node_id}")
async def remove_breakpoint(
    workflow_id: str,
    node_id: str
):
    """Remove a breakpoint"""
    debugger = get_debugger(workflow_id)
    success = debugger.remove_breakpoint(node_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Breakpoint not found")
    
    return {"message": "Breakpoint removed", "node_id": node_id}


@router.post("/{workflow_id}/breakpoints/{node_id}/toggle")
async def toggle_breakpoint(
    workflow_id: str,
    node_id: str
):
    """Toggle breakpoint enabled state"""
    debugger = get_debugger(workflow_id)
    enabled = debugger.toggle_breakpoint(node_id)
    
    return {
        "message": "Breakpoint toggled",
        "node_id": node_id,
        "enabled": enabled
    }


@router.get("/{workflow_id}/breakpoints")
async def list_breakpoints(
    workflow_id: str
) -> List[BreakpointResponse]:
    """List all breakpoints"""
    debugger = get_debugger(workflow_id)
    
    return [
        BreakpointResponse(
            node_id=bp.node_id,
            enabled=bp.enabled,
            condition=bp.condition,
            hit_count=bp.hit_count
        )
        for bp in debugger.breakpoints.values()
    ]


@router.post("/{workflow_id}/continue")
async def continue_execution(
    workflow_id: str
):
    """Continue execution from pause"""
    debugger = get_debugger(workflow_id)
    debugger.continue_execution()
    
    return {"message": "Execution continued"}


@router.post("/{workflow_id}/step-over")
async def step_over(
    workflow_id: str
):
    """Step over (execute current node and pause at next)"""
    debugger = get_debugger(workflow_id)
    debugger.step_over()
    
    return {"message": "Stepping over"}


@router.post("/{workflow_id}/step-into")
async def step_into(
    workflow_id: str
):
    """Step into (if node has sub-workflow, step into it)"""
    debugger = get_debugger(workflow_id)
    debugger.step_into()
    
    return {"message": "Stepping into"}


@router.get("/{workflow_id}/history")
async def get_execution_history(
    workflow_id: str
) -> List[ExecutionStateResponse]:
    """Get execution history"""
    debugger = get_debugger(workflow_id)
    
    return [
        ExecutionStateResponse(
            node_id=state.node_id,
            timestamp=state.timestamp,
            status=state.status.value,
            input_data=state.input_data,
            output_data=state.output_data,
            error=state.error,
            duration_ms=state.duration_ms,
            memory_mb=state.memory_mb,
            cpu_percent=state.cpu_percent
        )
        for state in debugger.execution_history
    ]


@router.get("/{workflow_id}/current-state")
async def get_current_state(
    workflow_id: str
) -> Optional[ExecutionStateResponse]:
    """Get current execution state"""
    debugger = get_debugger(workflow_id)
    state = debugger.get_current_state()
    
    if not state:
        return None
    
    return ExecutionStateResponse(
        node_id=state.node_id,
        timestamp=state.timestamp,
        status=state.status.value,
        input_data=state.input_data,
        output_data=state.output_data,
        error=state.error,
        duration_ms=state.duration_ms,
        memory_mb=state.memory_mb,
        cpu_percent=state.cpu_percent
    )


@router.get("/{workflow_id}/metrics")
async def get_performance_metrics(
    workflow_id: str
) -> PerformanceMetricsResponse:
    """Get performance metrics"""
    debugger = get_debugger(workflow_id)
    metrics = debugger.get_performance_metrics()
    
    return PerformanceMetricsResponse(
        total_duration_ms=metrics["total_duration_ms"],
        avg_duration_ms=metrics["avg_duration_ms"],
        success_rate=metrics["success_rate"],
        error_rate=metrics["error_rate"],
        node_metrics={
            node_id: NodeMetricsResponse(**node_metrics)
            for node_id, node_metrics in metrics["node_metrics"].items()
        }
    )


@router.get("/{workflow_id}/bottlenecks")
async def get_bottlenecks(
    workflow_id: str,
    threshold_percent: float = 20.0
) -> List[BottleneckResponse]:
    """Get performance bottlenecks"""
    debugger = get_debugger(workflow_id)
    bottlenecks = debugger.identify_bottlenecks(threshold_percent)
    
    return [BottleneckResponse(**b) for b in bottlenecks]


@router.get("/{workflow_id}/recommendations")
async def get_recommendations(
    workflow_id: str
) -> List[RecommendationResponse]:
    """Get optimization recommendations"""
    debugger = get_debugger(workflow_id)
    recommendations = debugger.get_optimization_recommendations()
    
    return [RecommendationResponse(**r) for r in recommendations]


@router.get("/{workflow_id}/session")
async def get_debug_session(
    workflow_id: str
) -> DebugSessionResponse:
    """Get complete debug session data"""
    debugger = get_debugger(workflow_id)
    session_data = debugger.export_debug_session()
    
    return DebugSessionResponse(
        is_debugging=session_data["is_debugging"],
        is_paused=session_data["is_paused"],
        current_node_id=session_data["current_node_id"],
        breakpoints=[BreakpointResponse(**bp) for bp in session_data["breakpoints"]],
        execution_history=[
            ExecutionStateResponse(**state) 
            for state in session_data["execution_history"]
        ],
        performance_metrics=PerformanceMetricsResponse(
            total_duration_ms=session_data["performance_metrics"]["total_duration_ms"],
            avg_duration_ms=session_data["performance_metrics"]["avg_duration_ms"],
            success_rate=session_data["performance_metrics"]["success_rate"],
            error_rate=session_data["performance_metrics"]["error_rate"],
            node_metrics={
                node_id: NodeMetricsResponse(**metrics)
                for node_id, metrics in session_data["performance_metrics"]["node_metrics"].items()
            }
        ),
        bottlenecks=[BottleneckResponse(**b) for b in session_data["bottlenecks"]],
        recommendations=[RecommendationResponse(**r) for r in session_data["recommendations"]]
    )


@router.post("/{workflow_id}/time-travel")
async def time_travel(
    workflow_id: str,
    timestamp: datetime
) -> Optional[ExecutionStateResponse]:
    """Time travel to specific execution state"""
    debugger = get_debugger(workflow_id)
    state = debugger.time_travel(timestamp)
    
    if not state:
        raise HTTPException(status_code=404, detail="Execution state not found")
    
    return ExecutionStateResponse(
        node_id=state.node_id,
        timestamp=state.timestamp,
        status=state.status.value,
        input_data=state.input_data,
        output_data=state.output_data,
        error=state.error,
        duration_ms=state.duration_ms,
        memory_mb=state.memory_mb,
        cpu_percent=state.cpu_percent
    )


@router.delete("/{workflow_id}/session")
async def clear_debug_session(
    workflow_id: str
):
    """Clear debug session data"""
    if workflow_id in debugger_sessions:
        del debugger_sessions[workflow_id]
    
    return {"message": "Debug session cleared", "workflow_id": workflow_id}
