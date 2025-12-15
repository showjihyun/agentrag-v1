"""
Gemini MultiModal Workflow Templates API
즉시 사용 가능한 멀티모달 워크플로우 템플릿 API
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.templates.gemini_templates import GeminiWorkflowTemplates
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/gemini-templates", tags=["Gemini Templates"])

# ============================================================================
# Request/Response Models
# ============================================================================

class TemplateResponse(BaseModel):
    """워크플로우 템플릿 응답 모델"""
    name: str
    description: str
    category: str
    tags: List[str]
    icon: str
    estimated_time: str
    difficulty: str
    nodes: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    roi_metrics: Dict[str, Any]
    created_at: str

class TemplateListResponse(BaseModel):
    """템플릿 목록 응답 모델"""
    templates: List[TemplateResponse]
    total: int
    categories: List[str]
    tags: List[str]

class CreateWorkflowRequest(BaseModel):
    """템플릿으로부터 워크플로우 생성 요청"""
    template_name: str
    workflow_name: Optional[str] = None
    customizations: Optional[Dict[str, Any]] = None

# ============================================================================
# Template Endpoints
# ============================================================================

@router.get("/", response_model=TemplateListResponse)
async def get_gemini_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    current_user: User = Depends(get_current_user)
):
    """
    Gemini 멀티모달 워크플로우 템플릿 목록 조회
    
    Query Parameters:
    - category: business_automation, productivity, ecommerce, customer_support
    - difficulty: beginner, intermediate, advanced
    """
    try:
        # 모든 템플릿 가져오기
        all_templates = GeminiWorkflowTemplates.get_all_templates()
        
        # 필터링
        filtered_templates = all_templates
        
        if category:
            filtered_templates = [t for t in filtered_templates if t.get('category') == category]
            
        if difficulty:
            filtered_templates = [t for t in filtered_templates if t.get('difficulty') == difficulty]
        
        # 메타데이터 추출
        categories = list(set(t.get('category', 'general') for t in all_templates))
        all_tags = []
        for t in all_templates:
            all_tags.extend(t.get('tags', []))
        unique_tags = list(set(all_tags))
        
        return TemplateListResponse(
            templates=[TemplateResponse(**template) for template in filtered_templates],
            total=len(filtered_templates),
            categories=categories,
            tags=unique_tags
        )
        
    except Exception as e:
        logger.error(f"Failed to get Gemini templates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_template_categories(
    current_user: User = Depends(get_current_user)
):
    """
    템플릿 카테고리 목록 조회
    """
    try:
        categories = [
            {
                "id": "business_automation",
                "name": "비즈니스 자동화",
                "description": "영수증 처리, 문서 분석 등 업무 자동화",
                "icon": "🏢",
                "count": 1
            },
            {
                "id": "productivity", 
                "name": "생산성 향상",
                "description": "회의록, 요약, 번역 등 생산성 도구",
                "icon": "⚡",
                "count": 1
            },
            {
                "id": "ecommerce",
                "name": "이커머스",
                "description": "제품 카탈로그, 리뷰 분석 등",
                "icon": "🛒",
                "count": 1
            },
            {
                "id": "customer_support",
                "name": "고객 지원",
                "description": "실시간 지원, 문제 해결 자동화",
                "icon": "🎧",
                "count": 1
            }
        ]
        
        return {
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Failed to get template categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/popular")
async def get_popular_templates(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    """
    인기 템플릿 조회 (사용량 기반)
    """
    try:
        # 초보자용 템플릿을 인기 템플릿으로 반환
        popular_templates = GeminiWorkflowTemplates.get_beginner_templates()
        
        # 제한된 수만 반환
        limited_templates = popular_templates[:limit]
        
        return {
            "templates": [TemplateResponse(**template) for template in limited_templates],
            "total": len(limited_templates)
        }
        
    except Exception as e:
        logger.error(f"Failed to get popular templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{template_name}")
async def get_template_detail(
    template_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    특정 템플릿 상세 정보 조회
    """
    try:
        all_templates = GeminiWorkflowTemplates.get_all_templates()
        
        # 템플릿 이름으로 찾기
        template = None
        for t in all_templates:
            if t['name'].replace(' ', '_').lower() == template_name.replace(' ', '_').lower():
                template = t
                break
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        return TemplateResponse(**template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Workflow Creation from Templates
# ============================================================================

@router.post("/create-workflow")
async def create_workflow_from_template(
    request: CreateWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    템플릿으로부터 새 워크플로우 생성
    
    템플릿을 기반으로 사용자 맞춤형 워크플로우를 생성합니다.
    """
    try:
        # 템플릿 찾기
        all_templates = GeminiWorkflowTemplates.get_all_templates()
        template = None
        
        for t in all_templates:
            if t['name'].replace(' ', '_').lower() == request.template_name.replace(' ', '_').lower():
                template = t
                break
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{request.template_name}' not found")
        
        # 워크플로우 이름 생성
        workflow_name = request.workflow_name or f"{template['name']} - {current_user.username}"
        
        # 템플릿 커스터마이징 적용
        customized_template = template.copy()
        if request.customizations:
            # 노드 설정 업데이트
            for node in customized_template['nodes']:
                node_id = node['id']
                if node_id in request.customizations:
                    node['config'].update(request.customizations[node_id])
        
        # 워크플로우 생성 (실제 DB 저장은 별도 구현 필요)
        workflow_data = {
            "name": workflow_name,
            "description": f"Generated from template: {template['name']}",
            "template_source": request.template_name,
            "nodes": customized_template['nodes'],
            "connections": customized_template['connections'],
            "created_by": current_user.id,
            "category": template.get('category', 'general'),
            "tags": template.get('tags', []) + ['generated', 'gemini'],
            "estimated_execution_time": template.get('estimated_time', 'Unknown'),
            "roi_metrics": template.get('roi_metrics', {})
        }
        
        logger.info(
            f"Workflow created from template",
            extra={
                'user_id': current_user.id,
                'template_name': request.template_name,
                'workflow_name': workflow_name
            }
        )
        
        return {
            "success": True,
            "workflow": workflow_data,
            "message": f"Workflow '{workflow_name}' created successfully from template"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workflow from template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Template Analytics
# ============================================================================

@router.get("/analytics/usage")
async def get_template_usage_analytics(
    current_user: User = Depends(get_current_user)
):
    """
    템플릿 사용 분석 데이터
    """
    try:
        # 모의 분석 데이터 (실제로는 DB에서 조회)
        analytics = {
            "most_used_templates": [
                {"name": "영수증 자동 처리", "usage_count": 150, "success_rate": 0.95},
                {"name": "회의록 자동 생성", "usage_count": 120, "success_rate": 0.92},
                {"name": "제품 카탈로그 자동 생성", "usage_count": 80, "success_rate": 0.88},
                {"name": "스마트 고객 지원", "usage_count": 45, "success_rate": 0.85}
            ],
            "category_distribution": {
                "business_automation": 40,
                "productivity": 35,
                "ecommerce": 15,
                "customer_support": 10
            },
            "total_workflows_created": 395,
            "average_success_rate": 0.90,
            "time_saved_hours": 1250
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get template analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Gemini 템플릿 서비스 상태 확인
    """
    try:
        # 템플릿 로딩 테스트
        templates = GeminiWorkflowTemplates.get_all_templates()
        
        return {
            "status": "healthy",
            "service": "gemini_templates",
            "templates_available": len(templates),
            "categories": len(set(t.get('category') for t in templates)),
            "timestamp": "2024-12-12T10:00:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "gemini_templates"
        }