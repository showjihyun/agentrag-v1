"""
AI-Powered Auto-optimization Service
AI 기반 자동 최적화 및 전략 선택 시스템
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import statistics

from backend.services.multimodal.gemini_service import get_gemini_service
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class OptimizationStrategy(Enum):
    """최적화 전략"""
    SPEED_FIRST = "speed_first"          # 속도 우선
    ACCURACY_FIRST = "accuracy_first"    # 정확도 우선
    BALANCED = "balanced"                # 균형
    COST_EFFICIENT = "cost_efficient"    # 비용 효율
    QUALITY_PREMIUM = "quality_premium"  # 품질 프리미엄

class ContentType(Enum):
    """콘텐츠 유형"""
    EDUCATIONAL = "educational"          # 교육
    MARKETING = "marketing"              # 마케팅
    ENTERTAINMENT = "entertainment"      # 엔터테인먼트
    BUSINESS = "business"                # 비즈니스
    SECURITY = "security"                # 보안
    MEDICAL = "medical"                  # 의료
    NEWS = "news"                        # 뉴스
    SOCIAL = "social"                    # 소셜미디어

class MediaComplexity(Enum):
    """미디어 복잡도"""
    SIMPLE = "simple"        # 단순 (정적 장면, 명확한 음성)
    MODERATE = "moderate"    # 보통 (일반적인 비디오)
    COMPLEX = "complex"      # 복잡 (다중 장면, 복잡한 오디오)
    VERY_COMPLEX = "very_complex"  # 매우 복잡 (고도의 편집, 다중 화자)

class OptimizationProfile:
    """최적화 프로필"""
    
    def __init__(self):
        self.content_type: Optional[ContentType] = None
        self.media_complexity: Optional[MediaComplexity] = None
        self.file_size_mb: float = 0
        self.duration_seconds: float = 0
        self.has_audio: bool = True
        self.user_priority: OptimizationStrategy = OptimizationStrategy.BALANCED
        
        # 성능 요구사항
        self.max_processing_time: Optional[float] = None
        self.min_accuracy_threshold: float = 0.85
        self.budget_constraint: Optional[float] = None
        
        # 컨텍스트 정보
        self.batch_size: int = 1
        self.is_realtime: bool = False
        self.user_experience_level: str = "intermediate"  # beginner, intermediate, expert

class OptimizationRecommendation:
    """최적화 추천 결과"""
    
    def __init__(self):
        self.recommended_analysis_type: str = "comprehensive"
        self.recommended_model: str = "gemini-1.5-pro"
        self.recommended_temperature: float = 0.7
        self.recommended_max_tokens: int = 4096
        self.recommended_frame_sampling: str = "auto"
        self.recommended_max_frames: int = 30
        self.recommended_fusion_strategy: Optional[str] = None
        
        # 예상 성능
        self.estimated_processing_time: float = 0
        self.estimated_accuracy: float = 0
        self.estimated_cost: float = 0
        self.confidence_score: float = 0
        
        # 설명 및 근거
        self.reasoning: str = ""
        self.alternative_options: List[Dict[str, Any]] = []
        self.optimization_tips: List[str] = []

class GeminiAutoOptimizer:
    """Gemini AI 기반 자동 최적화기"""
    
    def __init__(self):
        self.gemini_service = None
        try:
            self.gemini_service = get_gemini_service()
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini service: {e}")
        
        # 성능 히스토리 (실제 구현에서는 데이터베이스 사용)
        self.performance_history: List[Dict[str, Any]] = []
        
        # 최적화 규칙 베이스
        self.optimization_rules = self._load_optimization_rules()
        
        # 성능 벤치마크
        self.performance_benchmarks = self._load_performance_benchmarks()
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """최적화 규칙 로드"""
        return {
            "content_type_rules": {
                ContentType.EDUCATIONAL.value: {
                    "preferred_analysis": "comprehensive",
                    "accuracy_weight": 0.8,
                    "speed_weight": 0.2,
                    "recommended_frames": 40
                },
                ContentType.MARKETING.value: {
                    "preferred_analysis": "objects",
                    "accuracy_weight": 0.7,
                    "speed_weight": 0.3,
                    "recommended_frames": 25
                },
                ContentType.ENTERTAINMENT.value: {
                    "preferred_analysis": "scenes",
                    "accuracy_weight": 0.6,
                    "speed_weight": 0.4,
                    "recommended_frames": 35
                },
                ContentType.SECURITY.value: {
                    "preferred_analysis": "objects",
                    "accuracy_weight": 0.9,
                    "speed_weight": 0.1,
                    "recommended_frames": 50
                }
            },
            "complexity_rules": {
                MediaComplexity.SIMPLE.value: {
                    "model": "gemini-1.5-flash",
                    "temperature": 0.3,
                    "max_frames": 20,
                    "processing_multiplier": 0.7
                },
                MediaComplexity.MODERATE.value: {
                    "model": "gemini-1.5-pro",
                    "temperature": 0.5,
                    "max_frames": 30,
                    "processing_multiplier": 1.0
                },
                MediaComplexity.COMPLEX.value: {
                    "model": "gemini-1.5-pro",
                    "temperature": 0.7,
                    "max_frames": 40,
                    "processing_multiplier": 1.3
                },
                MediaComplexity.VERY_COMPLEX.value: {
                    "model": "gemini-1.5-pro",
                    "temperature": 0.8,
                    "max_frames": 50,
                    "processing_multiplier": 1.6
                }
            },
            "strategy_rules": {
                OptimizationStrategy.SPEED_FIRST.value: {
                    "model_preference": "gemini-1.5-flash",
                    "max_frames_limit": 20,
                    "temperature_range": [0.3, 0.5],
                    "analysis_preference": "summary"
                },
                OptimizationStrategy.ACCURACY_FIRST.value: {
                    "model_preference": "gemini-1.5-pro",
                    "max_frames_limit": 50,
                    "temperature_range": [0.7, 0.9],
                    "analysis_preference": "comprehensive"
                },
                OptimizationStrategy.BALANCED.value: {
                    "model_preference": "gemini-1.5-pro",
                    "max_frames_limit": 30,
                    "temperature_range": [0.5, 0.7],
                    "analysis_preference": "comprehensive"
                }
            }
        }
    
    def _load_performance_benchmarks(self) -> Dict[str, Any]:
        """성능 벤치마크 로드"""
        return {
            "model_performance": {
                "gemini-1.5-flash": {
                    "avg_processing_time": 15.2,
                    "accuracy_score": 0.89,
                    "cost_per_token": 0.001,
                    "max_context": 1000000
                },
                "gemini-1.5-pro": {
                    "avg_processing_time": 32.5,
                    "accuracy_score": 0.94,
                    "cost_per_token": 0.003,
                    "max_context": 2000000
                }
            },
            "analysis_performance": {
                "summary": {"time_factor": 0.6, "accuracy": 0.88},
                "comprehensive": {"time_factor": 1.0, "accuracy": 0.94},
                "transcript": {"time_factor": 0.8, "accuracy": 0.91},
                "objects": {"time_factor": 0.7, "accuracy": 0.92},
                "scenes": {"time_factor": 0.9, "accuracy": 0.90}
            }
        }
    
    async def optimize_configuration(
        self,
        profile: OptimizationProfile,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> OptimizationRecommendation:
        """
        최적화된 설정 추천
        
        Args:
            profile: 최적화 프로필
            user_preferences: 사용자 선호도
            
        Returns:
            최적화 추천 결과
        """
        try:
            logger.info("Starting auto-optimization analysis")
            
            # 1. 콘텐츠 분석 및 복잡도 추정
            if not profile.content_type or not profile.media_complexity:
                await self._analyze_content_characteristics(profile)
            
            # 2. 규칙 기반 초기 추천
            base_recommendation = self._apply_optimization_rules(profile)
            
            # 3. AI 기반 세부 조정
            ai_recommendation = await self._ai_optimize_configuration(profile, base_recommendation)
            
            # 4. 성능 예측
            await self._predict_performance(ai_recommendation, profile)
            
            # 5. 대안 옵션 생성
            ai_recommendation.alternative_options = self._generate_alternatives(ai_recommendation, profile)
            
            # 6. 최적화 팁 생성
            ai_recommendation.optimization_tips = self._generate_optimization_tips(profile, ai_recommendation)
            
            logger.info(f"Auto-optimization completed with confidence: {ai_recommendation.confidence_score:.2f}")
            
            return ai_recommendation
            
        except Exception as e:
            logger.error(f"Auto-optimization failed: {str(e)}", exc_info=True)
            # 폴백: 기본 설정 반환
            return self._get_fallback_recommendation(profile)
    
    async def _analyze_content_characteristics(self, profile: OptimizationProfile):
        """콘텐츠 특성 자동 분석"""
        try:
            # 파일 크기와 길이 기반 복잡도 추정
            if profile.file_size_mb > 50 or profile.duration_seconds > 600:
                profile.media_complexity = MediaComplexity.COMPLEX
            elif profile.file_size_mb > 20 or profile.duration_seconds > 300:
                profile.media_complexity = MediaComplexity.MODERATE
            else:
                profile.media_complexity = MediaComplexity.SIMPLE
            
            # 기본 콘텐츠 타입 (실제로는 더 정교한 분석 필요)
            if not profile.content_type:
                profile.content_type = ContentType.BUSINESS  # 기본값
            
            logger.info(f"Analyzed content: {profile.content_type.value}, complexity: {profile.media_complexity.value}")
            
        except Exception as e:
            logger.warning(f"Content analysis failed, using defaults: {e}")
            profile.content_type = ContentType.BUSINESS
            profile.media_complexity = MediaComplexity.MODERATE
    
    def _apply_optimization_rules(self, profile: OptimizationProfile) -> OptimizationRecommendation:
        """규칙 기반 최적화 적용"""
        recommendation = OptimizationRecommendation()
        
        # 콘텐츠 타입 규칙 적용
        content_rules = self.optimization_rules["content_type_rules"].get(
            profile.content_type.value, 
            self.optimization_rules["content_type_rules"][ContentType.BUSINESS.value]
        )
        
        recommendation.recommended_analysis_type = content_rules["preferred_analysis"]
        recommendation.recommended_max_frames = content_rules["recommended_frames"]
        
        # 복잡도 규칙 적용
        complexity_rules = self.optimization_rules["complexity_rules"].get(
            profile.media_complexity.value,
            self.optimization_rules["complexity_rules"][MediaComplexity.MODERATE.value]
        )
        
        recommendation.recommended_model = complexity_rules["model"]
        recommendation.recommended_temperature = complexity_rules["temperature"]
        recommendation.recommended_max_frames = min(
            recommendation.recommended_max_frames,
            complexity_rules["max_frames"]
        )
        
        # 전략 규칙 적용
        strategy_rules = self.optimization_rules["strategy_rules"].get(
            profile.user_priority.value,
            self.optimization_rules["strategy_rules"][OptimizationStrategy.BALANCED.value]
        )
        
        # 모델 선택 조정
        if profile.user_priority == OptimizationStrategy.SPEED_FIRST:
            recommendation.recommended_model = "gemini-1.5-flash"
            recommendation.recommended_analysis_type = "summary"
            recommendation.recommended_max_frames = min(recommendation.recommended_max_frames, 20)
        elif profile.user_priority == OptimizationStrategy.ACCURACY_FIRST:
            recommendation.recommended_model = "gemini-1.5-pro"
            recommendation.recommended_analysis_type = "comprehensive"
            recommendation.recommended_max_frames = min(recommendation.recommended_max_frames, 50)
        
        # 배치 처리 최적화
        if profile.batch_size > 1:
            # 배치 처리 시 개별 파일 처리 시간 단축
            recommendation.recommended_max_frames = max(10, recommendation.recommended_max_frames - 10)
            if profile.batch_size > 5:
                recommendation.recommended_model = "gemini-1.5-flash"
        
        # 실시간 처리 최적화
        if profile.is_realtime:
            recommendation.recommended_model = "gemini-1.5-flash"
            recommendation.recommended_analysis_type = "summary"
            recommendation.recommended_max_frames = 15
            recommendation.recommended_temperature = 0.3
        
        return recommendation
    
    async def _ai_optimize_configuration(
        self,
        profile: OptimizationProfile,
        base_recommendation: OptimizationRecommendation
    ) -> OptimizationRecommendation:
        """AI 기반 세부 최적화"""
        if not self.gemini_service:
            return base_recommendation
        
        try:
            # AI에게 최적화 요청
            optimization_prompt = f"""
