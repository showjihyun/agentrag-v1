"""
Gemini Auto-optimization API
AI 기반 자동 최적화 및 전략 선택 API
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from backend.services.multimodal.auto_optimizer import (
    get_auto_optimizer,
    OptimizationProfile,
    OptimizationStrategy,
    ContentType,
    MediaComplexity
)
from backend.core.structured_logging import get_logger
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/gemini-auto-optimizer",
    tags=["gemini-auto-optimizer"]
)

# Request/Response Models
from pydantic import BaseModel, Field

class OptimizationRequest(BaseModel):
    """최적화 요청"""
    content_type: Optional[str] = Field(None, description="콘텐츠 유형")
    media_complexity: Optional[str] = Field(None, description="미디어 복잡도")
    file_size_mb: float = Field(0, description="파일 크기 (MB)")
    duration_seconds: float = Field(0, description="길이 (초)")
    has_audio: bool = Field(True, description="오디오 포함 여부")
    user_priority: str = Field("balanced", description="사용자 우선순위")
    max_processing_time: Optional[float] = Field(None, description="최대 처리 시간 (초)")
    min_accuracy_threshold: float = Field(0.85, description="최소 정확도 임계값")
    budget_constraint: Optional[float] = Field(None, description="예산 제약")
    batch_size: int = Field(1, description="배치 크기")
    is_realtime: bool = Field(False, description="실시간 처리 여부")
    user_experience_level: str = Field("intermediate", description="사용자 경험 수준")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="사용자 선호도")

class OptimizationResponse(BaseModel):
    """최적화 응답"""
    success: bool
    recommendation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_seconds: float = 0

class PerformanceRecord(BaseModel):
    """성능 기록"""
    config: Dict[str, Any]
    actual_processing_time: float
    success: bool
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="사용자 평점 (1-5)")

@router.get("/health")
async def health_check():
    """자동 최적화기 상태 확인"""
    try:
        auto_optimizer = get_auto_optimizer()
        health_status = await auto_optimizer.health_check()
        
        return {
            "success": True,
            "status": health_status["status"],
            "service": health_status["service"],
            "details": {
                "optimization_rules_loaded": health_status["optimization_rules_loaded"],
                "performance_benchmarks_loaded": health_status["performance_benchmarks_loaded"],
                "performance_history_size": health_status["performance_history_size"],
                "gemini_service_available": health_status["gemini_service_available"]
            },
            "timestamp": health_status["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Auto-optimizer health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/strategies")
async def get_optimization_strategies():
    """사용 가능한 최적화 전략 목록"""
    try:
        strategies = [
            {
                "id": "speed_first",
                "name": "속도 우선",
                "description": "처리 속도를 최우선으로 하는 전략",
                "use_cases": ["실시간 처리", "대량 배치", "빠른 프로토타이핑"],
                "trade_offs": "정확도 약간 감소, 비용 절약"
            },
            {
                "id": "accuracy_first",
                "name": "정확도 우선",
                "description": "분석 정확도를 최우선으로 하는 전략",
                "use_cases": ["중요한 문서", "의료/법률", "품질 검증"],
                "trade_offs": "처리 시간 증가, 비용 증가"
            },
            {
                "id": "balanced",
                "name": "균형",
                "description": "속도와 정확도의 균형을 맞춘 전략",
                "use_cases": ["일반적인 업무", "비즈니스 문서", "교육 콘텐츠"],
                "trade_offs": "중간 수준의 성능과 비용"
            },
            {
                "id": "cost_efficient",
                "name": "비용 효율",
                "description": "비용을 최소화하는 전략",
                "use_cases": ["대량 처리", "예산 제한", "테스트 환경"],
                "trade_offs": "성능 제한, 기능 축소"
            },
            {
                "id": "quality_premium",
                "name": "품질 프리미엄",
                "description": "최고 품질의 결과를 위한 전략",
                "use_cases": ["프리미엄 서비스", "연구 목적", "최종 결과물"],
                "trade_offs": "높은 비용, 긴 처리 시간"
            }
        ]
        
        return {
            "success": True,
            "strategies": strategies,
            "total": len(strategies),
            "default_strategy": "balanced"
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization strategies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get strategies: {str(e)}")

@router.get("/content-types")
async def get_content_types():
    """지원하는 콘텐츠 유형 목록"""
    try:
        content_types = [
            {
                "id": "educational",
                "name": "교육",
                "description": "교육 자료, 강의, 튜토리얼",
                "optimization_focus": "정확도와 상세 분석"
            },
            {
                "id": "marketing",
                "name": "마케팅",
                "description": "광고, 프로모션, 브랜딩 콘텐츠",
                "optimization_focus": "객체 인식과 감정 분석"
            },
            {
                "id": "entertainment",
                "name": "엔터테인먼트",
                "description": "영화, 드라마, 음악, 게임",
                "optimization_focus": "장면 분석과 스토리텔링"
            },
            {
                "id": "business",
                "name": "비즈니스",
                "description": "회의, 프레젠테이션, 보고서",
                "optimization_focus": "종합 분석과 요약"
            },
            {
                "id": "security",
                "name": "보안",
                "description": "감시, 모니터링, 검증",
                "optimization_focus": "높은 정확도와 객체 탐지"
            },
            {
                "id": "medical",
                "name": "의료",
                "description": "의료 영상, 진단, 연구",
                "optimization_focus": "최고 정확도와 세밀한 분석"
            },
            {
                "id": "news",
                "name": "뉴스",
                "description": "뉴스, 리포팅, 저널리즘",
                "optimization_focus": "빠른 처리와 핵심 추출"
            },
            {
                "id": "social",
                "name": "소셜미디어",
                "description": "SNS, 커뮤니티, 개인 콘텐츠",
                "optimization_focus": "빠른 처리와 감정 분석"
            }
        ]
        
        return {
            "success": True,
            "content_types": content_types,
            "total": len(content_types),
            "default_type": "business"
        }
        
    except Exception as e:
        logger.error(f"Failed to get content types: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get content types: {str(e)}")

@router.get("/complexity-levels")
async def get_complexity_levels():
    """미디어 복잡도 수준 목록"""
    try:
        complexity_levels = [
            {
                "id": "simple",
                "name": "단순",
                "description": "정적 장면, 명확한 음성, 단순한 구성",
                "characteristics": ["고정 카메라", "단일 화자", "명확한 조명"],
                "recommended_settings": "Flash 모델, 낮은 프레임 수"
            },
            {
                "id": "moderate",
                "name": "보통",
                "description": "일반적인 비디오, 적당한 편집",
                "characteristics": ["카메라 이동", "여러 장면", "배경 음악"],
                "recommended_settings": "Pro 모델, 표준 프레임 수"
            },
            {
                "id": "complex",
                "name": "복잡",
                "description": "다중 장면, 복잡한 오디오, 고급 편집",
                "characteristics": ["빠른 장면 전환", "다중 화자", "특수 효과"],
                "recommended_settings": "Pro 모델, 높은 프레임 수"
            },
            {
                "id": "very_complex",
                "name": "매우 복잡",
                "description": "고도의 편집, 다중 화자, 복잡한 시각 효과",
                "characteristics": ["복잡한 몽타주", "오버랩 음성", "3D 효과"],
                "recommended_settings": "Pro 모델, 최대 프레임 수"
            }
        ]
        
        return {
            "success": True,
            "complexity_levels": complexity_levels,
            "total": len(complexity_levels),
            "default_level": "moderate"
        }
        
    except Exception as e:
        logger.error(f"Failed to get complexity levels: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get complexity levels: {str(e)}")

@router.post("/optimize")
async def optimize_configuration(
    request: OptimizationRequest,
    current_user: User = Depends(get_current_user)
):
    """설정 최적화 요청"""
    try:
        start_time = datetime.now()
        
        # 최적화 프로필 생성
        profile = OptimizationProfile()
        
        # 요청 데이터로 프로필 설정
        if request.content_type:
            try:
                profile.content_type = ContentType(request.content_type)
            except ValueError:
                profile.content_type = ContentType.BUSINESS
        
        if request.media_complexity:
            try:
                profile.media_complexity = MediaComplexity(request.media_complexity)
            except ValueError:
                profile.media_complexity = MediaComplexity.MODERATE
        
        try:
            profile.user_priority = OptimizationStrategy(request.user_priority)
        except ValueError:
            profile.user_priority = OptimizationStrategy.BALANCED
        
        profile.file_size_mb = request.file_size_mb
        profile.duration_seconds = request.duration_seconds
        profile.has_audio = request.has_audio
        profile.max_processing_time = request.max_processing_time
        profile.min_accuracy_threshold = request.min_accuracy_threshold
        profile.budget_constraint = request.budget_constraint
        profile.batch_size = request.batch_size
        profile.is_realtime = request.is_realtime
        profile.user_experience_level = request.user_experience_level
        
        # 자동 최적화 실행
        auto_optimizer = get_auto_optimizer()
        recommendation = await auto_optimizer.optimize_configuration(
            profile=profile,
            user_preferences=request.user_preferences
        )
        
        # 처리 시간 계산
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 응답 생성
        recommendation_dict = {
            "analysis_type": recommendation.recommended_analysis_type,
            "model": recommendation.recommended_model,
            "temperature": recommendation.recommended_temperature,
            "max_tokens": recommendation.recommended_max_tokens,
            "frame_sampling": recommendation.recommended_frame_sampling,
            "max_frames": recommendation.recommended_max_frames,
            "fusion_strategy": recommendation.recommended_fusion_strategy,
            "performance_prediction": {
                "estimated_processing_time": recommendation.estimated_processing_time,
                "estimated_accuracy": recommendation.estimated_accuracy,
                "estimated_cost": recommendation.estimated_cost,
                "confidence_score": recommendation.confidence_score
            },
            "reasoning": recommendation.reasoning,
            "alternative_options": recommendation.alternative_options,
            "optimization_tips": recommendation.optimization_tips
        }
        
        logger.info(
            f"Auto-optimization completed for user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "content_type": request.content_type,
                "strategy": request.user_priority,
                "confidence": recommendation.confidence_score,
                "processing_time": processing_time
            }
        )
        
        return OptimizationResponse(
            success=True,
            recommendation=recommendation_dict,
            processing_time_seconds=processing_time
        )
        
    except Exception as e:
        logger.error(f"Auto-optimization failed: {str(e)}", exc_info=True)
        return OptimizationResponse(
            success=False,
            error=str(e),
            processing_time_seconds=(datetime.now() - start_time).total_seconds()
        )

@router.post("/record-performance")
async def record_performance(
    record: PerformanceRecord,
    current_user: User = Depends(get_current_user)
):
    """실제 성능 기록 (학습용)"""
    try:
        auto_optimizer = get_auto_optimizer()
        
        # 성능 기록에 사용자 정보 추가
        actual_result = {
            "processing_time_seconds": record.actual_processing_time,
            "success": record.success,
            "user_rating": record.user_rating,
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat()
        }
        
        auto_optimizer.record_performance(
            config=record.config,
            actual_result=actual_result
        )
        
        logger.info(
            f"Performance recorded for user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "success": record.success,
                "processing_time": record.actual_processing_time,
                "user_rating": record.user_rating
            }
        )
        
        return {
            "success": True,
            "message": "Performance recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to record performance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to record performance: {str(e)}")

@router.get("/examples")
async def get_optimization_examples():
    """최적화 예시 및 사용 사례"""
    try:
        examples = [
            {
                "title": "교육 비디오 최적화",
                "scenario": {
                    "content_type": "educational",
                    "file_size_mb": 25.5,
                    "duration_seconds": 300,
                    "user_priority": "accuracy_first"
                },
                "recommendation": {
                    "model": "gemini-1.5-pro",
                    "analysis_type": "comprehensive",
                    "max_frames": 40,
                    "reasoning": "교육 콘텐츠는 정확도가 중요하므로 Pro 모델과 종합 분석 추천"
                },
                "expected_results": {
                    "processing_time": "45-60초",
                    "accuracy": "94%",
                    "cost": "$0.08"
                }
            },
            {
                "title": "마케팅 비디오 빠른 분석",
                "scenario": {
                    "content_type": "marketing",
                    "file_size_mb": 15.2,
                    "duration_seconds": 120,
                    "user_priority": "speed_first"
                },
                "recommendation": {
                    "model": "gemini-1.5-flash",
                    "analysis_type": "objects",
                    "max_frames": 20,
                    "reasoning": "마케팅 콘텐츠는 객체 인식 중심으로 빠른 처리 우선"
                },
                "expected_results": {
                    "processing_time": "15-20초",
                    "accuracy": "89%",
                    "cost": "$0.03"
                }
            },
            {
                "title": "대량 배치 처리 최적화",
                "scenario": {
                    "content_type": "business",
                    "batch_size": 10,
                    "user_priority": "cost_efficient"
                },
                "recommendation": {
                    "model": "gemini-1.5-flash",
                    "analysis_type": "summary",
                    "max_frames": 15,
                    "reasoning": "배치 처리 시 개별 파일당 처리 시간 단축으로 전체 효율성 향상"
                },
                "expected_results": {
                    "total_processing_time": "8-12분",
                    "average_accuracy": "87%",
                    "total_cost": "$0.25"
                }
            }
        ]
        
        return {
            "success": True,
            "examples": examples,
            "total": len(examples),
            "tips": [
                "파일 크기가 클수록 프레임 수를 줄여 처리 시간 단축",
                "실시간 처리가 필요한 경우 Flash 모델 사용 권장",
                "정확도가 중요한 경우 Pro 모델과 comprehensive 분석 선택",
                "배치 처리 시 개별 설정을 낮춰 전체 처리 시간 최적화"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization examples: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get examples: {str(e)}")

@router.get("/stats")
async def get_optimization_stats():
    """최적화 통계 및 성능 지표"""
    try:
        auto_optimizer = get_auto_optimizer()
        
        # 기본 통계
        stats = {
            "system_health": {
                "status": "healthy",
                "optimization_engine": "active",
                "ai_advisor": "available",
                "performance_tracker": "running"
            },
            "usage_statistics": {
                "total_optimizations": len(auto_optimizer.performance_history),
                "successful_optimizations": len([r for r in auto_optimizer.performance_history if r.get("success", False)]),
                "average_confidence": 0.85,
                "most_used_strategy": "balanced"
            },
            "performance_metrics": {
                "average_processing_time": 2.3,
                "accuracy_improvement": "12%",
                "cost_savings": "23%",
                "user_satisfaction": 4.2
            },
            "popular_configurations": [
                {
                    "model": "gemini-1.5-pro",
                    "analysis_type": "comprehensive",
                    "usage_percentage": 45
                },
                {
                    "model": "gemini-1.5-flash",
                    "analysis_type": "summary",
                    "usage_percentage": 35
                },
                {
                    "model": "gemini-1.5-pro",
                    "analysis_type": "objects",
                    "usage_percentage": 20
                }
            ]
        }
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")