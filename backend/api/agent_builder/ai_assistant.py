"""
AI Assistant API Endpoints

Provides AI-powered assistance for workflow development
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from backend.services.agent_builder.ai_assistant import (
    AIAssistant,
    ErrorDiagnosis as AIErrorDiagnosis,
    BreakpointSuggestion as AIBreakpointSuggestion,
    OptimizationSuggestion as AIOptimizationSuggestion,
)
from backend.services.agent_builder.workflow_debugger import (
    WorkflowDebugger,
    ExecutionState,
    ExecutionStatus,
)

router = APIRouter(prefix="/ai-assistant", tags=["ai-assistant"])

# Global instances
ai_assistant = AIAssistant()
debugger_sessions: Dict[str, WorkflowDebugger] = {}


# Pydantic Models
class ErrorDiagnosisRequest(BaseModel):
    workflow_id: str
    error_message: str
    node_id: str
    workflow_context: Dict[str, Any] = Field(default_factory=dict)


class ErrorDiagnosisResponse(BaseModel):
    error_type: str
    root_cause: str
    explanation: str
    suggested_fixes: List[str]
    related_nodes: List[str]
    confidence: float


class BreakpointSuggestionResponse(BaseModel):
    node_id: str
    reason: str
    priority: str
    condition: Optional[str]


class OptimizationSuggestionResponse(BaseModel):
    node_id: str
    issue: str
    suggestion: str
    expected_improvement: str
    implementation_difficulty: str
    code_example: Optional[str]


class DebugQueryRequest(BaseModel):
    workflow_id: str
    query: str
    workflow_context: Dict[str, Any] = Field(default_factory=dict)


class DebugQueryResponse(BaseModel):
    answer: str
    confidence: float = 0.8


def get_debugger(workflow_id: str) -> WorkflowDebugger:
    """Get or create debugger instance"""
    if workflow_id not in debugger_sessions:
        debugger_sessions[workflow_id] = WorkflowDebugger()
    return debugger_sessions[workflow_id]


@router.post("/diagnose-error")
async def diagnose_error(
    request: ErrorDiagnosisRequest,
    
) -> ErrorDiagnosisResponse:
    """
    Diagnose error using AI
    
    Analyzes error message and execution context to provide:
    - Root cause analysis
    - Detailed explanation
    - Suggested fixes
    - Related nodes that might be affected
    """
    debugger = get_debugger(request.workflow_id)
    
    # Get current execution state
    current_state = debugger.get_current_state()
    
    if not current_state:
        # Create mock state for diagnosis
        current_state = ExecutionState(
            node_id=request.node_id,
            timestamp=datetime.now(),
            status=ExecutionStatus.ERROR,
            error=request.error_message
        )
    
    # Get AI diagnosis
    diagnosis = await ai_assistant.diagnose_error(
        error_message=request.error_message,
        execution_state=current_state,
        workflow_context=request.workflow_context
    )
    
    return ErrorDiagnosisResponse(
        error_type=diagnosis.error_type,
        root_cause=diagnosis.root_cause,
        explanation=diagnosis.explanation,
        suggested_fixes=diagnosis.suggested_fixes,
        related_nodes=diagnosis.related_nodes,
        confidence=diagnosis.confidence
    )


@router.get("/{workflow_id}/suggest-breakpoints")
async def suggest_breakpoints(
    workflow_id: str,
    
) -> List[BreakpointSuggestionResponse]:
    """
    Get AI-suggested breakpoints
    
    Analyzes execution history to suggest strategic breakpoints
    that would help debug issues.
    """
    debugger = get_debugger(workflow_id)
    
    # Get workflow context (in production, fetch from database)
    workflow_context = {
        "workflow_id": workflow_id,
        "total_nodes": len(set(s.node_id for s in debugger.execution_history))
    }
    
    # Get AI suggestions
    suggestions = await ai_assistant.suggest_breakpoints(
        debugger=debugger,
        workflow_context=workflow_context
    )
    
    return [
        BreakpointSuggestionResponse(
            node_id=s.node_id,
            reason=s.reason,
            priority=s.priority,
            condition=s.condition
        )
        for s in suggestions
    ]


@router.get("/{workflow_id}/predict-bottlenecks")
async def predict_bottlenecks(
    workflow_id: str,
    
) -> List[Dict[str, Any]]:
    """
    Predict potential bottlenecks
    
    Uses AI to predict nodes that might become bottlenecks
    as the workflow scales.
    """
    debugger = get_debugger(workflow_id)
    
    workflow_context = {
        "workflow_id": workflow_id,
        "execution_count": len(debugger.execution_history)
    }
    
    predictions = await ai_assistant.predict_bottlenecks(
        debugger=debugger,
        workflow_context=workflow_context
    )
    
    return predictions


@router.post("/debug-query")
async def answer_debug_query(
    request: DebugQueryRequest,
    
) -> DebugQueryResponse:
    """
    Answer natural language debugging query
    
    Ask questions like:
    - "Why did node-3 fail?"
    - "Which node is taking the most time?"
    - "How can I optimize this workflow?"
    """
    debugger = get_debugger(request.workflow_id)
    
    answer = await ai_assistant.answer_debug_query(
        query=request.query,
        debugger=debugger,
        workflow_context=request.workflow_context
    )
    
    return DebugQueryResponse(answer=answer)


@router.get("/{workflow_id}/suggest-optimizations")
async def suggest_optimizations(
    workflow_id: str,
    
) -> List[OptimizationSuggestionResponse]:
    """
    Get AI-suggested optimizations
    
    Analyzes bottlenecks and suggests specific code optimizations
    with expected improvements.
    """
    debugger = get_debugger(workflow_id)
    
    workflow_context = {
        "workflow_id": workflow_id,
        "total_executions": len(debugger.execution_history)
    }
    
    suggestions = await ai_assistant.suggest_optimizations(
        debugger=debugger,
        workflow_context=workflow_context
    )
    
    return [
        OptimizationSuggestionResponse(
            node_id=s.node_id,
            issue=s.issue,
            suggestion=s.suggestion,
            expected_improvement=s.expected_improvement,
            implementation_difficulty=s.implementation_difficulty,
            code_example=s.code_example
        )
        for s in suggestions
    ]


@router.get("/{workflow_id}/explain-execution")
async def explain_execution_flow(
    workflow_id: str,
    
) -> Dict[str, str]:
    """
    Get natural language explanation of execution flow
    
    Returns a human-readable explanation of what happened
    during workflow execution.
    """
    debugger = get_debugger(workflow_id)
    
    workflow_context = {
        "workflow_id": workflow_id
    }
    
    explanation = await ai_assistant.explain_execution_flow(
        debugger=debugger,
        workflow_context=workflow_context
    )
    
    return {"explanation": explanation}


@router.delete("/{workflow_id}/session")
async def clear_ai_session(
    workflow_id: str,
    
):
    """Clear AI assistant session data"""
    if workflow_id in debugger_sessions:
        del debugger_sessions[workflow_id]
    
    return {"message": "AI session cleared", "workflow_id": workflow_id}


# Import datetime for mock state
from datetime import datetime
