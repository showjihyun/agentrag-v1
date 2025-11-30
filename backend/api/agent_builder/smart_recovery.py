"""
Smart Error Recovery API Endpoints

AI-powered error analysis and recovery for workflows.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from backend.services.agent_builder.smart_error_recovery import (
    get_smart_recovery_service,
    WorkflowError,
    ErrorType,
    RecoveryType,
    ImpactLevel,
)

router = APIRouter(prefix="/smart-recovery", tags=["smart-recovery"])


# Request/Response Models
class ErrorInput(BaseModel):
    node_id: str = Field(..., description="ID of the node that errored")
    node_name: str = Field(..., description="Name of the node")
    node_type: str = Field(..., description="Type of the node")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code if available")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    retry_count: int = Field(0, description="Current retry count")
    max_retries: int = Field(3, description="Maximum retries allowed")


class AnalyzeErrorRequest(BaseModel):
    error: ErrorInput
    workflow_context: Optional[Dict[str, Any]] = Field(None, description="Workflow context")
    available_fallbacks: Optional[List[str]] = Field(None, description="Available fallback services")
    has_cache: bool = Field(False, description="Whether cached response is available")


class RecoveryOptionResponse(BaseModel):
    id: str
    type: str
    title: str
    description: str
    confidence: float
    estimated_time: Optional[str]
    is_recommended: bool
    requires_input: bool
    input_label: Optional[str]


class AIAnalysisResponse(BaseModel):
    summary: str
    root_cause: str
    impact: str
    similar_errors: int
    suggested_fix: Optional[str]
    code_snippet: Optional[str]
    documentation: Optional[str]


class AnalyzeErrorResponse(BaseModel):
    error_id: str
    error_type: str
    analysis: AIAnalysisResponse
    recovery_options: List[RecoveryOptionResponse]


class ExecuteRecoveryRequest(BaseModel):
    error_id: str = Field(..., description="ID of the error")
    recovery_type: str = Field(..., description="Type of recovery to execute")
    input_data: Optional[str] = Field(None, description="Manual input data if required")


class ExecuteRecoveryResponse(BaseModel):
    success: bool
    message: str
    result: Optional[Dict[str, Any]]


class ErrorPatternResponse(BaseModel):
    pattern_hash: str
    error_type: str
    node_type: str
    message_pattern: str
    occurrence_count: int
    successful_recoveries: Dict[str, int]
    last_seen: str


@router.post("/analyze", response_model=AnalyzeErrorResponse)
async def analyze_error(request: AnalyzeErrorRequest):
    """
    Analyze an error and get AI-powered recovery suggestions.
    
    This endpoint:
    1. Classifies the error type
    2. Generates AI analysis with root cause and impact
    3. Suggests recovery options ranked by confidence
    """
    service = get_smart_recovery_service()
    
    # Create WorkflowError object
    error_type = service.classify_error(
        request.error.message,
        request.error.error_code
    )
    
    error = WorkflowError(
        id=str(uuid.uuid4()),
        node_id=request.error.node_id,
        node_name=request.error.node_name,
        node_type=request.error.node_type,
        error_type=error_type,
        message=request.error.message,
        error_code=request.error.error_code,
        stack_trace=request.error.stack_trace,
        context=request.error.context,
        retry_count=request.error.retry_count,
        max_retries=request.error.max_retries,
    )
    
    # Get AI analysis
    analysis = await service.analyze_error_with_ai(error, request.workflow_context)
    
    # Generate recovery options
    recovery_options = service.generate_recovery_options(
        error,
        available_fallbacks=request.available_fallbacks,
        has_cache=request.has_cache,
    )
    
    return AnalyzeErrorResponse(
        error_id=error.id,
        error_type=error_type.value,
        analysis=AIAnalysisResponse(
            summary=analysis.summary,
            root_cause=analysis.root_cause,
            impact=analysis.impact.value,
            similar_errors=analysis.similar_errors,
            suggested_fix=analysis.suggested_fix,
            code_snippet=analysis.code_snippet,
            documentation=analysis.documentation,
        ),
        recovery_options=[
            RecoveryOptionResponse(
                id=opt.id,
                type=opt.type.value,
                title=opt.title,
                description=opt.description,
                confidence=opt.confidence,
                estimated_time=opt.estimated_time,
                is_recommended=opt.is_recommended,
                requires_input=opt.requires_input,
                input_label=opt.input_label,
            )
            for opt in recovery_options
        ]
    )


@router.post("/execute", response_model=ExecuteRecoveryResponse)
async def execute_recovery(request: ExecuteRecoveryRequest):
    """
    Execute a recovery action for an error.
    
    Supported recovery types:
    - retry_with_backoff: Retry with exponential backoff
    - use_fallback: Switch to fallback service
    - use_cache: Use cached response
    - skip_node: Skip the errored node
    - manual_input: Use manually provided input
    - modify_config: Modify node configuration
    """
    service = get_smart_recovery_service()
    
    try:
        recovery_type = RecoveryType(request.recovery_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid recovery type: {request.recovery_type}"
        )
    
    # Create a minimal error object for recovery
    error = WorkflowError(
        id=request.error_id,
        node_id="",
        node_name="",
        node_type="",
        error_type=ErrorType.UNKNOWN,
        message="",
    )
    
    success, message, result = await service.execute_recovery(
        error,
        recovery_type,
        request.input_data,
    )
    
    # Record the result for learning
    service.record_recovery_result(error, recovery_type, success)
    
    return ExecuteRecoveryResponse(
        success=success,
        message=message,
        result=result,
    )


@router.get("/patterns", response_model=List[ErrorPatternResponse])
async def get_error_patterns(
    limit: int = 50,
    min_occurrences: int = 1,
):
    """
    Get learned error patterns.
    
    Returns patterns sorted by occurrence count, useful for:
    - Understanding common errors
    - Identifying recurring issues
    - Improving error handling
    """
    service = get_smart_recovery_service()
    
    patterns = sorted(
        service.error_patterns.values(),
        key=lambda p: p.occurrence_count,
        reverse=True
    )
    
    filtered = [p for p in patterns if p.occurrence_count >= min_occurrences][:limit]
    
    return [
        ErrorPatternResponse(
            pattern_hash=p.pattern_hash,
            error_type=p.error_type.value,
            node_type=p.node_type,
            message_pattern=p.message_pattern,
            occurrence_count=p.occurrence_count,
            successful_recoveries={k.value: v for k, v in p.successful_recoveries.items()},
            last_seen=p.last_seen.isoformat(),
        )
        for p in filtered
    ]


@router.get("/statistics")
async def get_recovery_statistics():
    """
    Get error recovery statistics.
    
    Returns:
    - Total errors analyzed
    - Recovery success rate
    - Most common error types
    - Most effective recovery methods
    """
    service = get_smart_recovery_service()
    
    # Calculate statistics
    total_patterns = len(service.error_patterns)
    total_occurrences = sum(p.occurrence_count for p in service.error_patterns.values())
    
    # Error type distribution
    error_type_counts: Dict[str, int] = {}
    for pattern in service.error_patterns.values():
        error_type = pattern.error_type.value
        error_type_counts[error_type] = error_type_counts.get(error_type, 0) + pattern.occurrence_count
    
    # Recovery success rates
    recovery_stats: Dict[str, Dict[str, int]] = {}
    for pattern in service.error_patterns.values():
        for recovery_type, count in pattern.successful_recoveries.items():
            rt = recovery_type.value
            if rt not in recovery_stats:
                recovery_stats[rt] = {"success": 0, "total": 0}
            recovery_stats[rt]["success"] += count
            recovery_stats[rt]["total"] += count
    
    # Recent recovery history
    recent_recoveries = service.recovery_history[-100:]
    success_count = sum(1 for r in recent_recoveries if r["success"])
    
    return {
        "total_patterns": total_patterns,
        "total_occurrences": total_occurrences,
        "error_type_distribution": error_type_counts,
        "recovery_statistics": recovery_stats,
        "recent_recovery_rate": success_count / len(recent_recoveries) if recent_recoveries else 0,
        "recent_recoveries_count": len(recent_recoveries),
    }


@router.post("/classify")
async def classify_error(
    message: str,
    error_code: Optional[str] = None,
):
    """
    Classify an error message into an error type.
    
    Useful for:
    - Testing error classification
    - Understanding how errors are categorized
    """
    service = get_smart_recovery_service()
    error_type = service.classify_error(message, error_code)
    
    return {
        "error_type": error_type.value,
        "message": message,
        "error_code": error_code,
    }


@router.delete("/patterns/{pattern_hash}")
async def delete_error_pattern(pattern_hash: str):
    """Delete a learned error pattern."""
    service = get_smart_recovery_service()
    
    if pattern_hash not in service.error_patterns:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    del service.error_patterns[pattern_hash]
    
    return {"message": "Pattern deleted", "pattern_hash": pattern_hash}


@router.post("/patterns/clear")
async def clear_error_patterns():
    """Clear all learned error patterns."""
    service = get_smart_recovery_service()
    service.error_patterns.clear()
    service.recovery_history.clear()
    
    return {"message": "All patterns cleared"}
