"""
Auto Scaling Manager

자동 스케일링 관리 시스템 - 부하에 따른 동적 리소스 조정
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import statistics
from collections import defaultdict, deque

from backend.core.event_bus.validated_event_bus import ValidatedEventBus, EventType
from backend.core.monitoring.plugin_performance_monitor import PluginPerformanceMonitor
from backend.core.monitoring.advanced_metrics_collector import AdvancedMetricsCollector

logger = logging.getLogger(__name__)


class ScalingAction(Enum):
    """스케일링 액션"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    EMERGENCY_SCALE = "emergency_scale"


class ScalingTrigger(Enum):
    """스케일링 트리거"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    QUEUE_LENGTH = "queue_length"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    PREDICTIVE = "predictive"


@dataclass
class ScalingMetric:
    """스케일링 메트릭"""
    metric_name: str
    current_value: float
    threshold_up: float
    threshold_down: float
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ScalingDecision:
    """스케일링 결정"""
    action: ScalingAction
    target_plugin: str
    current_instances: int
    target_instances: int
    confidence: float
    reasoning: str
    triggers: List[ScalingTrigger]
    estimated_impact: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ScalingPolicy:
    """스케일링 정책"""
    plugin_type: str
    min_instances: int = 1
    max_instances: int = 10
    target_cpu_utilization: float = 70.0
    target_memory_utilization: float = 80.0
    target_response_time: float = 2.0
    scale_up_cooldown: int = 300  # 5분
    scale_down_cooldown: int = 600  # 10분
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 30.0
    aggressive_scaling: bool = False


class LoadPredictor:
    """부하 예측기"""
    
    def __init__(self):
        self.historical_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.prediction_models: Dict[str, Any] = {}
    
    async def predict_load(
        self, 
        plugin_type: str, 
        time_horizon_minutes: int = 30
    ) -> Dict[str, Any]:
        """부하 예측"""
        
        if plugin_type not in self.historical_data:
            return {
                'predicted_load': 0.0,
                'confidence': 0.0,
                'trend': 'unknown'
            }
        
        data = list(self.historical_data[plugin_type])
        if len(data) < 10:
            return {
                'predicted_load': data[-1] if data else 0.0,
                'confidence': 0.3,
                'trend': 'insufficient_data'
            }
        
        # 간단한 선형 회귀 예측
        x_values = list(range(len(data)))
        y_values = [d['load'] for d in data]
        
        # 최소제곱법으로 기울기 계산
        n = len(data)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # 예측값 계산
        future_x = len(data) + (time_horizon_minutes / 5)  # 5분 간격 가정
        predicted_load = slope * future_x + intercept
        
        # 신뢰도 계산 (R-squared 기반)
        y_mean = statistics.mean(y_values)
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # 트렌드 결정
        if abs(slope) < 0.1:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        return {
            'predicted_load': max(0, predicted_load),
            'confidence': max(0, min(1, r_squared)),
            'trend': trend,
            'slope': slope,
            'current_load': y_values[-1] if y_values else 0
        }
    
    def update_historical_data(self, plugin_type: str, load_data: Dict[str, Any]):
        """이력 데이터 업데이트"""
        self.historical_data[plugin_type].append({
            'timestamp': datetime.now(),
            'load': load_data.get('cpu_usage', 0.0),
            'memory': load_data.get('memory_usage', 0.0),
            'queue_length': load_data.get('queue_length', 0),
            'response_time': load_data.get('response_time', 0.0)
        })


class ResourceManager:
    """리소스 관리자"""
    
    def __init__(self):
        self.plugin_instances: Dict[str, int] = defaultdict(int)
        self.resource_limits = {
            'max_total_instances': 50,
            'max_cpu_cores': 16,
            'max_memory_gb': 32
        }
        self.current_resource_usage = {
            'total_instances': 0,
            'cpu_cores_used': 0,
            'memory_gb_used': 0
        }
    
    async def can_scale_up(self, plugin_type: str, instances: int = 1) -> Tuple[bool, str]:
        """스케일 업 가능 여부 확인"""
        
        # 전체 인스턴스 제한 확인
        if (self.current_resource_usage['total_instances'] + instances > 
            self.resource_limits['max_total_instances']):
            return False, "Total instance limit exceeded"
        
        # CPU 제한 확인 (인스턴스당 0.5 코어 가정)
        cpu_needed = instances * 0.5
        if (self.current_resource_usage['cpu_cores_used'] + cpu_needed > 
            self.resource_limits['max_cpu_cores']):
            return False, "CPU limit exceeded"
        
        # 메모리 제한 확인 (인스턴스당 1GB 가정)
        memory_needed = instances * 1.0
        if (self.current_resource_usage['memory_gb_used'] + memory_needed > 
            self.resource_limits['max_memory_gb']):
            return False, "Memory limit exceeded"
        
        return True, "Resources available"
    
    async def scale_up_plugin(self, plugin_type: str, instances: int = 1) -> bool:
        """플러그인 스케일 업"""
        
        can_scale, reason = await self.can_scale_up(plugin_type, instances)
        if not can_scale:
            logger.warning(f"Cannot scale up {plugin_type}: {reason}")
            return False
        
        # 리소스 할당
        self.plugin_instances[plugin_type] += instances
        self.current_resource_usage['total_instances'] += instances
        self.current_resource_usage['cpu_cores_used'] += instances * 0.5
        self.current_resource_usage['memory_gb_used'] += instances * 1.0
        
        logger.info(f"Scaled up {plugin_type} by {instances} instances")
        return True
    
    async def scale_down_plugin(self, plugin_type: str, instances: int = 1) -> bool:
        """플러그인 스케일 다운"""
        
        current_instances = self.plugin_instances.get(plugin_type, 0)
        if current_instances < instances:
            logger.warning(f"Cannot scale down {plugin_type}: insufficient instances")
            return False
        
        # 최소 인스턴스 확인 (1개는 유지)
        if current_instances - instances < 1:
            instances = current_instances - 1
            if instances <= 0:
                return False
        
        # 리소스 해제
        self.plugin_instances[plugin_type] -= instances
        self.current_resource_usage['total_instances'] -= instances
        self.current_resource_usage['cpu_cores_used'] -= instances * 0.5
        self.current_resource_usage['memory_gb_used'] -= instances * 1.0
        
        logger.info(f"Scaled down {plugin_type} by {instances} instances")
        return True
    
    def get_plugin_instances(self, plugin_type: str) -> int:
        """플러그인 인스턴스 수 조회"""
        return self.plugin_instances.get(plugin_type, 1)  # 기본 1개
    
    def get_resource_utilization(self) -> Dict[str, float]:
        """리소스 사용률 조회"""
        return {
            'instance_utilization': (
                self.current_resource_usage['total_instances'] / 
                self.resource_limits['max_total_instances'] * 100
            ),
            'cpu_utilization': (
                self.current_resource_usage['cpu_cores_used'] / 
                self.resource_limits['max_cpu_cores'] * 100
            ),
            'memory_utilization': (
                self.current_resource_usage['memory_gb_used'] / 
                self.resource_limits['max_memory_gb'] * 100
            )
        }


class AutoScalingManager:
    """자동 스케일링 관리자"""
    
    def __init__(
        self, 
        event_bus: ValidatedEventBus,
        performance_monitor: PluginPerformanceMonitor,
        metrics_collector: AdvancedMetricsCollector
    ):
        self.event_bus = event_bus
        self.performance_monitor = performance_monitor
        self.metrics_collector = metrics_collector
        
        # 핵심 컴포넌트
        self.load_predictor = LoadPredictor()
        self.resource_manager = ResourceManager()
        
        # 스케일링 정책
        self.scaling_policies: Dict[str, ScalingPolicy] = {}
        self.default_policy = ScalingPolicy(plugin_type="default")
        
        # 스케일링 이력
        self.scaling_history: deque = deque(maxlen=1000)
        self.last_scaling_time: Dict[str, datetime] = {}
        
        # 자동 스케일링 설정
        self.auto_scaling_enabled = True
        self.monitoring_interval = 30  # 30초마다 확인
        self.emergency_threshold = 95.0  # 95% 이상시 긴급 스케일링
        
        # 모니터링 태스크
        self._monitoring_task: Optional[asyncio.Task] = None
    
    async def start_auto_scaling(self):
        """자동 스케일링 시작"""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Auto scaling started")
            
            await self.event_bus.publish(
                'auto_scaling_started',
                {
                    'monitoring_interval': self.monitoring_interval,
                    'emergency_threshold': self.emergency_threshold,
                    'timestamp': datetime.now().isoformat()
                },
                source='auto_scaling_manager'
            )
    
    async def stop_auto_scaling(self):
        """자동 스케일링 중지"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Auto scaling stopped")
    
    async def _monitoring_loop(self):
        """모니터링 루프"""
        while True:
            try:
                if self.auto_scaling_enabled:
                    await self._evaluate_scaling_needs()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto scaling monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _evaluate_scaling_needs(self):
        """스케일링 필요성 평가"""
        
        # 모든 플러그인의 성능 메트릭 수집
        performance_summary = self.performance_monitor.get_all_metrics_summary()
        
        for plugin_type, metrics in performance_summary.get('plugins', {}).items():
            
            # 스케일링 정책 가져오기
            policy = self.scaling_policies.get(plugin_type, self.default_policy)
            
            # 현재 메트릭 수집
            current_metrics = await self._collect_scaling_metrics(plugin_type, metrics)
            
            # 스케일링 결정
            decision = await self._make_scaling_decision(plugin_type, current_metrics, policy)
            
            if decision.action != ScalingAction.MAINTAIN:
                await self._execute_scaling_decision(decision)
    
    async def _collect_scaling_metrics(
        self, 
        plugin_type: str, 
        performance_metrics: Dict[str, Any]
    ) -> List[ScalingMetric]:
        """스케일링 메트릭 수집"""
        
        metrics = []
        
        # CPU 사용률 (추정)
        avg_execution_time = performance_metrics.get('avg_execution_time', 0.0)
        cpu_usage = min(100, avg_execution_time * 20)  # 간단한 추정
        
        metrics.append(ScalingMetric(
            metric_name='cpu_usage',
            current_value=cpu_usage,
            threshold_up=80.0,
            threshold_down=30.0,
            weight=1.0
        ))
        
        # 메모리 사용률 (추정)
        memory_usage = performance_metrics.get('avg_memory_usage', 0.0)
        
        metrics.append(ScalingMetric(
            metric_name='memory_usage',
            current_value=memory_usage,
            threshold_up=85.0,
            threshold_down=40.0,
            weight=0.8
        ))
        
        # 응답 시간
        response_time = performance_metrics.get('avg_execution_time', 0.0)
        
        metrics.append(ScalingMetric(
            metric_name='response_time',
            current_value=response_time,
            threshold_up=5.0,  # 5초 이상
            threshold_down=1.0,  # 1초 이하
            weight=1.2
        ))
        
        # 에러율
        total_executions = performance_metrics.get('total_executions', 1)
        failure_count = performance_metrics.get('failure_count', 0)
        error_rate = (failure_count / total_executions) * 100
        
        metrics.append(ScalingMetric(
            metric_name='error_rate',
            current_value=error_rate,
            threshold_up=10.0,  # 10% 이상
            threshold_down=2.0,   # 2% 이하
            weight=1.5
        ))
        
        # 처리량 (초당 실행 수 추정)
        throughput = performance_metrics.get('throughput', 0.0)
        
        metrics.append(ScalingMetric(
            metric_name='throughput',
            current_value=throughput,
            threshold_up=0.5,   # 초당 0.5개 이하면 스케일 업 고려
            threshold_down=5.0,  # 초당 5개 이상이면 스케일 다운 고려
            weight=0.9
        ))
        
        return metrics
    
    async def _make_scaling_decision(
        self, 
        plugin_type: str, 
        metrics: List[ScalingMetric], 
        policy: ScalingPolicy
    ) -> ScalingDecision:
        """스케일링 결정"""
        
        current_instances = self.resource_manager.get_plugin_instances(plugin_type)
        
        # 쿨다운 확인
        last_scaling = self.last_scaling_time.get(plugin_type)
        if last_scaling:
            time_since_last = (datetime.now() - last_scaling).total_seconds()
            if time_since_last < policy.scale_up_cooldown:
                return ScalingDecision(
                    action=ScalingAction.MAINTAIN,
                    target_plugin=plugin_type,
                    current_instances=current_instances,
                    target_instances=current_instances,
                    confidence=1.0,
                    reasoning="Cooldown period active",
                    triggers=[],
                    estimated_impact={}
                )
        
        # 스케일링 점수 계산
        scale_up_score = 0.0
        scale_down_score = 0.0
        triggered_metrics = []
        
        for metric in metrics:
            if metric.current_value > metric.threshold_up:
                scale_up_score += metric.weight * (
                    (metric.current_value - metric.threshold_up) / metric.threshold_up
                )
                triggered_metrics.append(ScalingTrigger(metric.metric_name))
            
            elif metric.current_value < metric.threshold_down:
                scale_down_score += metric.weight * (
                    (metric.threshold_down - metric.current_value) / metric.threshold_down
                )
        
        # 예측 기반 조정
        prediction = await self.load_predictor.predict_load(plugin_type)
        if prediction['trend'] == 'increasing' and prediction['confidence'] > 0.7:
            scale_up_score += 0.5
            triggered_metrics.append(ScalingTrigger.PREDICTIVE)
        elif prediction['trend'] == 'decreasing' and prediction['confidence'] > 0.7:
            scale_down_score += 0.3
        
        # 긴급 스케일링 확인
        emergency_metrics = [m for m in metrics if m.current_value > self.emergency_threshold]
        if emergency_metrics:
            return ScalingDecision(
                action=ScalingAction.EMERGENCY_SCALE,
                target_plugin=plugin_type,
                current_instances=current_instances,
                target_instances=min(current_instances + 3, policy.max_instances),
                confidence=1.0,
                reasoning=f"Emergency scaling due to {len(emergency_metrics)} critical metrics",
                triggers=[ScalingTrigger(m.metric_name) for m in emergency_metrics],
                estimated_impact={
                    'performance_improvement': 60.0,
                    'cost_increase': 200.0
                }
            )
        
        # 스케일링 결정
        if scale_up_score > 1.0 and current_instances < policy.max_instances:
            target_instances = min(current_instances + 1, policy.max_instances)
            
            return ScalingDecision(
                action=ScalingAction.SCALE_UP,
                target_plugin=plugin_type,
                current_instances=current_instances,
                target_instances=target_instances,
                confidence=min(1.0, scale_up_score / 2.0),
                reasoning=f"Scale up score: {scale_up_score:.2f}",
                triggers=triggered_metrics,
                estimated_impact={
                    'performance_improvement': min(50.0, scale_up_score * 20),
                    'cost_increase': 100.0 / current_instances
                }
            )
        
        elif scale_down_score > 1.0 and current_instances > policy.min_instances:
            target_instances = max(current_instances - 1, policy.min_instances)
            
            return ScalingDecision(
                action=ScalingAction.SCALE_DOWN,
                target_plugin=plugin_type,
                current_instances=current_instances,
                target_instances=target_instances,
                confidence=min(1.0, scale_down_score / 2.0),
                reasoning=f"Scale down score: {scale_down_score:.2f}",
                triggers=triggered_metrics,
                estimated_impact={
                    'cost_reduction': 100.0 / current_instances,
                    'performance_impact': -min(20.0, scale_down_score * 10)
                }
            )
        
        return ScalingDecision(
            action=ScalingAction.MAINTAIN,
            target_plugin=plugin_type,
            current_instances=current_instances,
            target_instances=current_instances,
            confidence=1.0,
            reasoning="No scaling needed",
            triggers=[],
            estimated_impact={}
        )
    
    async def _execute_scaling_decision(self, decision: ScalingDecision):
        """스케일링 결정 실행"""
        
        success = False
        
        if decision.action == ScalingAction.SCALE_UP or decision.action == ScalingAction.EMERGENCY_SCALE:
            instances_to_add = decision.target_instances - decision.current_instances
            success = await self.resource_manager.scale_up_plugin(
                decision.target_plugin, instances_to_add
            )
        
        elif decision.action == ScalingAction.SCALE_DOWN:
            instances_to_remove = decision.current_instances - decision.target_instances
            success = await self.resource_manager.scale_down_plugin(
                decision.target_plugin, instances_to_remove
            )
        
        # 실행 결과 기록
        if success:
            self.last_scaling_time[decision.target_plugin] = datetime.now()
            self.scaling_history.append(decision)
            
            # 부하 예측기 데이터 업데이트
            self.load_predictor.update_historical_data(
                decision.target_plugin,
                {'cpu_usage': 50.0}  # 실제로는 현재 메트릭 사용
            )
        
        # 스케일링 이벤트 발행
        await self.event_bus.publish(
            EventType.SCALING_EVENT,
            {
                'action': decision.action.value,
                'plugin_type': decision.target_plugin,
                'current_instances': decision.current_instances,
                'target_instances': decision.target_instances,
                'success': success,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning,
                'triggers': [t.value for t in decision.triggers],
                'estimated_impact': decision.estimated_impact,
                'timestamp': decision.timestamp.isoformat()
            },
            source='auto_scaling_manager'
        )
        
        logger.info(
            f"Scaling decision executed: {decision.action.value} "
            f"{decision.target_plugin} from {decision.current_instances} "
            f"to {decision.target_instances} (success: {success})"
        )
    
    def set_scaling_policy(self, plugin_type: str, policy: ScalingPolicy):
        """스케일링 정책 설정"""
        self.scaling_policies[plugin_type] = policy
        logger.info(f"Scaling policy set for {plugin_type}")
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """스케일링 상태 조회"""
        
        resource_utilization = self.resource_manager.get_resource_utilization()
        
        # 최근 스케일링 이력
        recent_scaling = list(self.scaling_history)[-10:]
        
        return {
            'auto_scaling_enabled': self.auto_scaling_enabled,
            'monitoring_interval': self.monitoring_interval,
            'resource_utilization': resource_utilization,
            'plugin_instances': dict(self.resource_manager.plugin_instances),
            'scaling_policies_count': len(self.scaling_policies),
            'recent_scaling_actions': [
                {
                    'action': s.action.value,
                    'plugin': s.target_plugin,
                    'timestamp': s.timestamp.isoformat(),
                    'success': True  # 실제로는 실행 결과 추적 필요
                }
                for s in recent_scaling
            ],
            'total_scaling_actions': len(self.scaling_history)
        }
    
    async def manual_scale(
        self, 
        plugin_type: str, 
        target_instances: int,
        reason: str = "Manual scaling"
    ) -> Dict[str, Any]:
        """수동 스케일링"""
        
        current_instances = self.resource_manager.get_plugin_instances(plugin_type)
        
        if target_instances == current_instances:
            return {
                'success': True,
                'message': 'No scaling needed',
                'current_instances': current_instances
            }
        
        # 스케일링 실행
        if target_instances > current_instances:
            instances_to_add = target_instances - current_instances
            success = await self.resource_manager.scale_up_plugin(plugin_type, instances_to_add)
            action = ScalingAction.SCALE_UP
        else:
            instances_to_remove = current_instances - target_instances
            success = await self.resource_manager.scale_down_plugin(plugin_type, instances_to_remove)
            action = ScalingAction.SCALE_DOWN
        
        # 결과 기록
        if success:
            decision = ScalingDecision(
                action=action,
                target_plugin=plugin_type,
                current_instances=current_instances,
                target_instances=target_instances,
                confidence=1.0,
                reasoning=reason,
                triggers=[],
                estimated_impact={}
            )
            
            self.scaling_history.append(decision)
            self.last_scaling_time[plugin_type] = datetime.now()
        
        return {
            'success': success,
            'action': action.value,
            'current_instances': current_instances,
            'target_instances': target_instances,
            'message': 'Manual scaling completed' if success else 'Manual scaling failed'
        }
    
    def get_scaling_recommendations(self) -> List[Dict[str, Any]]:
        """스케일링 권장사항"""
        
        recommendations = []
        
        # 리소스 사용률 기반 권장사항
        utilization = self.resource_manager.get_resource_utilization()
        
        if utilization['instance_utilization'] > 80:
            recommendations.append({
                'type': 'resource_optimization',
                'priority': 'high',
                'message': 'Consider increasing resource limits or optimizing plugin efficiency',
                'current_utilization': utilization['instance_utilization']
            })
        
        # 스케일링 이력 기반 권장사항
        if len(self.scaling_history) > 0:
            recent_actions = list(self.scaling_history)[-20:]
            scale_up_count = sum(1 for s in recent_actions if s.action == ScalingAction.SCALE_UP)
            
            if scale_up_count > 10:
                recommendations.append({
                    'type': 'policy_adjustment',
                    'priority': 'medium',
                    'message': 'Frequent scale-up events detected. Consider adjusting thresholds.',
                    'scale_up_frequency': scale_up_count
                })
        
        return recommendations