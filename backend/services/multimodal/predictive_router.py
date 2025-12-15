"""
Predictive Routing Engine
AI 기반 예측적 라우팅 및 전략 선택 시스템
"""

import asyncio
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, asdict
import pickle
import os

from backend.services.multimodal.gemini_service import get_gemini_service
from backend.services.multimodal.auto_optimizer import (
    get_auto_optimizer, 
    OptimizationProfile, 
    OptimizationStrategy,
    ContentType,
    MediaComplexity
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class RoutingStrategy(Enum):
    """라우팅 전략"""
    PERFORMANCE_FIRST = "performance_first"      # 성능 우선
    COST_OPTIMIZED = "cost_optimized"           # 비용 최적화
    QUALITY_ASSURED = "quality_assured"         # 품질 보장
    ADAPTIVE_LEARNING = "adaptive_learning"     # 적응형 학습
    PREDICTIVE_SCALING = "predictive_scaling"   # 예측적 스케일링

class ProcessingMode(Enum):
    """처리 모드"""
    SINGLE_SHOT = "single_shot"                 # 단일 처리
    BATCH_OPTIMIZED = "batch_optimized"         # 배치 최적화
    STREAMING = "streaming"                     # 스트리밍
    HYBRID = "hybrid"                          # 하이브리드

@dataclass
class RoutingContext:
    """라우팅 컨텍스트"""
    user_id: str
    session_id: str
    content_profile: OptimizationProfile
    historical_performance: Dict[str, Any]
    current_system_load: float
    user_preferences: Dict[str, Any]
    business_priority: str
    deadline_constraint: Optional[datetime] = None
    budget_limit: Optional[float] = None
    quality_threshold: float = 0.85

@dataclass
class RoutingDecision:
    """라우팅 결정"""
    selected_strategy: str
    processing_mode: str
    model_selection: str
    configuration: Dict[str, Any]
    confidence_score: float
    reasoning: str
    estimated_performance: Dict[str, Any]
    fallback_options: List[Dict[str, Any]]
    monitoring_metrics: List[str]

@dataclass
class PerformanceMetrics:
    """성능 지표"""
    processing_time: float
    accuracy_score: float
    cost: float
    user_satisfaction: float
    resource_utilization: float
    error_rate: float
    throughput: float

class PredictiveRouter:
    """예측적 라우터"""
    
    def __init__(self):
        self.gemini_service = None
        self.auto_optimizer = None
        try:
            self.gemini_service = get_gemini_service()
            self.auto_optimizer = get_auto_optimizer()
        except Exception as e:
            logger.warning(f"Failed to initialize services: {e}")
        
        # 성능 히스토리 (실제로는 데이터베이스 사용)
        self.performance_history: List[Dict[str, Any]] = []
        self.routing_patterns: Dict[str, Any] = {}
        self.user_behavior_models: Dict[str, Any] = {}
        
        # 예측 모델 (간단한 규칙 기반 + ML 시뮬레이션)
        self.prediction_models = self._initialize_prediction_models()
        
        # 시스템 상태 모니터링
        self.system_metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "gpu_usage": 0.0,
            "queue_length": 0,
            "active_sessions": 0,
            "error_rate": 0.0
        }
        
        # 학습된 패턴 로드
        self._load_learned_patterns()
    
    def _initialize_prediction_models(self) -> Dict[str, Any]:
        """예측 모델 초기화"""
        return {
            "performance_predictor": {
                "model_type": "ensemble",
                "features": [
                    "content_type", "file_size", "complexity", 
                    "user_history", "system_load", "time_of_day"
                ],
                "accuracy": 0.89,
                "last_trained": datetime.now().isoformat()
            },
            "cost_predictor": {
                "model_type": "regression",
                "features": ["model_choice", "token_count", "processing_time"],
                "accuracy": 0.94,
                "last_trained": datetime.now().isoformat()
            },
            "user_satisfaction_predictor": {
                "model_type": "classification",
                "features": [
                    "response_time", "accuracy", "user_experience_level",
                    "expectation_alignment"
                ],
                "accuracy": 0.87,
                "last_trained": datetime.now().isoformat()
            },
            "system_load_predictor": {
                "model_type": "time_series",
                "features": ["historical_load", "time_patterns", "seasonal_trends"],
                "accuracy": 0.82,
                "last_trained": datetime.now().isoformat()
            }
        }
    
    def _load_learned_patterns(self):
        """학습된 패턴 로드"""
        try:
            # 실제로는 데이터베이스나 파일에서 로드
            self.routing_patterns = {
                "peak_hours": {
                    "9-12": {"strategy": "cost_optimized", "load_factor": 1.5},
                    "13-17": {"strategy": "performance_first", "load_factor": 2.0},
                    "18-22": {"strategy": "quality_assured", "load_factor": 1.2}
                },
                "user_segments": {
                    "enterprise": {"priority": "quality_assured", "budget_flexible": True},
                    "startup": {"priority": "cost_optimized", "speed_important": True},
                    "individual": {"priority": "performance_first", "simple_interface": True}
                },
                "content_patterns": {
                    "educational": {"accuracy_critical": True, "time_flexible": True},
                    "marketing": {"speed_critical": True, "cost_sensitive": True},
                    "security": {"accuracy_critical": True, "cost_flexible": True}
                }
            }
            
            logger.info("Learned patterns loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load learned patterns: {e}")
    
    async def route_request(
        self, 
        context: RoutingContext,
        request_data: Dict[str, Any]
    ) -> RoutingDecision:
        """
        요청 라우팅 결정
        
        Args:
            context: 라우팅 컨텍스트
            request_data: 요청 데이터
            
        Returns:
            라우팅 결정
        """
        try:
            logger.info(f"Starting predictive routing for user {context.user_id}")
            
            # 1. 컨텍스트 분석
            context_analysis = await self._analyze_context(context)
            
            # 2. 성능 예측
            performance_prediction = await self._predict_performance(context, request_data)
            
            # 3. 최적 전략 선택
            optimal_strategy = await self._select_optimal_strategy(
                context, context_analysis, performance_prediction
            )
            
            # 4. 설정 최적화
            optimized_config = await self._optimize_configuration(
                context, optimal_strategy, request_data
            )
            
            # 5. 폴백 옵션 생성
            fallback_options = await self._generate_fallback_options(
                context, optimal_strategy, optimized_config
            )
            
            # 6. 모니터링 지표 설정
            monitoring_metrics = self._setup_monitoring_metrics(optimal_strategy)
            
            # 7. 라우팅 결정 생성
            decision = RoutingDecision(
                selected_strategy=optimal_strategy["strategy"],
                processing_mode=optimal_strategy["mode"],
                model_selection=optimized_config["model"],
                configuration=optimized_config,
                confidence_score=optimal_strategy["confidence"],
                reasoning=optimal_strategy["reasoning"],
                estimated_performance=performance_prediction,
                fallback_options=fallback_options,
                monitoring_metrics=monitoring_metrics
            )
            
            # 8. 결정 기록 (학습용)
            await self._record_routing_decision(context, decision)
            
            logger.info(
                f"Routing decision completed",
                extra={
                    "user_id": context.user_id,
                    "strategy": decision.selected_strategy,
                    "confidence": decision.confidence_score,
                    "model": decision.model_selection
                }
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Routing failed: {str(e)}", exc_info=True)
            return self._get_fallback_decision(context)
    
    async def _analyze_context(self, context: RoutingContext) -> Dict[str, Any]:
        """컨텍스트 분석"""
        try:
            # 사용자 행동 패턴 분석
            user_pattern = self._analyze_user_pattern(context.user_id, context.historical_performance)
            
            # 시스템 부하 분석
            system_analysis = self._analyze_system_load()
            
            # 시간대 패턴 분석
            time_pattern = self._analyze_time_pattern()
            
            # 콘텐츠 특성 분석
            content_analysis = self._analyze_content_characteristics(context.content_profile)
            
            return {
                "user_pattern": user_pattern,
                "system_analysis": system_analysis,
                "time_pattern": time_pattern,
                "content_analysis": content_analysis,
                "priority_score": self._calculate_priority_score(context),
                "urgency_level": self._assess_urgency(context)
            }
            
        except Exception as e:
            logger.warning(f"Context analysis failed: {e}")
            return {"analysis_failed": True, "fallback_mode": True}
    
    def _analyze_user_pattern(self, user_id: str, history: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 패턴 분석"""
        # 사용자의 과거 사용 패턴 분석
        if not history:
            return {"pattern_type": "new_user", "confidence": 0.3}
        
        # 선호하는 전략 분석
        preferred_strategies = {}
        satisfaction_scores = {}
        
        for record in history.get("past_requests", []):
            strategy = record.get("strategy", "unknown")
            satisfaction = record.get("user_satisfaction", 0.5)
            
            if strategy not in preferred_strategies:
                preferred_strategies[strategy] = 0
                satisfaction_scores[strategy] = []
            
            preferred_strategies[strategy] += 1
            satisfaction_scores[strategy].append(satisfaction)
        
        # 가장 선호하는 전략 계산
        if preferred_strategies:
            most_used = max(preferred_strategies.items(), key=lambda x: x[1])
            avg_satisfaction = {
                strategy: np.mean(scores) 
                for strategy, scores in satisfaction_scores.items()
            }
            
            return {
                "pattern_type": "returning_user",
                "most_used_strategy": most_used[0],
                "usage_frequency": most_used[1],
                "average_satisfaction": avg_satisfaction,
                "confidence": min(0.9, most_used[1] / 10)  # 사용 횟수 기반 신뢰도
            }
        
        return {"pattern_type": "limited_history", "confidence": 0.5}
    
    def _analyze_system_load(self) -> Dict[str, Any]:
        """시스템 부하 분석"""
        # 현재 시스템 상태 (실제로는 모니터링 시스템에서 가져옴)
        current_load = {
            "cpu_usage": np.random.uniform(0.2, 0.8),  # 시뮬레이션
            "memory_usage": np.random.uniform(0.3, 0.7),
            "gpu_usage": np.random.uniform(0.1, 0.9),
            "queue_length": np.random.randint(0, 20),
            "active_sessions": np.random.randint(5, 100)
        }
        
        # 부하 수준 계산
        load_score = (
            current_load["cpu_usage"] * 0.3 +
            current_load["memory_usage"] * 0.2 +
            current_load["gpu_usage"] * 0.4 +
            min(current_load["queue_length"] / 20, 1.0) * 0.1
        )
        
        if load_score < 0.3:
            load_level = "low"
            recommended_strategy = "quality_assured"
        elif load_score < 0.7:
            load_level = "medium"
            recommended_strategy = "performance_first"
        else:
            load_level = "high"
            recommended_strategy = "cost_optimized"
        
        return {
            "current_load": current_load,
            "load_score": load_score,
            "load_level": load_level,
            "recommended_strategy": recommended_strategy,
            "scaling_needed": load_score > 0.8
        }
    
    def _analyze_time_pattern(self) -> Dict[str, Any]:
        """시간대 패턴 분석"""
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        
        # 시간대별 패턴
        if 9 <= hour <= 12:
            time_category = "morning_peak"
            load_multiplier = 1.5
        elif 13 <= hour <= 17:
            time_category = "afternoon_peak"
            load_multiplier = 2.0
        elif 18 <= hour <= 22:
            time_category = "evening"
            load_multiplier = 1.2
        else:
            time_category = "off_peak"
            load_multiplier = 0.8
        
        # 요일별 패턴
        if day_of_week < 5:  # 평일
            day_category = "weekday"
            business_priority = True
        else:  # 주말
            day_category = "weekend"
            business_priority = False
        
        return {
            "time_category": time_category,
            "day_category": day_category,
            "load_multiplier": load_multiplier,
            "business_priority": business_priority,
            "hour": hour,
            "day_of_week": day_of_week
        }
    
    def _analyze_content_characteristics(self, profile: OptimizationProfile) -> Dict[str, Any]:
        """콘텐츠 특성 분석"""
        # 콘텐츠 복잡도 점수 계산
        complexity_score = 0.0
        
        if profile.media_complexity:
            complexity_map = {
                MediaComplexity.SIMPLE: 0.2,
                MediaComplexity.MODERATE: 0.5,
                MediaComplexity.COMPLEX: 0.8,
                MediaComplexity.VERY_COMPLEX: 1.0
            }
            complexity_score = complexity_map.get(profile.media_complexity, 0.5)
        
        # 파일 크기 기반 처리 난이도
        size_difficulty = min(profile.file_size_mb / 100, 1.0)  # 100MB 기준 정규화
        
        # 길이 기반 처리 시간 예측
        duration_factor = min(profile.duration_seconds / 3600, 1.0)  # 1시간 기준 정규화
        
        # 배치 크기 영향
        batch_complexity = min(profile.batch_size / 10, 1.0)  # 10개 기준 정규화
        
        # 종합 복잡도 점수
        overall_complexity = (
            complexity_score * 0.4 +
            size_difficulty * 0.3 +
            duration_factor * 0.2 +
            batch_complexity * 0.1
        )
        
        # 추천 처리 전략
        if overall_complexity < 0.3:
            recommended_approach = "fast_track"
        elif overall_complexity < 0.7:
            recommended_approach = "standard"
        else:
            recommended_approach = "careful_processing"
        
        return {
            "complexity_score": complexity_score,
            "size_difficulty": size_difficulty,
            "duration_factor": duration_factor,
            "batch_complexity": batch_complexity,
            "overall_complexity": overall_complexity,
            "recommended_approach": recommended_approach,
            "processing_priority": "high" if profile.is_realtime else "normal"
        }
    
    def _calculate_priority_score(self, context: RoutingContext) -> float:
        """우선순위 점수 계산"""
        score = 0.5  # 기본 점수
        
        # 사용자 우선순위 반영
        if context.user_preferences.get("premium_user", False):
            score += 0.3
        
        # 데드라인 제약 반영
        if context.deadline_constraint:
            time_left = (context.deadline_constraint - datetime.now()).total_seconds()
            if time_left < 3600:  # 1시간 미만
                score += 0.4
            elif time_left < 86400:  # 24시간 미만
                score += 0.2
        
        # 비즈니스 우선순위 반영
        business_priority_map = {
            "critical": 0.5,
            "high": 0.3,
            "medium": 0.1,
            "low": -0.1
        }
        score += business_priority_map.get(context.business_priority, 0.0)
        
        # 실시간 처리 요구사항
        if context.content_profile.is_realtime:
            score += 0.3
        
        return min(max(score, 0.0), 1.0)  # 0-1 범위로 제한
    
    def _assess_urgency(self, context: RoutingContext) -> str:
        """긴급도 평가"""
        urgency_factors = []
        
        # 데드라인 기반 긴급도
        if context.deadline_constraint:
            time_left = (context.deadline_constraint - datetime.now()).total_seconds()
            if time_left < 1800:  # 30분 미만
                urgency_factors.append("critical")
            elif time_left < 3600:  # 1시간 미만
                urgency_factors.append("high")
            elif time_left < 86400:  # 24시간 미만
                urgency_factors.append("medium")
        
        # 실시간 처리 요구사항
        if context.content_profile.is_realtime:
            urgency_factors.append("high")
        
        # 비즈니스 우선순위
        if context.business_priority == "critical":
            urgency_factors.append("high")
        
        # 가장 높은 긴급도 반환
        if "critical" in urgency_factors:
            return "critical"
        elif "high" in urgency_factors:
            return "high"
        elif "medium" in urgency_factors:
            return "medium"
        else:
            return "low"
    
    async def _predict_performance(
        self, 
        context: RoutingContext, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """성능 예측"""
        try:
            # 기본 성능 예측 (규칙 기반)
            base_prediction = self._calculate_base_performance(context)
            
            # AI 기반 성능 예측 (Gemini 활용)
            ai_prediction = await self._ai_performance_prediction(context, request_data)
            
            # 히스토리 기반 예측
            history_prediction = self._history_based_prediction(context)
            
            # 앙상블 예측 (가중 평균)
            ensemble_prediction = self._ensemble_predictions([
                {"prediction": base_prediction, "weight": 0.4},
                {"prediction": ai_prediction, "weight": 0.4},
                {"prediction": history_prediction, "weight": 0.2}
            ])
            
            return ensemble_prediction
            
        except Exception as e:
            logger.warning(f"Performance prediction failed: {e}")
            return self._get_default_performance_prediction()
    
    def _calculate_base_performance(self, context: RoutingContext) -> Dict[str, Any]:
        """기본 성능 계산"""
        profile = context.content_profile
        
        # 기본 처리 시간 계산
        base_time = 10.0  # 기본 10초
        
        # 파일 크기 영향
        size_factor = 1 + (profile.file_size_mb / 50)  # 50MB당 2배
        
        # 복잡도 영향
        complexity_factor = 1.0
        if profile.media_complexity == MediaComplexity.SIMPLE:
            complexity_factor = 0.7
        elif profile.media_complexity == MediaComplexity.COMPLEX:
            complexity_factor = 1.5
        elif profile.media_complexity == MediaComplexity.VERY_COMPLEX:
            complexity_factor = 2.0
        
        # 배치 크기 영향
        batch_factor = 1 + (profile.batch_size - 1) * 0.8  # 배치당 80% 추가
        
        # 최종 처리 시간
        processing_time = base_time * size_factor * complexity_factor * batch_factor
        
        # 정확도 예측
        base_accuracy = 0.90
        if profile.user_priority == OptimizationStrategy.ACCURACY_FIRST:
            base_accuracy = 0.95
        elif profile.user_priority == OptimizationStrategy.SPEED_FIRST:
            base_accuracy = 0.85
        
        # 비용 예측
        base_cost = 0.05  # 기본 5센트
        cost = base_cost * size_factor * complexity_factor
        
        return {
            "processing_time": processing_time,
            "accuracy": base_accuracy,
            "cost": cost,
            "confidence": 0.7,
            "method": "rule_based"
        }
    
    async def _ai_performance_prediction(
        self, 
        context: RoutingContext, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI 기반 성능 예측"""
        if not self.gemini_service:
            return self._get_default_performance_prediction()
        
        try:
            # Gemini에게 성능 예측 요청
            prediction_prompt = f"""
다음 멀티모달 처리 작업의 성능을 예측해주세요:

작업 정보:
- 콘텐츠 유형: {context.content_profile.content_type.value if context.content_profile.content_type else 'unknown'}
- 파일 크기: {context.content_profile.file_size_mb}MB
- 길이: {context.content_profile.duration_seconds}초
- 복잡도: {context.content_profile.media_complexity.value if context.content_profile.media_complexity else 'unknown'}
- 배치 크기: {context.content_profile.batch_size}
- 우선순위: {context.content_profile.user_priority.value}
- 실시간 처리: {context.content_profile.is_realtime}

시스템 상태:
- 현재 부하: {context.current_system_load}
- 사용자 경험 수준: {context.content_profile.user_experience_level}

다음 형식으로 JSON 응답해주세요:
{{
    "processing_time_seconds": 예상 처리 시간,
    "accuracy_score": 0.0-1.0 예상 정확도,
    "cost_usd": 예상 비용(달러),
    "confidence": 0.0-1.0 예측 신뢰도,
    "bottleneck": "주요 병목 지점",
    "optimization_suggestions": ["최적화 제안 목록"]
}}
"""
            
            result = await self.gemini_service.analyze_image_with_text(
                image_data="",  # 텍스트만 사용
                prompt=prediction_prompt,
                model="gemini-1.5-pro",
                temperature=0.3,
                max_tokens=1024
            )
            
            if result["success"]:
                ai_prediction = self._parse_ai_prediction(result["result"])
                if ai_prediction:
                    ai_prediction["method"] = "ai_based"
                    return ai_prediction
            
        except Exception as e:
            logger.warning(f"AI performance prediction failed: {e}")
        
        return self._get_default_performance_prediction()
    
    def _parse_ai_prediction(self, response_text: str) -> Optional[Dict[str, Any]]:
        """AI 예측 응답 파싱"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                prediction = json.loads(json_match.group())
                return {
                    "processing_time": prediction.get("processing_time_seconds", 30.0),
                    "accuracy": prediction.get("accuracy_score", 0.9),
                    "cost": prediction.get("cost_usd", 0.05),
                    "confidence": prediction.get("confidence", 0.8),
                    "bottleneck": prediction.get("bottleneck", "unknown"),
                    "optimization_suggestions": prediction.get("optimization_suggestions", [])
                }
        except Exception as e:
            logger.warning(f"Failed to parse AI prediction: {e}")
        return None
    
    def _history_based_prediction(self, context: RoutingContext) -> Dict[str, Any]:
        """히스토리 기반 예측"""
        # 유사한 과거 작업 찾기
        similar_tasks = self._find_similar_tasks(context)
        
        if not similar_tasks:
            return self._get_default_performance_prediction()
        
        # 평균 성능 계산
        avg_time = np.mean([task["processing_time"] for task in similar_tasks])
        avg_accuracy = np.mean([task["accuracy"] for task in similar_tasks])
        avg_cost = np.mean([task["cost"] for task in similar_tasks])
        
        return {
            "processing_time": avg_time,
            "accuracy": avg_accuracy,
            "cost": avg_cost,
            "confidence": min(0.9, len(similar_tasks) / 10),  # 유사 작업 수 기반 신뢰도
            "method": "history_based",
            "similar_tasks_count": len(similar_tasks)
        }
    
    def _find_similar_tasks(self, context: RoutingContext) -> List[Dict[str, Any]]:
        """유사한 과거 작업 찾기"""
        similar_tasks = []
        
        for record in self.performance_history:
            similarity_score = self._calculate_task_similarity(context, record)
            if similarity_score > 0.7:  # 70% 이상 유사한 작업
                similar_tasks.append({
                    "processing_time": record.get("processing_time", 30.0),
                    "accuracy": record.get("accuracy", 0.9),
                    "cost": record.get("cost", 0.05),
                    "similarity": similarity_score
                })
        
        # 유사도 순으로 정렬하고 상위 10개만 반환
        similar_tasks.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_tasks[:10]
    
    def _calculate_task_similarity(self, context: RoutingContext, record: Dict[str, Any]) -> float:
        """작업 유사도 계산"""
        similarity = 0.0
        
        # 콘텐츠 유형 유사도
        if (context.content_profile.content_type and 
            record.get("content_type") == context.content_profile.content_type.value):
            similarity += 0.3
        
        # 파일 크기 유사도
        size_diff = abs(context.content_profile.file_size_mb - record.get("file_size_mb", 0))
        size_similarity = max(0, 1 - size_diff / 100)  # 100MB 차이까지 허용
        similarity += size_similarity * 0.2
        
        # 복잡도 유사도
        if (context.content_profile.media_complexity and
            record.get("complexity") == context.content_profile.media_complexity.value):
            similarity += 0.2
        
        # 우선순위 유사도
        if (context.content_profile.user_priority and
            record.get("priority") == context.content_profile.user_priority.value):
            similarity += 0.15
        
        # 배치 크기 유사도
        batch_diff = abs(context.content_profile.batch_size - record.get("batch_size", 1))
        batch_similarity = max(0, 1 - batch_diff / 10)
        similarity += batch_similarity * 0.15
        
        return similarity
    
    def _ensemble_predictions(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """앙상블 예측"""
        total_weight = sum(p["weight"] for p in predictions)
        
        weighted_time = sum(
            p["prediction"]["processing_time"] * p["weight"] 
            for p in predictions
        ) / total_weight
        
        weighted_accuracy = sum(
            p["prediction"]["accuracy"] * p["weight"] 
            for p in predictions
        ) / total_weight
        
        weighted_cost = sum(
            p["prediction"]["cost"] * p["weight"] 
            for p in predictions
        ) / total_weight
        
        weighted_confidence = sum(
            p["prediction"]["confidence"] * p["weight"] 
            for p in predictions
        ) / total_weight
        
        return {
            "processing_time": weighted_time,
            "accuracy": weighted_accuracy,
            "cost": weighted_cost,
            "confidence": weighted_confidence,
            "method": "ensemble",
            "component_predictions": [p["prediction"] for p in predictions]
        }
    
    def _get_default_performance_prediction(self) -> Dict[str, Any]:
        """기본 성능 예측"""
        return {
            "processing_time": 30.0,
            "accuracy": 0.9,
            "cost": 0.05,
            "confidence": 0.5,
            "method": "default"
        }
    
    async def _select_optimal_strategy(
        self,
        context: RoutingContext,
        context_analysis: Dict[str, Any],
        performance_prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """최적 전략 선택"""
        try:
            # 전략 후보 생성
            strategy_candidates = self._generate_strategy_candidates(
                context, context_analysis, performance_prediction
            )
            
            # 각 전략 평가
            evaluated_strategies = []
            for candidate in strategy_candidates:
                score = self._evaluate_strategy(candidate, context, performance_prediction)
                evaluated_strategies.append({
                    **candidate,
                    "score": score
                })
            
            # 최고 점수 전략 선택
            best_strategy = max(evaluated_strategies, key=lambda x: x["score"])
            
            # 신뢰도 계산
            confidence = self._calculate_strategy_confidence(
                best_strategy, evaluated_strategies, context_analysis
            )
            
            return {
                "strategy": best_strategy["strategy"],
                "mode": best_strategy["mode"],
                "reasoning": best_strategy["reasoning"],
                "confidence": confidence,
                "alternatives": [s for s in evaluated_strategies if s != best_strategy][:2]
            }
            
        except Exception as e:
            logger.warning(f"Strategy selection failed: {e}")
            return self._get_fallback_strategy()
    
    def _generate_strategy_candidates(
        self,
        context: RoutingContext,
        context_analysis: Dict[str, Any],
        performance_prediction: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """전략 후보 생성"""
        candidates = []
        
        # 성능 우선 전략
        candidates.append({
            "strategy": RoutingStrategy.PERFORMANCE_FIRST.value,
            "mode": ProcessingMode.SINGLE_SHOT.value,
            "reasoning": "최고 성능을 위한 단일 처리 전략",
            "expected_time": performance_prediction["processing_time"] * 0.8,
            "expected_accuracy": performance_prediction["accuracy"] * 1.1,
            "expected_cost": performance_prediction["cost"] * 1.2
        })
        
        # 비용 최적화 전략
        candidates.append({
            "strategy": RoutingStrategy.COST_OPTIMIZED.value,
            "mode": ProcessingMode.BATCH_OPTIMIZED.value if context.content_profile.batch_size > 1 else ProcessingMode.SINGLE_SHOT.value,
            "reasoning": "비용 효율성을 위한 최적화 전략",
            "expected_time": performance_prediction["processing_time"] * 1.2,
            "expected_accuracy": performance_prediction["accuracy"] * 0.95,
            "expected_cost": performance_prediction["cost"] * 0.7
        })
        
        # 품질 보장 전략
        candidates.append({
            "strategy": RoutingStrategy.QUALITY_ASSURED.value,
            "mode": ProcessingMode.SINGLE_SHOT.value,
            "reasoning": "최고 품질을 위한 신중한 처리 전략",
            "expected_time": performance_prediction["processing_time"] * 1.3,
            "expected_accuracy": performance_prediction["accuracy"] * 1.15,
            "expected_cost": performance_prediction["cost"] * 1.4
        })
        
        # 적응형 학습 전략
        if context_analysis.get("user_pattern", {}).get("pattern_type") == "returning_user":
            candidates.append({
                "strategy": RoutingStrategy.ADAPTIVE_LEARNING.value,
                "mode": ProcessingMode.HYBRID.value,
                "reasoning": "사용자 패턴 기반 적응형 전략",
                "expected_time": performance_prediction["processing_time"],
                "expected_accuracy": performance_prediction["accuracy"] * 1.05,
                "expected_cost": performance_prediction["cost"] * 0.9
            })
        
        # 예측적 스케일링 전략
        if context_analysis.get("system_analysis", {}).get("scaling_needed", False):
            candidates.append({
                "strategy": RoutingStrategy.PREDICTIVE_SCALING.value,
                "mode": ProcessingMode.STREAMING.value,
                "reasoning": "시스템 부하 대응 스케일링 전략",
                "expected_time": performance_prediction["processing_time"] * 0.9,
                "expected_accuracy": performance_prediction["accuracy"],
                "expected_cost": performance_prediction["cost"] * 1.1
            })
        
        return candidates
    
    def _evaluate_strategy(
        self,
        strategy: Dict[str, Any],
        context: RoutingContext,
        performance_prediction: Dict[str, Any]
    ) -> float:
        """전략 평가"""
        score = 0.0
        
        # 사용자 우선순위 반영
        priority_weights = {
            OptimizationStrategy.SPEED_FIRST: {"time": 0.6, "accuracy": 0.2, "cost": 0.2},
            OptimizationStrategy.ACCURACY_FIRST: {"time": 0.2, "accuracy": 0.6, "cost": 0.2},
            OptimizationStrategy.BALANCED: {"time": 0.33, "accuracy": 0.33, "cost": 0.34},
            OptimizationStrategy.COST_EFFICIENT: {"time": 0.2, "accuracy": 0.2, "cost": 0.6},
            OptimizationStrategy.QUALITY_PREMIUM: {"time": 0.1, "accuracy": 0.7, "cost": 0.2}
        }
        
        weights = priority_weights.get(
            context.content_profile.user_priority,
            priority_weights[OptimizationStrategy.BALANCED]
        )
        
        # 시간 점수 (빠를수록 좋음)
        time_score = max(0, 1 - strategy["expected_time"] / 120)  # 2분 기준
        score += time_score * weights["time"]
        
        # 정확도 점수
        accuracy_score = strategy["expected_accuracy"]
        score += accuracy_score * weights["accuracy"]
        
        # 비용 점수 (저렴할수록 좋음)
        cost_score = max(0, 1 - strategy["expected_cost"] / 1.0)  # $1 기준
        score += cost_score * weights["cost"]
        
        # 컨텍스트 보너스
        if context.deadline_constraint:
            time_left = (context.deadline_constraint - datetime.now()).total_seconds()
            if strategy["expected_time"] < time_left:
                score += 0.2  # 데드라인 준수 보너스
        
        if context.content_profile.is_realtime and strategy["expected_time"] < 10:
            score += 0.3  # 실시간 처리 보너스
        
        # 시스템 부하 고려
        if context.current_system_load > 0.8 and "cost_optimized" in strategy["strategy"]:
            score += 0.2  # 부하 분산 보너스
        
        return min(score, 1.0)
    
    def _calculate_strategy_confidence(
        self,
        best_strategy: Dict[str, Any],
        all_strategies: List[Dict[str, Any]],
        context_analysis: Dict[str, Any]
    ) -> float:
        """전략 신뢰도 계산"""
        # 최고 점수와 차순위 점수 차이
        scores = [s["score"] for s in all_strategies]
        scores.sort(reverse=True)
        
        if len(scores) > 1:
            score_gap = scores[0] - scores[1]
            confidence = 0.5 + score_gap * 0.5  # 점수 차이 기반 신뢰도
        else:
            confidence = 0.7
        
        # 컨텍스트 분석 품질 반영
        analysis_quality = context_analysis.get("user_pattern", {}).get("confidence", 0.5)
        confidence = (confidence + analysis_quality) / 2
        
        return min(max(confidence, 0.3), 0.95)  # 0.3-0.95 범위
    
    def _get_fallback_strategy(self) -> Dict[str, Any]:
        """폴백 전략"""
        return {
            "strategy": RoutingStrategy.PERFORMANCE_FIRST.value,
            "mode": ProcessingMode.SINGLE_SHOT.value,
            "reasoning": "기본 성능 우선 전략 (분석 실패로 인한 폴백)",
            "confidence": 0.3
        }
    
    async def _optimize_configuration(
        self,
        context: RoutingContext,
        strategy: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """설정 최적화"""
        try:
            if self.auto_optimizer:
                # Auto-optimizer 활용
                recommendation = await self.auto_optimizer.optimize_configuration(
                    profile=context.content_profile,
                    user_preferences=context.user_preferences
                )
                
                # 전략에 맞게 설정 조정
                config = self._adjust_config_for_strategy(recommendation, strategy)
                return config
            else:
                # 기본 설정 생성
                return self._generate_default_config(strategy)
                
        except Exception as e:
            logger.warning(f"Configuration optimization failed: {e}")
            return self._generate_default_config(strategy)
    
    def _adjust_config_for_strategy(
        self,
        recommendation: Any,
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """전략에 맞는 설정 조정"""
        config = {
            "model": recommendation.recommended_model,
            "analysis_type": recommendation.recommended_analysis_type,
            "temperature": recommendation.recommended_temperature,
            "max_tokens": recommendation.recommended_max_tokens,
            "max_frames": recommendation.recommended_max_frames
        }
        
        # 전략별 조정
        if strategy["strategy"] == RoutingStrategy.PERFORMANCE_FIRST.value:
            config["model"] = "gemini-1.5-flash"
            config["max_frames"] = min(config["max_frames"], 20)
        elif strategy["strategy"] == RoutingStrategy.QUALITY_ASSURED.value:
            config["model"] = "gemini-1.5-pro"
            config["analysis_type"] = "comprehensive"
        elif strategy["strategy"] == RoutingStrategy.COST_OPTIMIZED.value:
            config["model"] = "gemini-1.5-flash"
            config["analysis_type"] = "summary"
            config["max_frames"] = min(config["max_frames"], 15)
        
        return config
    
    def _generate_default_config(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """기본 설정 생성"""
        base_config = {
            "model": "gemini-1.5-pro",
            "analysis_type": "comprehensive",
            "temperature": 0.7,
            "max_tokens": 4096,
            "max_frames": 30
        }
        
        # 전략별 기본 설정
        if strategy["strategy"] == RoutingStrategy.PERFORMANCE_FIRST.value:
            base_config.update({
                "model": "gemini-1.5-flash",
                "analysis_type": "summary",
                "max_frames": 20
            })
        elif strategy["strategy"] == RoutingStrategy.COST_OPTIMIZED.value:
            base_config.update({
                "model": "gemini-1.5-flash",
                "analysis_type": "summary",
                "max_frames": 15,
                "temperature": 0.3
            })
        
        return base_config
    
    async def _generate_fallback_options(
        self,
        context: RoutingContext,
        strategy: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """폴백 옵션 생성"""
        fallback_options = []
        
        # 빠른 처리 폴백
        fallback_options.append({
            "name": "빠른 처리",
            "strategy": RoutingStrategy.PERFORMANCE_FIRST.value,
            "config": {
                **config,
                "model": "gemini-1.5-flash",
                "analysis_type": "summary",
                "max_frames": 15
            },
            "trigger_condition": "processing_time > 60",
            "description": "처리 시간이 1분을 초과할 경우 빠른 처리로 전환"
        })
        
        # 오류 복구 폴백
        fallback_options.append({
            "name": "오류 복구",
            "strategy": RoutingStrategy.COST_OPTIMIZED.value,
            "config": {
                **config,
                "model": "gemini-1.5-flash",
                "analysis_type": "summary",
                "max_frames": 10,
                "temperature": 0.3
            },
            "trigger_condition": "error_rate > 0.1",
            "description": "오류율이 10%를 초과할 경우 안정적인 설정으로 전환"
        })
        
        # 품질 보장 폴백
        if strategy["strategy"] != RoutingStrategy.QUALITY_ASSURED.value:
            fallback_options.append({
                "name": "품질 보장",
                "strategy": RoutingStrategy.QUALITY_ASSURED.value,
                "config": {
                    **config,
                    "model": "gemini-1.5-pro",
                    "analysis_type": "comprehensive",
                    "max_frames": 40
                },
                "trigger_condition": "accuracy < 0.85",
                "description": "정확도가 85% 미만일 경우 품질 우선 처리로 전환"
            })
        
        return fallback_options
    
    def _setup_monitoring_metrics(self, strategy: Dict[str, Any]) -> List[str]:
        """모니터링 지표 설정"""
        base_metrics = [
            "processing_time",
            "accuracy_score",
            "cost",
            "user_satisfaction",
            "error_rate"
        ]
        
        # 전략별 추가 지표
        if strategy["strategy"] == RoutingStrategy.PERFORMANCE_FIRST.value:
            base_metrics.extend(["throughput", "latency"])
        elif strategy["strategy"] == RoutingStrategy.QUALITY_ASSURED.value:
            base_metrics.extend(["precision", "recall", "f1_score"])
        elif strategy["strategy"] == RoutingStrategy.COST_OPTIMIZED.value:
            base_metrics.extend(["cost_per_token", "resource_utilization"])
        
        return base_metrics
    
    async def _record_routing_decision(
        self,
        context: RoutingContext,
        decision: RoutingDecision
    ):
        """라우팅 결정 기록"""
        try:
            record = {
                "timestamp": datetime.now().isoformat(),
                "user_id": context.user_id,
                "session_id": context.session_id,
                "decision": asdict(decision),
                "context": {
                    "content_type": context.content_profile.content_type.value if context.content_profile.content_type else None,
                    "file_size_mb": context.content_profile.file_size_mb,
                    "complexity": context.content_profile.media_complexity.value if context.content_profile.media_complexity else None,
                    "user_priority": context.content_profile.user_priority.value,
                    "system_load": context.current_system_load
                }
            }
            
            # 실제로는 데이터베이스에 저장
            self.performance_history.append(record)
            
            # 히스토리 크기 제한
            if len(self.performance_history) > 10000:
                self.performance_history = self.performance_history[-5000:]
            
            logger.info("Routing decision recorded for learning")
            
        except Exception as e:
            logger.warning(f"Failed to record routing decision: {e}")
    
    def _get_fallback_decision(self, context: RoutingContext) -> RoutingDecision:
        """폴백 라우팅 결정"""
        return RoutingDecision(
            selected_strategy=RoutingStrategy.PERFORMANCE_FIRST.value,
            processing_mode=ProcessingMode.SINGLE_SHOT.value,
            model_selection="gemini-1.5-pro",
            configuration={
                "model": "gemini-1.5-pro",
                "analysis_type": "comprehensive",
                "temperature": 0.7,
                "max_tokens": 4096,
                "max_frames": 30
            },
            confidence_score=0.3,
            reasoning="기본 설정 적용 (라우팅 분석 실패)",
            estimated_performance={
                "processing_time": 30.0,
                "accuracy": 0.9,
                "cost": 0.05,
                "confidence": 0.5
            },
            fallback_options=[],
            monitoring_metrics=["processing_time", "accuracy_score", "error_rate"]
        )
    
    async def update_performance_feedback(
        self,
        routing_id: str,
        actual_metrics: PerformanceMetrics,
        user_feedback: Optional[Dict[str, Any]] = None
    ):
        """성능 피드백 업데이트"""
        try:
            # 실제 성능과 예측 성능 비교
            feedback_record = {
                "routing_id": routing_id,
                "timestamp": datetime.now().isoformat(),
                "actual_metrics": asdict(actual_metrics),
                "user_feedback": user_feedback,
                "prediction_accuracy": self._calculate_prediction_accuracy(routing_id, actual_metrics)
            }
            
            # 학습 데이터에 추가
            self.performance_history.append(feedback_record)
            
            # 예측 모델 업데이트 (실제로는 ML 파이프라인)
            await self._update_prediction_models(feedback_record)
            
            logger.info(f"Performance feedback updated for routing {routing_id}")
            
        except Exception as e:
            logger.error(f"Failed to update performance feedback: {e}")
    
    def _calculate_prediction_accuracy(
        self,
        routing_id: str,
        actual_metrics: PerformanceMetrics
    ) -> Dict[str, float]:
        """예측 정확도 계산"""
        # 해당 라우팅의 예측값 찾기 (실제로는 데이터베이스에서 조회)
        predicted_metrics = {
            "processing_time": 30.0,  # 예시값
            "accuracy": 0.9,
            "cost": 0.05
        }
        
        # 예측 정확도 계산
        time_accuracy = 1 - abs(actual_metrics.processing_time - predicted_metrics["processing_time"]) / predicted_metrics["processing_time"]
        accuracy_accuracy = 1 - abs(actual_metrics.accuracy_score - predicted_metrics["accuracy"]) / predicted_metrics["accuracy"]
        cost_accuracy = 1 - abs(actual_metrics.cost - predicted_metrics["cost"]) / predicted_metrics["cost"]
        
        return {
            "time_prediction_accuracy": max(0, time_accuracy),
            "accuracy_prediction_accuracy": max(0, accuracy_accuracy),
            "cost_prediction_accuracy": max(0, cost_accuracy),
            "overall_accuracy": (time_accuracy + accuracy_accuracy + cost_accuracy) / 3
        }
    
    async def _update_prediction_models(self, feedback_record: Dict[str, Any]):
        """예측 모델 업데이트"""
        try:
            # 실제로는 ML 모델 재학습
            # 여기서는 간단한 통계 업데이트
            
            for model_name, model_info in self.prediction_models.items():
                model_info["last_updated"] = datetime.now().isoformat()
                
                # 정확도 업데이트 (실제로는 더 복잡한 로직)
                if "accuracy" in model_info:
                    current_accuracy = model_info["accuracy"]
                    feedback_accuracy = feedback_record["prediction_accuracy"]["overall_accuracy"]
                    
                    # 지수 이동 평균으로 정확도 업데이트
                    alpha = 0.1  # 학습률
                    model_info["accuracy"] = current_accuracy * (1 - alpha) + feedback_accuracy * alpha
            
            logger.info("Prediction models updated with new feedback")
            
        except Exception as e:
            logger.warning(f"Failed to update prediction models: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """예측적 라우터 상태 확인"""
        return {
            "status": "healthy",
            "service": "predictive_router",
            "prediction_models": {
                name: {
                    "status": "active",
                    "accuracy": info["accuracy"],
                    "last_updated": info.get("last_updated", "unknown")
                }
                for name, info in self.prediction_models.items()
            },
            "performance_history_size": len(self.performance_history),
            "routing_patterns_loaded": len(self.routing_patterns) > 0,
            "system_metrics": self.system_metrics,
            "gemini_service_available": self.gemini_service is not None,
            "auto_optimizer_available": self.auto_optimizer is not None,
            "timestamp": datetime.now().isoformat()
        }

# 싱글톤 인스턴스
_predictive_router = None

def get_predictive_router() -> PredictiveRouter:
    """예측적 라우터 싱글톤 인스턴스 반환"""
    global _predictive_router
    if _predictive_router is None:
        _predictive_router = PredictiveRouter()
    return _predictive_router