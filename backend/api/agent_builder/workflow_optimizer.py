"""
Workflow Optimizer API Endpoints

AI-powered workflow optimization suggestions and application.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from backend.services.agent_builder.ai_workflow_optimizer import (
    get_workflow_optimizer,
    OptimizationType,
)

router = APIRouter(prefix="/workflow-optimizer", tags=["workflow-optimizer"])


# Request/Response Models
class WorkflowNode(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowEdge(BaseModel):
    source: str
    target: str
    data: Optional[Dict[str, Any]] = None


class AnalyzeRequest(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")
    nodes: List[Dict[str, Any]] = Field(..., description="Workflow nodes")
    edges: List[Dict[str, Any]] = Field(..., description="Workflow edges")


class ImpactResponse(BaseModel):
    level: str
    time_reduction: Optional[float] = None
    cost_reduction: Optional[float] = None


class SuggestionResponse(BaseModel):
    id: str
    type: str
    title: str
    description: str
    impact: ImpactResponse
    affected_nodes: List[str]
    estimated_savings: Optional[Dict[str, str]] = None
    auto_applicable: bool
    applied: bool
    details: Optional[str] = None


class MetricsResponse(BaseModel):
    total_nodes: int
    estimated_duration: str
    estimated_cost: str
    parallelizable_nodes: int
    cacheable_nodes: int
    redundant_nodes: int


class AnalyzeResponse(BaseModel):
    workflow_id: str
    suggestions: List[SuggestionResponse]
    metrics: MetricsResponse


class ApplyRequest(BaseModel):
    workflow_id: str
    suggestion_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class ApplyResponse(BaseModel):
    success: bool
    message: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class ApplyAllRequest(BaseModel):
    workflow_id: str
    suggestion_ids: List[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_workflow(request: AnalyzeRequest):
    """
    Analyze a workflow and get optimization suggestions.
    
    Returns:
    - Parallelization opportunities
    - Caching recommendations
    - Redundant node detection
    - Cost optimization suggestions
    - Error handling gaps
    - Timeout adjustments
    """
    optimizer = get_workflow_optimizer()
    
    suggestions, metrics = optimizer.analyze_workflow(
        nodes=request.nodes,
        edges=request.edges,
    )
    
    return AnalyzeResponse(
        workflow_id=request.workflow_id,
        suggestions=[
            SuggestionResponse(
                id=s.id,
                type=s.type.value,
                title=s.title,
                description=s.description,
                impact=ImpactResponse(
                    level=s.impact.level.value,
                    time_reduction=s.impact.time_reduction,
                    cost_reduction=s.impact.cost_reduction,
                ),
                affected_nodes=s.affected_nodes,
                estimated_savings=s.estimated_savings,
                auto_applicable=s.auto_applicable,
                applied=s.applied,
                details=s.details,
            )
            for s in suggestions
        ],
        metrics=MetricsResponse(
            total_nodes=metrics.total_nodes,
            estimated_duration=metrics.estimated_duration,
            estimated_cost=metrics.estimated_cost,
            parallelizable_nodes=metrics.parallelizable_nodes,
            cacheable_nodes=metrics.cacheable_nodes,
            redundant_nodes=metrics.redundant_nodes,
        ),
    )


@router.post("/apply", response_model=ApplyResponse)
async def apply_optimization(request: ApplyRequest):
    """
    Apply a single optimization suggestion to a workflow.
    
    Returns the modified workflow nodes and edges.
    """
    optimizer = get_workflow_optimizer()
    
    try:
        modified_nodes, modified_edges = await optimizer.apply_optimization(
            workflow_id=request.workflow_id,
            suggestion_id=request.suggestion_id,
            nodes=request.nodes,
            edges=request.edges,
        )
        
        return ApplyResponse(
            success=True,
            message="최적화가 적용되었습니다.",
            nodes=modified_nodes,
            edges=modified_edges,
        )
    except Exception as e:
        return ApplyResponse(
            success=False,
            message=f"최적화 적용 실패: {str(e)}",
            nodes=request.nodes,
            edges=request.edges,
        )


@router.post("/apply-all", response_model=ApplyResponse)
async def apply_all_optimizations(request: ApplyAllRequest):
    """
    Apply multiple optimization suggestions to a workflow.
    
    Applies suggestions in order, each building on the previous result.
    """
    optimizer = get_workflow_optimizer()
    
    current_nodes = request.nodes
    current_edges = request.edges
    applied_count = 0
    
    for suggestion_id in request.suggestion_ids:
        try:
            current_nodes, current_edges = await optimizer.apply_optimization(
                workflow_id=request.workflow_id,
                suggestion_id=suggestion_id,
                nodes=current_nodes,
                edges=current_edges,
            )
            applied_count += 1
        except Exception:
            continue  # Skip failed optimizations
    
    return ApplyResponse(
        success=applied_count > 0,
        message=f"{applied_count}개의 최적화가 적용되었습니다.",
        nodes=current_nodes,
        edges=current_edges,
    )


@router.get("/types")
async def get_optimization_types():
    """
    Get all available optimization types with descriptions.
    """
    return {
        "types": [
            {
                "id": OptimizationType.PARALLELIZATION.value,
                "name": "병렬화",
                "description": "독립적인 노드들을 병렬로 실행하여 전체 실행 시간을 단축합니다.",
            },
            {
                "id": OptimizationType.CACHING.value,
                "name": "캐싱",
                "description": "반복되는 요청의 결과를 캐시하여 비용과 시간을 절약합니다.",
            },
            {
                "id": OptimizationType.REDUNDANT_REMOVAL.value,
                "name": "중복 제거",
                "description": "중복되거나 불필요한 노드를 식별하고 제거합니다.",
            },
            {
                "id": OptimizationType.BATCH_PROCESSING.value,
                "name": "배치 처리",
                "description": "여러 요청을 하나의 배치로 묶어 효율성을 높입니다.",
            },
            {
                "id": OptimizationType.COST_OPTIMIZATION.value,
                "name": "비용 최적화",
                "description": "더 저렴한 대안을 제안하여 운영 비용을 절감합니다.",
            },
            {
                "id": OptimizationType.ERROR_HANDLING.value,
                "name": "에러 처리",
                "description": "에러 처리가 누락된 노드에 재시도 및 폴백 로직을 추가합니다.",
            },
            {
                "id": OptimizationType.TIMEOUT_ADJUSTMENT.value,
                "name": "타임아웃 조정",
                "description": "적절한 타임아웃 값을 설정하여 안정성을 향상시킵니다.",
            },
        ]
    }


@router.post("/estimate")
async def estimate_savings(request: AnalyzeRequest):
    """
    Estimate potential savings from applying all optimizations.
    """
    optimizer = get_workflow_optimizer()
    
    suggestions, metrics = optimizer.analyze_workflow(
        nodes=request.nodes,
        edges=request.edges,
    )
    
    total_time_savings = sum(
        s.impact.time_reduction or 0 
        for s in suggestions
    )
    total_cost_savings = sum(
        s.impact.cost_reduction or 0 
        for s in suggestions
    )
    
    return {
        "workflow_id": request.workflow_id,
        "current_metrics": metrics.to_dict(),
        "potential_savings": {
            "time_seconds": total_time_savings,
            "cost_dollars": total_cost_savings,
            "suggestion_count": len(suggestions),
        },
        "optimized_metrics": {
            "estimated_duration": f"{float(metrics.estimated_duration.replace('초', '')) - total_time_savings:.1f}초",
            "estimated_cost": f"${float(metrics.estimated_cost.replace('$', '')) - total_cost_savings:.3f}",
        },
    }
