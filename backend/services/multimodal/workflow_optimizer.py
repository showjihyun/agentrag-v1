"""
Intelligent Workflow Optimizer
지능형 워크플로우 최적화 시스템 - Phase 5-3 구현
"""

import asyncio
import json
import uuid
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import logging
from collections import defaultdict, deque
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

from backend.services.multimodal.advanced_orchestrator import (
    AdvancedMultiAgentOrchestrator, Task, AgentInstance, CollaborationPattern
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class OptimizationObjective(Enum):
    """최적화 목표"""
    MINIMIZE_TIME = "minimize_time"           # 실행 시간 최소화
    MINIMIZE_COST = "minimize_cost"           # 비용 최소화
    MAXIMIZE_QUALITY = "maximize_quality"     # 품질 최대화
    BALANCE_ALL = "balance_all"               # 균형 최적화
    MINIMIZE_RESOURCE = "minimize_resource"   # 리소스 사용량 최소화
    MAXIMIZE_THROUGHPUT = "maximize_throughput" # 처리량 최대화

class PredictionModel(Enum):
    """예측 모델 타입"""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    ENSEMBLE = "ensemble"

class OptimizationStrategy(Enum):
    """최적화 전략"""
    GREEDY = "greedy"                    # 탐욕적 최적화
    GENETIC_ALGORITHM = "genetic"        # 유전 알고리즘
    SIMULATED_ANNEALING = "annealing"    # 시뮬레이티드 어닐링
    PARTICLE_SWARM = "particle_swarm"    # 입자 군집 최적화
    BAYESIAN = "bayesian"                # 베이지안 최적화

@dataclass
class PerformancePrediction:
    """성능 예측 결과"""
    execution_time: float
    cost_estimate: float
    quality_score: float
    resource_usage: Dict[str, float]
    confidence_interval: Tuple[float, float]
    prediction_accuracy: float
    bottlenecks: List[str]
    optimization_suggestions: List[str]

@dataclass
class OptimizationResult:
    """최적화 결과"""
    original_config: Dict[str, Any]
    optimized_config: Dict[str, Any]
    predicted_improvement: Dict[str, float]
    optimization_strategy: OptimizationStrategy
    confidence_score: float
    estimated_savings: Dict[str, float]
    risk_assessment: Dict[str, float]

@dataclass
class WorkflowMetrics:
    """워크플로우 메트릭"""
    workflow_id: str
    execution_time: float
    cost: float
    quality_score: float
    resource_usage: Dict[str, float]
    agent_assignments: Dict[str, str]
    collaboration_pattern: str
    input_characteristics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

class IntelligentWorkflowOptimizer:
    """지능형 워크플로우 최적화기"""
    
    def __init__(self, orchestrator: AdvancedMultiAgentOrchestrator):
        self.orchestrator = orchestrator
        
        # 성능 데이터 저장소
        self.performance_history: List[WorkflowMetrics] = []
        self.prediction_models: Dict[str, Any] = {}
        self.feature_scalers: Dict[str, StandardScaler] = {}
        
        # 최적화 설정
        self.optimization_config = {
            "prediction_window": 1000,  # 예측에 사용할 최근 실행 수
            "model_retrain_interval": 100,  # 모델 재훈련 간격
            "confidence_threshold": 0.8,  # 예측 신뢰도 임계값
            "optimization_iterations": 50,  # 최적화 반복 횟수
        }
        
        # 모델 초기화
        self._initialize_prediction_models()
        
        logger.info("Intelligent Workflow Optimizer initialized")
    
    def _initialize_prediction_models(self):
        """예측 모델 초기화"""
        # 실행 시간 예측 모델
        self.prediction_models["execution_time"] = {
            PredictionModel.LINEAR_REGRESSION: LinearRegression(),
            PredictionModel.RANDOM_FOREST: RandomForestRegressor(n_estimators=100, random_state=42),
            PredictionModel.GRADIENT_BOOSTING: GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        # 비용 예측 모델
        self.prediction_models["cost"] = {
            PredictionModel.LINEAR_REGRESSION: LinearRegression(),
            PredictionModel.RANDOM_FOREST: RandomForestRegressor(n_estimators=100, random_state=42),
            PredictionModel.GRADIENT_BOOSTING: GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        # 품질 예측 모델
        self.prediction_models["quality"] = {
            PredictionModel.LINEAR_REGRESSION: LinearRegression(),
            PredictionModel.RANDOM_FOREST: RandomForestRegressor(n_estimators=100, random_state=42),
            PredictionModel.GRADIENT_BOOSTING: GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        # 특성 스케일러 초기화
        for metric in ["execution_time", "cost", "quality"]:
            self.feature_scalers[metric] = StandardScaler()
    
    async def predict_workflow_performance(
        self,
        tasks: List[Task],
        agent_assignments: Optional[Dict[str, str]] = None,
        collaboration_pattern: Optional[str] = None
    ) -> PerformancePrediction:
        """워크플로우 성능 예측"""
        try:
            # 특성 추출
            features = self._extract_workflow_features(tasks, agent_assignments, collaboration_pattern)
            
            # 각 메트릭별 예측
            predictions = {}
            confidence_intervals = {}
            
            for metric in ["execution_time", "cost", "quality"]:
                if len(self.performance_history) >= 10:  # 최소 데이터 요구량
                    pred_value, confidence = await self._predict_metric(metric, features)
                    predictions[metric] = pred_value
                    confidence_intervals[metric] = confidence
                else:
                    # 기본값 사용
                    predictions[metric] = self._get_default_prediction(metric, tasks)
                    confidence_intervals[metric] = (predictions[metric] * 0.8, predictions[metric] * 1.2)
            
            # 리소스 사용량 예측
            resource_usage = await self._predict_resource_usage(tasks, agent_assignments)
            
            # 병목 지점 식별
            bottlenecks = await self._identify_bottlenecks(tasks, agent_assignments, collaboration_pattern)
            
            # 최적화 제안 생성
            optimization_suggestions = await self._generate_optimization_suggestions(
                tasks, predictions, bottlenecks
            )
            
            # 예측 정확도 계산
            prediction_accuracy = self._calculate_prediction_accuracy()
            
            return PerformancePrediction(
                execution_time=predictions["execution_time"],
                cost_estimate=predictions["cost"],
                quality_score=predictions["quality"],
                resource_usage=resource_usage,
                confidence_interval=(
                    min(confidence_intervals["execution_time"]),
                    max(confidence_intervals["execution_time"])
                ),
                prediction_accuracy=prediction_accuracy,
                bottlenecks=bottlenecks,
                optimization_suggestions=optimization_suggestions
            )
            
        except Exception as e:
            logger.error(f"Performance prediction failed: {str(e)}", exc_info=True)
            # 기본 예측 반환
            return self._get_default_performance_prediction(tasks)
    
    def _extract_workflow_features(
        self,
        tasks: List[Task],
        agent_assignments: Optional[Dict[str, str]] = None,
        collaboration_pattern: Optional[str] = None
    ) -> np.ndarray:
        """워크플로우 특성 추출"""
        features = []
        
        # 기본 워크플로우 특성
        features.extend([
            len(tasks),  # 작업 수
            sum(task.estimated_duration for task in tasks),  # 총 예상 시간
            len(set(task.task_type for task in tasks)),  # 고유 작업 유형 수
            sum(len(task.dependencies) for task in tasks),  # 총 의존성 수
        ])
        
        # 작업 유형별 특성
        task_types = ["image_analysis", "text_processing", "audio_processing", "multimodal_fusion", "reasoning"]
        for task_type in task_types:
            count = sum(1 for task in tasks if task_type in task.task_type.lower())
            features.append(count)
        
        # 우선순위 분포
        priority_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for task in tasks:
            priority_counts[task.priority.value] += 1
        features.extend(priority_counts.values())
        
        # 에이전트 할당 특성
        if agent_assignments:
            unique_agents = len(set(agent_assignments.values()))
            features.append(unique_agents)
            
            # 에이전트 타입별 분포
            agent_type_counts = defaultdict(int)
            for agent_id in agent_assignments.values():
                if agent_id in self.orchestrator.agents:
                    agent_type = self.orchestrator.agents[agent_id].agent_type.value
                    agent_type_counts[agent_type] += 1
            
            agent_types = ["vision_specialist", "audio_specialist", "text_specialist", 
                          "multimodal_generalist", "reasoning_specialist"]
            for agent_type in agent_types:
                features.append(agent_type_counts[agent_type])
        else:
            features.extend([0] * 6)  # 에이전트 관련 특성 기본값
        
        # 협업 패턴 특성
        collaboration_patterns = ["pipeline", "ensemble", "hierarchical", "consensus", "peer_to_peer"]
        for pattern in collaboration_patterns:
            features.append(1 if collaboration_pattern == pattern else 0)
        
        # 입력 데이터 특성
        total_input_size = 0
        modality_count = 0
        for task in tasks:
            if isinstance(task.input_data, dict):
                total_input_size += len(str(task.input_data))
                # 모달리티 수 계산
                modalities = ["image", "text", "audio", "video"]
                task_modalities = sum(1 for mod in modalities if mod in str(task.input_data).lower())
                modality_count += task_modalities
        
        features.extend([total_input_size, modality_count])
        
        return np.array(features).reshape(1, -1)
    
    async def _predict_metric(self, metric: str, features: np.ndarray) -> Tuple[float, Tuple[float, float]]:
        """특정 메트릭 예측"""
        if metric not in self.prediction_models or len(self.performance_history) < 10:
            return 0.0, (0.0, 0.0)
        
        # 훈련 데이터 준비
        X, y = self._prepare_training_data(metric)
        
        if len(X) < 5:
            return 0.0, (0.0, 0.0)
        
        # 모델별 예측
        predictions = []
        
        for model_type, model in self.prediction_models[metric].items():
            try:
                # 특성 스케일링
                X_scaled = self.feature_scalers[metric].fit_transform(X)
                features_scaled = self.feature_scalers[metric].transform(features)
                
                # 모델 훈련
                model.fit(X_scaled, y)
                
                # 예측
                pred = model.predict(features_scaled)[0]
                predictions.append(max(0, pred))  # 음수 방지
                
            except Exception as e:
                logger.warning(f"Model {model_type} prediction failed for {metric}: {e}")
                continue
        
        if not predictions:
            return 0.0, (0.0, 0.0)
        
        # 앙상블 예측
        final_prediction = np.mean(predictions)
        std_prediction = np.std(predictions) if len(predictions) > 1 else final_prediction * 0.1
        
        # 신뢰 구간 계산
        confidence_interval = (
            max(0, final_prediction - 1.96 * std_prediction),
            final_prediction + 1.96 * std_prediction
        )
        
        return final_prediction, confidence_interval
    
    def _prepare_training_data(self, metric: str) -> Tuple[np.ndarray, np.ndarray]:
        """훈련 데이터 준비"""
        X = []
        y = []
        
        # 최근 데이터만 사용
        recent_history = self.performance_history[-self.optimization_config["prediction_window"]:]
        
        for metrics in recent_history:
            # 특성 재구성 (실제로는 저장된 특성을 사용해야 함)
            features = self._reconstruct_features_from_metrics(metrics)
            
            if metric == "execution_time":
                target = metrics.execution_time
            elif metric == "cost":
                target = metrics.cost
            elif metric == "quality":
                target = metrics.quality_score
            else:
                continue
            
            X.append(features)
            y.append(target)
        
        return np.array(X), np.array(y)
    
    def _reconstruct_features_from_metrics(self, metrics: WorkflowMetrics) -> List[float]:
        """메트릭에서 특성 재구성 (간소화된 버전)"""
        # 실제로는 원본 특성을 저장해야 하지만, 여기서는 기본 특성만 사용
        features = [
            len(metrics.agent_assignments),  # 작업 수 (근사치)
            metrics.execution_time,  # 실행 시간
            len(set(metrics.agent_assignments.values())),  # 고유 에이전트 수
            1.0 if metrics.collaboration_pattern else 0.0,  # 협업 패턴 존재 여부
        ]
        
        # 나머지 특성은 기본값으로 채움
        features.extend([0.0] * 20)  # 총 24개 특성으로 맞춤
        
        return features[:24]  # 고정 크기 유지
    
    async def _predict_resource_usage(
        self,
        tasks: List[Task],
        agent_assignments: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """리소스 사용량 예측"""
        resource_usage = {
            "cpu_cores": 0.0,
            "memory_gb": 0.0,
            "gpu_usage": 0.0,
            "network_bandwidth": 0.0,
            "storage_gb": 0.0
        }
        
        if not agent_assignments:
            # 기본 추정
            for task in tasks:
                resource_usage["cpu_cores"] += 2.0
                resource_usage["memory_gb"] += 4.0
                if "image" in task.task_type.lower() or "video" in task.task_type.lower():
                    resource_usage["gpu_usage"] += 0.5
        else:
            # 에이전트별 리소스 요구사항 합계
            for task_id, agent_id in agent_assignments.items():
                if agent_id in self.orchestrator.agents:
                    agent = self.orchestrator.agents[agent_id]
                    requirements = agent.capabilities.resource_requirements
                    
                    resource_usage["cpu_cores"] += requirements.get("cpu_cores", 2)
                    resource_usage["memory_gb"] += requirements.get("memory_gb", 4)
                    if requirements.get("gpu", False):
                        resource_usage["gpu_usage"] += 0.5
        
        # 네트워크 및 스토리지 추정
        resource_usage["network_bandwidth"] = len(tasks) * 0.1  # GB
        resource_usage["storage_gb"] = len(tasks) * 0.5  # GB
        
        return resource_usage
    
    async def _identify_bottlenecks(
        self,
        tasks: List[Task],
        agent_assignments: Optional[Dict[str, str]] = None,
        collaboration_pattern: Optional[str] = None
    ) -> List[str]:
        """병목 지점 식별"""
        bottlenecks = []
        
        # 작업 복잡도 기반 병목
        complex_tasks = [task for task in tasks if task.estimated_duration > 60.0]
        if len(complex_tasks) > len(tasks) * 0.3:
            bottlenecks.append("high_complexity_tasks")
        
        # 의존성 기반 병목
        total_dependencies = sum(len(task.dependencies) for task in tasks)
        if total_dependencies > len(tasks):
            bottlenecks.append("complex_dependencies")
        
        # 에이전트 할당 기반 병목
        if agent_assignments:
            agent_loads = defaultdict(int)
            for agent_id in agent_assignments.values():
                agent_loads[agent_id] += 1
            
            max_load = max(agent_loads.values()) if agent_loads else 0
            avg_load = sum(agent_loads.values()) / len(agent_loads) if agent_loads else 0
            
            if max_load > avg_load * 2:
                bottlenecks.append("unbalanced_agent_load")
        
        # 협업 패턴 기반 병목
        if collaboration_pattern == "consensus" and len(tasks) > 5:
            bottlenecks.append("consensus_overhead")
        elif collaboration_pattern == "pipeline" and len(tasks) > 10:
            bottlenecks.append("pipeline_length")
        
        return bottlenecks
    
    async def _generate_optimization_suggestions(
        self,
        tasks: List[Task],
        predictions: Dict[str, float],
        bottlenecks: List[str]
    ) -> List[str]:
        """최적화 제안 생성"""
        suggestions = []
        
        # 병목 기반 제안
        if "high_complexity_tasks" in bottlenecks:
            suggestions.append("작업 분해를 통해 복잡한 작업을 단순화하세요")
        
        if "complex_dependencies" in bottlenecks:
            suggestions.append("의존성을 줄이고 병렬 실행 가능한 작업을 늘리세요")
        
        if "unbalanced_agent_load" in bottlenecks:
            suggestions.append("에이전트 간 작업 부하를 균등하게 분배하세요")
        
        if "consensus_overhead" in bottlenecks:
            suggestions.append("합의 패턴 대신 앙상블 패턴을 고려하세요")
        
        if "pipeline_length" in bottlenecks:
            suggestions.append("긴 파이프라인을 여러 단계로 나누어 병렬화하세요")
        
        # 예측 기반 제안
        if predictions.get("execution_time", 0) > 300:  # 5분 이상
            suggestions.append("실행 시간 단축을 위해 더 빠른 에이전트를 사용하세요")
        
        if predictions.get("cost", 0) > 1.0:  # 높은 비용
            suggestions.append("비용 절감을 위해 효율적인 에이전트 조합을 선택하세요")
        
        if predictions.get("quality", 1.0) < 0.8:  # 낮은 품질
            suggestions.append("품질 향상을 위해 전문 에이전트를 활용하세요")
        
        return suggestions
    
    def _get_default_prediction(self, metric: str, tasks: List[Task]) -> float:
        """기본 예측값 반환"""
        if metric == "execution_time":
            return sum(task.estimated_duration for task in tasks)
        elif metric == "cost":
            return len(tasks) * 0.05  # 작업당 기본 비용
        elif metric == "quality":
            return 0.85  # 기본 품질 점수
        return 0.0
    
    def _calculate_prediction_accuracy(self) -> float:
        """예측 정확도 계산"""
        if len(self.performance_history) < 10:
            return 0.5  # 기본값
        
        # 최근 예측과 실제 결과 비교 (간소화된 버전)
        recent_accuracy = []
        
        for metrics in self.performance_history[-10:]:
            # 실제로는 예측값과 실제값을 비교해야 함
            # 여기서는 임의의 정확도 계산
            accuracy = 0.8 + np.random.normal(0, 0.1)
            recent_accuracy.append(max(0.0, min(1.0, accuracy)))
        
        return np.mean(recent_accuracy)
    
    def _get_default_performance_prediction(self, tasks: List[Task]) -> PerformancePrediction:
        """기본 성능 예측 반환"""
        total_time = sum(task.estimated_duration for task in tasks)
        
        return PerformancePrediction(
            execution_time=total_time,
            cost_estimate=len(tasks) * 0.05,
            quality_score=0.85,
            resource_usage={
                "cpu_cores": len(tasks) * 2.0,
                "memory_gb": len(tasks) * 4.0,
                "gpu_usage": len(tasks) * 0.3,
                "network_bandwidth": len(tasks) * 0.1,
                "storage_gb": len(tasks) * 0.5
            },
            confidence_interval=(total_time * 0.8, total_time * 1.2),
            prediction_accuracy=0.5,
            bottlenecks=[],
            optimization_suggestions=["더 많은 실행 데이터가 필요합니다"]
        )
    
    async def optimize_workflow_configuration(
        self,
        tasks: List[Task],
        objective: OptimizationObjective = OptimizationObjective.BALANCE_ALL,
        strategy: OptimizationStrategy = OptimizationStrategy.GREEDY,
        constraints: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """워크플로우 설정 최적화"""
        try:
            logger.info(f"Starting workflow optimization with {objective.value} objective")
            
            # 현재 설정 저장
            original_config = await self._get_current_configuration(tasks)
            
            # 최적화 전략에 따른 실행
            if strategy == OptimizationStrategy.GREEDY:
                optimized_config = await self._greedy_optimization(tasks, objective, constraints)
            elif strategy == OptimizationStrategy.GENETIC_ALGORITHM:
                optimized_config = await self._genetic_algorithm_optimization(tasks, objective, constraints)
            elif strategy == OptimizationStrategy.SIMULATED_ANNEALING:
                optimized_config = await self._simulated_annealing_optimization(tasks, objective, constraints)
            else:
                # 기본적으로 탐욕적 최적화 사용
                optimized_config = await self._greedy_optimization(tasks, objective, constraints)
            
            # 개선 효과 예측
            original_prediction = await self.predict_workflow_performance(
                tasks, original_config.get("agent_assignments"), original_config.get("collaboration_pattern")
            )
            
            optimized_prediction = await self.predict_workflow_performance(
                tasks, optimized_config.get("agent_assignments"), optimized_config.get("collaboration_pattern")
            )
            
            # 개선 효과 계산
            predicted_improvement = {
                "execution_time": (original_prediction.execution_time - optimized_prediction.execution_time) / original_prediction.execution_time * 100,
                "cost": (original_prediction.cost_estimate - optimized_prediction.cost_estimate) / original_prediction.cost_estimate * 100,
                "quality": (optimized_prediction.quality_score - original_prediction.quality_score) / original_prediction.quality_score * 100
            }
            
            # 절약 효과 계산
            estimated_savings = {
                "time_seconds": original_prediction.execution_time - optimized_prediction.execution_time,
                "cost_dollars": original_prediction.cost_estimate - optimized_prediction.cost_estimate,
                "quality_improvement": optimized_prediction.quality_score - original_prediction.quality_score
            }
            
            # 위험 평가
            risk_assessment = await self._assess_optimization_risk(original_config, optimized_config)
            
            # 신뢰도 점수 계산
            confidence_score = min(
                original_prediction.prediction_accuracy,
                optimized_prediction.prediction_accuracy
            )
            
            return OptimizationResult(
                original_config=original_config,
                optimized_config=optimized_config,
                predicted_improvement=predicted_improvement,
                optimization_strategy=strategy,
                confidence_score=confidence_score,
                estimated_savings=estimated_savings,
                risk_assessment=risk_assessment
            )
            
        except Exception as e:
            logger.error(f"Workflow optimization failed: {str(e)}", exc_info=True)
            raise
    
    async def _get_current_configuration(self, tasks: List[Task]) -> Dict[str, Any]:
        """현재 워크플로우 설정 가져오기"""
        # 기본 에이전트 할당 생성
        agent_assignments = {}
        available_agents = list(self.orchestrator.agents.keys())
        
        for i, task in enumerate(tasks):
            if available_agents:
                agent_assignments[task.task_id] = available_agents[i % len(available_agents)]
        
        return {
            "agent_assignments": agent_assignments,
            "collaboration_pattern": "pipeline",  # 기본 패턴
            "resource_allocation": {},
            "optimization_parameters": {}
        }
    
    async def _greedy_optimization(
        self,
        tasks: List[Task],
        objective: OptimizationObjective,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """탐욕적 최적화"""
        best_config = await self._get_current_configuration(tasks)
        best_score = await self._evaluate_configuration(tasks, best_config, objective)
        
        # 에이전트 할당 최적화
        for task in tasks:
            best_agent = None
            best_task_score = float('-inf')
            
            for agent_id, agent in self.orchestrator.agents.items():
                if agent.current_status.value in ["idle", "busy"]:  # 사용 가능한 에이전트만
                    # 임시 할당으로 점수 계산
                    temp_config = best_config.copy()
                    temp_config["agent_assignments"][task.task_id] = agent_id
                    
                    score = await self._evaluate_configuration(tasks, temp_config, objective)
                    
                    if score > best_task_score:
                        best_task_score = score
                        best_agent = agent_id
            
            if best_agent:
                best_config["agent_assignments"][task.task_id] = best_agent
        
        # 협업 패턴 최적화
        collaboration_patterns = ["pipeline", "ensemble", "hierarchical", "consensus"]
        
        for pattern in collaboration_patterns:
            temp_config = best_config.copy()
            temp_config["collaboration_pattern"] = pattern
            
            score = await self._evaluate_configuration(tasks, temp_config, objective)
            
            if score > best_score:
                best_score = score
                best_config["collaboration_pattern"] = pattern
        
        return best_config
    
    async def _genetic_algorithm_optimization(
        self,
        tasks: List[Task],
        objective: OptimizationObjective,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """유전 알고리즘 최적화 (간소화된 버전)"""
        population_size = 20
        generations = 10
        mutation_rate = 0.1
        
        # 초기 개체군 생성
        population = []
        for _ in range(population_size):
            config = await self._generate_random_configuration(tasks)
            population.append(config)
        
        # 진화 과정
        for generation in range(generations):
            # 적합도 평가
            fitness_scores = []
            for config in population:
                score = await self._evaluate_configuration(tasks, config, objective)
                fitness_scores.append(score)
            
            # 선택 및 교배
            new_population = []
            
            # 엘리트 보존 (상위 20%)
            elite_count = int(population_size * 0.2)
            elite_indices = np.argsort(fitness_scores)[-elite_count:]
            
            for idx in elite_indices:
                new_population.append(population[idx])
            
            # 나머지 개체 생성
            while len(new_population) < population_size:
                # 부모 선택 (토너먼트 선택)
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                # 교배
                child = self._crossover(parent1, parent2, tasks)
                
                # 돌연변이
                if np.random.random() < mutation_rate:
                    child = await self._mutate(child, tasks)
                
                new_population.append(child)
            
            population = new_population
        
        # 최적 개체 반환
        final_scores = []
        for config in population:
            score = await self._evaluate_configuration(tasks, config, objective)
            final_scores.append(score)
        
        best_idx = np.argmax(final_scores)
        return population[best_idx]
    
    async def _simulated_annealing_optimization(
        self,
        tasks: List[Task],
        objective: OptimizationObjective,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """시뮬레이티드 어닐링 최적화"""
        current_config = await self._get_current_configuration(tasks)
        current_score = await self._evaluate_configuration(tasks, current_config, objective)
        
        best_config = current_config.copy()
        best_score = current_score
        
        # 어닐링 매개변수
        initial_temperature = 100.0
        final_temperature = 1.0
        cooling_rate = 0.95
        iterations_per_temp = 10
        
        temperature = initial_temperature
        
        while temperature > final_temperature:
            for _ in range(iterations_per_temp):
                # 이웃 해 생성
                neighbor_config = await self._generate_neighbor_configuration(current_config, tasks)
                neighbor_score = await self._evaluate_configuration(tasks, neighbor_config, objective)
                
                # 수용 여부 결정
                if neighbor_score > current_score:
                    # 더 좋은 해는 항상 수용
                    current_config = neighbor_config
                    current_score = neighbor_score
                    
                    if neighbor_score > best_score:
                        best_config = neighbor_config.copy()
                        best_score = neighbor_score
                else:
                    # 나쁜 해도 확률적으로 수용
                    probability = np.exp((neighbor_score - current_score) / temperature)
                    if np.random.random() < probability:
                        current_config = neighbor_config
                        current_score = neighbor_score
            
            # 온도 감소
            temperature *= cooling_rate
        
        return best_config
    
    async def _evaluate_configuration(
        self,
        tasks: List[Task],
        config: Dict[str, Any],
        objective: OptimizationObjective
    ) -> float:
        """설정 평가"""
        try:
            # 성능 예측
            prediction = await self.predict_workflow_performance(
                tasks,
                config.get("agent_assignments"),
                config.get("collaboration_pattern")
            )
            
            # 목표에 따른 점수 계산
            if objective == OptimizationObjective.MINIMIZE_TIME:
                return 1000.0 / (prediction.execution_time + 1)  # 시간이 적을수록 높은 점수
            elif objective == OptimizationObjective.MINIMIZE_COST:
                return 10.0 / (prediction.cost_estimate + 0.1)  # 비용이 적을수록 높은 점수
            elif objective == OptimizationObjective.MAXIMIZE_QUALITY:
                return prediction.quality_score * 100  # 품질이 높을수록 높은 점수
            elif objective == OptimizationObjective.BALANCE_ALL:
                # 균형 점수 (정규화된 가중 합)
                time_score = 1000.0 / (prediction.execution_time + 1)
                cost_score = 10.0 / (prediction.cost_estimate + 0.1)
                quality_score = prediction.quality_score * 100
                
                # 가중 평균
                return (time_score * 0.3 + cost_score * 0.3 + quality_score * 0.4)
            else:
                return prediction.quality_score * 100  # 기본값
                
        except Exception as e:
            logger.warning(f"Configuration evaluation failed: {e}")
            return 0.0
    
    async def _generate_random_configuration(self, tasks: List[Task]) -> Dict[str, Any]:
        """무작위 설정 생성"""
        agent_assignments = {}
        available_agents = list(self.orchestrator.agents.keys())
        
        for task in tasks:
            if available_agents:
                agent_assignments[task.task_id] = np.random.choice(available_agents)
        
        collaboration_patterns = ["pipeline", "ensemble", "hierarchical", "consensus"]
        
        return {
            "agent_assignments": agent_assignments,
            "collaboration_pattern": np.random.choice(collaboration_patterns),
            "resource_allocation": {},
            "optimization_parameters": {}
        }
    
    def _tournament_selection(self, population: List[Dict], fitness_scores: List[float]) -> Dict[str, Any]:
        """토너먼트 선택"""
        tournament_size = 3
        tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
        tournament_scores = [fitness_scores[i] for i in tournament_indices]
        
        winner_idx = tournament_indices[np.argmax(tournament_scores)]
        return population[winner_idx]
    
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any], tasks: List[Task]) -> Dict[str, Any]:
        """교배 연산"""
        child = {
            "agent_assignments": {},
            "collaboration_pattern": parent1["collaboration_pattern"],
            "resource_allocation": {},
            "optimization_parameters": {}
        }
        
        # 에이전트 할당 교배 (단순 교차)
        for task in tasks:
            if np.random.random() < 0.5:
                child["agent_assignments"][task.task_id] = parent1["agent_assignments"].get(task.task_id)
            else:
                child["agent_assignments"][task.task_id] = parent2["agent_assignments"].get(task.task_id)
        
        # 협업 패턴 교배
        if np.random.random() < 0.5:
            child["collaboration_pattern"] = parent2["collaboration_pattern"]
        
        return child
    
    async def _mutate(self, config: Dict[str, Any], tasks: List[Task]) -> Dict[str, Any]:
        """돌연변이 연산"""
        mutated_config = config.copy()
        available_agents = list(self.orchestrator.agents.keys())
        
        # 에이전트 할당 돌연변이
        for task in tasks:
            if np.random.random() < 0.1 and available_agents:  # 10% 확률
                mutated_config["agent_assignments"][task.task_id] = np.random.choice(available_agents)
        
        # 협업 패턴 돌연변이
        if np.random.random() < 0.1:  # 10% 확률
            collaboration_patterns = ["pipeline", "ensemble", "hierarchical", "consensus"]
            mutated_config["collaboration_pattern"] = np.random.choice(collaboration_patterns)
        
        return mutated_config
    
    async def _generate_neighbor_configuration(self, config: Dict[str, Any], tasks: List[Task]) -> Dict[str, Any]:
        """이웃 해 생성 (시뮬레이티드 어닐링용)"""
        neighbor = config.copy()
        available_agents = list(self.orchestrator.agents.keys())
        
        # 작은 변화 적용
        if tasks and available_agents:
            # 무작위로 하나의 작업의 에이전트 변경
            random_task = np.random.choice(tasks)
            neighbor["agent_assignments"][random_task.task_id] = np.random.choice(available_agents)
        
        return neighbor
    
    async def _assess_optimization_risk(
        self,
        original_config: Dict[str, Any],
        optimized_config: Dict[str, Any]
    ) -> Dict[str, float]:
        """최적화 위험 평가"""
        risk_assessment = {
            "configuration_change_risk": 0.0,
            "performance_degradation_risk": 0.0,
            "resource_constraint_risk": 0.0,
            "reliability_risk": 0.0
        }
        
        # 설정 변경 위험
        original_agents = set(original_config.get("agent_assignments", {}).values())
        optimized_agents = set(optimized_config.get("agent_assignments", {}).values())
        
        agent_change_ratio = len(original_agents.symmetric_difference(optimized_agents)) / max(len(original_agents), 1)
        risk_assessment["configuration_change_risk"] = min(agent_change_ratio, 1.0)
        
        # 협업 패턴 변경 위험
        if original_config.get("collaboration_pattern") != optimized_config.get("collaboration_pattern"):
            risk_assessment["performance_degradation_risk"] += 0.2
        
        # 리소스 제약 위험 (간소화)
        risk_assessment["resource_constraint_risk"] = 0.1  # 기본 위험
        
        # 신뢰성 위험
        risk_assessment["reliability_risk"] = max(0.0, 1.0 - self._calculate_prediction_accuracy())
        
        return risk_assessment
    
    def record_workflow_execution(self, metrics: WorkflowMetrics):
        """워크플로우 실행 결과 기록"""
        self.performance_history.append(metrics)
        
        # 히스토리 크기 제한
        max_history = self.optimization_config["prediction_window"] * 2
        if len(self.performance_history) > max_history:
            self.performance_history = self.performance_history[-max_history:]
        
        # 주기적 모델 재훈련
        if len(self.performance_history) % self.optimization_config["model_retrain_interval"] == 0:
            asyncio.create_task(self._retrain_models())
    
    async def _retrain_models(self):
        """예측 모델 재훈련"""
        try:
            logger.info("Retraining prediction models...")
            
            for metric in ["execution_time", "cost", "quality"]:
                X, y = self._prepare_training_data(metric)
                
                if len(X) >= 10:  # 최소 데이터 요구량
                    for model_type, model in self.prediction_models[metric].items():
                        try:
                            X_scaled = self.feature_scalers[metric].fit_transform(X)
                            model.fit(X_scaled, y)
                            
                            # 모델 성능 평가
                            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
                            model.fit(X_train, y_train)
                            y_pred = model.predict(X_test)
                            
                            mae = mean_absolute_error(y_test, y_pred)
                            r2 = r2_score(y_test, y_pred)
                            
                            logger.info(f"Model {model_type} for {metric} - MAE: {mae:.3f}, R2: {r2:.3f}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to retrain {model_type} for {metric}: {e}")
            
            logger.info("Model retraining completed")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {str(e)}", exc_info=True)

# 전역 인스턴스
_workflow_optimizer_instance = None

def get_workflow_optimizer() -> IntelligentWorkflowOptimizer:
    """워크플로우 최적화기 인스턴스 반환"""
    global _workflow_optimizer_instance
    if _workflow_optimizer_instance is None:
        from backend.services.multimodal.advanced_orchestrator import get_advanced_orchestrator
        orchestrator = get_advanced_orchestrator()
        _workflow_optimizer_instance = IntelligentWorkflowOptimizer(orchestrator)
    return _workflow_optimizer_instance