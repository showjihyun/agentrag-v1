"""
Plugin Performance Monitor

Plugin 성능 모니터링 및 분석 시스템
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncio
import time
import psutil
import logging
from contextlib import asynccontextmanager

from backend.services.plugins.agents.base_agent_plugin import IAgentPlugin
from backend.core.event_bus.validated_event_bus import ValidatedEventBus, EventType


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터"""
    timestamp: datetime
    execution_time: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None
    input_size: Optional[int] = None
    output_size: Optional[int] = None


@dataclass
class AggregatedMetrics:
    """집계된 성능 메트릭"""
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    avg_memory_usage: float = 0.0
    avg_cpu_usage: float = 0.0
    success_rate: float = 0.0
    throughput: float = 0.0  # executions per second
    error_types: Dict[str, int] = field(default_factory=dict)
    
    def update(self, metric: PerformanceMetric):
        """메트릭 업데이트"""
        self.total_executions += 1
        
        if metric.success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if metric.error_message:
                error_type = type(metric.error_message).__name__
                self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        
        # 실행 시간 통계
        self.avg_execution_time = (
            (self.avg_execution_time * (self.total_executions - 1) + metric.execution_time) 
            / self.total_executions
        )
        self.min_execution_time = min(self.min_execution_time, metric.execution_time)
        self.max_execution_time = max(self.max_execution_time, metric.execution_time)
        
        # 리소스 사용량 통계
        self.avg_memory_usage = (
            (self.avg_memory_usage * (self.total_executions - 1) + metric.memory_usage) 
            / self.total_executions
        )
        self.avg_cpu_usage = (
            (self.avg_cpu_usage * (self.total_executions - 1) + metric.cpu_usage) 
            / self.total_executions
        )
        
        # 성공률 계산
        self.success_rate = self.success_count / self.total_executions
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'total_executions': self.total_executions,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'avg_execution_time': round(self.avg_execution_time, 4),
            'min_execution_time': round(self.min_execution_time, 4) if self.min_execution_time != float('inf') else 0,
            'max_execution_time': round(self.max_execution_time, 4),
            'avg_memory_usage': round(self.avg_memory_usage, 2),
            'avg_cpu_usage': round(self.avg_cpu_usage, 2),
            'success_rate': round(self.success_rate, 4),
            'throughput': round(self.throughput, 2),
            'error_types': self.error_types
        }


