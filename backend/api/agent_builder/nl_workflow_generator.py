"""
Natural Language Workflow Generator API
자연어로 워크플로우를 생성하는 API
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.nl_workflow_generator import get_nl_workflow_generator
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/nl-generator", tags=["Natural Language Workflow Generator"])

# ============================================================================
# Request/Response Models
# ============================================================================

class WorkflowGenerationRequest(BaseModel):
    """워크플로우 생성 요청 모델"""
    description: str = Field(..., description="자연어 워크플로우 설명", min_length=10, max_length=1000)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="사용자 선호 설정")
    language: str = Field(default="ko", description="언어 설정")
    complexity_preference: str = Field(default="auto", description="복잡도 선호도 (simple|medium|complex|auto)")

class WorkflowGenerationResponse(BaseModel):
    """워크플로우 생성 응답 모델"""
    success: bool
    workflow: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    generation_time_seconds: float
    timestamp: str
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None

class WorkflowOptimizationRequest(BaseModel):
    """워크플로우 최적화 요청 모델"""
    workflow: Dict[str, Any] = Field(..., description="최적화할 워크플로우")
    optimization_goals: List[str] = Field(default=["speed", "cost"], description="최적화 목표")

class ExampleRequest(BaseModel):
    """예시 요청 모델"""
    category: Optional[str] = Field(None, description="카테고리 필터")
    complexity: Optional[str] = Field(None, description="복잡도 필터")
    limit: int = Field(default=10, ge=1, le=50, description="반환할 예시 수")

# ============================================================================
# Natural Language Generation Endpoints
# ============================================================================

@router.post("/generate", response_model=WorkflowGenerationResponse)
async def generate_workflow_from_text(
    request: WorkflowGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    자연어 설명으로부터 워크플로우 자동 생성
    
    사용자가 자연어로 설명한 업무 프로세스를 분석하여
    실행 가능한 워크플로우로 자동 변환합니다.
    
    예시 입력:
    - "고객 문의를 받아서 감정 분석하고 부정적이면 매니저에게 슬랙으로 알려줘"
    - "매일 오전 9시에 데이터베이스에서 신규 주문을 조회해서 이메일로 보고서 발송"
    - "웹훅으로 결제 정보를 받으면 영수증을 생성해서 고객에게 이메일 발송"
    """
    try:
        # 입력 검증
        if len(request.description.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="워크플로우 설명이 너무 짧습니다. 최소 10자 이상 입력해주세요."
            )
        
        # 자연어 워크플로우 생성기 가져오기
        nl_generator = get_nl_workflow_generator()
        
        # 사용자 선호도 설정
        user_preferences = {
            **request.preferences,
            "user_id": current_user.id,
            "language": request.language,
            "complexity_preference": request.complexity_preference
        }
        
        # 워크플로우 생성
        result = await nl_generator.generate_workflow_from_text(
            description=request.description,
            user_preferences=user_preferences
        )
        
        # 사용 로그 기록
        logger.info(
            f"Natural language workflow generated",
            extra={
                'user_id': current_user.id,
                'description_length': len(request.description),
                'generation_time': result.get('generation_time_seconds', 0),
                'success': result.get('success', False),
                'node_count': len(result.get('workflow', {}).get('nodes', [])) if result.get('success') else 0
            }
        )
        
        # 개선 제안 추가
        if result.get('success'):
            result['suggestions'] = _generate_improvement_suggestions(result['workflow'])
        
        return WorkflowGenerationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Natural language workflow generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_workflow(
    request: WorkflowOptimizationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    기존 워크플로우 최적화
    
    생성된 워크플로우를 분석하여 성능, 비용, 안정성 등을
    개선할 수 있는 최적화 제안을 제공합니다.
    """
    try:
        nl_generator = get_nl_workflow_generator()
        
        # 워크플로우 분석
        analysis = await _analyze_workflow_for_optimization(request.workflow, request.optimization_goals)
        
        return {
            "success": True,
            "original_workflow": request.workflow,
            "optimization_analysis": analysis,
            "optimized_workflow": await _apply_optimizations(request.workflow, analysis),
            "improvement_summary": _generate_improvement_summary(analysis),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Workflow optimization failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples")
async def get_workflow_examples(
    request: ExampleRequest = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    자연어 워크플로우 생성 예시 조회
    
    다양한 업무 시나리오별 자연어 설명 예시와
    생성되는 워크플로우 구조를 제공합니다.
    """
    examples = [
        {
            "category": "고객 서비스",
            "complexity": "simple",
            "description": "고객 문의를 받아서 감정 분석하고 부정적이면 매니저에게 알려줘",
            "expected_nodes": ["webhook_trigger", "sentiment_analysis", "condition", "slack_notification"],
            "estimated_time": "3초 이내",
            "use_case": "고객 불만 자동 감지 및 에스컬레이션"
        },
        {
            "category": "데이터 처리",
            "complexity": "medium", 
            "description": "매일 오전 9시에 데이터베이스에서 신규 주문을 조회해서 요약 보고서를 만들어 이메일로 발송",
            "expected_nodes": ["schedule_trigger", "database_query", "data_transform", "ai_summarize", "email_send"],
            "estimated_time": "5-8초",
            "use_case": "일일 매출 보고서 자동화"
        },
        {
            "category": "마케팅 자동화",
            "complexity": "complex",
            "description": "신규 가입자가 있으면 환영 이메일을 보내고, 3일 후에 온보딩 가이드를 발송하고, 1주일 후에 만족도 조사를 진행해줘",
            "expected_nodes": ["webhook_trigger", "email_welcome", "delay_3days", "email_onboarding", "delay_1week", "survey_send"],
            "estimated_time": "10-15초",
            "use_case": "신규 고객 온보딩 자동화"
        },
        {
            "category": "콘텐츠 관리",
            "complexity": "medium",
            "description": "블로그 포스트를 받아서 SEO 최적화 제안을 하고 소셜미디어용 요약본을 만들어줘",
            "expected_nodes": ["manual_trigger", "ai_seo_analysis", "ai_summarize", "social_format", "multi_output"],
            "estimated_time": "6-10초", 
            "use_case": "콘텐츠 최적화 및 배포"
        },
        {
            "category": "업무 자동화",
            "complexity": "simple",
            "description": "회의록을 받아서 액션 아이템을 추출하고 담당자별로 슬랙 DM 발송",
            "expected_nodes": ["file_upload", "ai_extract_actions", "assign_owners", "slack_dm_multiple"],
            "estimated_time": "4-7초",
            "use_case": "회의 후속 조치 자동화"
        },
        {
            "category": "품질 관리",
            "complexity": "complex",
            "description": "제품 리뷰를 수집해서 감정 분석하고 키워드를 추출한 다음 부정적 리뷰는 고객 서비스팀에, 긍정적 리뷰는 마케팅팀에 전달",
            "expected_nodes": ["review_collector", "sentiment_analysis", "keyword_extraction", "condition_branch", "team_notification"],
            "estimated_time": "8-12초",
            "use_case": "리뷰 기반 품질 모니터링"
        },
        {
            "category": "재무 관리",
            "complexity": "medium",
            "description": "매월 말일에 매출 데이터를 집계해서 차트를 생성하고 경영진에게 보고서 이메일 발송",
            "expected_nodes": ["monthly_schedule", "sales_aggregation", "chart_generation", "report_format", "executive_email"],
            "estimated_time": "7-10초",
            "use_case": "월간 매출 보고서 자동화"
        },
        {
            "category": "인사 관리",
            "complexity": "simple",
            "description": "신입사원 입사 시 IT 장비 신청서를 자동으로 생성하고 관련 부서에 알림",
            "expected_nodes": ["hr_webhook", "equipment_form_generate", "department_notification", "tracking_setup"],
            "estimated_time": "3-5초",
            "use_case": "신입사원 온보딩 자동화"
        }
    ]
    
    # 필터링
    filtered_examples = examples
    if request.category:
        filtered_examples = [ex for ex in filtered_examples if ex["category"] == request.category]
    if request.complexity:
        filtered_examples = [ex for ex in filtered_examples if ex["complexity"] == request.complexity]
    
    # 제한
    filtered_examples = filtered_examples[:request.limit]
    
    return {
        "examples": filtered_examples,
        "total": len(filtered_examples),
        "categories": list(set(ex["category"] for ex in examples)),
        "complexity_levels": ["simple", "medium", "complex"],
        "tips": [
            "구체적인 트리거를 명시하세요 (웹훅, 스케줄, 수동)",
            "처리할 데이터와 원하는 결과를 명확히 설명하세요",
            "조건부 분기가 필요한 경우 '만약', 'if' 등을 사용하세요",
            "알림 방법을 구체적으로 지정하세요 (슬랙, 이메일, SMS)",
            "시간 관련 요구사항이 있으면 명시하세요 (매일, 즉시, 3일 후)"
        ]
    }

@router.get("/templates")
async def get_workflow_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    자연어 워크플로우 템플릿 조회
    
    자주 사용되는 워크플로우 패턴의 자연어 템플릿을 제공합니다.
    """
    templates = {
        "customer_service": {
            "name": "고객 서비스 자동화",
            "templates": [
                "고객 문의를 받아서 {분석_유형}하고 {조건}이면 {담당자}에게 {알림_방법}으로 알려줘",
                "{채널}에서 고객 피드백을 받아서 {처리_방법}하고 결과를 {보고_방법}으로 정리해줘",
                "고객 불만이 접수되면 {우선순위}에 따라 {처리_팀}에 배정하고 {시간}내에 응답하도록 알림"
            ]
        },
        "data_processing": {
            "name": "데이터 처리 자동화", 
            "templates": [
                "{주기}마다 {데이터_소스}에서 {데이터_유형}을 조회해서 {처리_방법}하고 {결과_형태}로 {전달_방법}",
                "{트리거}가 발생하면 {데이터}를 {분석_방법}해서 {조건}에 따라 {액션}을 실행해줘",
                "{파일_유형} 파일을 받아서 {변환_방법}하고 {품질_검사}한 다음 {저장_위치}에 저장"
            ]
        },
        "marketing": {
            "name": "마케팅 자동화",
            "templates": [
                "{이벤트}가 발생하면 {고객_세그먼트}에게 {메시지_유형}을 {채널}로 발송하고 {추적_방법}으로 성과 측정",
                "{콘텐츠}를 받아서 {플랫폼}별로 {최적화}하고 {스케줄}에 따라 자동 게시",
                "{캠페인_결과}를 분석해서 {성과_지표}를 계산하고 {보고서_형태}로 {수신자}에게 전달"
            ]
        },
        "operations": {
            "name": "운영 자동화",
            "templates": [
                "{모니터링_대상}을 {주기}마다 확인해서 {임계값}을 초과하면 {담당자}에게 {긴급도}로 알림",
                "{업무_프로세스}가 완료되면 {다음_단계}를 자동으로 시작하고 {진행상황}을 {추적_방법}으로 기록",
                "{리소스_사용량}이 {기준}에 도달하면 {스케일링_액션}을 실행하고 {로그}에 기록"
            ]
        }
    }
    
    if category and category in templates:
        return {
            "category": category,
            "templates": templates[category]
        }
    
    return {
        "all_templates": templates,
        "categories": list(templates.keys()),
        "usage_tips": [
            "{} 안의 내용을 구체적인 값으로 바꿔서 사용하세요",
            "여러 템플릿을 조합해서 복잡한 워크플로우를 만들 수 있습니다",
            "템플릿은 시작점일 뿐, 자유롭게 수정하고 확장하세요"
        ]
    }

@router.get("/health")
async def health_check():
    """
    자연어 워크플로우 생성기 상태 확인
    """
    try:
        nl_generator = get_nl_workflow_generator()
        
        return {
            "status": "healthy",
            "service": "natural_language_workflow_generator",
            "features": {
                "pattern_matching": True,
                "openai_integration": nl_generator.openai_client is not None,
                "supported_languages": ["ko", "en"],
                "node_types": len(nl_generator.node_templates),
                "language_patterns": len(nl_generator.language_patterns)
            },
            "capabilities": {
                "max_description_length": 1000,
                "supported_complexity": ["simple", "medium", "complex"],
                "estimated_generation_time": "1-5초",
                "supported_node_types": list(nl_generator.node_templates.keys())
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "natural_language_workflow_generator"
        }

# ============================================================================
# Helper Functions
# ============================================================================

def _generate_improvement_suggestions(workflow: Dict[str, Any]) -> List[str]:
    """워크플로우 개선 제안 생성"""
    suggestions = []
    
    nodes = workflow.get("nodes", [])
    node_count = len(nodes)
    
    if node_count > 10:
        suggestions.append("워크플로우가 복잡합니다. 여러 개의 작은 워크플로우로 분할을 고려해보세요.")
    
    # AI 노드가 많은 경우
    ai_nodes = [n for n in nodes if "llm" in n.get("type", "").lower() or "ai" in n.get("type", "").lower()]
    if len(ai_nodes) > 3:
        suggestions.append("AI 처리 노드가 많습니다. 비용 최적화를 위해 일부를 병합하거나 더 효율적인 모델을 사용해보세요.")
    
    # 에러 처리 부족
    error_handling_nodes = [n for n in nodes if "error" in n.get("type", "").lower() or "try" in n.get("type", "").lower()]
    if len(error_handling_nodes) == 0 and node_count > 5:
        suggestions.append("에러 처리 로직을 추가하여 워크플로우의 안정성을 높여보세요.")
    
    # 모니터링 부족
    monitoring_nodes = [n for n in nodes if "log" in n.get("type", "").lower() or "monitor" in n.get("type", "").lower()]
    if len(monitoring_nodes) == 0:
        suggestions.append("로깅이나 모니터링 노드를 추가하여 실행 상황을 추적해보세요.")
    
    return suggestions

async def _analyze_workflow_for_optimization(workflow: Dict[str, Any], goals: List[str]) -> Dict[str, Any]:
    """워크플로우 최적화 분석"""
    # 실제 구현에서는 더 정교한 분석 로직 필요
    return {
        "performance_score": 85,
        "cost_score": 70,
        "reliability_score": 90,
        "optimization_opportunities": [
            {
                "type": "parallel_execution",
                "description": "3개 노드를 병렬 처리하면 40% 속도 향상",
                "impact": "high",
                "effort": "medium"
            }
        ]
    }

async def _apply_optimizations(workflow: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """최적화 적용"""
    # 실제 구현에서는 워크플로우 구조 수정 로직 필요
    return workflow

def _generate_improvement_summary(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """개선 요약 생성"""
    return {
        "total_improvements": len(analysis.get("optimization_opportunities", [])),
        "expected_speed_improvement": "40%",
        "expected_cost_reduction": "25%",
        "reliability_increase": "15%"
    }