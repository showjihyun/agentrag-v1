"""Agent Builder API endpoints for Natural Language Workflow Generation."""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.nlp_workflow_service import (
    NLPWorkflowService,
    GenerationResult,
    NODE_SCHEMAS,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/workflow-nlp",
    tags=["agent-builder-workflow-nlp"],
)


class NLPGenerateRequest(BaseModel):
    """Request for NLP workflow generation."""
    description: str = Field(..., min_length=10, max_length=2000, description="Natural language description")
    language: str = Field(default="ko", description="Output language (ko, en)")
    use_llm: bool = Field(default=True, description="Use LLM for generation (fallback to rules if False)")


class NLPRefineRequest(BaseModel):
    """Request for workflow refinement."""
    workflow: Dict[str, Any] = Field(..., description="Current workflow definition")
    refinement: str = Field(..., min_length=5, description="Refinement request")
    language: str = Field(default="ko")


class NodeInfo(BaseModel):
    """Node information."""
    id: str
    type: str
    label: str
    config: Dict[str, Any]
    position: Dict[str, int]


class EdgeInfo(BaseModel):
    """Edge information."""
    id: str
    source: str
    target: str
    label: Optional[str] = None


class NLPGenerateResponse(BaseModel):
    """Response from NLP workflow generation."""
    success: bool
    workflow_name: str
    workflow_description: str
    graph_definition: Dict[str, Any]
    explanation: str
    confidence: float
    suggestions: List[str]
    complexity: str
    estimated_execution_time: str
    error: Optional[str] = None


class NodeSchemaResponse(BaseModel):
    """Node schema information."""
    type: str
    category: str
    description: str
    config_schema: Dict[str, str]


def _result_to_response(result: GenerationResult) -> NLPGenerateResponse:
    """Convert GenerationResult to API response."""
    nodes = [
        {
            "id": n.id,
            "type": n.type,
            "position": n.position,
            "data": {
                "label": n.label,
                **n.config,
            },
        }
        for n in result.nodes
    ]
    
    edges = [
        {
            "id": e.id,
            "source": e.source,
            "target": e.target,
            **({"label": e.label} if e.label else {}),
            **({"sourceHandle": e.source_handle} if e.source_handle else {}),
        }
        for e in result.edges
    ]
    
    return NLPGenerateResponse(
        success=result.success,
        workflow_name=result.workflow_name,
        workflow_description=result.workflow_description,
        graph_definition={
            "nodes": nodes,
            "edges": edges,
        },
        explanation=result.explanation,
        confidence=result.confidence,
        suggestions=result.suggestions,
        complexity=result.complexity.value,
        estimated_execution_time=result.estimated_execution_time,
        error=result.error,
    )