class PerformanceAnalyzer:
    """성능 분석기"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
    
    def analyze_trends(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        if len(metrics) < 2:
            return {'trend': 'insufficient_data'}
        
        # 최근 메트릭들을 시간순으로 정렬
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        
        # 실행 시간 트렌드
        execution_times = [m.execution_time for m in sorted_metrics]
        time_trend = self._calculate_trend(execution_times)
        
        # 성공률 트렌드 (최근 10개 구간으로 나누어 분석)
        success_rates = self._calculate_success_rate_trend(sorted_metrics)
        
        # 메모리 사용량 트렌드
        memory_usage = [m.memory_usage for m in sorted_metrics]
        memory_trend = self._calculate_trend(memory_usage)
        
        return {
            'execution_time_trend': time_trend,
            'success_rate_trend': success_rates,
            'memory_usage_trend': memory_trend,
            'analysis_window': len(sorted_metrics),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """값들의 트렌드 계산"""
        if len(values) < 2:
            return {'direction': 'stable', 'change_rate': 0.0}
        
        # 선형 회귀를 통한 트렌드 계산 (간단한 버전)
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        # 트렌드 방향 결정
        if abs(slope) < 0.01:  # 임계값
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # 변화율 계산 (첫 번째 값 대비 마지막 값의 변화율)
        change_rate = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        
        return {
            'direction': direction,
            'slope': slope,
            'change_rate': round(change_rate, 2)
        }
    
    def _calculate_success_rate_trend(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """성공률 트렌드 계산"""
        if len(metrics) < 10:
            return {'trend': 'insufficient_data'}
        
        # 10개 구간으로 나누어 각 구간의 성공률 계산
        chunk_size = len(metrics) // 10
        success_rates = []
        
        for i in range(0, len(metrics), chunk_size):
            chunk = metrics[i:i + chunk_size]
            if chunk:
                success_count = sum(1 for m in chunk if m.success)
                success_rate = success_count / len(chunk)
                success_rates.append(success_rate)
        
        return self._calculate_trend(success_rates)
    
    def detect_anomalies(self, metrics: List[PerformanceMetric]) -> List[Dict[str, Any]]:
        """성능 이상 탐지"""
        if len(metrics) < 10:
            return []
        
        anomalies = []
        
        # 실행 시간 이상 탐지 (Z-score 기반)
        execution_times = [m.execution_time for m in metrics]
        mean_time = sum(execution_times) / len(execution_times)
        std_time = (sum((t - mean_time) ** 2 for t in execution_times) / len(execution_times)) ** 0.5
        
        for i, metric in enumerate(metrics):
            z_score = abs(metric.execution_time - mean_time) / std_time if std_time > 0 else 0
            
            if z_score > 2.5:  # 2.5 표준편차 이상
                anomalies.append({
                    'type': 'execution_time_anomaly',
                    'timestamp': metric.timestamp.isoformat(),
                    'value': metric.execution_time,
                    'z_score': round(z_score, 2),
                    'severity': 'high' if z_score > 3 else 'medium'
                })
        
        # 연속 실패 탐지
        consecutive_failures = 0
        for metric in metrics:
            if not metric.success:
                consecutive_failures += 1
            else:
                if consecutive_failures >= 3:
                    anomalies.append({
                        'type': 'consecutive_failures',
                        'timestamp': metric.timestamp.isoformat(),
                        'failure_count': consecutive_failures,
                        'severity': 'high' if consecutive_failures >= 5 else 'medium'
                    })
                consecutive_failures = 0
        
        return anomalies


class PluginPerformanceMonitor:
    """Plugin 성능 모니터"""
    
    def __init__(self, event_bus: ValidatedEventBus, retention_hours: int = 24):
        self.event_bus = event_bus
        self.retention_hours = retention_hours
        
        # 메트릭 저장소 (plugin_type -> metrics)
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._aggregated_metrics: Dict[str, AggregatedMetrics] = defaultdict(AggregatedMetrics)
        
        # 성능 분석기
        self.analyzer = PerformanceAnalyzer()
        
        # 모니터링 설정
        self._monitoring_enabled = True
        self._alert_thresholds = {
            'max_execution_time': 30.0,  # 30초
            'min_success_rate': 0.8,     # 80%
            'max_memory_usage': 500.0,   # 500MB
            'max_consecutive_failures': 5
        }
        
        # 정리 작업 태스크
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def enable_monitoring(self, enabled: bool = True):
        """모니터링 활성화/비활성화"""
        self._monitoring_enabled = enabled
        logger.info(f"Plugin performance monitoring {'enabled' if enabled else 'disabled'}")
    
    def set_alert_thresholds(self, thresholds: Dict[str, float]):
        """알림 임계값 설정"""
        self._alert_thresholds.update(thresholds)
        logger.info(f"Updated alert thresholds: {thresholds}")
    
    @asynccontextmanager
    async def monitor_execution(self, plugin: IAgentPlugin, function_name: str):
        """Plugin 실행 모니터링 컨텍스트 매니저"""
        if not self._monitoring_enabled:
            yield
            return
        
        plugin_type = plugin.get_agent_type()
        start_time = time.time()
        
        # 시작 시점 리소스 사용량
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        cpu_before = process.cpu_percent()
        
        success = False
        error_message = None
        
        try:
            yield
            success = True
            
        except Exception as e:
            error_message = str(e)
            raise
            
        finally:
            # 종료 시점 메트릭 수집
            end_time = time.time()
            execution_time = end_time - start_time
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = memory_after - memory_before
            
            # CPU 사용량 (간단한 측정)
            cpu_usage = process.cpu_percent()
            
            # 메트릭 생성
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                success=success,
                error_message=error_message
            )
            
            # 메트릭 저장
            await self._record_metric(plugin_type, metric)
    
    async def _record_metric(self, plugin_type: str, metric: PerformanceMetric):
        """메트릭 기록"""
        # 메트릭 저장
        self._metrics[plugin_type].append(metric)
        
        # 집계 메트릭 업데이트
        self._aggregated_metrics[plugin_type].update(metric)
        
        # 성능 메트릭 이벤트 발행
        await self.event_bus.publish(
            EventType.PERFORMANCE_METRICS,
            {
                'agent_type': plugin_type,
                'metrics': {
                    'execution_time': metric.execution_time,
                    'memory_usage': metric.memory_usage,
                    'cpu_usage': metric.cpu_usage,
                    'success': metric.success
                },
                'measurement_window': '1m',
                'timestamp': metric.timestamp
            },
            source='plugin_performance_monitor'
        )
        
        # 임계값 확인 및 알림
        await self._check_thresholds(plugin_type, metric)
    
    async def _check_thresholds(self, plugin_type: str, metric: PerformanceMetric):
        """임계값 확인 및 알림"""
        alerts = []
        
        # 실행 시간 임계값 확인
        if metric.execution_time > self._alert_thresholds['max_execution_time']:
            alerts.append({
                'type': 'execution_time_exceeded',
                'plugin_type': plugin_type,
                'value': metric.execution_time,
                'threshold': self._alert_thresholds['max_execution_time'],
                'severity': 'high'
            })
        
        # 메모리 사용량 임계값 확인
        if metric.memory_usage > self._alert_thresholds['max_memory_usage']:
            alerts.append({
                'type': 'memory_usage_exceeded',
                'plugin_type': plugin_type,
                'value': metric.memory_usage,
                'threshold': self._alert_thresholds['max_memory_usage'],
                'severity': 'medium'
            })
        
        # 성공률 임계값 확인
        aggregated = self._aggregated_metrics[plugin_type]
        if aggregated.success_rate < self._alert_thresholds['min_success_rate']:
            alerts.append({
                'type': 'success_rate_low',
                'plugin_type': plugin_type,
                'value': aggregated.success_rate,
                'threshold': self._alert_thresholds['min_success_rate'],
                'severity': 'high'
            })
        
        # 알림 발행
        for alert in alerts:
            await self.event_bus.publish(
                'performance_alert',
                alert,
                source='plugin_performance_monitor'
            )
    
    def get_plugin_metrics(self, plugin_type: str) -> Dict[str, Any]:
        """특정 Plugin의 성능 메트릭 조회"""
        if plugin_type not in self._metrics:
            return {'error': f'No metrics found for plugin: {plugin_type}'}
        
        metrics_list = list(self._metrics[plugin_type])
        aggregated = self._aggregated_metrics[plugin_type]
        
        # 트렌드 분석
        trends = self.analyzer.analyze_trends(metrics_list)
        
        # 이상 탐지
        anomalies = self.analyzer.detect_anomalies(metrics_list)
        
        return {
            'plugin_type': plugin_type,
            'aggregated_metrics': aggregated.to_dict(),
            'trends': trends,
            'anomalies': anomalies,
            'recent_metrics': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'execution_time': m.execution_time,
                    'memory_usage': m.memory_usage,
                    'success': m.success
                }
                for m in metrics_list[-10:]  # 최근 10개
            ],
            'metrics_count': len(metrics_list)
        }
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """전체 Plugin 성능 요약"""
        summary = {
            'total_plugins': len(self._aggregated_metrics),
            'monitoring_enabled': self._monitoring_enabled,
            'alert_thresholds': self._alert_thresholds,
            'plugins': {}
        }
        
        for plugin_type, aggregated in self._aggregated_metrics.items():
            summary['plugins'][plugin_type] = {
                'total_executions': aggregated.total_executions,
                'success_rate': aggregated.success_rate,
                'avg_execution_time': aggregated.avg_execution_time,
                'avg_memory_usage': aggregated.avg_memory_usage
            }
        
        return summary
    
    async def start_cleanup_task(self):
        """정리 작업 시작"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """정리 작업 중지"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """오래된 메트릭 정리 루프"""
        while True:
            try:
                await asyncio.sleep(3600)  # 1시간마다 실행
                await self._cleanup_old_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
    
    async def _cleanup_old_metrics(self):
        """오래된 메트릭 정리"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        for plugin_type, metrics in self._metrics.items():
            # 오래된 메트릭 제거
            while metrics and metrics[0].timestamp < cutoff_time:
                metrics.popleft()
        
        logger.info(f"Cleaned up metrics older than {self.retention_hours} hours")