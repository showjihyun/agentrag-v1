"""
Adaptive Workflow Optimizer

Analyzes workflow execution patterns and provides intelligent optimization suggestions
for improved performance, cost efficiency, and reliability.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.db.models.flows import Agentflow, FlowExecution
from backend.services.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    PERFORMANCE = "performance"
    COST = "cost"
    RELIABILITY = "reliability"
    RESOURCE = "resource"


class OptimizationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OptimizationImpact(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class OptimizationSuggestion:
    """Optimization suggestion with detailed analysis."""
    type: OptimizationType
    title: str
    description: str
    impact: OptimizationImpact
    priority: OptimizationPriority
    action: Optional[str] = None
    estimated_improvement: Optional[float] = None
    implementation_effort: Optional[str] = None
    confidence_score: Optional[float] = None


@dataclass
class WorkflowAnalysis:
    """Comprehensive workflow analysis results."""
    workflow_id: str
    analysis_timestamp: datetime
    execution_count: int
    success_rate: float
    average_duration: float
    bottlenecks: List[Dict[str, Any]]
    resource_usage: Dict[str, float]
    cost_analysis: Dict[str, float]
    optimization_score: float
    suggestions: List[OptimizationSuggestion]


@dataclass
class BottleneckAnalysis:
    """Analysis of workflow bottlenecks."""
    agent_id: str
    agent_name: str
    bottleneck_type: str  # sequential_dependency, resource_contention, slow_execution
    severity: float  # 0-1 scale
    frequency: float  # How often this bottleneck occurs
    impact_on_total_time: float  # Percentage of total execution time
    suggested_fixes: List[str]


class AdaptiveWorkflowOptimizer:
    """
    Intelligent workflow optimizer that learns from execution patterns
    and provides actionable optimization recommendations.
    """

    def __init__(self, db: Session, llm_manager: Optional[LLMManager] = None):
        """
        Initialize the workflow optimizer.

        Args:
            db: Database session
            llm_manager: Optional LLM manager for advanced analysis
        """
        self.db = db
        self.llm = llm_manager
        self.analysis_cache = {}
        self.cache_ttl = timedelta(minutes=30)

    async def analyze_workflow(self, workflow_id: str, days_back: int = 30) -> WorkflowAnalysis:
        """
        Perform comprehensive workflow analysis.

        Args:
            workflow_id: ID of the workflow to analyze
            days_back: Number of days of execution history to analyze

        Returns:
            Comprehensive workflow analysis
        """
        # Check cache first
        cache_key = f"{workflow_id}_{days_back}"
        if cache_key in self.analysis_cache:
            cached_analysis, timestamp = self.analysis_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_analysis

        logger.info(f"Analyzing workflow {workflow_id} (last {days_back} days)")

        # Get workflow and execution history
        workflow = self.db.query(Agentflow).filter(Agentflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        cutoff_date = datetime.now() - timedelta(days=days_back)
        executions = (
            self.db.query(FlowExecution)
            .filter(
                FlowExecution.agentflow_id == workflow_id,
                FlowExecution.started_at >= cutoff_date
            )
            .order_by(desc(FlowExecution.started_at))
            .all()
        )

        if not executions:
            logger.warning(f"No executions found for workflow {workflow_id}")
            return self._create_empty_analysis(workflow_id)

        # Perform analysis
        execution_count = len(executions)
        success_rate = len([e for e in executions if e.status == 'completed']) / execution_count
        average_duration = sum(e.duration_ms or 0 for e in executions) / execution_count

        # Analyze bottlenecks
        bottlenecks = await self._analyze_bottlenecks(workflow, executions)

        # Analyze resource usage
        resource_usage = self._analyze_resource_usage(executions)

        # Analyze costs
        cost_analysis = self._analyze_costs(executions)

        # Calculate optimization score
        optimization_score = self._calculate_optimization_score(
            success_rate, average_duration, bottlenecks, resource_usage
        )

        # Generate optimization suggestions
        suggestions = await self._generate_optimization_suggestions(
            workflow, executions, bottlenecks, resource_usage, cost_analysis
        )

        analysis = WorkflowAnalysis(
            workflow_id=workflow_id,
            analysis_timestamp=datetime.now(),
            execution_count=execution_count,
            success_rate=success_rate,
            average_duration=average_duration,
            bottlenecks=[b.__dict__ for b in bottlenecks],
            resource_usage=resource_usage,
            cost_analysis=cost_analysis,
            optimization_score=optimization_score,
            suggestions=suggestions
        )

        # Cache the analysis
        self.analysis_cache[cache_key] = (analysis, datetime.now())

        return analysis

    async def _analyze_bottlenecks(self, 
                                 workflow: Agentflow, 
                                 executions: List[FlowExecution]) -> List[BottleneckAnalysis]:
        """Analyze workflow bottlenecks."""
        bottlenecks = []

        # Get agent execution data
        agent_stats = {}
        for execution in executions:
            if not execution.metrics:
                continue

            # FlowExecution uses metrics field instead of execution_details
            metrics = execution.metrics
            agent_timings = metrics.get('agent_timings', {})

            for agent_id, timing_data in agent_timings.items():
                if agent_id not in agent_stats:
                    agent_stats[agent_id] = {
                        'durations': [],
                        'failures': 0,
                        'total_executions': 0,
                        'agent_name': timing_data.get('name', agent_id)
                    }

                agent_stats[agent_id]['durations'].append(timing_data.get('duration_ms', 0))
                agent_stats[agent_id]['total_executions'] += 1
                if timing_data.get('status') == 'failed':
                    agent_stats[agent_id]['failures'] += 1

        # Identify bottlenecks
        total_avg_duration = sum(
            sum(stats['durations']) / len(stats['durations']) 
            for stats in agent_stats.values() if stats['durations']
        )

        for agent_id, stats in agent_stats.items():
            if not stats['durations']:
                continue

            avg_duration = sum(stats['durations']) / len(stats['durations'])
            failure_rate = stats['failures'] / stats['total_executions']

            # Check for slow execution bottleneck
            if avg_duration > total_avg_duration * 0.3:  # Takes >30% of total time
                bottlenecks.append(BottleneckAnalysis(
                    agent_id=agent_id,
                    agent_name=stats['agent_name'],
                    bottleneck_type='slow_execution',
                    severity=min(1.0, avg_duration / total_avg_duration),
                    frequency=1.0,  # Always slow
                    impact_on_total_time=avg_duration / total_avg_duration,
                    suggested_fixes=[
                        'Consider optimizing agent logic',
                        'Check for inefficient API calls',
                        'Implement caching for repeated operations',
                        'Consider parallel processing within agent'
                    ]
                ))

            # Check for reliability bottleneck
            if failure_rate > 0.1:  # >10% failure rate
                bottlenecks.append(BottleneckAnalysis(
                    agent_id=agent_id,
                    agent_name=stats['agent_name'],
                    bottleneck_type='reliability_issue',
                    severity=failure_rate,
                    frequency=failure_rate,
                    impact_on_total_time=0.0,  # Doesn't add time, but affects success
                    suggested_fixes=[
                        'Add retry logic with exponential backoff',
                        'Implement circuit breaker pattern',
                        'Add input validation and error handling',
                        'Consider fallback mechanisms'
                    ]
                ))

        return bottlenecks

    def _analyze_resource_usage(self, executions: List[FlowExecution]) -> Dict[str, float]:
        """Analyze resource usage patterns."""
        total_tokens = 0
        total_memory_mb = 0
        total_cpu_seconds = 0
        execution_count = 0

        for execution in executions:
            if not execution.metrics:
                continue

            metrics = execution.metrics
            
            # Extract resource usage from metrics
            tokens = metrics.get('llm_tokens', 0)
            memory = metrics.get('peak_memory_mb', 0)
            cpu = metrics.get('cpu_seconds', 0)

            total_tokens += tokens
            total_memory_mb += memory
            total_cpu_seconds += cpu
            execution_count += 1

        if execution_count == 0:
            return {}

        return {
            'avg_tokens_per_execution': total_tokens / execution_count,
            'avg_memory_mb_per_execution': total_memory_mb / execution_count,
            'avg_cpu_seconds_per_execution': total_cpu_seconds / execution_count,
            'total_tokens': total_tokens,
            'total_memory_gb_hours': (total_memory_mb / 1024) * (total_cpu_seconds / 3600),
            'resource_efficiency_score': self._calculate_resource_efficiency(
                total_tokens, total_memory_mb, total_cpu_seconds, execution_count
            )
        }

    def _analyze_costs(self, executions: List[FlowExecution]) -> Dict[str, float]:
        """Analyze cost patterns and trends."""
        total_cost = 0
        costs_by_day = {}

        for execution in executions:
            if not execution.metrics:
                continue

            metrics = execution.metrics
            cost = metrics.get('estimated_cost', 0)
            total_cost += cost

            # Group by day for trend analysis
            day = execution.started_at.date()
            if day not in costs_by_day:
                costs_by_day[day] = []
            costs_by_day[day].append(cost)

        # Calculate cost trends
        daily_costs = [sum(costs) for costs in costs_by_day.values()]
        avg_daily_cost = sum(daily_costs) / len(daily_costs) if daily_costs else 0

        # Calculate cost efficiency
        avg_cost_per_execution = total_cost / len(executions) if executions else 0
        
        return {
            'total_cost': total_cost,
            'avg_cost_per_execution': avg_cost_per_execution,
            'avg_daily_cost': avg_daily_cost,
            'cost_trend': self._calculate_cost_trend(daily_costs),
            'cost_efficiency_score': self._calculate_cost_efficiency(avg_cost_per_execution)
        }

    def _calculate_optimization_score(self, 
                                    success_rate: float,
                                    average_duration: float,
                                    bottlenecks: List[BottleneckAnalysis],
                                    resource_usage: Dict[str, float]) -> float:
        """Calculate overall optimization score (0-1)."""
        # Success rate component (40% weight)
        success_component = success_rate * 0.4

        # Performance component (30% weight)
        # Assume 5 seconds is optimal, penalize longer durations
        optimal_duration = 5000  # 5 seconds in ms
        performance_score = max(0, 1 - (average_duration - optimal_duration) / optimal_duration)
        performance_component = performance_score * 0.3

        # Bottleneck component (20% weight)
        bottleneck_penalty = sum(b.severity for b in bottlenecks) / max(1, len(bottlenecks))
        bottleneck_component = max(0, 1 - bottleneck_penalty) * 0.2

        # Resource efficiency component (10% weight)
        resource_efficiency = resource_usage.get('resource_efficiency_score', 0.5)
        resource_component = resource_efficiency * 0.1

        total_score = success_component + performance_component + bottleneck_component + resource_component
        return min(1.0, max(0.0, total_score))

    async def _generate_optimization_suggestions(self,
                                               workflow: Agentflow,
                                               executions: List[FlowExecution],
                                               bottlenecks: List[BottleneckAnalysis],
                                               resource_usage: Dict[str, float],
                                               cost_analysis: Dict[str, float]) -> List[OptimizationSuggestion]:
        """Generate intelligent optimization suggestions."""
        suggestions = []

        # Performance optimizations
        if bottlenecks:
            for bottleneck in bottlenecks:
                if bottleneck.bottleneck_type == 'slow_execution':
                    suggestions.append(OptimizationSuggestion(
                        type=OptimizationType.PERFORMANCE,
                        title=f"{bottleneck.agent_name} 성능 최적화",
                        description=f"이 에이전트가 전체 실행 시간의 {bottleneck.impact_on_total_time*100:.1f}%를 차지합니다. 최적화를 통해 {bottleneck.severity*30:.0f}% 성능 향상이 가능합니다.",
                        impact=OptimizationImpact.HIGH if bottleneck.severity > 0.7 else OptimizationImpact.MEDIUM,
                        priority=OptimizationPriority.HIGH if bottleneck.severity > 0.7 else OptimizationPriority.MEDIUM,
                        action="에이전트 로직 최적화 및 캐싱 구현",
                        estimated_improvement=bottleneck.severity * 0.3,
                        confidence_score=0.8
                    ))

        # Cost optimizations
        avg_cost = cost_analysis.get('avg_cost_per_execution', 0)
        if avg_cost > 0.01:  # If cost per execution > $0.01
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.COST,
                title="토큰 사용량 최적화",
                description=f"실행당 평균 비용이 ${avg_cost:.4f}입니다. 프롬프트 최적화와 캐싱을 통해 비용을 30-50% 절감할 수 있습니다.",
                impact=OptimizationImpact.MEDIUM,
                priority=OptimizationPriority.MEDIUM,
                action="프롬프트 최적화 및 결과 캐싱 활성화",
                estimated_improvement=0.4,
                confidence_score=0.7
            ))

        # Reliability optimizations
        success_rate = len([e for e in executions if e.status == 'completed']) / len(executions)
        if success_rate < 0.95:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.RELIABILITY,
                title="안정성 개선",
                description=f"현재 성공률이 {success_rate*100:.1f}%입니다. 에러 처리와 재시도 로직을 개선하여 95% 이상의 성공률을 달성할 수 있습니다.",
                impact=OptimizationImpact.HIGH,
                priority=OptimizationPriority.HIGH,
                action="재시도 로직 및 에러 처리 강화",
                estimated_improvement=(0.95 - success_rate),
                confidence_score=0.9
            ))

        # Resource optimizations
        resource_efficiency = resource_usage.get('resource_efficiency_score', 0.5)
        if resource_efficiency < 0.7:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.RESOURCE,
                title="리소스 사용량 최적화",
                description="메모리 및 CPU 사용량을 최적화하여 시스템 부하를 줄이고 동시 실행 성능을 향상시킬 수 있습니다.",
                impact=OptimizationImpact.MEDIUM,
                priority=OptimizationPriority.MEDIUM,
                action="메모리 풀링 및 비동기 처리 개선",
                estimated_improvement=0.7 - resource_efficiency,
                confidence_score=0.6
            ))

        # Parallelization suggestions
        if len(workflow.agents) > 1:
            # Check if agents can be parallelized
            sequential_agents = self._identify_sequential_dependencies(workflow)
            if len(sequential_agents) > 2:
                suggestions.append(OptimizationSuggestion(
                    type=OptimizationType.PERFORMANCE,
                    title="병렬 처리 최적화",
                    description=f"{len(sequential_agents)}개의 에이전트가 순차적으로 실행되고 있습니다. 일부를 병렬로 실행하여 전체 시간을 단축할 수 있습니다.",
                    impact=OptimizationImpact.HIGH,
                    priority=OptimizationPriority.HIGH,
                    action="독립적인 에이전트들을 병렬 그룹으로 재구성",
                    estimated_improvement=0.4,
                    confidence_score=0.8
                ))

        return suggestions

    def _identify_sequential_dependencies(self, workflow: Agentflow) -> List[str]:
        """Identify agents that are executed sequentially."""
        # This is a simplified implementation
        # In a real scenario, you'd analyze the workflow graph
        return [agent.id for agent in workflow.agents if agent.execution_order is not None]

    def _calculate_resource_efficiency(self, 
                                     total_tokens: int,
                                     total_memory_mb: float,
                                     total_cpu_seconds: float,
                                     execution_count: int) -> float:
        """Calculate resource efficiency score (0-1)."""
        if execution_count == 0:
            return 0.5

        # Normalize metrics (these thresholds would be tuned based on actual data)
        tokens_per_exec = total_tokens / execution_count
        memory_per_exec = total_memory_mb / execution_count
        cpu_per_exec = total_cpu_seconds / execution_count

        # Score based on reasonable thresholds
        token_score = max(0, 1 - (tokens_per_exec - 1000) / 10000)  # Optimal: 1000 tokens
        memory_score = max(0, 1 - (memory_per_exec - 100) / 1000)   # Optimal: 100MB
        cpu_score = max(0, 1 - (cpu_per_exec - 2) / 10)             # Optimal: 2 seconds

        return (token_score + memory_score + cpu_score) / 3

    def _calculate_cost_efficiency(self, avg_cost_per_execution: float) -> float:
        """Calculate cost efficiency score (0-1)."""
        # Assume $0.005 per execution is optimal
        optimal_cost = 0.005
        if avg_cost_per_execution <= optimal_cost:
            return 1.0
        else:
            # Penalize higher costs
            return max(0, 1 - (avg_cost_per_execution - optimal_cost) / optimal_cost)

    def _calculate_cost_trend(self, daily_costs: List[float]) -> str:
        """Calculate cost trend direction."""
        if len(daily_costs) < 2:
            return "stable"

        recent_avg = sum(daily_costs[-3:]) / min(3, len(daily_costs))
        older_avg = sum(daily_costs[:-3]) / max(1, len(daily_costs) - 3)

        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    def _create_empty_analysis(self, workflow_id: str) -> WorkflowAnalysis:
        """Create empty analysis for workflows with no execution history."""
        return WorkflowAnalysis(
            workflow_id=workflow_id,
            analysis_timestamp=datetime.now(),
            execution_count=0,
            success_rate=0.0,
            average_duration=0.0,
            bottlenecks=[],
            resource_usage={},
            cost_analysis={},
            optimization_score=0.5,
            suggestions=[
                OptimizationSuggestion(
                    type=OptimizationType.PERFORMANCE,
                    title="워크플로우 실행 데이터 수집",
                    description="최적화 제안을 위해 워크플로우를 몇 번 실행해보세요.",
                    impact=OptimizationImpact.LOW,
                    priority=OptimizationPriority.LOW,
                    action="워크플로우 테스트 실행",
                    confidence_score=1.0
                )
            ]
        )

    async def get_optimization_recommendations(self, 
                                            workflow_id: str,
                                            limit: int = 5) -> List[OptimizationSuggestion]:
        """Get top optimization recommendations for a workflow."""
        analysis = await self.analyze_workflow(workflow_id)
        
        # Sort suggestions by priority and impact
        sorted_suggestions = sorted(
            analysis.suggestions,
            key=lambda s: (
                s.priority == OptimizationPriority.HIGH,
                s.impact == OptimizationImpact.HIGH,
                s.confidence_score or 0
            ),
            reverse=True
        )
        
        return sorted_suggestions[:limit]

    def clear_cache(self):
        """Clear the analysis cache."""
        self.analysis_cache.clear()
        logger.info("Workflow optimizer cache cleared")