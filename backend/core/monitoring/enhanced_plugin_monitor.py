"""
강화된 Agent Plugin 성능 모니터링 시스템
상세한 성능 메트릭 수집 및 분석
"""
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import psutil
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

from backend.core.utils.circular_buffer import TimedCircularBuffer
from backend.core.dependencies import get_redis_client

logger = logging.getLogger(__name__)

@dataclass
class PluginMetrics:
    """플러그인 메트릭"""
    plugin_id: str
    timestamp: str
    
    # 실행 메트릭
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_execution_time: float = 0.0
    p95_execution_time: float = 0.0
    p99_execution_time: float = 0.0
    
    # 리소스 메트릭
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    memory_peak_mb: float = 0.0
    
    # 네트워크 메트릭
    network_requests: int = 0
    network_errors: int = 0
    avg_network_latency: float = 0.0
    
    # 캐시 메트릭
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0

@dataclass
class SystemMetrics:
    """시스템 전체 메트릭"""
    timestamp: str
    
    # 전체 시스템
    total_cpu_percent: float = 0.0
    total_memory_percent: float = 0.0
    total_disk_percent: float = 0.0
    
    # 플러그인 시스템
    active_plugins: int = 0
    total_executions: int = 0
    total_errors: int = 0
    system_health_score: float = 100.0

