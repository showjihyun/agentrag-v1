"""
Advanced Metrics Collector

고급 메트릭 수집 및 비즈니스 인사이트 생성
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
from backend.services.plugins.agents.enhanced_agent_plugin_manager import EnhancedAgentPluginManager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """메트릭 타입"""
    PERFORMANCE = "performance"
    BUSINESS = "business"
    OPERATIONAL = "operational"
    SECURITY = "security"
    USER_EXPERIENCE = "user_experience"


class AlertSeverity(Enum):
    """알림 심각도"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class BusinessMetric:
    """비즈니스 메트릭"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class UserSatisfactionMetric:
    """사용자 만족도 메트릭"""
    user_id: str
    workflow_id: str
    satisfaction_score: float  # 0-10
    execution_time: float
    success: bool
    feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ROIMetric:
    """ROI 메트릭"""
    workflow_id: str
    cost_saved: float
    time_saved: float  # seconds
    revenue_generated: float
    efficiency_gain: float  # percentage
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SLAMetric:
    """SLA 메트릭"""
    service_name: str
    target_value: float
    actual_value: float
    compliance_percentage: float
    breach_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class BusinessMetricsCollector:
    """비즈니스 메트릭 수집기"""
    
    def __init__(self, event_bus: ValidatedEventBus):
        self.event_bus = event_bus
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.user_satisfaction_scores: deque = deque(maxlen=5000)
        self.roi_metrics: deque = deque(maxlen=1000)
        self.sla_metrics: Dict[str, SLAMetric] = {}
        
        # SLA 목표값 설정
        self.sla_targets = {
            'execution_time': 5.0,  # 5초 이내
            'success_rate': 0.95,   # 95% 이상
            'availability': 0.999,  # 99.9% 이상
            'response_time': 1.0    # 1초 이내
        }
    
    async def collect_user_satisfaction(
        self, 
        user_id: str, 
        workflow_id: str, 
        execution_result: Dict[str, Any]
    ) -> float:
        """사용자 만족도 수집 및 계산"""
        
        # 실행 결과 기반 만족도 계산
        base_score = 8.0 if execution_result.get('success', False) else 3.0
        
        # 실행 시간에 따른 조정
        execution_time = execution_result.get('execution_time', 0)
        if execution_time < 2.0:
            time_bonus = 1.0
        elif execution_time < 5.0:
            time_bonus = 0.5
        elif execution_time < 10.0:
            time_bonus = 0.0
        else:
            time_bonus = -1.0
        
        # 에러 발생에 따른 조정
        error_penalty = -2.0 if execution_result.get('error') else 0.0
        
        # 최종 만족도 점수 (0-10)
        satisfaction_score = max(0, min(10, base_score + time_bonus + error_penalty))
        
        # 메트릭 저장
        metric = UserSatisfactionMetric(
            user_id=user_id,
            workflow_id=workflow_id,
            satisfaction_score=satisfaction_score,
            execution_time=execution_time,
            success=execution_result.get('success', False)
        )
        
        self.user_satisfaction_scores.append(metric)
        
        # 이벤트 발행
        await self.event_bus.publish(
            EventType.BUSINESS_METRICS,
            {
                'metric_type': 'user_satisfaction',
                'user_id': user_id,
                'workflow_id': workflow_id,
                'satisfaction_score': satisfaction_score,
                'timestamp': metric.timestamp.isoformat()
            },
            source='business_metrics_collector'
        )
        
        return satisfaction_score
    
    async def calculate_business_value(
        self, 
        workflow_id: str, 
        workflow_outcomes: List[Dict[str, Any]]
    ) -> ROIMetric:
        """비즈니스 가치 계산"""
        
        total_time_saved = 0.0
        total_cost_saved = 0.0
        revenue_generated = 0.0
        
        for outcome in workflow_outcomes:
            # 시간 절약 계산 (자동화로 인한)
            manual_time = outcome.get('estimated_manual_time', 0)
            automated_time = outcome.get('execution_time', 0)
            time_saved = max(0, manual_time - automated_time)
            total_time_saved += time_saved
            
            # 비용 절약 계산 (시간당 비용 기준)
            hourly_cost = outcome.get('hourly_cost', 50.0)  # $50/hour 기본값
            cost_saved = (time_saved / 3600) * hourly_cost
            total_cost_saved += cost_saved
            
            # 수익 생성 계산
            revenue_generated += outcome.get('revenue_impact', 0.0)
        
        # 효율성 향상 계산
        if workflow_outcomes:
            avg_manual_time = sum(o.get('estimated_manual_time', 0) for o in workflow_outcomes) / len(workflow_outcomes)
            avg_automated_time = sum(o.get('execution_time', 0) for o in workflow_outcomes) / len(workflow_outcomes)
            efficiency_gain = ((avg_manual_time - avg_automated_time) / max(avg_manual_time, 1)) * 100
        else:
            efficiency_gain = 0.0
        
        roi_metric = ROIMetric(
            workflow_id=workflow_id,
            cost_saved=total_cost_saved,
            time_saved=total_time_saved,
            revenue_generated=revenue_generated,
            efficiency_gain=efficiency_gain
        )
        
        self.roi_metrics.append(roi_metric)
        
        # 이벤트 발행
        await self.event_bus.publish(
            EventType.BUSINESS_METRICS,
            {
                'metric_type': 'roi',
                'workflow_id': workflow_id,
                'cost_saved': total_cost_saved,
                'time_saved': total_time_saved,
                'revenue_generated': revenue_generated,
                'efficiency_gain': efficiency_gain,
                'timestamp': roi_metric.timestamp.isoformat()
            },
            source='business_metrics_collector'
        )
        
        return roi_metric
    
    async def calculate_sla_compliance(
        self, 
        service_name: str, 
        performance_data: Dict[str, Any]
    ) -> SLAMetric:
        """SLA 준수율 계산"""
        
        target_value = self.sla_targets.get(service_name, 0.0)
        actual_value = performance_data.get('actual_value', 0.0)
        
        # 준수율 계산
        if service_name in ['success_rate', 'availability']:
            # 높을수록 좋은 메트릭
            compliance_percentage = min(100, (actual_value / target_value) * 100)
        else:
            # 낮을수록 좋은 메트릭 (execution_time, response_time)
            compliance_percentage = min(100, (target_value / max(actual_value, 0.001)) * 100)
        
        # 위반 횟수 계산
        breach_count = 1 if compliance_percentage < 100 else 0
        
        sla_metric = SLAMetric(
            service_name=service_name,
            target_value=target_value,
            actual_value=actual_value,
            compliance_percentage=compliance_percentage,
            breach_count=breach_count
        )
        
        self.sla_metrics[service_name] = sla_metric
        
        # 이벤트 발행
        await self.event_bus.publish(
            EventType.SLA_METRICS,
            {
                'service_name': service_name,
                'target_value': target_value,
                'actual_value': actual_value,
                'compliance_percentage': compliance_percentage,
                'breach_count': breach_count,
                'timestamp': sla_metric.timestamp.isoformat()
            },
            source='business_metrics_collector'
        )
        
        return sla_metric
    
    def get_user_satisfaction_summary(self, hours: int = 24) -> Dict[str, Any]:
        """사용자 만족도 요약"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_scores = [
            metric.satisfaction_score 
            for metric in self.user_satisfaction_scores 
            if metric.timestamp >= cutoff_time
        ]
        
        if not recent_scores:
            return {'status': 'no_data'}
        
        return {
            'average_satisfaction': statistics.mean(recent_scores),
            'median_satisfaction': statistics.median(recent_scores),
            'total_responses': len(recent_scores),
            'satisfaction_distribution': {
                'excellent': len([s for s in recent_scores if s >= 8]),
                'good': len([s for s in recent_scores if 6 <= s < 8]),
                'fair': len([s for s in recent_scores if 4 <= s < 6]),
                'poor': len([s for s in recent_scores if s < 4])
            }
        }
    
    def get_roi_summary(self, days: int = 30) -> Dict[str, Any]:
        """ROI 요약"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        recent_roi = [
            metric for metric in self.roi_metrics 
            if metric.timestamp >= cutoff_time
        ]
        
        if not recent_roi:
            return {'status': 'no_data'}
        
        total_cost_saved = sum(roi.cost_saved for roi in recent_roi)
        total_time_saved = sum(roi.time_saved for roi in recent_roi)
        total_revenue = sum(roi.revenue_generated for roi in recent_roi)
        avg_efficiency = statistics.mean([roi.efficiency_gain for roi in recent_roi])
        
        return {
            'total_cost_saved': total_cost_saved,
            'total_time_saved_hours': total_time_saved / 3600,
            'total_revenue_generated': total_revenue,
            'average_efficiency_gain': avg_efficiency,
            'total_workflows': len(recent_roi),
            'roi_percentage': ((total_cost_saved + total_revenue) / max(total_cost_saved * 0.1, 1)) * 100
        }
    
    def get_sla_summary(self) -> Dict[str, Any]:
        """SLA 요약"""
        if not self.sla_metrics:
            return {'status': 'no_data'}
        
        overall_compliance = statistics.mean([
            sla.compliance_percentage for sla in self.sla_metrics.values()
        ])
        
        total_breaches = sum(sla.breach_count for sla in self.sla_metrics.values())
        
        return {
            'overall_compliance_percentage': overall_compliance,
            'total_breaches': total_breaches,
            'services_monitored': len(self.sla_metrics),
            'sla_details': {
                name: {
                    'compliance': sla.compliance_percentage,
                    'target': sla.target_value,
                    'actual': sla.actual_value,
                    'breaches': sla.breach_count
                }
                for name, sla in self.sla_metrics.items()
            }
        }


class PredictiveAnalyticsEngine:
    """예측 분석 엔진"""
    
    def __init__(self, performance_monitor: PluginPerformanceMonitor):
        self.performance_monitor = performance_monitor
        self.prediction_history: Dict[str, List] = defaultdict(list)
    
    async def predict_system_load(self, time_horizon_hours: int = 24) -> Dict[str, Any]:
        """시스템 부하 예측"""
        
        # 현재 성능 메트릭 수집
        current_metrics = self.performance_monitor.get_all_metrics_summary()
        
        # 간단한 선형 예측 (실제로는 더 복잡한 ML 모델 사용)
        predicted_load = {}
        
        for plugin_type, metrics in current_metrics.get('plugins', {}).items():
            current_executions = metrics.get('total_executions', 0)
            avg_execution_time = metrics.get('avg_execution_time', 1.0)
            
            # 시간대별 패턴 고려 (간단한 사인파 모델)
            import math
            hour_factor = 1 + 0.3 * math.sin((datetime.now().hour / 24) * 2 * math.pi)
            
            # 예측된 실행 횟수
            predicted_executions = current_executions * hour_factor * (time_horizon_hours / 24)
            predicted_cpu_load = predicted_executions * avg_execution_time * 0.1  # 추정
            
            predicted_load[plugin_type] = {
                'predicted_executions': int(predicted_executions),
                'predicted_cpu_load': predicted_cpu_load,
                'confidence': 0.7,  # 70% 신뢰도
                'recommendation': self._generate_load_recommendation(predicted_cpu_load)
            }
        
        return {
            'prediction_horizon_hours': time_horizon_hours,
            'predicted_load': predicted_load,
            'overall_system_load': sum(p['predicted_cpu_load'] for p in predicted_load.values()),
            'prediction_timestamp': datetime.now().isoformat()
        }
    
    def _generate_load_recommendation(self, predicted_load: float) -> str:
        """부하 예측에 따른 권장사항"""
        if predicted_load > 80:
            return "scale_up_recommended"
        elif predicted_load < 20:
            return "scale_down_possible"
        else:
            return "current_capacity_sufficient"
    
    async def detect_performance_anomalies(self) -> List[Dict[str, Any]]:
        """성능 이상 탐지"""
        anomalies = []
        
        # 모든 플러그인의 성능 메트릭 분석
        all_metrics = self.performance_monitor.get_all_metrics_summary()
        
        for plugin_type, metrics in all_metrics.get('plugins', {}).items():
            plugin_metrics = self.performance_monitor.get_plugin_metrics(plugin_type)
            
            # 기존 이상 탐지 결과 활용
            existing_anomalies = plugin_metrics.get('anomalies', [])
            
            for anomaly in existing_anomalies:
                anomalies.append({
                    'plugin_type': plugin_type,
                    'anomaly_type': anomaly['type'],
                    'severity': anomaly['severity'],
                    'description': anomaly.get('description', ''),
                    'timestamp': anomaly.get('timestamp'),
                    'recommendation': self._generate_anomaly_recommendation(anomaly)
                })
        
        return anomalies
    
    def _generate_anomaly_recommendation(self, anomaly: Dict[str, Any]) -> str:
        """이상 현상에 대한 권장사항"""
        anomaly_type = anomaly.get('type', '')
        severity = anomaly.get('severity', 'medium')
        
        if anomaly_type == 'execution_time_anomaly':
            if severity == 'high':
                return "investigate_performance_bottleneck"
            else:
                return "monitor_execution_patterns"
        elif anomaly_type == 'consecutive_failures':
            return "check_plugin_health_and_dependencies"
        else:
            return "general_monitoring_recommended"
    
    async def recommend_scaling_actions(self) -> List[Dict[str, Any]]:
        """스케일링 권장사항"""
        recommendations = []
        
        # 시스템 부하 예측
        load_prediction = await self.predict_system_load()
        
        for plugin_type, prediction in load_prediction['predicted_load'].items():
            recommendation_type = prediction['recommendation']
            
            if recommendation_type == "scale_up_recommended":
                recommendations.append({
                    'action': 'scale_up',
                    'plugin_type': plugin_type,
                    'priority': 'high',
                    'reason': 'High predicted load',
                    'predicted_load': prediction['predicted_cpu_load'],
                    'confidence': prediction['confidence']
                })
            elif recommendation_type == "scale_down_possible":
                recommendations.append({
                    'action': 'scale_down',
                    'plugin_type': plugin_type,
                    'priority': 'low',
                    'reason': 'Low predicted load',
                    'predicted_load': prediction['predicted_cpu_load'],
                    'confidence': prediction['confidence']
                })
        
        return recommendations


class AdvancedMetricsCollector:
    """고급 메트릭 수집기 통합 클래스"""
    
    def __init__(
        self, 
        event_bus: ValidatedEventBus,
        performance_monitor: PluginPerformanceMonitor
    ):
        self.event_bus = event_bus
        self.performance_monitor = performance_monitor
        self.business_metrics = BusinessMetricsCollector(event_bus)
        self.predictive_analytics = PredictiveAnalyticsEngine(performance_monitor)
        
        # 메트릭 수집 태스크
        self._collection_task: Optional[asyncio.Task] = None
        self._collection_interval = 60  # 1분마다
    
    async def start_collection(self):
        """메트릭 수집 시작"""
        if self._collection_task is None or self._collection_task.done():
            self._collection_task = asyncio.create_task(self._collection_loop())
            logger.info("Advanced metrics collection started")
    
    async def stop_collection(self):
        """메트릭 수집 중지"""
        if self._collection_task and not self._collection_task.done():
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
            logger.info("Advanced metrics collection stopped")
    
    async def _collection_loop(self):
        """메트릭 수집 루프"""
        while True:
            try:
                await self._collect_periodic_metrics()
                await asyncio.sleep(self._collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self._collection_interval)
    
    async def _collect_periodic_metrics(self):
        """주기적 메트릭 수집"""
        
        # 성능 메트릭 기반 SLA 계산
        performance_summary = self.performance_monitor.get_all_metrics_summary()
        
        for plugin_type, metrics in performance_summary.get('plugins', {}).items():
            # SLA 메트릭 계산
            await self.business_metrics.calculate_sla_compliance(
                'success_rate',
                {'actual_value': metrics.get('success_rate', 0.0)}
            )
            
            await self.business_metrics.calculate_sla_compliance(
                'execution_time',
                {'actual_value': metrics.get('avg_execution_time', 0.0)}
            )
        
        # 예측 분석 실행
        anomalies = await self.predictive_analytics.detect_performance_anomalies()
        if anomalies:
            await self.event_bus.publish(
                'performance_anomalies_detected',
                {'anomalies': anomalies},
                source='advanced_metrics_collector'
            )
    
    async def get_comprehensive_dashboard_data(self) -> Dict[str, Any]:
        """종합 대시보드 데이터"""
        
        # 기본 성능 메트릭
        performance_summary = self.performance_monitor.get_all_metrics_summary()
        
        # 비즈니스 메트릭
        user_satisfaction = self.business_metrics.get_user_satisfaction_summary()
        roi_summary = self.business_metrics.get_roi_summary()
        sla_summary = self.business_metrics.get_sla_summary()
        
        # 예측 분석
        load_prediction = await self.predictive_analytics.predict_system_load()
        anomalies = await self.predictive_analytics.detect_performance_anomalies()
        scaling_recommendations = await self.predictive_analytics.recommend_scaling_actions()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'performance_metrics': performance_summary,
            'business_metrics': {
                'user_satisfaction': user_satisfaction,
                'roi_summary': roi_summary,
                'sla_summary': sla_summary
            },
            'predictive_analytics': {
                'load_prediction': load_prediction,
                'anomalies': anomalies,
                'scaling_recommendations': scaling_recommendations
            },
            'system_health': {
                'overall_score': self._calculate_overall_health_score(
                    performance_summary, user_satisfaction, sla_summary
                ),
                'status': 'healthy'  # 실제로는 복합 계산
            }
        }
    
    def _calculate_overall_health_score(
        self, 
        performance: Dict[str, Any], 
        satisfaction: Dict[str, Any], 
        sla: Dict[str, Any]
    ) -> float:
        """전체 시스템 건강도 점수 계산"""
        
        scores = []
        
        # 성능 점수 (0-100)
        if performance.get('total_plugins', 0) > 0:
            avg_success_rate = sum(
                p.get('success_rate', 0) for p in performance.get('plugins', {}).values()
            ) / len(performance.get('plugins', {}))
            scores.append(avg_success_rate * 100)
        
        # 사용자 만족도 점수 (0-100)
        if satisfaction.get('average_satisfaction'):
            scores.append(satisfaction['average_satisfaction'] * 10)
        
        # SLA 준수 점수 (0-100)
        if sla.get('overall_compliance_percentage'):
            scores.append(sla['overall_compliance_percentage'])
        
        return statistics.mean(scores) if scores else 50.0