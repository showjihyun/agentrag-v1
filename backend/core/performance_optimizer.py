"""
Performance Optimizer
실시간 업데이트 및 애니메이션 성능 최적화
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from dataclasses import dataclass, field
import weakref

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    request_count: int = 0
    total_response_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    active_connections: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

@dataclass
class CacheEntry:
    """캐시 엔트리"""
    data: Any
    timestamp: datetime
    ttl: int  # seconds
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

class PerformanceOptimizer:
    """성능 최적화 관리자"""
    
    def __init__(self):
        # 성능 메트릭
        self.metrics = PerformanceMetrics()
        
        # 실시간 캐시 (L1 - 메모리)
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_config = {
            "max_size": 1000,
            "default_ttl": 300,  # 5분
            "cleanup_interval": 60,  # 1분
            "hit_rate_threshold": 0.6
        }
        
        # 연결 풀링
        self.connection_pools: Dict[str, Any] = {}
        
        # 요청 배칭
        self.batch_queues: Dict[str, deque] = defaultdict(deque)
        self.batch_config = {
            "max_batch_size": 50,
            "batch_timeout": 100,  # 100ms
            "enabled_endpoints": [
                "/api/agent-builder/agent-olympics/competitions/*/progress",
                "/api/agent-builder/emotional-ai/users/*/emotion",
                "/api/agent-builder/workflow-dna/experiments/*/population"
            ]
        }
        
        # 응답 압축
        self.compression_config = {
            "enabled": True,
            "min_size": 1024,  # 1KB
            "compression_level": 6
        }
        
        # 실시간 업데이트 최적화
        self.websocket_connections: Dict[str, weakref.WeakSet] = defaultdict(weakref.WeakSet)
        self.update_throttling = {
            "max_updates_per_second": 10,
            "update_queues": defaultdict(deque),
            "last_update_times": defaultdict(float)
        }
        
        # 백그라운드 작업 시작 플래그
        self._background_tasks_started = False
        
        logger.info("Performance Optimizer initialized")
    
    async def _ensure_background_tasks_started(self):
        """백그라운드 작업이 시작되었는지 확인하고 필요시 시작"""
        if not self._background_tasks_started:
            await self._start_background_tasks()
            self._background_tasks_started = True
    
    async def _start_background_tasks(self):
        """백그라운드 작업 시작"""
        # 캐시 정리
        asyncio.create_task(self._cache_cleanup_loop())
        # 메트릭 수집
        asyncio.create_task(self._metrics_collection_loop())
        # 배치 처리
        asyncio.create_task(self._batch_processing_loop())
    
    async def _cache_cleanup_loop(self):
        """캐시 정리 루프"""
        while True:
            try:
                await self._cleanup_expired_cache()
                await asyncio.sleep(self.cache_config["cleanup_interval"])
            except Exception as e:
                logger.error(f"Cache cleanup failed: {str(e)}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _cleanup_expired_cache(self):
        """만료된 캐시 정리"""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            if (now - entry.timestamp).total_seconds() > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # 캐시 크기 제한
        if len(self.memory_cache) > self.cache_config["max_size"]:
            # LRU 방식으로 제거
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            remove_count = len(self.memory_cache) - self.cache_config["max_size"]
            for i in range(remove_count):
                key = sorted_entries[i][0]
                del self.memory_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _metrics_collection_loop(self):
        """메트릭 수집 루프"""
        while True:
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(30)  # 30초마다 수집
            except Exception as e:
                logger.error(f"Metrics collection failed: {str(e)}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _collect_performance_metrics(self):
        """성능 메트릭 수집"""
        try:
            import psutil
            
            # CPU 및 메모리 사용률
            self.metrics.cpu_usage = psutil.cpu_percent(interval=1)
            self.metrics.memory_usage = psutil.virtual_memory().percent
            
            # 캐시 히트율 계산
            total_requests = self.metrics.cache_hits + self.metrics.cache_misses
            hit_rate = self.metrics.cache_hits / total_requests if total_requests > 0 else 0
            
            # 성능 경고
            if hit_rate < self.cache_config["hit_rate_threshold"]:
                logger.warning(f"Low cache hit rate: {hit_rate:.2f}")
            
            if self.metrics.cpu_usage > 80:
                logger.warning(f"High CPU usage: {self.metrics.cpu_usage:.1f}%")
            
            if self.metrics.memory_usage > 85:
                logger.warning(f"High memory usage: {self.metrics.memory_usage:.1f}%")
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
    
    async def _batch_processing_loop(self):
        """배치 처리 루프"""
        while True:
            try:
                await self._process_batched_requests()
                await asyncio.sleep(self.batch_config["batch_timeout"] / 1000)
            except Exception as e:
                logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_batched_requests(self):
        """배치된 요청 처리"""
        for endpoint, queue in self.batch_queues.items():
            if len(queue) >= self.batch_config["max_batch_size"] or \
               (queue and time.time() - queue[0]["timestamp"] > self.batch_config["batch_timeout"] / 1000):
                
                # 배치 처리
                batch = []
                while queue and len(batch) < self.batch_config["max_batch_size"]:
                    batch.append(queue.popleft())
                
                if batch:
                    await self._execute_batch(endpoint, batch)
    
    async def _execute_batch(self, endpoint: str, batch: List[Dict[str, Any]]):
        """배치 실행"""
        try:
            # 실제 배치 처리 로직은 엔드포인트별로 구현
            logger.debug(f"Processing batch for {endpoint}: {len(batch)} requests")
            
            # 예시: 올림픽 진행률 배치 업데이트
            if "agent-olympics" in endpoint and "progress" in endpoint:
                await self._batch_olympics_progress_update(batch)
            
        except Exception as e:
            logger.error(f"Batch execution failed for {endpoint}: {str(e)}")
    
    async def _batch_olympics_progress_update(self, batch: List[Dict[str, Any]]):
        """올림픽 진행률 배치 업데이트"""
        try:
            from backend.services.olympics.agent_olympics_manager import get_olympics_manager
            
            olympics_manager = get_olympics_manager()
            
            # 경쟁 ID별로 그룹화
            competition_groups = defaultdict(list)
            for request in batch:
                comp_id = request.get("competition_id")
                if comp_id:
                    competition_groups[comp_id].append(request)
            
            # 각 경쟁별로 한 번만 업데이트
            for comp_id, requests in competition_groups.items():
                progress = await olympics_manager.get_live_progress(comp_id)
                
                # 모든 요청에 같은 결과 반환
                for request in requests:
                    callback = request.get("callback")
                    if callback:
                        await callback(progress)
            
        except Exception as e:
            logger.error(f"Olympics progress batch update failed: {str(e)}")
    
    # Public API Methods
    
    def get_cache(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        entry = self.memory_cache.get(key)
        if entry:
            # TTL 확인
            if (datetime.now() - entry.timestamp).total_seconds() <= entry.ttl:
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self.metrics.cache_hits += 1
                return entry.data
            else:
                # 만료된 엔트리 제거
                del self.memory_cache[key]
        
        self.metrics.cache_misses += 1
        return None
    
    def set_cache(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """캐시에 데이터 저장"""
        if ttl is None:
            ttl = self.cache_config["default_ttl"]
        
        entry = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            ttl=ttl
        )
        
        self.memory_cache[key] = entry
    
    def invalidate_cache(self, pattern: str) -> int:
        """패턴에 맞는 캐시 무효화"""
        invalidated = 0
        keys_to_remove = []
        
        for key in self.memory_cache.keys():
            if pattern in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.memory_cache[key]
            invalidated += 1
        
        return invalidated
    
    async def optimize_response(self, data: Any, compress: bool = True) -> Any:
        """응답 최적화"""
        try:
            # 백그라운드 작업 시작 확인
            await self._ensure_background_tasks_started()
            
            # JSON 직렬화 최적화
            if isinstance(data, dict) or isinstance(data, list):
                # 불필요한 필드 제거
                optimized_data = self._remove_unnecessary_fields(data)
                
                # 압축 적용
                if compress and self.compression_config["enabled"]:
                    serialized = json.dumps(optimized_data, separators=(',', ':'))
                    if len(serialized) >= self.compression_config["min_size"]:
                        # 실제 압축은 FastAPI의 GZip 미들웨어에서 처리
                        return optimized_data
                
                return optimized_data
            
            return data
            
        except Exception as e:
            logger.error(f"Response optimization failed: {str(e)}")
            return data
    
    def _remove_unnecessary_fields(self, data: Any) -> Any:
        """불필요한 필드 제거"""
        if isinstance(data, dict):
            # 큰 데이터에서 불필요한 필드 제거
            optimized = {}
            for key, value in data.items():
                # 디버그 정보나 내부 필드 제거
                if not key.startswith('_') and key not in ['debug_info', 'internal_state']:
                    optimized[key] = self._remove_unnecessary_fields(value)
            return optimized
        elif isinstance(data, list):
            return [self._remove_unnecessary_fields(item) for item in data]
        else:
            return data
    
    async def throttle_updates(self, channel: str, update_func: Callable, *args, **kwargs) -> bool:
        """업데이트 스로틀링"""
        now = time.time()
        last_update = self.update_throttling["last_update_times"].get(channel, 0)
        
        min_interval = 1.0 / self.update_throttling["max_updates_per_second"]
        
        if now - last_update >= min_interval:
            self.update_throttling["last_update_times"][channel] = now
            await update_func(*args, **kwargs)
            return True
        else:
            # 큐에 추가하여 나중에 처리
            self.update_throttling["update_queues"][channel].append({
                "func": update_func,
                "args": args,
                "kwargs": kwargs,
                "timestamp": now
            })
            return False
    
    def add_batch_request(self, endpoint: str, request_data: Dict[str, Any]) -> None:
        """배치 요청 추가"""
        if any(pattern in endpoint for pattern in self.batch_config["enabled_endpoints"]):
            request_data["timestamp"] = time.time()
            self.batch_queues[endpoint].append(request_data)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        total_requests = self.metrics.cache_hits + self.metrics.cache_misses
        hit_rate = self.metrics.cache_hits / total_requests if total_requests > 0 else 0
        
        avg_response_time = (
            self.metrics.total_response_time / self.metrics.request_count
            if self.metrics.request_count > 0 else 0
        )
        
        return {
            "cache_hit_rate": hit_rate,
            "cache_size": len(self.memory_cache),
            "average_response_time": avg_response_time,
            "active_connections": self.metrics.active_connections,
            "cpu_usage": self.metrics.cpu_usage,
            "memory_usage": self.metrics.memory_usage,
            "total_requests": total_requests,
            "batch_queues": {k: len(v) for k, v in self.batch_queues.items()}
        }
    
    async def preload_cache(self, preload_config: Dict[str, Any]) -> None:
        """캐시 사전 로드"""
        try:
            # 자주 사용되는 데이터 사전 로드
            if "olympics_leaderboard" in preload_config:
                from backend.services.olympics.agent_olympics_manager import get_olympics_manager
                olympics_manager = get_olympics_manager()
                leaderboard = await olympics_manager.get_leaderboard()
                self.set_cache("olympics:leaderboard", leaderboard, ttl=60)
            
            if "emotional_ai_themes" in preload_config:
                themes = {
                    "warm": {"primary_color": "#f59e0b", "background": "gradient-to-br from-orange-50 to-yellow-50"},
                    "cool": {"primary_color": "#06b6d4", "background": "gradient-to-br from-blue-50 to-green-50"},
                    "minimal": {"primary_color": "#6b7280", "background": "white"},
                    "soothing": {"primary_color": "#8b5cf6", "background": "gradient-to-br from-purple-50 to-pink-50"},
                    "vibrant": {"primary_color": "#ef4444", "background": "gradient-to-br from-red-50 to-orange-50"}
                }
                self.set_cache("emotional_ai:themes", themes, ttl=3600)  # 1시간
            
            logger.info("Cache preloading completed")
            
        except Exception as e:
            logger.error(f"Cache preloading failed: {str(e)}", exc_info=True)

# 싱글톤 인스턴스
_performance_optimizer = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """Performance Optimizer 싱글톤 인스턴스 반환"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer