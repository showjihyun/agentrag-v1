"""
Cost Optimization Engine

비용 최적화 엔진 - 워크플로우 실행 비용을 최소화하는 시스템
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio

from backend.core.ml.orchestration_optimizer import ResourceCost
from backend.core.event_bus.validated_event_bus import ValidatedEventBus


logger = logging.getLogger(__name__)


class CostOptimizationStrategy(str, Enum):
    """비용 최적화 전략"""
    AGGRESSIVE = "aggressive"      # 적극적 - 최대 비용 절감
    BALANCED = "balanced"          # 균형 - 성능과 비용 균형
    CONSERVATIVE = "conservative"  # 보수적 - 성능 유지하며 비용 절감


@dataclass
class CostBreakdown:
    """비용 분석"""
    compute_cost: float = 0.0      # 컴퓨팅 비용
    llm_api_cost: float = 0.0      # LLM API 비용
    storage_cost: float = 0.0      # 저장소 비용
    network_cost: float = 0.0      # 네트워크 비용
    overhead_cost: float = 0.0     # 오버헤드 비용
    
    @property
    def total_cost(self) -> float:
        return (self.compute_cost + self.llm_api_cost + 
                self.storage_cost + self.network_cost + self.overhead_cost)


@dataclass
class CostOptimizationRecommendation:
    """비용 최적화 추천"""
    workflow_id: str
    current_cost: CostBreakdown
    optimized_cost: CostBreakdown
    optimization_actions: List[Dict[str, Any]]
    estimated_savings: Dict[str, float]
    confidence: float
    risk_level: str
    implementation_effort: str
    created_at: datetime = field(default_factory=datetime.now)


class CostOptimizationEngine:
    """비용 최적화 엔진"""
    
    def __init__(
        self,
        event_bus: ValidatedEventBus,
        resource_costs: Optional[ResourceCost] = None
    ):
        self.event_bus = event_bus
        self.resource_costs = resource_costs or ResourceCost()
        
        # 비용 최적화 설정
        self.optimization_enabled = True
        self.cost_tracking_enabled = True
        
        # 비용 데이터 저장소
        self.cost_history: Dict[str, List[Dict[str, Any]]] = {}
        self.cost_baselines: Dict[str, CostBreakdown] = {}
        
        # 최적화 규칙
        self.optimization_rules = self._initialize_optimization_rules()
        
        # 비용 임계값
        self.cost_thresholds = {
            'max_cost_per_execution': 0.50,
            'max_monthly_cost': 1000.0,
            'cost_increase_alert_threshold': 0.20  # 20% 증가 시 알림
        }
    
    def _initialize_optimization_rules(self) -> List[Dict[str, Any]]:
        """비용 최적화 규칙 초기화"""
        return [
            {
                'name': 'llm_model_optimization',
                'description': '더 저렴한 LLM 모델 사용',
                'condition': lambda cost: cost.llm_api_cost > cost.total_cost * 0.6,
                'action': 'suggest_cheaper_llm_model',
                'potential_savings': 0.3  # 30% 절감 가능
            },
            {
                'name': 'parallel_to_sequential',
                'description': '병렬 실행을 순차 실행으로 변경',
                'condition': lambda cost: cost.compute_cost > cost.total_cost * 0.4,
                'action': 'suggest_sequential_execution',
                'potential_savings': 0.25
            },
            {
                'name': 'agent_consolidation',
                'description': 'Agent 통합으로 오버헤드 감소',
                'condition': lambda cost: cost.overhead_cost > cost.total_cost * 0.2,
                'action': 'suggest_agent_consolidation',
                'potential_savings': 0.15
            },
            {
                'name': 'caching_optimization',
                'description': '캐싱 활용으로 중복 계산 방지',
                'condition': lambda cost: True,  # 항상 적용 가능
                'action': 'suggest_caching',
                'potential_savings': 0.20
            }
        ]
    
    async def analyze_workflow_costs(
        self,
        workflow_id: str,
        pattern: str,
        agents: List[str],
        recent_executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """워크플로우 비용 분석"""
        if not recent_executions:
            return {
                'status': 'insufficient_data',
                'message': '비용 분석을 위한 실행 데이터가 부족합니다.'
            }
        
        # 비용 분석
        cost_breakdown = await self._calculate_cost_breakdown(
            pattern, agents, recent_executions
        )
        
        # 비용 트렌드 분석
        cost_trend = self._analyze_cost_trend(workflow_id, recent_executions)
        
        # 비용 효율성 분석
        efficiency_analysis = await self._analyze_cost_efficiency(
            cost_breakdown, recent_executions
        )
        
        # 비용 최적화 기회 식별
        optimization_opportunities = await self._identify_cost_optimization_opportunities(
            workflow_id, pattern, agents, cost_breakdown
        )
        
        return {
            'workflow_id': workflow_id,
            'analysis_period': {
                'start': recent_executions[0].get('timestamp') if recent_executions else None,
                'end': recent_executions[-1].get('timestamp') if recent_executions else None,
                'execution_count': len(recent_executions)
            },
            'cost_breakdown': {
                'compute_cost': round(cost_breakdown.compute_cost, 4),
                'llm_api_cost': round(cost_breakdown.llm_api_cost, 4),
                'storage_cost': round(cost_breakdown.storage_cost, 4),
                'network_cost': round(cost_breakdown.network_cost, 4),
                'overhead_cost': round(cost_breakdown.overhead_cost, 4),
                'total_cost': round(cost_breakdown.total_cost, 4)
            },
            'cost_trend': cost_trend,
            'efficiency_analysis': efficiency_analysis,
            'optimization_opportunities': optimization_opportunities,
            'cost_grade': self._calculate_cost_grade(cost_breakdown),
            'monthly_projection': self._project_monthly_costs(cost_breakdown, recent_executions)
        }
    
    async def generate_cost_optimization_plan(
        self,
        workflow_id: str,
        pattern: str,
        agents: List[str],
        cost_analysis: Dict[str, Any],
        strategy: CostOptimizationStrategy = CostOptimizationStrategy.BALANCED
    ) -> CostOptimizationRecommendation:
        """비용 최적화 계획 생성"""
        current_cost = CostBreakdown(
            compute_cost=cost_analysis['cost_breakdown']['compute_cost'],
            llm_api_cost=cost_analysis['cost_breakdown']['llm_api_cost'],
            storage_cost=cost_analysis['cost_breakdown']['storage_cost'],
            network_cost=cost_analysis['cost_breakdown']['network_cost'],
            overhead_cost=cost_analysis['cost_breakdown']['overhead_cost']
        )
        
        # 최적화 액션 생성
        optimization_actions = await self._generate_optimization_actions(
            pattern, agents, current_cost, strategy
        )
        
        # 최적화 후 비용 계산
        optimized_cost = await self._calculate_optimized_cost(
            current_cost, optimization_actions
        )
        
        # 절약 추정치 계산
        estimated_savings = self._calculate_estimated_savings(
            current_cost, optimized_cost, cost_analysis.get('monthly_projection', {})
        )
        
        # 위험 및 노력 평가
        risk_level, implementation_effort = self._assess_optimization_complexity(
            optimization_actions, strategy
        )
        
        # 신뢰도 계산
        confidence = self._calculate_optimization_confidence(
            optimization_actions, cost_analysis
        )
        
        return CostOptimizationRecommendation(
            workflow_id=workflow_id,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            optimization_actions=optimization_actions,
            estimated_savings=estimated_savings,
            confidence=confidence,
            risk_level=risk_level,
            implementation_effort=implementation_effort
        )
    
    async def implement_cost_optimization(
        self,
        recommendation: CostOptimizationRecommendation,
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """비용 최적화 구현"""
        try:
            implementation_results = []
            
            for action in recommendation.optimization_actions:
                if auto_apply or action.get('auto_applicable', False):
                    result = await self._implement_optimization_action(action)
                    implementation_results.append(result)
                else:
                    implementation_results.append({
                        'action': action['type'],
                        'status': 'manual_review_required',
                        'message': '수동 검토가 필요한 최적화입니다.'
                    })
            
            # 구현 완료 이벤트 발행
            await self.event_bus.publish(
                'cost_optimization_implemented',
                {
                    'workflow_id': recommendation.workflow_id,
                    'estimated_savings': recommendation.estimated_savings,
                    'implementation_results': implementation_results
                },
                source='cost_optimization_engine'
            )
            
            return {
                'success': True,
                'implementation_results': implementation_results,
                'estimated_annual_savings': recommendation.estimated_savings.get('annual_savings', 0)
            }
            
        except Exception as e:
            logger.error(f"Cost optimization implementation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def track_cost_savings(
        self,
        workflow_id: str,
        optimization_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """비용 절감 효과 추적"""
        # 최적화 전후 비용 비교
        optimization_date = datetime.now() - timedelta(days=period_days)
        
        before_costs = await self._get_cost_data(
            workflow_id, 
            optimization_date - timedelta(days=period_days),
            optimization_date
        )
        
        after_costs = await self._get_cost_data(
            workflow_id,
            optimization_date,
            datetime.now()
        )
        
        if not before_costs or not after_costs:
            return {
                'status': 'insufficient_data',
                'message': '비용 추적을 위한 데이터가 부족합니다.'
            }
        
        # 비용 절감 계산
        avg_before_cost = sum(before_costs) / len(before_costs)
        avg_after_cost = sum(after_costs) / len(after_costs)
        
        cost_reduction = avg_before_cost - avg_after_cost
        cost_reduction_percent = (cost_reduction / avg_before_cost * 100) if avg_before_cost > 0 else 0
        
        # 월간 절약 추정
        monthly_savings = cost_reduction * 30  # 일일 절약 * 30일
        
        return {
            'workflow_id': workflow_id,
            'optimization_id': optimization_id,
            'tracking_period_days': period_days,
            'cost_comparison': {
                'before_optimization': {
                    'avg_cost_per_execution': round(avg_before_cost, 4),
                    'total_executions': len(before_costs)
                },
                'after_optimization': {
                    'avg_cost_per_execution': round(avg_after_cost, 4),
                    'total_executions': len(after_costs)
                }
            },
            'savings': {
                'cost_reduction_per_execution': round(cost_reduction, 4),
                'cost_reduction_percent': round(cost_reduction_percent, 2),
                'estimated_monthly_savings': round(monthly_savings, 2),
                'estimated_annual_savings': round(monthly_savings * 12, 2)
            },
            'effectiveness': self._calculate_optimization_effectiveness(cost_reduction_percent)
        }
    
    # 내부 메서드들
    
    async def _calculate_cost_breakdown(
        self,
        pattern: str,
        agents: List[str],
        executions: List[Dict[str, Any]]
    ) -> CostBreakdown:
        """비용 분석 계산"""
        total_compute_cost = 0.0
        total_llm_cost = 0.0
        total_storage_cost = 0.0
        total_network_cost = 0.0
        total_overhead_cost = 0.0
        
        for execution in executions:
            execution_time = execution.get('execution_time', 0)
            
            # 컴퓨팅 비용 (CPU + 메모리)
            cpu_cost = execution_time * len(agents) * self.resource_costs.cpu_cost_per_second
            memory_cost = execution.get('memory_usage', 100) * execution_time * self.resource_costs.memory_cost_per_mb_second
            total_compute_cost += cpu_cost + memory_cost
            
            # LLM API 비용 (추정)
            estimated_tokens = execution.get('token_usage', 1000)  # 기본값
            total_llm_cost += estimated_tokens * self.resource_costs.llm_api_cost_per_token
            
            # 저장소 비용
            data_size = execution.get('data_size_mb', 10)  # 기본값
            total_storage_cost += data_size * self.resource_costs.storage_cost_per_mb
            
            # 네트워크 비용
            network_usage = execution.get('network_usage_mb', 5)  # 기본값
            total_network_cost += network_usage * self.resource_costs.network_cost_per_mb
            
            # 오버헤드 비용 (패턴별)
            overhead_multiplier = {
                'sequential': 1.0,
                'parallel': 1.2,
                'consensus': 1.5,
                'swarm': 2.0
            }.get(pattern, 1.1)
            
            base_overhead = (cpu_cost + memory_cost) * 0.1
            total_overhead_cost += base_overhead * overhead_multiplier
        
        # 평균 비용 계산
        execution_count = len(executions)
        
        return CostBreakdown(
            compute_cost=total_compute_cost / execution_count,
            llm_api_cost=total_llm_cost / execution_count,
            storage_cost=total_storage_cost / execution_count,
            network_cost=total_network_cost / execution_count,
            overhead_cost=total_overhead_cost / execution_count
        )
    
    def _analyze_cost_trend(
        self,
        workflow_id: str,
        executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """비용 트렌드 분석"""
        if len(executions) < 10:
            return {'trend': 'insufficient_data'}
        
        # 시간순 정렬
        sorted_executions = sorted(executions, key=lambda x: x.get('timestamp', ''))
        
        # 최근 절반과 이전 절반 비교
        mid_point = len(sorted_executions) // 2
        recent_costs = [e.get('cost', 0) for e in sorted_executions[mid_point:]]
        earlier_costs = [e.get('cost', 0) for e in sorted_executions[:mid_point]]
        
        recent_avg = sum(recent_costs) / len(recent_costs) if recent_costs else 0
        earlier_avg = sum(earlier_costs) / len(earlier_costs) if earlier_costs else 0
        
        cost_change = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        
        # 트렌드 결정
        if abs(cost_change) < 5:
            trend = 'stable'
        elif cost_change > 10:
            trend = 'increasing'
        elif cost_change < -10:
            trend = 'decreasing'
        else:
            trend = 'fluctuating'
        
        return {
            'trend': trend,
            'cost_change_percent': round(cost_change, 2),
            'recent_avg_cost': round(recent_avg, 4),
            'earlier_avg_cost': round(earlier_avg, 4)
        }
    
    async def _analyze_cost_efficiency(
        self,
        cost_breakdown: CostBreakdown,
        executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """비용 효율성 분석"""
        # 성공한 실행만 고려
        successful_executions = [e for e in executions if e.get('success', False)]
        
        if not successful_executions:
            return {'efficiency': 'no_successful_executions'}
        
        # 비용 대비 성공률
        success_rate = len(successful_executions) / len(executions)
        cost_per_success = cost_breakdown.total_cost / success_rate if success_rate > 0 else float('inf')
        
        # 시간 대비 비용 효율성
        avg_execution_time = sum(e.get('execution_time', 0) for e in successful_executions) / len(successful_executions)
        cost_per_second = cost_breakdown.total_cost / avg_execution_time if avg_execution_time > 0 else float('inf')
        
        # 효율성 등급
        if cost_per_success <= 0.05:
            efficiency_grade = 'excellent'
        elif cost_per_success <= 0.1:
            efficiency_grade = 'good'
        elif cost_per_success <= 0.2:
            efficiency_grade = 'fair'
        else:
            efficiency_grade = 'poor'
        
        return {
            'success_rate': round(success_rate, 4),
            'cost_per_success': round(cost_per_success, 4),
            'cost_per_second': round(cost_per_second, 6),
            'efficiency_grade': efficiency_grade,
            'avg_execution_time': round(avg_execution_time, 2)
        }
    
    async def _identify_cost_optimization_opportunities(
        self,
        workflow_id: str,
        pattern: str,
        agents: List[str],
        cost_breakdown: CostBreakdown
    ) -> List[Dict[str, Any]]:
        """비용 최적화 기회 식별"""
        opportunities = []
        
        # 각 최적화 규칙 적용
        for rule in self.optimization_rules:
            if rule['condition'](cost_breakdown):
                opportunities.append({
                    'type': rule['action'],
                    'title': rule['name'],
                    'description': rule['description'],
                    'potential_savings_percent': rule['potential_savings'] * 100,
                    'estimated_monthly_savings': cost_breakdown.total_cost * rule['potential_savings'] * 30,
                    'priority': self._calculate_opportunity_priority(rule['potential_savings'], cost_breakdown)
                })
        
        # 비용 구성 요소별 특화 기회
        if cost_breakdown.llm_api_cost > cost_breakdown.total_cost * 0.5:
            opportunities.append({
                'type': 'llm_optimization',
                'title': 'LLM 사용 최적화',
                'description': 'LLM API 비용이 전체의 50% 이상을 차지합니다. 모델 선택이나 프롬프트 최적화를 고려하세요.',
                'potential_savings_percent': 25,
                'estimated_monthly_savings': cost_breakdown.llm_api_cost * 0.25 * 30,
                'priority': 'high'
            })
        
        if cost_breakdown.compute_cost > cost_breakdown.total_cost * 0.4:
            opportunities.append({
                'type': 'compute_optimization',
                'title': '컴퓨팅 리소스 최적화',
                'description': '컴퓨팅 비용이 높습니다. Agent 수를 줄이거나 실행 패턴을 최적화하세요.',
                'potential_savings_percent': 20,
                'estimated_monthly_savings': cost_breakdown.compute_cost * 0.20 * 30,
                'priority': 'medium'
            })
        
        return sorted(opportunities, key=lambda x: x['potential_savings_percent'], reverse=True)
    
    def _calculate_opportunity_priority(self, potential_savings: float, cost_breakdown: CostBreakdown) -> str:
        """기회 우선순위 계산"""
        savings_amount = cost_breakdown.total_cost * potential_savings
        
        if savings_amount > 0.05:  # $0.05 이상 절약
            return 'high'
        elif savings_amount > 0.02:  # $0.02 이상 절약
            return 'medium'
        else:
            return 'low'
    
    def _calculate_cost_grade(self, cost_breakdown: CostBreakdown) -> str:
        """비용 등급 계산"""
        total_cost = cost_breakdown.total_cost
        
        if total_cost <= 0.05:
            return 'A+'
        elif total_cost <= 0.1:
            return 'A'
        elif total_cost <= 0.2:
            return 'B'
        elif total_cost <= 0.3:
            return 'C'
        else:
            return 'D'
    
    def _project_monthly_costs(
        self,
        cost_breakdown: CostBreakdown,
        executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """월간 비용 예측"""
        # 일일 실행 횟수 추정
        execution_days = len(set(e.get('timestamp', '')[:10] for e in executions))
        daily_executions = len(executions) / max(1, execution_days)
        
        # 월간 예측
        monthly_executions = daily_executions * 30
        monthly_cost = cost_breakdown.total_cost * monthly_executions
        
        return {
            'daily_executions': round(daily_executions, 1),
            'monthly_executions': round(monthly_executions, 0),
            'monthly_cost': round(monthly_cost, 2),
            'annual_cost': round(monthly_cost * 12, 2),
            'cost_breakdown': {
                'monthly_compute': round(cost_breakdown.compute_cost * monthly_executions, 2),
                'monthly_llm': round(cost_breakdown.llm_api_cost * monthly_executions, 2),
                'monthly_storage': round(cost_breakdown.storage_cost * monthly_executions, 2),
                'monthly_network': round(cost_breakdown.network_cost * monthly_executions, 2),
                'monthly_overhead': round(cost_breakdown.overhead_cost * monthly_executions, 2)
            }
        }
    
    async def _generate_optimization_actions(
        self,
        pattern: str,
        agents: List[str],
        current_cost: CostBreakdown,
        strategy: CostOptimizationStrategy
    ) -> List[Dict[str, Any]]:
        """최적화 액션 생성"""
        actions = []
        
        # 전략별 액션 생성
        if strategy == CostOptimizationStrategy.AGGRESSIVE:
            # 적극적 비용 절감
            if current_cost.llm_api_cost > current_cost.total_cost * 0.3:
                actions.append({
                    'type': 'llm_model_downgrade',
                    'description': '더 저렴한 LLM 모델로 변경',
                    'target': 'llm_model',
                    'change': 'gpt-4 → gpt-3.5-turbo',
                    'estimated_savings': current_cost.llm_api_cost * 0.7,
                    'risk_level': 'medium',
                    'auto_applicable': False
                })
            
            if pattern == 'parallel' and len(agents) > 2:
                actions.append({
                    'type': 'pattern_change',
                    'description': '병렬 실행을 순차 실행으로 변경',
                    'target': 'execution_pattern',
                    'change': f'{pattern} → sequential',
                    'estimated_savings': current_cost.compute_cost * 0.4,
                    'risk_level': 'high',
                    'auto_applicable': False
                })
        
        elif strategy == CostOptimizationStrategy.BALANCED:
            # 균형잡힌 최적화
            if current_cost.overhead_cost > current_cost.total_cost * 0.15:
                actions.append({
                    'type': 'caching_implementation',
                    'description': '결과 캐싱으로 중복 계산 방지',
                    'target': 'caching_layer',
                    'change': 'cache_ttl: 3600s',
                    'estimated_savings': current_cost.total_cost * 0.2,
                    'risk_level': 'low',
                    'auto_applicable': True
                })
            
            if len(agents) > 3:
                actions.append({
                    'type': 'agent_optimization',
                    'description': '중복 기능 Agent 통합',
                    'target': 'agent_configuration',
                    'change': f'agents: {len(agents)} → {len(agents)-1}',
                    'estimated_savings': current_cost.compute_cost * 0.15,
                    'risk_level': 'medium',
                    'auto_applicable': False
                })
        
        else:  # CONSERVATIVE
            # 보수적 최적화 (위험 최소화)
            actions.append({
                'type': 'resource_right_sizing',
                'description': '리소스 사용량 최적화',
                'target': 'resource_allocation',
                'change': 'memory_limit: 512MB → 256MB',
                'estimated_savings': current_cost.compute_cost * 0.1,
                'risk_level': 'low',
                'auto_applicable': True
            })
        
        # 공통 최적화 액션
        actions.append({
            'type': 'monitoring_optimization',
            'description': '불필요한 로깅 및 모니터링 최적화',
            'target': 'monitoring_configuration',
            'change': 'log_level: DEBUG → INFO',
            'estimated_savings': current_cost.overhead_cost * 0.1,
            'risk_level': 'low',
            'auto_applicable': True
        })
        
        return actions
    
    async def _calculate_optimized_cost(
        self,
        current_cost: CostBreakdown,
        optimization_actions: List[Dict[str, Any]]
    ) -> CostBreakdown:
        """최적화 후 비용 계산"""
        optimized_cost = CostBreakdown(
            compute_cost=current_cost.compute_cost,
            llm_api_cost=current_cost.llm_api_cost,
            storage_cost=current_cost.storage_cost,
            network_cost=current_cost.network_cost,
            overhead_cost=current_cost.overhead_cost
        )
        
        for action in optimization_actions:
            savings = action.get('estimated_savings', 0)
            action_type = action.get('type', '')
            
            # 액션 타입별 비용 조정
            if 'llm' in action_type:
                optimized_cost.llm_api_cost = max(0, optimized_cost.llm_api_cost - savings)
            elif 'compute' in action_type or 'pattern' in action_type:
                optimized_cost.compute_cost = max(0, optimized_cost.compute_cost - savings)
            elif 'caching' in action_type or 'monitoring' in action_type:
                optimized_cost.overhead_cost = max(0, optimized_cost.overhead_cost - savings)
            else:
                # 전체 비용에서 비례적으로 차감
                total_reduction_ratio = savings / current_cost.total_cost
                optimized_cost.compute_cost *= (1 - total_reduction_ratio)
                optimized_cost.llm_api_cost *= (1 - total_reduction_ratio)
                optimized_cost.overhead_cost *= (1 - total_reduction_ratio)
        
        return optimized_cost
    
    def _calculate_estimated_savings(
        self,
        current_cost: CostBreakdown,
        optimized_cost: CostBreakdown,
        monthly_projection: Dict[str, Any]
    ) -> Dict[str, float]:
        """절약 추정치 계산"""
        cost_reduction = current_cost.total_cost - optimized_cost.total_cost
        reduction_percent = (cost_reduction / current_cost.total_cost * 100) if current_cost.total_cost > 0 else 0
        
        monthly_executions = monthly_projection.get('monthly_executions', 1000)
        
        return {
            'cost_reduction_per_execution': round(cost_reduction, 4),
            'cost_reduction_percent': round(reduction_percent, 2),
            'monthly_savings': round(cost_reduction * monthly_executions, 2),
            'annual_savings': round(cost_reduction * monthly_executions * 12, 2),
            'roi_months': round(current_cost.total_cost / max(0.01, cost_reduction), 1) if cost_reduction > 0 else float('inf')
        }
    
    def _assess_optimization_complexity(
        self,
        optimization_actions: List[Dict[str, Any]],
        strategy: CostOptimizationStrategy
    ) -> Tuple[str, str]:
        """최적화 복잡도 평가"""
        risk_scores = []
        effort_scores = []
        
        risk_mapping = {'low': 1, 'medium': 2, 'high': 3}
        
        for action in optimization_actions:
            risk_level = action.get('risk_level', 'medium')
            risk_scores.append(risk_mapping.get(risk_level, 2))
            
            # 노력 점수 (액션 타입별)
            action_type = action.get('type', '')
            if 'model' in action_type or 'pattern' in action_type:
                effort_scores.append(3)  # 높은 노력
            elif 'agent' in action_type:
                effort_scores.append(2)  # 중간 노력
            else:
                effort_scores.append(1)  # 낮은 노력
        
        # 평균 위험도
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 1
        if avg_risk <= 1.5:
            risk_level = 'low'
        elif avg_risk <= 2.5:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        # 평균 노력도
        avg_effort = sum(effort_scores) / len(effort_scores) if effort_scores else 1
        if avg_effort <= 1.5:
            implementation_effort = 'low'
        elif avg_effort <= 2.5:
            implementation_effort = 'medium'
        else:
            implementation_effort = 'high'
        
        return risk_level, implementation_effort
    
    def _calculate_optimization_confidence(
        self,
        optimization_actions: List[Dict[str, Any]],
        cost_analysis: Dict[str, Any]
    ) -> float:
        """최적화 신뢰도 계산"""
        base_confidence = 0.7
        
        # 데이터 품질에 따른 조정
        execution_count = cost_analysis.get('analysis_period', {}).get('execution_count', 0)
        if execution_count >= 50:
            data_quality_factor = 1.0
        elif execution_count >= 20:
            data_quality_factor = 0.9
        elif execution_count >= 10:
            data_quality_factor = 0.8
        else:
            data_quality_factor = 0.6
        
        # 액션 복잡도에 따른 조정
        complex_actions = sum(1 for action in optimization_actions if action.get('risk_level') == 'high')
        complexity_factor = max(0.7, 1.0 - (complex_actions * 0.1))
        
        confidence = base_confidence * data_quality_factor * complexity_factor
        return min(0.95, confidence)
    
    async def _implement_optimization_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """최적화 액션 구현"""
        action_type = action.get('type', '')
        
        try:
            if action_type == 'caching_implementation':
                # 캐싱 구현 (시뮬레이션)
                return {
                    'action': action_type,
                    'status': 'success',
                    'message': '캐싱이 성공적으로 구현되었습니다.',
                    'estimated_savings': action.get('estimated_savings', 0)
                }
            
            elif action_type == 'resource_right_sizing':
                # 리소스 최적화 (시뮬레이션)
                return {
                    'action': action_type,
                    'status': 'success',
                    'message': '리소스 할당이 최적화되었습니다.',
                    'estimated_savings': action.get('estimated_savings', 0)
                }
            
            elif action_type == 'monitoring_optimization':
                # 모니터링 최적화 (시뮬레이션)
                return {
                    'action': action_type,
                    'status': 'success',
                    'message': '모니터링 설정이 최적화되었습니다.',
                    'estimated_savings': action.get('estimated_savings', 0)
                }
            
            else:
                # 수동 구현 필요
                return {
                    'action': action_type,
                    'status': 'manual_implementation_required',
                    'message': '이 최적화는 수동 구현이 필요합니다.',
                    'instructions': action.get('description', '')
                }
                
        except Exception as e:
            return {
                'action': action_type,
                'status': 'failed',
                'error': str(e)
            }
    
    async def _get_cost_data(
        self,
        workflow_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[float]:
        """기간별 비용 데이터 조회"""
        # 실제 구현에서는 데이터베이스에서 조회
        # 여기서는 시뮬레이션 데이터 반환
        import random
        
        days = (end_date - start_date).days
        costs = []
        
        for _ in range(min(days * 5, 50)):  # 일일 최대 5회 실행 가정
            costs.append(random.uniform(0.05, 0.15))
        
        return costs
    
    def _calculate_optimization_effectiveness(self, cost_reduction_percent: float) -> str:
        """최적화 효과성 계산"""
        if cost_reduction_percent >= 30:
            return 'excellent'
        elif cost_reduction_percent >= 20:
            return 'good'
        elif cost_reduction_percent >= 10:
            return 'moderate'
        elif cost_reduction_percent >= 5:
            return 'minimal'
        else:
            return 'negligible'