class EnhancedPluginMonitor:
    """강화된 플러그인 성능 모니터"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        
        # 메트릭 버퍼 (24시간 보관)
        self.plugin_metrics: Dict[str, TimedCircularBuffer] = {}
        self.system_metrics = TimedCircularBuffer(max_size=1440, max_age_seconds=86400)  # 24시간
        
        # 실시간 추적
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.execution_times: Dict[str, List[float]] = defaultdict(list)
        self.resource_usage: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # 모니터링 설정
        self.monitoring_interval = 60  # 1분
        self.detailed_monitoring_interval = 10  # 10초
        self.cleanup_interval = 3600  # 1시간
        
        self._monitoring_task = None
        self._detailed_task = None
        self._cleanup_task = None
    
    async def start_monitoring(self):
        """모니터링 시작"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._detailed_task = asyncio.create_task(self._detailed_monitoring_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Enhanced plugin monitoring started")
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
        
        if self._detailed_task:
            self._detailed_task.cancel()
            self._detailed_task = None
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        
        logger.info("Enhanced plugin monitoring stopped")
    
    async def _monitoring_loop(self):
        """메인 모니터링 루프"""
        while True:
            try:
                await self._collect_system_metrics()
                await self._collect_plugin_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _detailed_monitoring_loop(self):
        """상세 모니터링 루프"""
        while True:
            try:
                await self._collect_resource_metrics()
                await asyncio.sleep(self.detailed_monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Detailed monitoring loop error: {e}")
                await asyncio.sleep(self.detailed_monitoring_interval)
    
    async def _cleanup_loop(self):
        """정리 루프"""
        while True:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(self.cleanup_interval)
    
    async def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # CPU, 메모리, 디스크 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 플러그인 시스템 메트릭
            active_plugins = len(self.plugin_metrics)
            total_executions = sum(
                len(buffer.get_all()) for buffer in self.plugin_metrics.values()
            )
            
            # 건강 점수 계산
            health_score = self._calculate_health_score(
                cpu_percent, memory.percent, disk.percent
            )
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                total_cpu_percent=cpu_percent,
                total_memory_percent=memory.percent,
                total_disk_percent=disk.percent,
                active_plugins=active_plugins,
                total_executions=total_executions,
                system_health_score=health_score
            )
            
            self.system_metrics.add(asdict(metrics))
            
        except Exception as e:
            logger.error(f"System metrics collection error: {e}")
    
    async def _collect_plugin_metrics(self):
        """플러그인별 메트릭 수집"""
        for plugin_id in list(self.plugin_metrics.keys()):
            try:
                await self._collect_single_plugin_metrics(plugin_id)
            except Exception as e:
                logger.error(f"Plugin metrics collection error for {plugin_id}: {e}")
    
    async def _collect_single_plugin_metrics(self, plugin_id: str):
        """단일 플러그인 메트릭 수집"""
        if plugin_id not in self.plugin_metrics:
            self.plugin_metrics[plugin_id] = TimedCircularBuffer(
                max_size=1440, max_age_seconds=86400
            )
        
        # 실행 통계 계산
        execution_times = self.execution_times.get(plugin_id, [])
        execution_count = len(execution_times)
        
        avg_time = statistics.mean(execution_times) if execution_times else 0.0
        p95_time = (
            statistics.quantiles(execution_times, n=20)[18] 
            if len(execution_times) >= 20 else avg_time
        )
        p99_time = (
            statistics.quantiles(execution_times, n=100)[98] 
            if len(execution_times) >= 100 else p95_time
        )
        
        # 리소스 사용량
        resource_data = self.resource_usage.get(plugin_id, {})
        
        # 캐시 메트릭 (Redis에서 조회)
        cache_stats = await self._get_cache_stats(plugin_id)
        
        metrics = PluginMetrics(
            plugin_id=plugin_id,
            timestamp=datetime.now().isoformat(),
            execution_count=execution_count,
            avg_execution_time=avg_time,
            p95_execution_time=p95_time,
            p99_execution_time=p99_time,
            cpu_usage_percent=resource_data.get('cpu', 0.0),
            memory_usage_mb=resource_data.get('memory', 0.0),
            cache_hits=cache_stats.get('hits', 0),
            cache_misses=cache_stats.get('misses', 0),
            cache_hit_rate=cache_stats.get('hit_rate', 0.0)
        )
        
        self.plugin_metrics[plugin_id].add(asdict(metrics))
    
    async def _collect_resource_metrics(self):
        """리소스 메트릭 수집"""
        try:
            # 프로세스별 리소스 사용량 수집
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    if 'plugin' in proc_info['name'].lower():
                        # 플러그인 프로세스로 추정되는 경우
                        plugin_id = self._extract_plugin_id_from_process(proc_info['name'])
                        if plugin_id:
                            self.resource_usage[plugin_id] = {
                                'cpu': proc_info['cpu_percent'] or 0.0,
                                'memory': (proc_info['memory_info'].rss / 1024 / 1024) if proc_info['memory_info'] else 0.0,
                                'timestamp': time.time()
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Resource metrics collection error: {e}")
    
    def _extract_plugin_id_from_process(self, process_name: str) -> Optional[str]:
        """프로세스 이름에서 플러그인 ID 추출"""
        # 실제 구현에서는 프로세스 명명 규칙에 따라 구현
        return None
    
    async def _get_cache_stats(self, plugin_id: str) -> Dict[str, Any]:
        """플러그인별 캐시 통계 조회"""
        try:
            # Redis에서 캐시 통계 조회
            cache_key = f"plugin_cache_stats:{plugin_id}"
            stats_data = await self.redis_client.get(cache_key)
            
            if stats_data:
                return eval(stats_data)  # 실제로는 json.loads 사용
            
            return {'hits': 0, 'misses': 0, 'hit_rate': 0.0}
            
        except Exception as e:
            logger.error(f"Cache stats retrieval error: {e}")
            return {'hits': 0, 'misses': 0, 'hit_rate': 0.0}
    
    def _calculate_health_score(
        self, 
        cpu_percent: float, 
        memory_percent: float, 
        disk_percent: float
    ) -> float:
        """시스템 건강 점수 계산"""
        # 각 메트릭별 점수 계산 (0-100)
        cpu_score = max(0, 100 - cpu_percent)
        memory_score = max(0, 100 - memory_percent)
        disk_score = max(0, 100 - disk_percent)
        
        # 가중 평균 (CPU 40%, 메모리 40%, 디스크 20%)
        health_score = (cpu_score * 0.4 + memory_score * 0.4 + disk_score * 0.2)
        
        return round(health_score, 2)
    
    async def _cleanup_old_data(self):
        """오래된 데이터 정리"""
        try:
            # 실행 시간 데이터 정리 (최근 1000개만 유지)
            for plugin_id in list(self.execution_times.keys()):
                times = self.execution_times[plugin_id]
                if len(times) > 1000:
                    self.execution_times[plugin_id] = times[-1000:]
            
            # 리소스 사용량 데이터 정리 (1시간 이상 된 데이터 제거)
            cutoff_time = time.time() - 3600
            for plugin_id in list(self.resource_usage.keys()):
                resource_data = self.resource_usage[plugin_id]
                if resource_data.get('timestamp', 0) < cutoff_time:
                    del self.resource_usage[plugin_id]
            
        except Exception as e:
            logger.error(f"Data cleanup error: {e}")
    
    def record_execution_start(self, plugin_id: str, execution_id: str):
        """실행 시작 기록"""
        self.active_executions[execution_id] = {
            'plugin_id': plugin_id,
            'start_time': time.time(),
            'status': 'running'
        }
    
    def record_execution_end(
        self, 
        execution_id: str, 
        success: bool = True, 
        error: Optional[str] = None
    ):
        """실행 종료 기록"""
        if execution_id in self.active_executions:
            execution_data = self.active_executions[execution_id]
            plugin_id = execution_data['plugin_id']
            duration = time.time() - execution_data['start_time']
            
            # 실행 시간 기록
            self.execution_times[plugin_id].append(duration)
            
            # 활성 실행 목록에서 제거
            del self.active_executions[execution_id]
    
    async def get_plugin_performance_report(
        self, 
        plugin_id: str, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """플러그인 성능 리포트 생성"""
        if plugin_id not in self.plugin_metrics:
            return {}
        
        try:
            # 지정된 시간 범위의 메트릭 조회
            cutoff_time = datetime.now() - timedelta(hours=hours)
            metrics_data = [
                metric for metric in self.plugin_metrics[plugin_id].get_all()
                if datetime.fromisoformat(metric['timestamp']) > cutoff_time
            ]
            
            if not metrics_data:
                return {}
            
            # 통계 계산
            execution_counts = [m['execution_count'] for m in metrics_data]
            avg_times = [m['avg_execution_time'] for m in metrics_data if m['avg_execution_time'] > 0]
            cpu_usages = [m['cpu_usage_percent'] for m in metrics_data if m['cpu_usage_percent'] > 0]
            memory_usages = [m['memory_usage_mb'] for m in metrics_data if m['memory_usage_mb'] > 0]
            
            return {
                'plugin_id': plugin_id,
                'time_range_hours': hours,
                'total_executions': sum(execution_counts),
                'avg_execution_time': statistics.mean(avg_times) if avg_times else 0,
                'max_execution_time': max(avg_times) if avg_times else 0,
                'avg_cpu_usage': statistics.mean(cpu_usages) if cpu_usages else 0,
                'peak_cpu_usage': max(cpu_usages) if cpu_usages else 0,
                'avg_memory_usage': statistics.mean(memory_usages) if memory_usages else 0,
                'peak_memory_usage': max(memory_usages) if memory_usages else 0,
                'data_points': len(metrics_data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance report generation error: {e}")
            return {}
    
    async def get_system_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """시스템 성능 리포트 생성"""
        try:
            # 지정된 시간 범위의 시스템 메트릭 조회
            cutoff_time = datetime.now() - timedelta(hours=hours)
            system_data = [
                metric for metric in self.system_metrics.get_all()
                if datetime.fromisoformat(metric['timestamp']) > cutoff_time
            ]
            
            if not system_data:
                return {}
            
            # 통계 계산
            cpu_usages = [m['total_cpu_percent'] for m in system_data]
            memory_usages = [m['total_memory_percent'] for m in system_data]
            health_scores = [m['system_health_score'] for m in system_data]
            
            return {
                'time_range_hours': hours,
                'avg_cpu_usage': statistics.mean(cpu_usages),
                'peak_cpu_usage': max(cpu_usages),
                'avg_memory_usage': statistics.mean(memory_usages),
                'peak_memory_usage': max(memory_usages),
                'avg_health_score': statistics.mean(health_scores),
                'min_health_score': min(health_scores),
                'active_plugins': system_data[-1]['active_plugins'] if system_data else 0,
                'total_executions': system_data[-1]['total_executions'] if system_data else 0,
                'data_points': len(system_data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System performance report generation error: {e}")
            return {}
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """실시간 메트릭 조회"""
        try:
            # 현재 시스템 상태
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # 활성 실행 수
            active_executions = len(self.active_executions)
            
            # 최근 메트릭
            latest_system = self.system_metrics.get_latest(1)
            latest_system_data = latest_system[0] if latest_system else {}
            
            return {
                'current_cpu_percent': cpu_percent,
                'current_memory_percent': memory.percent,
                'active_executions': active_executions,
                'active_plugins': len(self.plugin_metrics),
                'system_health_score': latest_system_data.get('system_health_score', 100.0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Real-time metrics error: {e}")
            return {}

# 전역 인스턴스
enhanced_plugin_monitor = EnhancedPluginMonitor()