"""
Real-time Performance Monitoring System
실시간 성능 모니터링 시스템
"""

import asyncio
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum
import json
import threading
from contextlib import asynccontextmanager

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """메트릭 타입"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """메트릭 데이터 포인트"""
    timestamp: float
    value: float
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class SystemMetrics:
    """시스템 메트릭"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: List[float]


@dataclass
class OrchestrationMetrics:
    """오케스트레이션 메트릭"""
    timestamp: float
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    current_active_executions: int
    cache_hit_rate: float
    security_validations: int
    pattern_usage: Dict[str, int]


@dataclass
class Alert:
    """알림"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: float
    metric_name: str
    current_value: float
    threshold_value: float
    resolved: bool = False
    resolved_at: Optional[float] = None


class MetricCollector:
    """메트릭 수집기"""
    
    def __init__(self, max_points: int = 1000):
        self.metrics: Dict[str, deque] = {}
        self.max_points = max_points
        self._lock = threading.Lock()
    
    def record(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """메트릭 기록"""
        with self._lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = deque(maxlen=self.max_points)
            
            point = MetricPoint(
                timestamp=time.time(),
                value=value,
                labels=labels or {}
            )
            self.metrics[metric_name].append(point)
    
    def get_metric(self, metric_name: str, since: Optional[float] = None) -> List[MetricPoint]:
        """메트릭 조회"""
        with self._lock:
            if metric_name not in self.metrics:
                return []
            
            points = list(self.metrics[metric_name])
            
            if since is not None:
                points = [p for p in points if p.timestamp >= since]
            
            return points
    
    def get_latest(self, metric_name: str) -> Optional[MetricPoint]:
        """최신 메트릭 조회"""
        with self._lock:
            if metric_name not in self.metrics or not self.metrics[metric_name]:
                return None
            return self.metrics[metric_name][-1]
    
    def get_average(self, metric_name: str, duration_seconds: int = 300) -> Optional[float]:
        """평균값 계산"""
        since = time.time() - duration_seconds
        points = self.get_metric(metric_name, since)
        
        if not points:
            return None
        
        return sum(p.value for p in points) / len(points)
    
    def clear_old_metrics(self, older_than_hours: int = 24):
        """오래된 메트릭 정리"""
        cutoff_time = time.time() - (older_than_hours * 3600)
        
        with self._lock:
            for metric_name in self.metrics:
                # deque는 자동으로 maxlen으로 제한되므로 추가 정리 불필요
                pass


class SystemMonitor:
    """시스템 모니터"""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self.process = psutil.Process(os.getpid())
        self._monitoring = False
        self._monitor_task = None
    
    async def start_monitoring(self, interval_seconds: int = 10):
        """모니터링 시작"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        logger.info("System monitoring started")
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("System monitoring stopped")
    
    async def _monitor_loop(self, interval_seconds: int):
        """모니터링 루프"""
        while self._monitoring:
            try:
                metrics = self._collect_system_metrics()
                self._record_system_metrics(metrics)
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(interval_seconds)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """시스템 메트릭 수집"""
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 정보
        memory = psutil.virtual_memory()
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        
        # 네트워크 정보
        network = psutil.net_io_counters()
        
        # 프로세스 수
        process_count = len(psutil.pids())
        
        # 로드 평균 (Unix 시스템에서만)
        try:
            load_avg = list(psutil.getloadavg())
        except AttributeError:
            load_avg = [0.0, 0.0, 0.0]  # Windows에서는 지원하지 않음
        
        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            disk_usage_percent=disk.percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            process_count=process_count,
            load_average=load_avg
        )
    
    def _record_system_metrics(self, metrics: SystemMetrics):
        """시스템 메트릭 기록"""
        self.collector.record("system.cpu_percent", metrics.cpu_percent)
        self.collector.record("system.memory_percent", metrics.memory_percent)
        self.collector.record("system.memory_used_mb", metrics.memory_used_mb)
        self.collector.record("system.disk_usage_percent", metrics.disk_usage_percent)
        self.collector.record("system.process_count", metrics.process_count)
        
        if metrics.load_average:
            self.collector.record("system.load_1m", metrics.load_average[0])
            self.collector.record("system.load_5m", metrics.load_average[1])
            self.collector.record("system.load_15m", metrics.load_average[2])