@router.post("/generate", response_model=NLPGenerateResponse)
async def generate_workflow_from_nlp(
    request: NLPGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a workflow from natural language description.
    
    Uses LLM (GPT-4o-mini) for intelligent workflow generation with:
    - Intent analysis
    - Structured output generation
    - Automatic validation and fixing
    - Confidence scoring
    
    Examples:
    - "매일 아침 뉴스를 검색해서 요약한 후 슬랙으로 보내줘"
    - "웹훅으로 데이터를 받아서 AI로 분석하고 데이터베이스에 저장해"
    - "사용자 질문을 받아서 관련 문서를 검색하고 AI로 답변을 생성해"
    
    **Request Body:**
    - description: Natural language description (10-2000 chars)
    - language: Output language (ko, en)
    - use_llm: Use LLM generation (default: True)
    
    **Returns:**
    - Generated workflow with nodes and edges
    - Confidence score
    - Improvement suggestions
    """
    try:
        logger.info(f"Generating workflow from NLP: {request.description[:100]}...")
        
        service = NLPWorkflowService()
        
        if request.use_llm:
            result = await service.generate_workflow(
                description=request.description,
                language=request.language,
                user_id=str(current_user.id),
            )
        else:
            result = await service._fallback_generation(
                description=request.description,
                language=request.language,
            )
        
        logger.info(f"Generated workflow: {result.workflow_name}, confidence: {result.confidence}")
        
        return _result_to_response(result)
        
    except Exception as e:
        logger.error(f"Failed to generate workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow generation failed: {str(e)}"
        )


@router.post("/refine", response_model=NLPGenerateResponse)
async def refine_workflow(
    request: NLPRefineRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Refine an existing workflow based on user feedback.
    
    Takes the current workflow and a refinement request, then uses LLM
    to modify the workflow accordingly.
    
    Examples:
    - "에러 처리 추가해줘"
    - "병렬 실행으로 변경해줘"
    - "슬랙 대신 이메일로 보내줘"
    
    **Request Body:**
    - workflow: Current workflow definition
    - refinement: Refinement request
    - language: Output language
    
    **Returns:**
    - Refined workflow
    """
    try:
        logger.info(f"Refining workflow: {request.refinement[:100]}...")
        
        service = NLPWorkflowService()
        result = await service.refine_workflow(
            workflow_data=request.workflow,
            refinement_request=request.refinement,
            language=request.language,
        )
        
        return _result_to_response(result)
        
    except Exception as e:
        logger.error(f"Failed to refine workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow refinement failed: {str(e)}"
        )


@router.get("/nodes")
async def get_available_nodes(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user),
):
    """
    Get available node types for workflow generation.
    
    **Query Parameters:**
    - category: Filter by category (trigger, ai, search, data, etc.)
    
    **Returns:**
    - List of available node types with schemas
    """
    nodes = []
    
    for node_type, schema in NODE_SCHEMAS.items():
        if category and schema["category"] != category:
            continue
        
        nodes.append({
            "type": node_type,
            "category": schema["category"],
            "description": schema["description"],
            "config_schema": schema["config_schema"],
        })
    
    # Group by category
    categories = {}
    for node in nodes:
        cat = node["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(node)
    
    return {
        "nodes": nodes,
        "by_category": categories,
        "total": len(nodes),
    }


@router.post("/suggest")
async def suggest_next_nodes(
    current_nodes: List[str] = [],
    partial_description: str = "",
    current_user: User = Depends(get_current_user),
):
    """
    Suggest next nodes based on current workflow state.
    
    **Request Body:**
    - current_nodes: List of current node types
    - partial_description: Partial description for context
    
    **Returns:**
    - Suggested next nodes with reasons
    """
    suggestions = []
    
    # Rule-based suggestions
    if not current_nodes or "manual_trigger" in current_nodes[-1:]:
        # After trigger, suggest data fetching or AI
        suggestions.extend([
            {"type": "http_request", "reason": "외부 API에서 데이터 가져오기"},
            {"type": "tavily_search", "reason": "웹 검색으로 정보 수집"},
            {"type": "postgresql_query", "reason": "데이터베이스에서 데이터 조회"},
        ])
    
    if any("search" in n for n in current_nodes):
        suggestions.extend([
            {"type": "openai_chat", "reason": "검색 결과를 AI로 분석/요약"},
            {"type": "transform", "reason": "검색 결과 데이터 변환"},
        ])
    
    if any("openai" in n or "claude" in n for n in current_nodes):
        suggestions.extend([
            {"type": "slack", "reason": "AI 결과를 Slack으로 전송"},
            {"type": "sendgrid", "reason": "AI 결과를 이메일로 전송"},
            {"type": "postgresql_query", "reason": "AI 결과를 데이터베이스에 저장"},
        ])
    
    if any("http" in n for n in current_nodes):
        suggestions.extend([
            {"type": "transform", "reason": "API 응답 데이터 변환"},
            {"type": "condition", "reason": "응답에 따른 조건 분기"},
        ])
    
    # Always suggest end if we have enough nodes
    if len(current_nodes) >= 3:
        suggestions.append({"type": "end", "reason": "워크플로우 완료"})
    
    # Remove duplicates
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s["type"] not in seen and s["type"] not in current_nodes:
            seen.add(s["type"])
            unique_suggestions.append(s)
    
    return {
        "suggestions": unique_suggestions[:5],
        "current_node_count": len(current_nodes),
    }


@router.post("/validate")
async def validate_workflow(
    workflow: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """
    Validate a workflow structure.
    
    Checks for:
    - Proper trigger node
    - Proper end node
    - All nodes connected
    - Valid node types
    - Required configurations
    
    **Request Body:**
    - workflow: Workflow definition to validate
    
    **Returns:**
    - Validation result with errors and warnings
    """
    errors = []
    warnings = []
    
    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])
    
    if not nodes:
        errors.append("워크플로우에 노드가 없습니다")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # Check trigger
    trigger_types = {"manual_trigger", "schedule_trigger", "webhook_trigger"}
    has_trigger = any(n.get("type") in trigger_types for n in nodes)
    if not has_trigger:
        errors.append("트리거 노드가 필요합니다 (manual_trigger, schedule_trigger, webhook_trigger)")
    
    # Check end
    end_types = {"end", "webhook_response"}
    has_end = any(n.get("type") in end_types for n in nodes)
    if not has_end:
        warnings.append("종료 노드(end)를 추가하는 것이 좋습니다")
    
    # Check node types
    node_ids = set()
    for node in nodes:
        node_id = node.get("id")
        node_type = node.get("type")
        
        if not node_id:
            errors.append("노드에 ID가 없습니다")
        else:
            node_ids.add(node_id)
        
        if node_type not in NODE_SCHEMAS:
            warnings.append(f"알 수 없는 노드 타입: {node_type}")
    
    # Check connectivity
    connected_nodes = set()
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        
        if source not in node_ids:
            errors.append(f"엣지의 소스 노드를 찾을 수 없습니다: {source}")
        if target not in node_ids:
            errors.append(f"엣지의 타겟 노드를 찾을 수 없습니다: {target}")
        
        connected_nodes.add(source)
        connected_nodes.add(target)
    
    # Check for disconnected nodes
    disconnected = node_ids - connected_nodes
    if disconnected and len(nodes) > 1:
        warnings.append(f"연결되지 않은 노드가 있습니다: {', '.join(disconnected)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


@router.post("/create-from-generation")
async def create_workflow_from_generation(
    name: str,
    graph_definition: Dict[str, Any],
    description: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a workflow from generated graph definition.
    
    **Request Body:**
    - name: Workflow name
    - graph_definition: Generated graph (nodes and edges)
    - description: Optional description
    
    **Returns:**
    - Created workflow ID
    """
    try:
        from backend.services.agent_builder.workflow_service import WorkflowService
        from backend.models.agent_builder import WorkflowCreate
        
        workflow_service = WorkflowService(db)
        
        workflow_data = WorkflowCreate(
            name=name,
            description=description,
            graph_definition=graph_definition,
            is_public=False,
        )
        
        workflow = workflow_service.create_workflow(
            user_id=str(current_user.id),
            workflow_data=workflow_data,
        )
        
        return {
            "workflow_id": str(workflow.id),
            "name": workflow.name,
            "message": "워크플로우가 생성되었습니다",
        }
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"워크플로우 생성 실패: {str(e)}"
        )