다음 비디오 분석 작업에 대한 최적의 설정을 추천해주세요:

콘텐츠 정보:
- 유형: {profile.content_type.value if profile.content_type else 'unknown'}
- 복잡도: {profile.media_complexity.value if profile.media_complexity else 'unknown'}
- 파일 크기: {profile.file_size_mb}MB
- 길이: {profile.duration_seconds}초
- 오디오 포함: {profile.has_audio}

사용자 요구사항:
- 우선순위: {profile.user_priority.value}
- 최대 처리 시간: {profile.max_processing_time or '제한 없음'}초
- 최소 정확도: {profile.min_accuracy_threshold * 100}%
- 배치 크기: {profile.batch_size}
- 실시간 처리: {profile.is_realtime}

현재 기본 추천:
- 분석 유형: {base_recommendation.recommended_analysis_type}
- 모델: {base_recommendation.recommended_model}
- 온도: {base_recommendation.recommended_temperature}
- 최대 프레임: {base_recommendation.recommended_max_frames}

위 정보를 바탕으로 다음 형식으로 최적화된 설정을 JSON으로 제공해주세요:
{{
    "analysis_type": "추천 분석 유형",
    "model": "추천 모델",
    "temperature": 추천 온도값,
    "max_frames": 추천 최대 프레임수,
    "reasoning": "추천 근거 설명",
    "confidence": 0.0-1.0 신뢰도,
    "expected_accuracy": 0.0-1.0 예상 정확도,
    "expected_time": 예상 처리 시간(초)
}}
"""
            
            result = await self.gemini_service.analyze_image_with_text(
                image_data="",  # 텍스트만 사용
                prompt=optimization_prompt,
                model="gemini-1.5-pro",
                temperature=0.3,
                max_tokens=1024
            )
            
            if result["success"]:
                # AI 응답 파싱
                ai_response = self._parse_ai_optimization_response(result["result"])
                if ai_response:
                    # AI 추천으로 업데이트
                    base_recommendation.recommended_analysis_type = ai_response.get("analysis_type", base_recommendation.recommended_analysis_type)
                    base_recommendation.recommended_model = ai_response.get("model", base_recommendation.recommended_model)
                    base_recommendation.recommended_temperature = ai_response.get("temperature", base_recommendation.recommended_temperature)
                    base_recommendation.recommended_max_frames = ai_response.get("max_frames", base_recommendation.recommended_max_frames)
                    base_recommendation.reasoning = ai_response.get("reasoning", "AI 기반 최적화 적용")
                    base_recommendation.confidence_score = ai_response.get("confidence", 0.8)
                    base_recommendation.estimated_accuracy = ai_response.get("expected_accuracy", 0.9)
                    base_recommendation.estimated_processing_time = ai_response.get("expected_time", 30)
            
        except Exception as e:
            logger.warning(f"AI optimization failed, using rule-based result: {e}")
            base_recommendation.confidence_score = 0.7
            base_recommendation.reasoning = "규칙 기반 최적화 적용 (AI 최적화 실패)"
        
        return base_recommendation
    
    def _parse_ai_optimization_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """AI 최적화 응답 파싱"""
        try:
            # JSON 추출 시도
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse AI optimization response: {e}")
        return None
    
    async def _predict_performance(self, recommendation: OptimizationRecommendation, profile: OptimizationProfile):
        """성능 예측"""
        try:
            # 모델 성능 기준
            model_perf = self.performance_benchmarks["model_performance"][recommendation.recommended_model]
            analysis_perf = self.performance_benchmarks["analysis_performance"][recommendation.recommended_analysis_type]
            
            # 기본 처리 시간 계산
            base_time = model_perf["avg_processing_time"]
            complexity_multiplier = self.optimization_rules["complexity_rules"][profile.media_complexity.value]["processing_multiplier"]
            analysis_multiplier = analysis_perf["time_factor"]
            frame_multiplier = recommendation.recommended_max_frames / 30.0  # 30프레임 기준
            
            recommendation.estimated_processing_time = base_time * complexity_multiplier * analysis_multiplier * frame_multiplier
            
            # 정확도 예측
            base_accuracy = model_perf["accuracy_score"]
            analysis_accuracy = analysis_perf["accuracy"]
            recommendation.estimated_accuracy = (base_accuracy + analysis_accuracy) / 2
            
            # 비용 예측 (토큰 기반)
            estimated_tokens = recommendation.recommended_max_tokens
            token_cost = model_perf["cost_per_token"]
            recommendation.estimated_cost = estimated_tokens * token_cost
            
        except Exception as e:
            logger.warning(f"Performance prediction failed: {e}")
            recommendation.estimated_processing_time = 30.0
            recommendation.estimated_accuracy = 0.9
            recommendation.estimated_cost = 0.01
    
    def _generate_alternatives(self, recommendation: OptimizationRecommendation, profile: OptimizationProfile) -> List[Dict[str, Any]]:
        """대안 옵션 생성"""
        alternatives = []
        
        # 속도 우선 대안
        if recommendation.recommended_model != "gemini-1.5-flash":
            alternatives.append({
                "name": "속도 우선",
                "model": "gemini-1.5-flash",
                "analysis_type": "summary",
                "max_frames": 20,
                "estimated_time": recommendation.estimated_processing_time * 0.5,
                "estimated_accuracy": recommendation.estimated_accuracy * 0.95,
                "description": "처리 속도를 우선시하는 설정"
            })
        
        # 정확도 우선 대안
        if recommendation.recommended_analysis_type != "comprehensive":
            alternatives.append({
                "name": "정확도 우선",
                "model": "gemini-1.5-pro",
                "analysis_type": "comprehensive",
                "max_frames": 50,
                "estimated_time": recommendation.estimated_processing_time * 1.5,
                "estimated_accuracy": recommendation.estimated_accuracy * 1.05,
                "description": "분석 정확도를 우선시하는 설정"
            })
        
        # 균형 대안
        alternatives.append({
            "name": "균형 설정",
            "model": "gemini-1.5-pro",
            "analysis_type": "comprehensive",
            "max_frames": 30,
            "estimated_time": recommendation.estimated_processing_time,
            "estimated_accuracy": recommendation.estimated_accuracy,
            "description": "속도와 정확도의 균형을 맞춘 설정"
        })
        
        return alternatives[:2]  # 최대 2개 대안
    
    def _generate_optimization_tips(self, profile: OptimizationProfile, recommendation: OptimizationRecommendation) -> List[str]:
        """최적화 팁 생성"""
        tips = []
        
        if profile.file_size_mb > 50:
            tips.append("큰 파일의 경우 프레임 수를 줄여 처리 시간을 단축할 수 있습니다.")
        
        if profile.batch_size > 5:
            tips.append("대량 배치 처리 시 Flash 모델을 사용하면 전체 처리 시간을 크게 단축할 수 있습니다.")
        
        if profile.user_priority == OptimizationStrategy.SPEED_FIRST:
            tips.append("요약 분석 유형을 선택하면 핵심 정보를 빠르게 얻을 수 있습니다.")
        
        if not profile.has_audio:
            tips.append("오디오가 없는 비디오의 경우 시각적 분석에 집중하여 더 나은 결과를 얻을 수 있습니다.")
        
        if profile.is_realtime:
            tips.append("실시간 처리가 필요한 경우 프레임 수를 15개 이하로 제한하는 것이 좋습니다.")
        
        return tips[:3]  # 최대 3개 팁
    
    def _get_fallback_recommendation(self, profile: OptimizationProfile) -> OptimizationRecommendation:
        """폴백 추천 (오류 시 기본값)"""
        recommendation = OptimizationRecommendation()
        recommendation.recommended_analysis_type = "comprehensive"
        recommendation.recommended_model = "gemini-1.5-pro"
        recommendation.recommended_temperature = 0.7
        recommendation.recommended_max_frames = 30
        recommendation.estimated_processing_time = 30.0
        recommendation.estimated_accuracy = 0.9
        recommendation.confidence_score = 0.5
        recommendation.reasoning = "기본 설정 적용 (최적화 실패)"
        return recommendation
    
    def record_performance(self, config: Dict[str, Any], actual_result: Dict[str, Any]):
        """실제 성능 기록 (학습용)"""
        try:
            performance_record = {
                "timestamp": datetime.now().isoformat(),
                "config": config,
                "actual_processing_time": actual_result.get("processing_time_seconds", 0),
                "success": actual_result.get("success", False),
                "user_feedback": actual_result.get("user_rating", None)
            }
            
            self.performance_history.append(performance_record)
            
            # 히스토리 크기 제한
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-500:]
            
            logger.info("Performance record added for learning")
            
        except Exception as e:
            logger.warning(f"Failed to record performance: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """자동 최적화기 상태 확인"""
        return {
            "status": "healthy",
            "service": "gemini_auto_optimizer",
            "optimization_rules_loaded": len(self.optimization_rules) > 0,
            "performance_benchmarks_loaded": len(self.performance_benchmarks) > 0,
            "performance_history_size": len(self.performance_history),
            "gemini_service_available": self.gemini_service is not None,
            "timestamp": datetime.now().isoformat()
        }

# 싱글톤 인스턴스
_auto_optimizer = None

def get_auto_optimizer() -> GeminiAutoOptimizer:
    """자동 최적화기 싱글톤 인스턴스 반환"""
    global _auto_optimizer
    if _auto_optimizer is None:
        _auto_optimizer = GeminiAutoOptimizer()
    return _auto_optimizer