class OrchestrationMonitor:
    """오케스트레이션 모니터"""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.active_executions = 0
        self.execution_times = deque(maxlen=100)
        self.pattern_usage = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.security_validations = 0
    
    def record_execution_start(self, pattern_type: str, execution_id: str):
        """실행 시작 기록"""
        self.execution_count += 1
        self.active_executions += 1
        self.pattern_usage[pattern_type] = self.pattern_usage.get(pattern_type, 0) + 1
        
        self.collector.record("orchestration.total_executions", self.execution_count)
        self.collector.record("orchestration.active_executions", self.active_executions)
        self.collector.record(f"orchestration.pattern_usage.{pattern_type}", self.pattern_usage[pattern_type])
        
        logger.info(f"Orchestration execution started: {execution_id} ({pattern_type})")
    
    def record_execution_end(self, execution_id: str, success: bool, execution_time: float):
        """실행 종료 기록"""
        self.active_executions = max(0, self.active_executions - 1)
        self.execution_times.append(execution_time)
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # 평균 실행 시간 계산
        avg_time = sum(self.execution_times) / len(self.execution_times)
        success_rate = self.success_count / self.execution_count if self.execution_count > 0 else 0
        
        self.collector.record("orchestration.active_executions", self.active_executions)
        self.collector.record("orchestration.successful_executions", self.success_count)
        self.collector.record("orchestration.failed_executions", self.failure_count)
        self.collector.record("orchestration.average_execution_time", avg_time)
        self.collector.record("orchestration.success_rate", success_rate)
        self.collector.record("orchestration.execution_time", execution_time)
        
        status = "success" if success else "failure"
        logger.info(f"Orchestration execution ended: {execution_id} ({status}, {execution_time:.2f}s)")
    
    def record_cache_hit(self):
        """캐시 히트 기록"""
        self.cache_hits += 1
        self._update_cache_metrics()
    
    def record_cache_miss(self):
        """캐시 미스 기록"""
        self.cache_misses += 1
        self._update_cache_metrics()
    
    def _update_cache_metrics(self):
        """캐시 메트릭 업데이트"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        self.collector.record("orchestration.cache_hit_rate", hit_rate)
        self.collector.record("orchestration.cache_hits", self.cache_hits)
        self.collector.record("orchestration.cache_misses", self.cache_misses)
    
    def record_security_validation(self):
        """보안 검증 기록"""
        self.security_validations += 1
        self.collector.record("orchestration.security_validations", self.security_validations)
    
    def get_current_metrics(self) -> OrchestrationMetrics:
        """현재 메트릭 조회"""
        avg_time = sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_cache_requests if total_cache_requests > 0 else 0
        
        return OrchestrationMetrics(
            timestamp=time.time(),
            total_executions=self.execution_count,
            successful_executions=self.success_count,
            failed_executions=self.failure_count,
            average_execution_time=avg_time,
            current_active_executions=self.active_executions,
            cache_hit_rate=cache_hit_rate,
            security_validations=self.security_validations,
            pattern_usage=self.pattern_usage.copy()
        )


class AlertManager:
    """알림 관리자"""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self.alerts: Dict[str, Alert] = {}
        self.thresholds: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self._monitoring = False
        self._monitor_task = None
    
    def add_threshold(self, metric_name: str, threshold_value: float, 
                     comparison: str = "greater", level: AlertLevel = AlertLevel.WARNING,
                     title: str = None, message_template: str = None):
        """임계값 추가"""
        self.thresholds[metric_name] = {
            "threshold_value": threshold_value,
            "comparison": comparison,  # "greater", "less", "equal"
            "level": level,
            "title": title or f"{metric_name} threshold exceeded",
            "message_template": message_template or f"{metric_name} is {{current_value}}, threshold is {{threshold_value}}"
        }
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """알림 콜백 추가"""
        self.alert_callbacks.append(callback)
    
    async def start_monitoring(self, check_interval_seconds: int = 30):
        """알림 모니터링 시작"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(check_interval_seconds))
        logger.info("Alert monitoring started")
    
    async def stop_monitoring(self):
        """알림 모니터링 중지"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Alert monitoring stopped")
    
    async def _monitor_loop(self, check_interval_seconds: int):
        """알림 모니터링 루프"""
        while self._monitoring:
            try:
                self._check_thresholds()
                await asyncio.sleep(check_interval_seconds)
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                await asyncio.sleep(check_interval_seconds)
    
    def _check_thresholds(self):
        """임계값 확인"""
        for metric_name, threshold_config in self.thresholds.items():
            latest_point = self.collector.get_latest(metric_name)
            
            if latest_point is None:
                continue
            
            current_value = latest_point.value
            threshold_value = threshold_config["threshold_value"]
            comparison = threshold_config["comparison"]
            
            # 임계값 비교
            threshold_exceeded = False
            if comparison == "greater" and current_value > threshold_value:
                threshold_exceeded = True
            elif comparison == "less" and current_value < threshold_value:
                threshold_exceeded = True
            elif comparison == "equal" and abs(current_value - threshold_value) < 0.001:
                threshold_exceeded = True
            
            alert_id = f"{metric_name}_threshold"
            
            if threshold_exceeded:
                # 새로운 알림 또는 기존 알림 업데이트
                if alert_id not in self.alerts or self.alerts[alert_id].resolved:
                    alert = Alert(
                        id=alert_id,
                        level=threshold_config["level"],
                        title=threshold_config["title"],
                        message=threshold_config["message_template"].format(
                            current_value=current_value,
                            threshold_value=threshold_value
                        ),
                        timestamp=time.time(),
                        metric_name=metric_name,
                        current_value=current_value,
                        threshold_value=threshold_value
                    )
                    
                    self.alerts[alert_id] = alert
                    self._trigger_alert(alert)
            else:
                # 알림 해결
                if alert_id in self.alerts and not self.alerts[alert_id].resolved:
                    self.alerts[alert_id].resolved = True
                    self.alerts[alert_id].resolved_at = time.time()
                    logger.info(f"Alert resolved: {alert_id}")
    
    def _trigger_alert(self, alert: Alert):
        """알림 발생"""
        logger.warning(f"Alert triggered: {alert.title} - {alert.message}")
        
        # 콜백 실행
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """활성 알림 조회"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_all_alerts(self, since: Optional[float] = None) -> List[Alert]:
        """모든 알림 조회"""
        alerts = list(self.alerts.values())
        
        if since is not None:
            alerts = [alert for alert in alerts if alert.timestamp >= since]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)


