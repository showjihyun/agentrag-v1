"""
Auto Performance Tuning Service

자동 성능 튜닝 및 최적화 서비스
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import logging
from enum import Enum

from backend.core.ml.orchestration_optimizer import (
    MLOrchestrationOptimizer, OptimizationObjective, OptimizationResult
)
from backend.core.event_bus.validated_event_bus import ValidatedEventBus
from backend.core.monitoring.plugin_performance_monitor import PluginPerformanceMonitor


logger = logging.getLogger(__name__)


class TuningStrategy(str, Enum):
    """튜닝 전략"""
    CONSERVATIVE = "conservative"  # 보수적 - 안정성 우선
    AGGRESSIVE = "aggressive"      # 적극적 - 성능 우선
    BALANCED = "balanced"          # 균형 - 성능과 안정성 균형
    COST_FOCUSED = "cost_focused"  # 비용 중심 - 비용 최적화 우선


@dataclass
class TuningConfiguration:
    """튜닝 설정"""
    strategy: TuningStrategy = TuningStrategy.BALANCED
    auto_apply: bool = False  # 자동 적용 여부
    min_improvement_threshold: float = 5.0  # 최소 개선율 (%)
    max_risk_tolerance: float = 0.1  # 최대 위험 허용도
    tuning_interval_hours: int = 24  # 튜닝 주기 (시간)
    performance_window_days: int = 7  # 성능 분석 기간 (일)
    enable_cost_optimization: bool = True
    enable_performance_optimization: bool = True
    enable_reliability_optimization: bool = True


@dataclass
class TuningRecommendation:
    """튜닝 추천"""
    workflow_id: str
    current_config: Dict[str, Any]
    recommended_config: Dict[str, Any]
    optimization_result: OptimizationResult
    risk_assessment: Dict[str, Any]
    estimated_impact: Dict[str, Any]
    confidence: float
    reasoning: str
    auto_applicable: bool
    created_at: datetime


class AutoTuningService:
    """자동 성능 튜닝 서비스"""
    
    def __init__(
        self,
        optimizer: MLOrchestrationOptimizer,
        performance_monitor: PluginPerformanceMonitor,
        event_bus: ValidatedEventBus
    ):
        self.optimizer = optimizer
        self.performance_monitor = performance_monitor
        self.event_bus = event_bus
        
        # 튜닝 설정
        self.tuning_config = TuningConfiguration()
        
        # 튜닝 이력 및 상태
        self.tuning_history: List[TuningRecommendation] = []
        self.active_tuning_sessions: Dict[str, Dict[str, Any]] = {}
        self.workflow_performance_baselines: Dict[str, Dict[str, Any]] = {}
        
        # 백그라운드 작업
        self._tuning_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # 성능 임계값
        self.performance_thresholds = {
            'max_execution_time': 10.0,  # 최대 실행 시간 (초)
            'min_success_rate': 0.9,     # 최소 성공률
            'max_cost_per_execution': 0.2,  # 최대 실행당 비용
            'max_memory_usage': 1000.0,  # 최대 메모리 사용량 (MB)
        }
    
    async def start_auto_tuning(self, config: Optional[TuningConfiguration] = None):
        """자동 튜닝 시작"""
        if config:
            self.tuning_config = config
        
        # 기존 작업 중지
        await self.stop_auto_tuning()
        
        # 백그라운드 작업 시작
        self._tuning_task = asyncio.create_task(self._auto_tuning_loop())
        self._monitoring_task = asyncio.create_task(self._performance_monitoring_loop())
        
        logger.info("Auto tuning service started")
        
        # 시작 이벤트 발행
        await self.event_bus.publish(
            'auto_tuning_started',
            {
                'strategy': self.tuning_config.strategy,
                'auto_apply': self.tuning_config.auto_apply,
                'tuning_interval_hours': self.tuning_config.tuning_interval_hours
            },
            source='auto_tuning_service'
        )
    
    async def stop_auto_tuning(self):
        """자동 튜닝 중지"""
        if self._tuning_task and not self._tuning_task.done():
            self._tuning_task.cancel()
            try:
                await self._tuning_task
            except asyncio.CancelledError:
                pass
        
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Auto tuning service stopped")
        
        await self.event_bus.publish(
            'auto_tuning_stopped',
            {},
            source='auto_tuning_service'
        )
    
    async def analyze_workflow_performance(
        self,
        workflow_id: str,
        pattern: str,
        agents: List[str],
        recent_executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """워크플로우 성능 분석"""
        if not recent_executions:
            return {
                'status': 'insufficient_data',
                'message': '분석할 실행 데이터가 부족합니다.'
            }
        
        # 성능 메트릭 계산
        execution_times = [e.get('execution_time', 0) for e in recent_executions if e.get('execution_time')]
        success_rates = [1 if e.get('success', False) else 0 for e in recent_executions]
        costs = [e.get('cost', 0) for e in recent_executions if e.get('cost')]
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        avg_cost = sum(costs) / len(costs) if costs else 0
        
        # 성능 트렌드 분석
        trend_analysis = self._analyze_performance_trend(recent_executions)
        
        # 병목 지점 식별
        bottlenecks = await self._identify_performance_bottlenecks(agents, recent_executions)
        
        # 성능 등급 계산
        performance_grade = self._calculate_performance_grade(
            avg_execution_time, success_rate, avg_cost
        )
        
        # 개선 기회 식별
        improvement_opportunities = await self._identify_improvement_opportunities(
            workflow_id, pattern, agents, {
                'avg_execution_time': avg_execution_time,
                'success_rate': success_rate,
                'avg_cost': avg_cost
            }
        )
        
        return {
            'workflow_id': workflow_id,
            'analysis_period': {
                'start': recent_executions[0].get('timestamp') if recent_executions else None,
                'end': recent_executions[-1].get('timestamp') if recent_executions else None,
                'execution_count': len(recent_executions)
            },
            'performance_metrics': {
                'avg_execution_time': round(avg_execution_time, 2),
                'success_rate': round(success_rate, 4),
                'avg_cost': round(avg_cost, 4),
                'performance_grade': performance_grade
            },
            'trend_analysis': trend_analysis,
            'bottlenecks': bottlenecks,
            'improvement_opportunities': improvement_opportunities,
            'meets_thresholds': self._check_performance_thresholds(
                avg_execution_time, success_rate, avg_cost
            )
        }
    
    async def generate_tuning_recommendation(
        self,
        workflow_id: str,
        current_pattern: str,
        current_agents: List[str],
        task: Dict[str, Any],
        performance_analysis: Dict[str, Any]
    ) -> Optional[TuningRecommendation]:
        """튜닝 추천 생성"""
        try:
            # 최적화 목표 결정
            objective = self._determine_optimization_objective(
                performance_analysis, self.tuning_config.strategy
            )
            
            # 제약 조건 설정
            constraints = self._build_optimization_constraints(performance_analysis)
            
            # 최적화 실행
            optimization_result = await self.optimizer.optimize_orchestration(
                current_pattern, current_agents, task, objective, constraints
            )
            
            # 위험 평가
            risk_assessment = await self._assess_optimization_risk(
                optimization_result, performance_analysis
            )
            
            # 영향 추정
            estimated_impact = await self._estimate_optimization_impact(
                optimization_result, performance_analysis
            )
            
            # 자동 적용 가능 여부 판단
            auto_applicable = self._is_auto_applicable(
                optimization_result, risk_assessment, estimated_impact
            )
            
            # 추천 생성
            recommendation = TuningRecommendation(
                workflow_id=workflow_id,
                current_config={
                    'pattern': current_pattern,
                    'agents': current_agents,
                    'task': task
                },
                recommended_config={
                    'pattern': optimization_result.optimized_pattern,
                    'agents': optimization_result.optimized_agents,
                    'task': task
                },
                optimization_result=optimization_result,
                risk_assessment=risk_assessment,
                estimated_impact=estimated_impact,
                confidence=optimization_result.confidence,
                reasoning=optimization_result.reasoning,
                auto_applicable=auto_applicable,
                created_at=datetime.now()
            )
            
            # 추천 이력에 추가
            self.tuning_history.append(recommendation)
            
            # 최근 100개만 유지
            if len(self.tuning_history) > 100:
                self.tuning_history = self.tuning_history[-100:]
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to generate tuning recommendation: {e}")
            return None
    
    async def apply_tuning_recommendation(
        self,
        recommendation: TuningRecommendation,
        force: bool = False
    ) -> Dict[str, Any]:
        """튜닝 추천 적용"""
        try:
            # 안전성 검사
            if not force and not recommendation.auto_applicable:
                return {
                    'success': False,
                    'message': '자동 적용이 불가능한 추천입니다. force=True로 강제 적용하거나 수동으로 적용하세요.',
                    'risk_level': recommendation.risk_assessment.get('level', 'unknown')
                }
            
            # 백업 생성
            backup_id = f"backup_{recommendation.workflow_id}_{datetime.now().timestamp()}"
            
            # 적용 전 이벤트 발행
            await self.event_bus.publish(
                'tuning_recommendation_applying',
                {
                    'workflow_id': recommendation.workflow_id,
                    'backup_id': backup_id,
                    'optimization_type': recommendation.optimization_result.optimized_pattern,
                    'estimated_improvement': {
                        'performance': recommendation.optimization_result.performance_improvement,
                        'cost': recommendation.optimization_result.cost_reduction,
                        'reliability': recommendation.optimization_result.reliability_improvement
                    }
                },
                source='auto_tuning_service'
            )
            
            # 실제 적용 로직 (여기서는 시뮬레이션)
            # 실제 구현에서는 워크플로우 설정을 업데이트
            
            # 적용 완료 이벤트 발행
            await self.event_bus.publish(
                'tuning_recommendation_applied',
                {
                    'workflow_id': recommendation.workflow_id,
                    'backup_id': backup_id,
                    'success': True,
                    'applied_at': datetime.now().isoformat()
                },
                source='auto_tuning_service'
            )
            
            return {
                'success': True,
                'backup_id': backup_id,
                'message': '튜닝 추천이 성공적으로 적용되었습니다.',
                'estimated_savings': recommendation.optimization_result.estimated_savings
            }
            
        except Exception as e:
            logger.error(f"Failed to apply tuning recommendation: {e}")
            
            await self.event_bus.publish(
                'tuning_recommendation_failed',
                {
                    'workflow_id': recommendation.workflow_id,
                    'error': str(e)
                },
                source='auto_tuning_service'
            )
            
            return {
                'success': False,
                'message': f'튜닝 적용 중 오류가 발생했습니다: {e}'
            }
    
    async def get_tuning_insights(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """튜닝 인사이트 조회"""
        if workflow_id:
            # 특정 워크플로우 인사이트
            workflow_recommendations = [
                rec for rec in self.tuning_history 
                if rec.workflow_id == workflow_id
            ]
            
            if not workflow_recommendations:
                return {
                    'workflow_id': workflow_id,
                    'message': '해당 워크플로우에 대한 튜닝 이력이 없습니다.'
                }
            
            latest_recommendation = workflow_recommendations[-1]
            
            return {
                'workflow_id': workflow_id,
                'latest_recommendation': {
                    'created_at': latest_recommendation.created_at.isoformat(),
                    'confidence': latest_recommendation.confidence,
                    'auto_applicable': latest_recommendation.auto_applicable,
                    'estimated_improvement': {
                        'performance': latest_recommendation.optimization_result.performance_improvement,
                        'cost': latest_recommendation.optimization_result.cost_reduction,
                        'reliability': latest_recommendation.optimization_result.reliability_improvement
                    },
                    'reasoning': latest_recommendation.reasoning
                },
                'recommendation_history': len(workflow_recommendations),
                'auto_applied_count': sum(1 for rec in workflow_recommendations if rec.auto_applicable)
            }
        else:
            # 전체 인사이트
            total_recommendations = len(self.tuning_history)
            auto_applicable_count = sum(1 for rec in self.tuning_history if rec.auto_applicable)
            
            # 최근 24시간 활동
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_recommendations = [
                rec for rec in self.tuning_history 
                if rec.created_at >= recent_cutoff
            ]
            
            # 평균 개선율 계산
            if self.tuning_history:
                avg_performance_improvement = sum(
                    rec.optimization_result.performance_improvement 
                    for rec in self.tuning_history
                ) / len(self.tuning_history)
                
                avg_cost_reduction = sum(
                    rec.optimization_result.cost_reduction 
                    for rec in self.tuning_history
                ) / len(self.tuning_history)
            else:
                avg_performance_improvement = 0
                avg_cost_reduction = 0
            
            return {
                'summary': {
                    'total_recommendations': total_recommendations,
                    'auto_applicable_rate': (auto_applicable_count / total_recommendations * 100) if total_recommendations > 0 else 0,
                    'recent_24h_recommendations': len(recent_recommendations),
                    'avg_performance_improvement': round(avg_performance_improvement, 2),
                    'avg_cost_reduction': round(avg_cost_reduction, 2)
                },
                'tuning_config': {
                    'strategy': self.tuning_config.strategy,
                    'auto_apply': self.tuning_config.auto_apply,
                    'tuning_interval_hours': self.tuning_config.tuning_interval_hours
                },
                'active_sessions': len(self.active_tuning_sessions)
            }
    
    # 내부 메서드들
    
    async def _auto_tuning_loop(self):
        """자동 튜닝 루프"""
        while True:
            try:
                await asyncio.sleep(self.tuning_config.tuning_interval_hours * 3600)
                
                # 활성 워크플로우 식별 (실제 구현에서는 DB에서 조회)
                active_workflows = await self._get_active_workflows()
                
                for workflow in active_workflows:
                    try:
                        await self._process_workflow_tuning(workflow)
                    except Exception as e:
                        logger.error(f"Failed to process tuning for workflow {workflow.get('id')}: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto tuning loop error: {e}")
    
    async def _performance_monitoring_loop(self):
        """성능 모니터링 루프"""
        while True:
            try:
                await asyncio.sleep(300)  # 5분마다 실행
                
                # 성능 임계값 위반 확인
                await self._check_performance_violations()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring loop error: {e}")
    
    async def _get_active_workflows(self) -> List[Dict[str, Any]]:
        """활성 워크플로우 목록 조회"""
        # 실제 구현에서는 데이터베이스에서 조회
        return [
            {
                'id': 'workflow_1',
                'pattern': 'sequential',
                'agents': ['vector_search', 'web_search'],
                'task': {'type': 'search_and_analyze'}
            },
            {
                'id': 'workflow_2', 
                'pattern': 'parallel',
                'agents': ['local_data', 'aggregator'],
                'task': {'type': 'data_processing'}
            }
        ]
    
    async def _process_workflow_tuning(self, workflow: Dict[str, Any]):
        """워크플로우 튜닝 처리"""
        workflow_id = workflow['id']
        
        # 최근 실행 데이터 조회
        recent_executions = await self._get_recent_executions(
            workflow_id, 
            days=self.tuning_config.performance_window_days
        )
        
        if len(recent_executions) < 5:  # 최소 실행 횟수
            return
        
        # 성능 분석
        performance_analysis = await self.analyze_workflow_performance(
            workflow_id,
            workflow['pattern'],
            workflow['agents'],
            recent_executions
        )
        
        # 개선이 필요한지 확인
        if not self._needs_tuning(performance_analysis):
            return
        
        # 튜닝 추천 생성
        recommendation = await self.generate_tuning_recommendation(
            workflow_id,
            workflow['pattern'],
            workflow['agents'],
            workflow['task'],
            performance_analysis
        )
        
        if not recommendation:
            return
        
        # 자동 적용 여부 확인
        if self.tuning_config.auto_apply and recommendation.auto_applicable:
            await self.apply_tuning_recommendation(recommendation)
        else:
            # 수동 검토 필요 알림
            await self.event_bus.publish(
                'tuning_recommendation_ready',
                {
                    'workflow_id': workflow_id,
                    'recommendation_id': len(self.tuning_history),
                    'auto_applicable': recommendation.auto_applicable,
                    'estimated_improvement': {
                        'performance': recommendation.optimization_result.performance_improvement,
                        'cost': recommendation.optimization_result.cost_reduction
                    }
                },
                source='auto_tuning_service'
            )
    
    async def _get_recent_executions(self, workflow_id: str, days: int) -> List[Dict[str, Any]]:
        """최근 실행 데이터 조회"""
        # 실제 구현에서는 데이터베이스에서 조회
        # 여기서는 시뮬레이션 데이터 반환
        import random
        
        executions = []
        for i in range(20):  # 20개 실행 데이터
            executions.append({
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'execution_time': random.uniform(2.0, 8.0),
                'success': random.choice([True, True, True, False]),  # 75% 성공률
                'cost': random.uniform(0.05, 0.15),
                'memory_usage': random.uniform(100, 500)
            })
        
        return executions
    
    def _analyze_performance_trend(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        if len(executions) < 5:
            return {'trend': 'insufficient_data'}
        
        # 시간순 정렬
        sorted_executions = sorted(executions, key=lambda x: x.get('timestamp', ''))
        
        # 최근 절반과 이전 절반 비교
        mid_point = len(sorted_executions) // 2
        recent_half = sorted_executions[mid_point:]
        earlier_half = sorted_executions[:mid_point]
        
        # 평균 실행 시간 비교
        recent_avg_time = sum(e.get('execution_time', 0) for e in recent_half) / len(recent_half)
        earlier_avg_time = sum(e.get('execution_time', 0) for e in earlier_half) / len(earlier_half)
        
        time_change = ((recent_avg_time - earlier_avg_time) / earlier_avg_time * 100) if earlier_avg_time > 0 else 0
        
        # 성공률 비교
        recent_success_rate = sum(1 for e in recent_half if e.get('success', False)) / len(recent_half)
        earlier_success_rate = sum(1 for e in earlier_half if e.get('success', False)) / len(earlier_half)
        
        success_change = ((recent_success_rate - earlier_success_rate) / earlier_success_rate * 100) if earlier_success_rate > 0 else 0
        
        # 트렌드 결정
        if abs(time_change) < 5 and abs(success_change) < 5:
            trend = 'stable'
        elif time_change > 10 or success_change < -10:
            trend = 'degrading'
        elif time_change < -10 or success_change > 10:
            trend = 'improving'
        else:
            trend = 'fluctuating'
        
        return {
            'trend': trend,
            'execution_time_change_percent': round(time_change, 2),
            'success_rate_change_percent': round(success_change, 2),
            'recent_avg_time': round(recent_avg_time, 2),
            'earlier_avg_time': round(earlier_avg_time, 2)
        }
    
    async def _identify_performance_bottlenecks(
        self, 
        agents: List[str], 
        executions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """성능 병목 지점 식별"""
        bottlenecks = []
        
        for agent in agents:
            # Agent별 성능 메트릭 조회
            metrics = self.performance_monitor.get_plugin_metrics(agent)
            
            if 'aggregated_metrics' in metrics:
                agent_metrics = metrics['aggregated_metrics']
                
                # 병목 조건 확인
                is_bottleneck = False
                reasons = []
                
                if agent_metrics.get('avg_execution_time', 0) > 5.0:
                    is_bottleneck = True
                    reasons.append('높은 평균 실행 시간')
                
                if agent_metrics.get('success_rate', 1.0) < 0.8:
                    is_bottleneck = True
                    reasons.append('낮은 성공률')
                
                if agent_metrics.get('avg_memory_usage', 0) > 800:
                    is_bottleneck = True
                    reasons.append('높은 메모리 사용량')
                
                if is_bottleneck:
                    bottlenecks.append({
                        'agent': agent,
                        'reasons': reasons,
                        'metrics': agent_metrics,
                        'severity': 'high' if len(reasons) > 1 else 'medium'
                    })
        
        return bottlenecks
    
    def _calculate_performance_grade(
        self, 
        avg_execution_time: float, 
        success_rate: float, 
        avg_cost: float
    ) -> str:
        """성능 등급 계산"""
        score = 0
        
        # 실행 시간 점수 (0-40점)
        if avg_execution_time <= 2.0:
            score += 40
        elif avg_execution_time <= 5.0:
            score += 30
        elif avg_execution_time <= 10.0:
            score += 20
        else:
            score += 10
        
        # 성공률 점수 (0-40점)
        score += success_rate * 40
        
        # 비용 점수 (0-20점)
        if avg_cost <= 0.05:
            score += 20
        elif avg_cost <= 0.1:
            score += 15
        elif avg_cost <= 0.2:
            score += 10
        else:
            score += 5
        
        # 등급 결정
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'
    
    async def _identify_improvement_opportunities(
        self,
        workflow_id: str,
        pattern: str,
        agents: List[str],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """개선 기회 식별"""
        opportunities = []
        
        # 실행 시간 개선
        if metrics['avg_execution_time'] > 5.0:
            if pattern != 'parallel' and len(agents) > 1:
                opportunities.append({
                    'type': 'pattern_optimization',
                    'title': '병렬 실행으로 성능 향상',
                    'description': '순차 실행을 병렬 실행으로 변경하여 실행 시간을 단축할 수 있습니다.',
                    'estimated_improvement': '30-50% 실행 시간 단축',
                    'priority': 'high'
                })
        
        # 성공률 개선
        if metrics['success_rate'] < 0.9:
            opportunities.append({
                'type': 'reliability_improvement',
                'title': '안정성 향상',
                'description': '합의 패턴 사용 또는 안정적인 Agent 추가로 성공률을 향상시킬 수 있습니다.',
                'estimated_improvement': f"{(0.95 - metrics['success_rate']) * 100:.1f}% 성공률 향상",
                'priority': 'high' if metrics['success_rate'] < 0.8 else 'medium'
            })
        
        # 비용 최적화
        if metrics['avg_cost'] > 0.1:
            opportunities.append({
                'type': 'cost_optimization',
                'title': '비용 최적화',
                'description': '더 효율적인 Agent 조합으로 비용을 절감할 수 있습니다.',
                'estimated_improvement': f"{((metrics['avg_cost'] - 0.05) / metrics['avg_cost'] * 100):.1f}% 비용 절감",
                'priority': 'medium'
            })
        
        return opportunities
    
    def _check_performance_thresholds(
        self, 
        avg_execution_time: float, 
        success_rate: float, 
        avg_cost: float
    ) -> Dict[str, bool]:
        """성능 임계값 확인"""
        return {
            'execution_time': avg_execution_time <= self.performance_thresholds['max_execution_time'],
            'success_rate': success_rate >= self.performance_thresholds['min_success_rate'],
            'cost': avg_cost <= self.performance_thresholds['max_cost_per_execution'],
            'overall': (
                avg_execution_time <= self.performance_thresholds['max_execution_time'] and
                success_rate >= self.performance_thresholds['min_success_rate'] and
                avg_cost <= self.performance_thresholds['max_cost_per_execution']
            )
        }
    
    def _determine_optimization_objective(
        self, 
        performance_analysis: Dict[str, Any], 
        strategy: TuningStrategy
    ) -> OptimizationObjective:
        """최적화 목표 결정"""
        metrics = performance_analysis.get('performance_metrics', {})
        
        if strategy == TuningStrategy.CONSERVATIVE:
            return OptimizationObjective.RELIABILITY
        elif strategy == TuningStrategy.AGGRESSIVE:
            return OptimizationObjective.PERFORMANCE
        elif strategy == TuningStrategy.COST_FOCUSED:
            return OptimizationObjective.COST
        else:  # BALANCED
            # 가장 문제가 되는 영역에 따라 결정
            if metrics.get('success_rate', 1.0) < 0.8:
                return OptimizationObjective.RELIABILITY
            elif metrics.get('avg_execution_time', 0) > 8.0:
                return OptimizationObjective.PERFORMANCE
            elif metrics.get('avg_cost', 0) > 0.15:
                return OptimizationObjective.COST
            else:
                return OptimizationObjective.BALANCED
    
    def _build_optimization_constraints(self, performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """최적화 제약 조건 구성"""
        constraints = {}
        
        # 전략에 따른 제약 조건
        if self.tuning_config.strategy == TuningStrategy.CONSERVATIVE:
            constraints['max_agents'] = 5  # Agent 수 제한
            constraints['forbidden_patterns'] = ['swarm']  # 복잡한 패턴 금지
        
        # 성능 기반 제약 조건
        metrics = performance_analysis.get('performance_metrics', {})
        if metrics.get('success_rate', 1.0) < 0.7:
            constraints['required_agents'] = ['aggregator']  # 안정적인 Agent 필수
        
        return constraints
    
    async def _assess_optimization_risk(
        self, 
        optimization_result: OptimizationResult, 
        performance_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """최적화 위험 평가"""
        risk_factors = []
        risk_score = 0.0
        
        # 패턴 변경 위험
        if optimization_result.original_pattern != optimization_result.optimized_pattern:
            risk_score += 0.2
            risk_factors.append('패턴 변경으로 인한 예상치 못한 동작 가능성')
        
        # Agent 변경 위험
        removed_agents = set(optimization_result.original_agents) - set(optimization_result.optimized_agents)
        added_agents = set(optimization_result.optimized_agents) - set(optimization_result.original_agents)
        
        if removed_agents:
            risk_score += len(removed_agents) * 0.1
            risk_factors.append(f'Agent 제거로 인한 기능 손실 가능성: {", ".join(removed_agents)}')
        
        if added_agents:
            risk_score += len(added_agents) * 0.05
            risk_factors.append(f'새 Agent 추가로 인한 복잡성 증가: {", ".join(added_agents)}')
        
        # 신뢰도 기반 위험
        if optimization_result.confidence < 0.7:
            risk_score += 0.3
            risk_factors.append('낮은 예측 신뢰도')
        
        # 위험 수준 결정
        if risk_score <= 0.2:
            risk_level = 'low'
        elif risk_score <= 0.5:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return {
            'level': risk_level,
            'score': round(risk_score, 2),
            'factors': risk_factors,
            'mitigation_suggestions': self._generate_risk_mitigation_suggestions(risk_factors)
        }
    
    def _generate_risk_mitigation_suggestions(self, risk_factors: List[str]) -> List[str]:
        """위험 완화 제안 생성"""
        suggestions = []
        
        for factor in risk_factors:
            if '패턴 변경' in factor:
                suggestions.append('단계적 롤아웃으로 패턴 변경 영향 최소화')
            elif 'Agent 제거' in factor:
                suggestions.append('제거 전 해당 Agent의 기능 검증')
            elif '새 Agent 추가' in factor:
                suggestions.append('새 Agent의 안정성 사전 테스트')
            elif '낮은 예측 신뢰도' in factor:
                suggestions.append('더 많은 데이터 수집 후 재평가')
        
        return suggestions
    
    async def _estimate_optimization_impact(
        self, 
        optimization_result: OptimizationResult, 
        performance_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """최적화 영향 추정"""
        current_metrics = performance_analysis.get('performance_metrics', {})
        
        # 월간 실행 횟수 추정 (실제로는 이력 데이터에서 계산)
        estimated_monthly_executions = 1000
        
        # 현재 월간 비용
        current_monthly_cost = current_metrics.get('avg_cost', 0.1) * estimated_monthly_executions
        
        # 최적화 후 예상 비용
        cost_reduction_rate = optimization_result.cost_reduction / 100
        optimized_monthly_cost = current_monthly_cost * (1 - cost_reduction_rate)
        
        # 시간 절약
        current_monthly_time = current_metrics.get('avg_execution_time', 5.0) * estimated_monthly_executions
        performance_improvement_rate = optimization_result.performance_improvement / 100
        optimized_monthly_time = current_monthly_time * (1 - performance_improvement_rate)
        
        return {
            'monthly_executions': estimated_monthly_executions,
            'cost_impact': {
                'current_monthly_cost': round(current_monthly_cost, 2),
                'optimized_monthly_cost': round(optimized_monthly_cost, 2),
                'monthly_savings': round(current_monthly_cost - optimized_monthly_cost, 2),
                'annual_savings': round((current_monthly_cost - optimized_monthly_cost) * 12, 2)
            },
            'time_impact': {
                'current_monthly_hours': round(current_monthly_time / 3600, 2),
                'optimized_monthly_hours': round(optimized_monthly_time / 3600, 2),
                'monthly_time_saved_hours': round((current_monthly_time - optimized_monthly_time) / 3600, 2)
            },
            'reliability_impact': {
                'current_success_rate': current_metrics.get('success_rate', 0.8),
                'estimated_improved_rate': min(0.99, current_metrics.get('success_rate', 0.8) * (1 + optimization_result.reliability_improvement / 100))
            }
        }
    
    def _is_auto_applicable(
        self, 
        optimization_result: OptimizationResult, 
        risk_assessment: Dict[str, Any], 
        estimated_impact: Dict[str, Any]
    ) -> bool:
        """자동 적용 가능 여부 판단"""
        # 기본 조건들
        conditions = [
            # 최소 개선율 충족
            optimization_result.performance_improvement >= self.tuning_config.min_improvement_threshold or
            optimization_result.cost_reduction >= self.tuning_config.min_improvement_threshold,
            
            # 위험 수준이 허용 범위 내
            risk_assessment['score'] <= self.tuning_config.max_risk_tolerance,
            
            # 신뢰도가 충분히 높음
            optimization_result.confidence >= 0.7,
            
            # 안정성이 저하되지 않음
            optimization_result.reliability_improvement >= -5.0  # 5% 이상 저하 방지
        ]
        
        return all(conditions)
    
    def _needs_tuning(self, performance_analysis: Dict[str, Any]) -> bool:
        """튜닝이 필요한지 판단"""
        metrics = performance_analysis.get('performance_metrics', {})
        thresholds = performance_analysis.get('meets_thresholds', {})
        
        # 임계값 위반이 있거나 성능 등급이 낮으면 튜닝 필요
        return (
            not thresholds.get('overall', True) or
            metrics.get('performance_grade', 'A') in ['C', 'D'] or
            len(performance_analysis.get('improvement_opportunities', [])) > 0
        )
    
    async def _check_performance_violations(self):
        """성능 임계값 위반 확인"""
        # 모든 활성 워크플로우의 성능 확인
        active_workflows = await self._get_active_workflows()
        
        for workflow in active_workflows:
            try:
                recent_executions = await self._get_recent_executions(workflow['id'], days=1)
                
                if len(recent_executions) < 3:
                    continue
                
                # 최근 성능 계산
                avg_time = sum(e.get('execution_time', 0) for e in recent_executions) / len(recent_executions)
                success_rate = sum(1 for e in recent_executions if e.get('success', False)) / len(recent_executions)
                
                # 임계값 위반 확인
                violations = []
                
                if avg_time > self.performance_thresholds['max_execution_time']:
                    violations.append({
                        'type': 'execution_time',
                        'current': avg_time,
                        'threshold': self.performance_thresholds['max_execution_time']
                    })
                
                if success_rate < self.performance_thresholds['min_success_rate']:
                    violations.append({
                        'type': 'success_rate',
                        'current': success_rate,
                        'threshold': self.performance_thresholds['min_success_rate']
                    })
                
                # 위반 사항이 있으면 알림
                if violations:
                    await self.event_bus.publish(
                        'performance_threshold_violation',
                        {
                            'workflow_id': workflow['id'],
                            'violations': violations,
                            'recent_executions_count': len(recent_executions)
                        },
                        source='auto_tuning_service'
                    )
                    
            except Exception as e:
                logger.error(f"Failed to check performance violations for workflow {workflow.get('id')}: {e}")