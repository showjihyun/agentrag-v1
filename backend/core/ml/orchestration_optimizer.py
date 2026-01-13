"""
AI-based Orchestration Optimizer

ML 기반 오케스트레이션 최적화 시스템
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np
import logging
from enum import Enum
import asyncio
import json

from backend.core.event_bus.validated_event_bus import ValidatedEventBus
from backend.core.monitoring.plugin_performance_monitor import PluginPerformanceMonitor


logger = logging.getLogger(__name__)


class OptimizationObjective(str, Enum):
    """최적화 목표"""
    PERFORMANCE = "performance"  # 성능 최적화
    COST = "cost"               # 비용 최적화
    RELIABILITY = "reliability"  # 안정성 최적화
    BALANCED = "balanced"       # 균형 최적화


@dataclass
class ResourceCost:
    """리소스 비용 정보"""
    cpu_cost_per_second: float = 0.001  # CPU 초당 비용
    memory_cost_per_mb_second: float = 0.0001  # 메모리 MB 초당 비용
    llm_api_cost_per_token: float = 0.00002  # LLM API 토큰당 비용
    storage_cost_per_mb: float = 0.00001  # 저장소 MB당 비용
    network_cost_per_mb: float = 0.0001  # 네트워크 MB당 비용


@dataclass
class PerformancePrediction:
    """성능 예측 결과"""
    pattern: str
    agents: List[str]
    predicted_execution_time: float
    predicted_success_rate: float
    predicted_cost: float
    confidence: float
    bottleneck_agents: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class OptimizationResult:
    """최적화 결과"""
    original_pattern: str
    optimized_pattern: str
    original_agents: List[str]
    optimized_agents: List[str]
    performance_improvement: float  # 성능 개선율 (%)
    cost_reduction: float          # 비용 절감율 (%)
    reliability_improvement: float  # 안정성 개선율 (%)
    confidence: float
    reasoning: str
    estimated_savings: Dict[str, float]


class MLOrchestrationOptimizer:
    """ML 기반 오케스트레이션 최적화기"""
    
    def __init__(
        self, 
        performance_monitor: PluginPerformanceMonitor,
        event_bus: ValidatedEventBus,
        resource_costs: Optional[ResourceCost] = None
    ):
        self.performance_monitor = performance_monitor
        self.event_bus = event_bus
        self.resource_costs = resource_costs or ResourceCost()
        
        # 학습 데이터 저장소
        self.execution_history: List[Dict[str, Any]] = []
        self.pattern_performance_matrix = {}
        self.agent_compatibility_matrix = {}
        
        # ML 모델 (간단한 통계 기반 모델로 시작)
        self.performance_model = PerformancePredictionModel()
        self.cost_model = CostPredictionModel()
        self.pattern_recommender = PatternRecommendationModel()
        
        # 최적화 설정
        self.optimization_enabled = True
        self.learning_rate = 0.1
        self.min_data_points = 10
        
    async def predict_performance(
        self,
        pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> PerformancePrediction:
        """성능 예측"""
        try:
            # 기존 실행 데이터 분석
            historical_data = self._get_historical_data(pattern, agents)
            
            # 성능 예측
            execution_time = await self._predict_execution_time(pattern, agents, task, historical_data)
            success_rate = await self._predict_success_rate(pattern, agents, historical_data)
            cost = await self._predict_cost(pattern, agents, task, execution_time)
            
            # 병목 지점 분석
            bottlenecks = await self._identify_bottlenecks(agents, historical_data)
            
            # 최적화 제안 생성
            suggestions = await self._generate_optimization_suggestions(
                pattern, agents, execution_time, success_rate, cost
            )
            
            # 신뢰도 계산
            confidence = self._calculate_prediction_confidence(historical_data)
            
            return PerformancePrediction(
                pattern=pattern,
                agents=agents,
                predicted_execution_time=execution_time,
                predicted_success_rate=success_rate,
                predicted_cost=cost,
                confidence=confidence,
                bottleneck_agents=bottlenecks,
                optimization_suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Performance prediction failed: {e}")
            # 기본값 반환
            return PerformancePrediction(
                pattern=pattern,
                agents=agents,
                predicted_execution_time=10.0,
                predicted_success_rate=0.8,
                predicted_cost=0.1,
                confidence=0.1
            )
    
    async def optimize_orchestration(
        self,
        current_pattern: str,
        current_agents: List[str],
        task: Dict[str, Any],
        objective: OptimizationObjective = OptimizationObjective.BALANCED,
        constraints: Dict[str, Any] = None
    ) -> OptimizationResult:
        """오케스트레이션 최적화"""
        constraints = constraints or {}
        
        try:
            # 현재 성능 예측
            current_prediction = await self.predict_performance(current_pattern, current_agents, task)
            
            # 최적화 후보 생성
            optimization_candidates = await self._generate_optimization_candidates(
                current_pattern, current_agents, task, objective, constraints
            )
            
            # 각 후보의 성능 예측
            candidate_predictions = []
            for candidate in optimization_candidates:
                prediction = await self.predict_performance(
                    candidate['pattern'], candidate['agents'], task
                )
                candidate_predictions.append((candidate, prediction))
            
            # 최적 후보 선택
            best_candidate, best_prediction = await self._select_best_candidate(
                candidate_predictions, objective, current_prediction
            )
            
            if not best_candidate:
                # 최적화 불가능한 경우
                return OptimizationResult(
                    original_pattern=current_pattern,
                    optimized_pattern=current_pattern,
                    original_agents=current_agents,
                    optimized_agents=current_agents,
                    performance_improvement=0.0,
                    cost_reduction=0.0,
                    reliability_improvement=0.0,
                    confidence=1.0,
                    reasoning="현재 설정이 이미 최적입니다.",
                    estimated_savings={}
                )
            
            # 개선율 계산
            performance_improvement = (
                (current_prediction.predicted_execution_time - best_prediction.predicted_execution_time) 
                / current_prediction.predicted_execution_time * 100
            )
            
            cost_reduction = (
                (current_prediction.predicted_cost - best_prediction.predicted_cost) 
                / current_prediction.predicted_cost * 100
            )
            
            reliability_improvement = (
                (best_prediction.predicted_success_rate - current_prediction.predicted_success_rate) 
                / current_prediction.predicted_success_rate * 100
            )
            
            # 절약 추정치 계산
            estimated_savings = await self._calculate_estimated_savings(
                current_prediction, best_prediction, task
            )
            
            # 최적화 이유 생성
            reasoning = await self._generate_optimization_reasoning(
                current_pattern, best_candidate['pattern'],
                current_agents, best_candidate['agents'],
                objective, performance_improvement, cost_reduction
            )
            
            return OptimizationResult(
                original_pattern=current_pattern,
                optimized_pattern=best_candidate['pattern'],
                original_agents=current_agents,
                optimized_agents=best_candidate['agents'],
                performance_improvement=max(0, performance_improvement),
                cost_reduction=max(0, cost_reduction),
                reliability_improvement=max(0, reliability_improvement),
                confidence=best_prediction.confidence,
                reasoning=reasoning,
                estimated_savings=estimated_savings
            )
            
        except Exception as e:
            logger.error(f"Orchestration optimization failed: {e}")
            raise
    
    async def auto_tune_performance(
        self,
        pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        target_metrics: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """자동 성능 튜닝"""
        target_metrics = target_metrics or {
            'max_execution_time': 5.0,
            'min_success_rate': 0.95,
            'max_cost': 0.1
        }
        
        tuning_results = {
            'original_config': {
                'pattern': pattern,
                'agents': agents,
                'task': task
            },
            'tuning_iterations': [],
            'final_config': None,
            'performance_gains': {},
            'tuning_successful': False
        }
        
        current_pattern = pattern
        current_agents = agents.copy()
        current_task = task.copy()
        
        max_iterations = 5
        
        for iteration in range(max_iterations):
            # 현재 성능 측정
            current_prediction = await self.predict_performance(
                current_pattern, current_agents, current_task
            )
            
            # 목표 달성 여부 확인
            meets_targets = (
                current_prediction.predicted_execution_time <= target_metrics['max_execution_time'] and
                current_prediction.predicted_success_rate >= target_metrics['min_success_rate'] and
                current_prediction.predicted_cost <= target_metrics['max_cost']
            )
            
            iteration_result = {
                'iteration': iteration + 1,
                'pattern': current_pattern,
                'agents': current_agents,
                'prediction': current_prediction,
                'meets_targets': meets_targets,
                'adjustments': []
            }
            
            if meets_targets:
                tuning_results['tuning_successful'] = True
                break
            
            # 성능 조정
            adjustments = []
            
            # 실행 시간 최적화
            if current_prediction.predicted_execution_time > target_metrics['max_execution_time']:
                if current_pattern != 'parallel' and len(current_agents) > 1:
                    current_pattern = 'parallel'
                    adjustments.append('패턴을 parallel로 변경하여 실행 시간 단축')
                
                # 느린 Agent 제거 또는 교체
                if current_prediction.bottleneck_agents:
                    for bottleneck in current_prediction.bottleneck_agents[:1]:  # 하나씩 처리
                        if bottleneck in current_agents and len(current_agents) > 1:
                            current_agents.remove(bottleneck)
                            adjustments.append(f'병목 Agent {bottleneck} 제거')
                            break
            
            # 성공률 최적화
            if current_prediction.predicted_success_rate < target_metrics['min_success_rate']:
                if current_pattern != 'consensus':
                    current_pattern = 'consensus'
                    adjustments.append('패턴을 consensus로 변경하여 안정성 향상')
                
                # 안정적인 Agent 추가
                reliable_agents = await self._get_reliable_agents()
                for agent in reliable_agents:
                    if agent not in current_agents and len(current_agents) < 5:
                        current_agents.append(agent)
                        adjustments.append(f'안정적인 Agent {agent} 추가')
                        break
            
            # 비용 최적화
            if current_prediction.predicted_cost > target_metrics['max_cost']:
                # 비용 효율적인 Agent로 교체
                cost_efficient_agents = await self._get_cost_efficient_agents()
                for i, agent in enumerate(current_agents):
                    if agent not in cost_efficient_agents and cost_efficient_agents:
                        current_agents[i] = cost_efficient_agents[0]
                        adjustments.append(f'Agent {agent}를 비용 효율적인 {cost_efficient_agents[0]}로 교체')
                        break
            
            iteration_result['adjustments'] = adjustments
            tuning_results['tuning_iterations'].append(iteration_result)
            
            # 조정이 없으면 중단
            if not adjustments:
                break
        
        # 최종 설정
        tuning_results['final_config'] = {
            'pattern': current_pattern,
            'agents': current_agents,
            'task': current_task
        }
        
        # 성능 향상 계산
        if tuning_results['tuning_iterations']:
            original = tuning_results['tuning_iterations'][0]['prediction']
            final = tuning_results['tuning_iterations'][-1]['prediction']
            
            tuning_results['performance_gains'] = {
                'execution_time_improvement': (
                    (original.predicted_execution_time - final.predicted_execution_time) 
                    / original.predicted_execution_time * 100
                ),
                'success_rate_improvement': (
                    (final.predicted_success_rate - original.predicted_success_rate) 
                    / original.predicted_success_rate * 100
                ),
                'cost_reduction': (
                    (original.predicted_cost - final.predicted_cost) 
                    / original.predicted_cost * 100
                )
            }
        
        return tuning_results
    
    async def learn_from_execution(
        self,
        pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        actual_result: Dict[str, Any]
    ):
        """실행 결과로부터 학습"""
        if not self.optimization_enabled:
            return
        
        try:
            execution_record = {
                'timestamp': datetime.now().isoformat(),
                'pattern': pattern,
                'agents': agents,
                'task': task,
                'actual_execution_time': actual_result.get('execution_time', 0),
                'actual_success': actual_result.get('success', False),
                'actual_cost': actual_result.get('cost', 0),
                'error_message': actual_result.get('error'),
                'agent_results': actual_result.get('agent_results', {})
            }
            
            # 실행 이력에 추가
            self.execution_history.append(execution_record)
            
            # 최근 1000개 기록만 유지
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
            
            # 패턴 성능 매트릭스 업데이트
            await self._update_pattern_performance_matrix(execution_record)
            
            # Agent 호환성 매트릭스 업데이트
            await self._update_agent_compatibility_matrix(execution_record)
            
            # ML 모델 재학습 (비동기)
            if len(self.execution_history) >= self.min_data_points:
                asyncio.create_task(self._retrain_models())
            
            # 학습 이벤트 발행
            await self.event_bus.publish(
                'orchestration_learning_update',
                {
                    'pattern': pattern,
                    'agents': agents,
                    'learning_data_size': len(self.execution_history),
                    'model_accuracy': await self._calculate_model_accuracy()
                },
                source='ml_orchestration_optimizer'
            )
            
        except Exception as e:
            logger.error(f"Learning from execution failed: {e}")
    
    # 내부 메서드들
    
    def _get_historical_data(self, pattern: str, agents: List[str]) -> List[Dict[str, Any]]:
        """패턴과 Agent에 대한 과거 데이터 조회"""
        return [
            record for record in self.execution_history
            if record['pattern'] == pattern and 
            set(record['agents']).intersection(set(agents))
        ]
    
    async def _predict_execution_time(
        self, 
        pattern: str, 
        agents: List[str], 
        task: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> float:
        """실행 시간 예측"""
        if not historical_data:
            # 기본 추정치
            base_time = 2.0
            if pattern == 'parallel':
                return base_time
            elif pattern == 'sequential':
                return base_time * len(agents)
            elif pattern == 'consensus':
                return base_time * 1.5
            else:
                return base_time * 1.2
        
        # 과거 데이터 기반 예측
        execution_times = [r['actual_execution_time'] for r in historical_data if r['actual_execution_time'] > 0]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            
            # 작업 복잡도에 따른 조정
            complexity_factor = self._calculate_task_complexity(task)
            return avg_time * complexity_factor
        
        return 5.0  # 기본값
    
    async def _predict_success_rate(
        self, 
        pattern: str, 
        agents: List[str],
        historical_data: List[Dict[str, Any]]
    ) -> float:
        """성공률 예측"""
        if not historical_data:
            # 패턴별 기본 성공률
            default_rates = {
                'sequential': 0.85,
                'parallel': 0.80,
                'consensus': 0.90,
                'swarm': 0.75,
                'dynamic_routing': 0.88
            }
            return default_rates.get(pattern, 0.80)
        
        # 과거 데이터 기반 예측
        successes = sum(1 for r in historical_data if r['actual_success'])
        total = len(historical_data)
        
        if total > 0:
            base_rate = successes / total
            
            # Agent 안정성 고려
            agent_reliability = await self._get_agent_reliability(agents)
            combined_reliability = sum(agent_reliability.values()) / len(agent_reliability) if agent_reliability else 0.8
            
            return min(0.99, base_rate * 0.7 + combined_reliability * 0.3)
        
        return 0.80
    
    async def _predict_cost(
        self, 
        pattern: str, 
        agents: List[str], 
        task: Dict[str, Any],
        execution_time: float
    ) -> float:
        """비용 예측"""
        total_cost = 0.0
        
        # CPU 비용
        cpu_usage = len(agents) * execution_time
        total_cost += cpu_usage * self.resource_costs.cpu_cost_per_second
        
        # 메모리 비용 (Agent당 평균 100MB 가정)
        memory_usage = len(agents) * 100 * execution_time
        total_cost += memory_usage * self.resource_costs.memory_cost_per_mb_second
        
        # LLM API 비용 (작업 복잡도에 따라)
        task_complexity = self._calculate_task_complexity(task)
        estimated_tokens = task_complexity * 1000  # 복잡도당 1000 토큰 가정
        total_cost += estimated_tokens * self.resource_costs.llm_api_cost_per_token
        
        # 패턴별 추가 비용
        pattern_multipliers = {
            'sequential': 1.0,
            'parallel': 1.2,  # 병렬 처리 오버헤드
            'consensus': 1.5,  # 합의 과정 비용
            'swarm': 1.8,     # 군집 지능 계산 비용
            'dynamic_routing': 1.1
        }
        
        total_cost *= pattern_multipliers.get(pattern, 1.0)
        
        return round(total_cost, 4)
    
    def _calculate_task_complexity(self, task: Dict[str, Any]) -> float:
        """작업 복잡도 계산"""
        complexity = 1.0
        
        # 입력 데이터 크기
        if 'input_size' in task:
            complexity += task['input_size'] / 1000  # KB당 0.001 추가
        
        # 요구사항 수
        if 'requirements' in task and isinstance(task['requirements'], list):
            complexity += len(task['requirements']) * 0.1
        
        # 출력 형식 복잡도
        if 'output_format' in task:
            format_complexity = {
                'text': 1.0,
                'json': 1.2,
                'structured': 1.5,
                'analysis': 2.0
            }
            complexity *= format_complexity.get(task['output_format'], 1.0)
        
        return min(5.0, complexity)  # 최대 5배
    
    async def _identify_bottlenecks(
        self, 
        agents: List[str],
        historical_data: List[Dict[str, Any]]
    ) -> List[str]:
        """병목 Agent 식별"""
        bottlenecks = []
        
        # 각 Agent의 성능 통계 분석
        for agent in agents:
            agent_performance = self.performance_monitor.get_plugin_metrics(agent)
            
            if 'aggregated_metrics' in agent_performance:
                metrics = agent_performance['aggregated_metrics']
                
                # 평균 실행 시간이 긴 Agent
                if metrics.get('avg_execution_time', 0) > 3.0:
                    bottlenecks.append(agent)
                
                # 성공률이 낮은 Agent
                elif metrics.get('success_rate', 1.0) < 0.8:
                    bottlenecks.append(agent)
        
        return bottlenecks
    
    async def _generate_optimization_suggestions(
        self,
        pattern: str,
        agents: List[str],
        execution_time: float,
        success_rate: float,
        cost: float
    ) -> List[str]:
        """최적화 제안 생성"""
        suggestions = []
        
        # 실행 시간 최적화
        if execution_time > 5.0:
            if pattern != 'parallel' and len(agents) > 1:
                suggestions.append("병렬 실행 패턴으로 변경하여 실행 시간 단축")
            
            if len(agents) > 3:
                suggestions.append("Agent 수를 줄여 오버헤드 감소")
        
        # 성공률 최적화
        if success_rate < 0.9:
            if pattern != 'consensus':
                suggestions.append("합의 패턴으로 변경하여 안정성 향상")
            
            suggestions.append("안정적인 Agent 추가로 신뢰성 향상")
        
        # 비용 최적화
        if cost > 0.1:
            suggestions.append("비용 효율적인 Agent로 교체")
            
            if pattern in ['swarm', 'consensus']:
                suggestions.append("더 간단한 패턴으로 변경하여 비용 절감")
        
        return suggestions
    
    def _calculate_prediction_confidence(self, historical_data: List[Dict[str, Any]]) -> float:
        """예측 신뢰도 계산"""
        if not historical_data:
            return 0.3  # 데이터 없음
        
        data_size = len(historical_data)
        
        # 데이터 크기에 따른 기본 신뢰도
        if data_size >= 50:
            base_confidence = 0.9
        elif data_size >= 20:
            base_confidence = 0.7
        elif data_size >= 10:
            base_confidence = 0.5
        else:
            base_confidence = 0.3
        
        # 데이터 일관성 확인
        if data_size >= 5:
            execution_times = [r['actual_execution_time'] for r in historical_data[-10:] if r['actual_execution_time'] > 0]
            if execution_times:
                variance = np.var(execution_times)
                mean_time = np.mean(execution_times)
                cv = variance / (mean_time ** 2) if mean_time > 0 else 1.0  # 변동계수
                
                # 변동이 적을수록 신뢰도 높음
                consistency_factor = max(0.5, 1.0 - cv)
                base_confidence *= consistency_factor
        
        return min(0.95, base_confidence)
    
    async def _generate_optimization_candidates(
        self,
        current_pattern: str,
        current_agents: List[str],
        task: Dict[str, Any],
        objective: OptimizationObjective,
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """최적화 후보 생성"""
        candidates = []
        
        available_patterns = ['sequential', 'parallel', 'consensus', 'dynamic_routing', 'swarm']
        available_agents = await self._get_available_agents()
        
        # 패턴 변경 후보
        for pattern in available_patterns:
            if pattern != current_pattern:
                candidates.append({
                    'pattern': pattern,
                    'agents': current_agents,
                    'change_type': 'pattern_change',
                    'description': f'패턴을 {pattern}으로 변경'
                })
        
        # Agent 조합 변경 후보
        if objective in [OptimizationObjective.PERFORMANCE, OptimizationObjective.BALANCED]:
            # 고성능 Agent 추가
            high_performance_agents = await self._get_high_performance_agents()
            for agent in high_performance_agents:
                if agent not in current_agents and len(current_agents) < 5:
                    new_agents = current_agents + [agent]
                    candidates.append({
                        'pattern': current_pattern,
                        'agents': new_agents,
                        'change_type': 'agent_addition',
                        'description': f'고성능 Agent {agent} 추가'
                    })
        
        if objective in [OptimizationObjective.COST, OptimizationObjective.BALANCED]:
            # 비용 효율적인 Agent로 교체
            cost_efficient_agents = await self._get_cost_efficient_agents()
            for i, current_agent in enumerate(current_agents):
                for efficient_agent in cost_efficient_agents:
                    if efficient_agent != current_agent:
                        new_agents = current_agents.copy()
                        new_agents[i] = efficient_agent
                        candidates.append({
                            'pattern': current_pattern,
                            'agents': new_agents,
                            'change_type': 'agent_replacement',
                            'description': f'{current_agent}를 {efficient_agent}로 교체'
                        })
        
        # 제약 조건 적용
        filtered_candidates = []
        for candidate in candidates:
            if self._meets_constraints(candidate, constraints):
                filtered_candidates.append(candidate)
        
        return filtered_candidates[:10]  # 최대 10개 후보
    
    def _meets_constraints(self, candidate: Dict[str, Any], constraints: Dict[str, Any]) -> bool:
        """제약 조건 확인"""
        if not constraints:
            return True
        
        # 최대 Agent 수 제약
        if 'max_agents' in constraints:
            if len(candidate['agents']) > constraints['max_agents']:
                return False
        
        # 필수 Agent 제약
        if 'required_agents' in constraints:
            required = set(constraints['required_agents'])
            current = set(candidate['agents'])
            if not required.issubset(current):
                return False
        
        # 금지된 패턴 제약
        if 'forbidden_patterns' in constraints:
            if candidate['pattern'] in constraints['forbidden_patterns']:
                return False
        
        return True
    
    async def _select_best_candidate(
        self,
        candidate_predictions: List[Tuple[Dict[str, Any], PerformancePrediction]],
        objective: OptimizationObjective,
        current_prediction: PerformancePrediction
    ) -> Tuple[Optional[Dict[str, Any]], Optional[PerformancePrediction]]:
        """최적 후보 선택"""
        if not candidate_predictions:
            return None, None
        
        best_candidate = None
        best_prediction = None
        best_score = float('-inf')
        
        for candidate, prediction in candidate_predictions:
            score = self._calculate_optimization_score(
                prediction, current_prediction, objective
            )
            
            if score > best_score:
                best_score = score
                best_candidate = candidate
                best_prediction = prediction
        
        # 개선이 있는 경우만 반환
        if best_score > 0:
            return best_candidate, best_prediction
        
        return None, None
    
    def _calculate_optimization_score(
        self,
        prediction: PerformancePrediction,
        current_prediction: PerformancePrediction,
        objective: OptimizationObjective
    ) -> float:
        """최적화 점수 계산"""
        # 성능 개선율
        time_improvement = (
            (current_prediction.predicted_execution_time - prediction.predicted_execution_time) 
            / current_prediction.predicted_execution_time
        )
        
        # 비용 절감율
        cost_reduction = (
            (current_prediction.predicted_cost - prediction.predicted_cost) 
            / current_prediction.predicted_cost
        )
        
        # 안정성 개선율
        reliability_improvement = (
            prediction.predicted_success_rate - current_prediction.predicted_success_rate
        )
        
        # 목표에 따른 가중치 적용
        if objective == OptimizationObjective.PERFORMANCE:
            score = time_improvement * 0.7 + reliability_improvement * 0.2 + cost_reduction * 0.1
        elif objective == OptimizationObjective.COST:
            score = cost_reduction * 0.7 + time_improvement * 0.2 + reliability_improvement * 0.1
        elif objective == OptimizationObjective.RELIABILITY:
            score = reliability_improvement * 0.7 + time_improvement * 0.2 + cost_reduction * 0.1
        else:  # BALANCED
            score = (time_improvement + cost_reduction + reliability_improvement) / 3
        
        # 신뢰도로 가중
        score *= prediction.confidence
        
        return score
    
    async def _calculate_estimated_savings(
        self,
        current_prediction: PerformancePrediction,
        optimized_prediction: PerformancePrediction,
        task: Dict[str, Any]
    ) -> Dict[str, float]:
        """절약 추정치 계산"""
        # 월간 실행 횟수 추정 (기본값: 1000회)
        monthly_executions = task.get('estimated_monthly_executions', 1000)
        
        # 시간 절약
        time_saved_per_execution = max(0, 
            current_prediction.predicted_execution_time - optimized_prediction.predicted_execution_time
        )
        monthly_time_saved = time_saved_per_execution * monthly_executions
        
        # 비용 절약
        cost_saved_per_execution = max(0,
            current_prediction.predicted_cost - optimized_prediction.predicted_cost
        )
        monthly_cost_saved = cost_saved_per_execution * monthly_executions
        
        # 연간 추정치
        annual_time_saved = monthly_time_saved * 12
        annual_cost_saved = monthly_cost_saved * 12
        
        return {
            'time_saved_per_execution_seconds': round(time_saved_per_execution, 2),
            'cost_saved_per_execution_dollars': round(cost_saved_per_execution, 4),
            'monthly_time_saved_hours': round(monthly_time_saved / 3600, 2),
            'monthly_cost_saved_dollars': round(monthly_cost_saved, 2),
            'annual_time_saved_hours': round(annual_time_saved / 3600, 2),
            'annual_cost_saved_dollars': round(annual_cost_saved, 2)
        }
    
    async def _generate_optimization_reasoning(
        self,
        original_pattern: str,
        optimized_pattern: str,
        original_agents: List[str],
        optimized_agents: List[str],
        objective: OptimizationObjective,
        performance_improvement: float,
        cost_reduction: float
    ) -> str:
        """최적화 이유 생성"""
        reasons = []
        
        # 패턴 변경 이유
        if original_pattern != optimized_pattern:
            pattern_reasons = {
                'parallel': '병렬 실행으로 처리 시간을 단축',
                'consensus': '합의 메커니즘으로 결과의 신뢰성을 향상',
                'sequential': '순차 실행으로 리소스 사용량을 최적화',
                'dynamic_routing': '동적 라우팅으로 최적 Agent를 선택',
                'swarm': '군집 지능으로 복잡한 문제를 효율적으로 해결'
            }
            reasons.append(pattern_reasons.get(optimized_pattern, f'{optimized_pattern} 패턴으로 변경'))
        
        # Agent 변경 이유
        added_agents = set(optimized_agents) - set(original_agents)
        removed_agents = set(original_agents) - set(optimized_agents)
        
        if added_agents:
            reasons.append(f'고성능 Agent {", ".join(added_agents)} 추가')
        
        if removed_agents:
            reasons.append(f'병목 Agent {", ".join(removed_agents)} 제거')
        
        # 개선 효과
        if performance_improvement > 5:
            reasons.append(f'실행 시간 {performance_improvement:.1f}% 개선')
        
        if cost_reduction > 5:
            reasons.append(f'비용 {cost_reduction:.1f}% 절감')
        
        # 목표별 추가 설명
        objective_explanations = {
            OptimizationObjective.PERFORMANCE: '성능 최적화를 위해',
            OptimizationObjective.COST: '비용 효율성을 위해',
            OptimizationObjective.RELIABILITY: '안정성 향상을 위해',
            OptimizationObjective.BALANCED: '균형잡힌 최적화를 위해'
        }
        
        prefix = objective_explanations.get(objective, '')
        
        if reasons:
            return f"{prefix} {', '.join(reasons)}했습니다."
        else:
            return "현재 설정이 이미 최적 상태입니다."
    
    # 헬퍼 메서드들
    
    async def _get_available_agents(self) -> List[str]:
        """사용 가능한 Agent 목록"""
        return ['vector_search', 'web_search', 'local_data', 'aggregator']
    
    async def _get_high_performance_agents(self) -> List[str]:
        """고성능 Agent 목록"""
        # 성능 메트릭 기반으로 상위 Agent 반환
        all_agents = await self._get_available_agents()
        performance_scores = {}
        
        for agent in all_agents:
            metrics = self.performance_monitor.get_plugin_metrics(agent)
            if 'aggregated_metrics' in metrics:
                # 성능 점수 = 성공률 / 평균 실행시간
                success_rate = metrics['aggregated_metrics'].get('success_rate', 0.5)
                avg_time = metrics['aggregated_metrics'].get('avg_execution_time', 10.0)
                performance_scores[agent] = success_rate / max(0.1, avg_time)
        
        # 성능 순으로 정렬
        sorted_agents = sorted(performance_scores.items(), key=lambda x: x[1], reverse=True)
        return [agent for agent, score in sorted_agents[:3]]  # 상위 3개
    
    async def _get_cost_efficient_agents(self) -> List[str]:
        """비용 효율적인 Agent 목록"""
        # 비용 대비 성능이 좋은 Agent 반환
        all_agents = await self._get_available_agents()
        efficiency_scores = {}
        
        for agent in all_agents:
            metrics = self.performance_monitor.get_plugin_metrics(agent)
            if 'aggregated_metrics' in metrics:
                success_rate = metrics['aggregated_metrics'].get('success_rate', 0.5)
                avg_time = metrics['aggregated_metrics'].get('avg_execution_time', 10.0)
                
                # 비용 추정 (실행시간 기반)
                estimated_cost = avg_time * 0.001  # 간단한 비용 모델
                
                # 효율성 = 성공률 / 비용
                efficiency_scores[agent] = success_rate / max(0.001, estimated_cost)
        
        sorted_agents = sorted(efficiency_scores.items(), key=lambda x: x[1], reverse=True)
        return [agent for agent, score in sorted_agents[:3]]
    
    async def _get_reliable_agents(self) -> List[str]:
        """안정적인 Agent 목록"""
        all_agents = await self._get_available_agents()
        reliability_scores = {}
        
        for agent in all_agents:
            metrics = self.performance_monitor.get_plugin_metrics(agent)
            if 'aggregated_metrics' in metrics:
                reliability_scores[agent] = metrics['aggregated_metrics'].get('success_rate', 0.5)
        
        sorted_agents = sorted(reliability_scores.items(), key=lambda x: x[1], reverse=True)
        return [agent for agent, score in sorted_agents if score > 0.8]
    
    async def _get_agent_reliability(self, agents: List[str]) -> Dict[str, float]:
        """Agent별 안정성 점수"""
        reliability = {}
        
        for agent in agents:
            metrics = self.performance_monitor.get_plugin_metrics(agent)
            if 'aggregated_metrics' in metrics:
                reliability[agent] = metrics['aggregated_metrics'].get('success_rate', 0.8)
            else:
                reliability[agent] = 0.8  # 기본값
        
        return reliability
    
    async def _update_pattern_performance_matrix(self, execution_record: Dict[str, Any]):
        """패턴 성능 매트릭스 업데이트"""
        pattern = execution_record['pattern']
        
        if pattern not in self.pattern_performance_matrix:
            self.pattern_performance_matrix[pattern] = {
                'total_executions': 0,
                'total_time': 0.0,
                'successes': 0,
                'total_cost': 0.0
            }
        
        matrix = self.pattern_performance_matrix[pattern]
        matrix['total_executions'] += 1
        matrix['total_time'] += execution_record['actual_execution_time']
        matrix['total_cost'] += execution_record['actual_cost']
        
        if execution_record['actual_success']:
            matrix['successes'] += 1
    
    async def _update_agent_compatibility_matrix(self, execution_record: Dict[str, Any]):
        """Agent 호환성 매트릭스 업데이트"""
        agents = execution_record['agents']
        success = execution_record['actual_success']
        
        # 모든 Agent 쌍에 대해 호환성 업데이트
        for i, agent1 in enumerate(agents):
            for j, agent2 in enumerate(agents):
                if i < j:  # 중복 방지
                    pair_key = f"{agent1}_{agent2}"
                    
                    if pair_key not in self.agent_compatibility_matrix:
                        self.agent_compatibility_matrix[pair_key] = {
                            'total_executions': 0,
                            'successes': 0
                        }
                    
                    matrix = self.agent_compatibility_matrix[pair_key]
                    matrix['total_executions'] += 1
                    
                    if success:
                        matrix['successes'] += 1
    
    async def _retrain_models(self):
        """ML 모델 재학습"""
        try:
            # 간단한 통계 기반 모델 업데이트
            await self.performance_model.update(self.execution_history)
            await self.cost_model.update(self.execution_history)
            await self.pattern_recommender.update(self.execution_history)
            
            logger.info("ML models retrained successfully")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
    
    async def _calculate_model_accuracy(self) -> float:
        """모델 정확도 계산"""
        if len(self.execution_history) < 10:
            return 0.5
        
        # 최근 10개 예측의 정확도 계산 (간단한 예시)
        recent_records = self.execution_history[-10:]
        accurate_predictions = 0
        
        for record in recent_records:
            # 실제 실행시간과 예측 실행시간 비교 (±20% 오차 허용)
            predicted_time = await self._predict_execution_time(
                record['pattern'], 
                record['agents'], 
                record['task'],
                []
            )
            
            actual_time = record['actual_execution_time']
            
            if actual_time > 0:
                error_rate = abs(predicted_time - actual_time) / actual_time
                if error_rate <= 0.2:  # 20% 이내 오차
                    accurate_predictions += 1
        
        return accurate_predictions / len(recent_records)


# 간단한 ML 모델 클래스들

class PerformancePredictionModel:
    """성능 예측 모델"""
    
    def __init__(self):
        self.pattern_stats = {}
    
    async def update(self, execution_history: List[Dict[str, Any]]):
        """모델 업데이트"""
        for record in execution_history:
            pattern = record['pattern']
            if pattern not in self.pattern_stats:
                self.pattern_stats[pattern] = []
            
            self.pattern_stats[pattern].append({
                'execution_time': record['actual_execution_time'],
                'success': record['actual_success'],
                'agent_count': len(record['agents'])
            })


class CostPredictionModel:
    """비용 예측 모델"""
    
    def __init__(self):
        self.cost_stats = {}
    
    async def update(self, execution_history: List[Dict[str, Any]]):
        """모델 업데이트"""
        for record in execution_history:
            pattern = record['pattern']
            if pattern not in self.cost_stats:
                self.cost_stats[pattern] = []
            
            self.cost_stats[pattern].append({
                'cost': record['actual_cost'],
                'execution_time': record['actual_execution_time'],
                'agent_count': len(record['agents'])
            })


class PatternRecommendationModel:
    """패턴 추천 모델"""
    
    def __init__(self):
        self.pattern_performance = {}
    
    async def update(self, execution_history: List[Dict[str, Any]]):
        """모델 업데이트"""
        for record in execution_history:
            pattern = record['pattern']
            if pattern not in self.pattern_performance:
                self.pattern_performance[pattern] = {
                    'total_executions': 0,
                    'successes': 0,
                    'total_time': 0.0
                }
            
            stats = self.pattern_performance[pattern]
            stats['total_executions'] += 1
            stats['total_time'] += record['actual_execution_time']
            
            if record['actual_success']:
                stats['successes'] += 1