class PerformanceMonitor:
    """통합 성능 모니터"""
    
    def __init__(self):
        self.collector = MetricCollector()
        self.system_monitor = SystemMonitor(self.collector)
        self.orchestration_monitor = OrchestrationMonitor(self.collector)
        self.alert_manager = AlertManager(self.collector)
        
        # 기본 임계값 설정
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """기본 임계값 설정"""
        # 시스템 메트릭 임계값
        self.alert_manager.add_threshold(
            "system.cpu_percent", 80.0, "greater", AlertLevel.WARNING,
            "High CPU Usage", "CPU usage is {current_value:.1f}%, threshold is {threshold_value}%"
        )
        
        self.alert_manager.add_threshold(
            "system.memory_percent", 85.0, "greater", AlertLevel.WARNING,
            "High Memory Usage", "Memory usage is {current_value:.1f}%, threshold is {threshold_value}%"
        )
        
        self.alert_manager.add_threshold(
            "system.disk_usage_percent", 90.0, "greater", AlertLevel.ERROR,
            "High Disk Usage", "Disk usage is {current_value:.1f}%, threshold is {threshold_value}%"
        )
        
        # 오케스트레이션 메트릭 임계값
        self.alert_manager.add_threshold(
            "orchestration.success_rate", 0.8, "less", AlertLevel.ERROR,
            "Low Success Rate", "Success rate is {current_value:.2%}, threshold is {threshold_value:.2%}"
        )
        
        self.alert_manager.add_threshold(
            "orchestration.average_execution_time", 10.0, "greater", AlertLevel.WARNING,
            "High Execution Time", "Average execution time is {current_value:.2f}s, threshold is {threshold_value}s"
        )
        
        self.alert_manager.add_threshold(
            "orchestration.cache_hit_rate", 0.5, "less", AlertLevel.WARNING,
            "Low Cache Hit Rate", "Cache hit rate is {current_value:.2%}, threshold is {threshold_value:.2%}"
        )
    
    async def start(self, system_interval: int = 10, alert_interval: int = 30):
        """모니터링 시작"""
        await self.system_monitor.start_monitoring(system_interval)
        await self.alert_manager.start_monitoring(alert_interval)
        logger.info("Performance monitoring started")
    
    async def stop(self):
        """모니터링 중지"""
        await self.system_monitor.stop_monitoring()
        await self.alert_manager.stop_monitoring()
        logger.info("Performance monitoring stopped")
    
    def get_dashboard_data(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """대시보드 데이터 조회"""
        since = time.time() - (duration_minutes * 60)
        
        # 시스템 메트릭
        system_metrics = {
            "cpu_percent": [asdict(p) for p in self.collector.get_metric("system.cpu_percent", since)],
            "memory_percent": [asdict(p) for p in self.collector.get_metric("system.memory_percent", since)],
            "disk_usage_percent": [asdict(p) for p in self.collector.get_metric("system.disk_usage_percent", since)],
        }
        
        # 오케스트레이션 메트릭
        orchestration_metrics = {
            "total_executions": [asdict(p) for p in self.collector.get_metric("orchestration.total_executions", since)],
            "success_rate": [asdict(p) for p in self.collector.get_metric("orchestration.success_rate", since)],
            "average_execution_time": [asdict(p) for p in self.collector.get_metric("orchestration.average_execution_time", since)],
            "cache_hit_rate": [asdict(p) for p in self.collector.get_metric("orchestration.cache_hit_rate", since)],
        }
        
        # 현재 상태
        current_orchestration = self.orchestration_monitor.get_current_metrics()
        
        # 활성 알림
        active_alerts = [asdict(alert) for alert in self.alert_manager.get_active_alerts()]
        
        return {
            "timestamp": time.time(),
            "system_metrics": system_metrics,
            "orchestration_metrics": orchestration_metrics,
            "current_status": {
                "orchestration": asdict(current_orchestration),
                "system": {
                    "cpu_percent": self.collector.get_latest("system.cpu_percent").value if self.collector.get_latest("system.cpu_percent") else 0,
                    "memory_percent": self.collector.get_latest("system.memory_percent").value if self.collector.get_latest("system.memory_percent") else 0,
                    "active_executions": current_orchestration.current_active_executions
                }
            },
            "alerts": active_alerts
        }
    
    @asynccontextmanager
    async def execution_context(self, pattern_type: str, execution_id: str):
        """실행 컨텍스트 매니저"""
        start_time = time.time()
        self.orchestration_monitor.record_execution_start(pattern_type, execution_id)
        
        try:
            yield
            # 성공
            execution_time = time.time() - start_time
            self.orchestration_monitor.record_execution_end(execution_id, True, execution_time)
        except Exception as e:
            # 실패
            execution_time = time.time() - start_time
            self.orchestration_monitor.record_execution_end(execution_id, False, execution_time)
            raise


# 전역 성능 모니터 인스턴스
_performance_monitor_instance: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """성능 모니터 인스턴스 조회"""
    global _performance_monitor_instance
    
    if _performance_monitor_instance is None:
        _performance_monitor_instance = PerformanceMonitor()
    
    return _performance_monitor_instance


# 편의 함수들
def record_cache_hit():
    """캐시 히트 기록"""
    monitor = get_performance_monitor()
    monitor.orchestration_monitor.record_cache_hit()


def record_cache_miss():
    """캐시 미스 기록"""
    monitor = get_performance_monitor()
    monitor.orchestration_monitor.record_cache_miss()


def record_security_validation():
    """보안 검증 기록"""
    monitor = get_performance_monitor()
    monitor.orchestration_monitor.record_security_validation()


def execution_context(pattern_type: str, execution_id: str):
    """실행 컨텍스트 매니저"""
    monitor = get_performance_monitor()
    return monitor.execution_context(pattern_type, execution_id)