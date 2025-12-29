"""
Knowledge Graph Cache Manager

다층 캐싱 시스템 with 지능형 캐시 무효화, 프리페칭, 압축
"""

import asyncio
import logging
import time
import pickle
import gzip
import json
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import hashlib
from concurrent.futures import ThreadPoolExecutor

import redis
from cachetools import TTLCache, LRUCache, LFUCache
import aioredis

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class CacheStrategy(Enum):
    """캐시 전략"""
    LRU = "lru"          # Least Recently Used
    LFU = "lfu"          # Least Frequently Used
    TTL = "ttl"          # Time To Live
    ADAPTIVE = "adaptive" # 적응형 (사용 패턴에 따라 자동 선택)


class CompressionType(Enum):
    """압축 타입"""
    NONE = "none"
    GZIP = "gzip"
    PICKLE = "pickle"
    JSON = "json"


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    key: str
    data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    compression: CompressionType = CompressionType.NONE
    ttl_seconds: Optional[int] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """캐시 통계"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    avg_access_time_ms: float = 0.0
    
    def hit_rate(self) -> float:
        return (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0.0
    
    def miss_rate(self) -> float:
        return (self.cache_misses / self.total_requests * 100) if self.total_requests > 0 else 0.0


class KGCacheManager:
    """지식 그래프 캐시 매니저"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        l1_cache_size: int = 1000,
        l2_cache_ttl: int = 3600,
        enable_compression: bool = True,
        compression_threshold: int = 1024,  # 1KB 이상일 때 압축
        enable_prefetching: bool = True,
        max_workers: int = 4
    ):
        self.redis_url = redis_url
        self.l1_cache_size = l1_cache_size
        self.l2_cache_ttl = l2_cache_ttl
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self.enable_prefetching = enable_prefetching
        
        # L1 캐시 (메모리) - 적응형 전략
        self.l1_cache = LRUCache(maxsize=l1_cache_size)
        self.l1_stats = CacheStats()
        
        # L2 캐시 (Redis) 클라이언트
        self.redis_client: Optional[aioredis.Redis] = None
        self.l2_stats = CacheStats()
        
        # 캐시 엔트리 메타데이터
        self.cache_metadata: Dict[str, CacheEntry] = {}
        
        # 프리페칭 시스템
        self.prefetch_queue: asyncio.Queue = asyncio.Queue()
        self.prefetch_patterns: Dict[str, List[str]] = {}
        
        # 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 캐시 무효화 태그
        self.invalidation_tags: Dict[str, Set[str]] = {}
        
        logger.info("KG Cache Manager initialized")
    
    async def initialize(self):
        """캐시 매니저 초기화"""
        try:
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
            # 프리페칭 워커 시작
            if self.enable_prefetching:
                asyncio.create_task(self._prefetch_worker())
            
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise
    
    async def get(
        self, 
        key: str, 
        default: Any = None,
        update_access_stats: bool = True
    ) -> Any:
        """캐시에서 데이터 조회"""
        
        start_time = time.time()
        
        try:
            # L1 캐시 확인
            if key in self.l1_cache:
                data = self.l1_cache[key]
                if update_access_stats:
                    self._update_l1_stats(True, time.time() - start_time)
                    self._update_access_metadata(key)
                logger.debug(f"L1 cache hit: {key}")
                return data
            
            # L2 캐시 (Redis) 확인
            if self.redis_client:
                cached_data = await self.redis_client.get(f"kg:{key}")
                if cached_data:
                    # 압축 해제
                    data = await self._decompress_data(cached_data, key)
                    
                    # L1 캐시에도 저장
                    self.l1_cache[key] = data
                    
                    if update_access_stats:
                        self._update_l2_stats(True, time.time() - start_time)
                        self._update_access_metadata(key)
                    
                    logger.debug(f"L2 cache hit: {key}")
                    return data
            
            # 캐시 미스
            if update_access_stats:
                self._update_l1_stats(False, time.time() - start_time)
                self._update_l2_stats(False, time.time() - start_time)
            
            logger.debug(f"Cache miss: {key}")
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        compression: Optional[CompressionType] = None
    ) -> bool:
        """캐시에 데이터 저장"""
        
        try:
            # 데이터 크기 계산
            data_size = len(str(data).encode('utf-8'))
            
            # 압축 결정
            if compression is None:
                compression = self._determine_compression(data, data_size)
            
            # L1 캐시에 저장
            self.l1_cache[key] = data
            
            # 메타데이터 업데이트
            self._create_cache_entry(key, data, data_size, compression, ttl, tags)
            
            # L2 캐시 (Redis)에 저장
            if self.redis_client:
                compressed_data = await self._compress_data(data, compression)
                cache_ttl = ttl or self.l2_cache_ttl
                
                await self.redis_client.setex(
                    f"kg:{key}",
                    cache_ttl,
                    compressed_data
                )
                
                # 메타데이터도 Redis에 저장
                metadata = {
                    "created_at": datetime.now().isoformat(),
                    "size_bytes": data_size,
                    "compression": compression.value,
                    "tags": list(tags) if tags else []
                }
                
                await self.redis_client.setex(
                    f"kg:meta:{key}",
                    cache_ttl,
                    json.dumps(metadata)
                )
            
            # 태그 기반 무효화를 위한 인덱스 업데이트
            if tags:
                for tag in tags:
                    if tag not in self.invalidation_tags:
                        self.invalidation_tags[tag] = set()
                    self.invalidation_tags[tag].add(key)
            
            logger.debug(f"Cached data for key: {key} (size: {data_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        
        try:
            # L1 캐시에서 삭제
            if key in self.l1_cache:
                del self.l1_cache[key]
            
            # L2 캐시에서 삭제
            if self.redis_client:
                await self.redis_client.delete(f"kg:{key}")
                await self.redis_client.delete(f"kg:meta:{key}")
            
            # 메타데이터 삭제
            if key in self.cache_metadata:
                entry = self.cache_metadata[key]
                # 태그 인덱스에서도 제거
                for tag in entry.tags:
                    if tag in self.invalidation_tags:
                        self.invalidation_tags[tag].discard(key)
                
                del self.cache_metadata[key]
            
            logger.debug(f"Deleted cache entry: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def invalidate_by_tags(self, tags: Set[str]) -> int:
        """태그 기반 캐시 무효화"""
        
        invalidated_count = 0
        keys_to_invalidate = set()
        
        for tag in tags:
            if tag in self.invalidation_tags:
                keys_to_invalidate.update(self.invalidation_tags[tag])
        
        for key in keys_to_invalidate:
            if await self.delete(key):
                invalidated_count += 1
        
        logger.info(f"Invalidated {invalidated_count} cache entries for tags: {tags}")
        return invalidated_count
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """배치 캐시 조회"""
        
        results = {}
        missing_keys = []
        
        # L1 캐시에서 먼저 조회
        for key in keys:
            if key in self.l1_cache:
                results[key] = self.l1_cache[key]
            else:
                missing_keys.append(key)
        
        # L2 캐시에서 누락된 키들 조회
        if missing_keys and self.redis_client:
            redis_keys = [f"kg:{key}" for key in missing_keys]
            cached_values = await self.redis_client.mget(redis_keys)
            
            for i, cached_data in enumerate(cached_values):
                if cached_data:
                    key = missing_keys[i]
                    data = await self._decompress_data(cached_data, key)
                    results[key] = data
                    # L1 캐시에도 저장
                    self.l1_cache[key] = data
        
        return results
    
    async def batch_set(
        self, 
        data_dict: Dict[str, Any], 
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None
    ) -> int:
        """배치 캐시 저장"""
        
        success_count = 0
        
        # L1 캐시에 저장
        for key, data in data_dict.items():
            self.l1_cache[key] = data
            self._create_cache_entry(key, data, len(str(data).encode('utf-8')), 
                                   CompressionType.NONE, ttl, tags)
        
        # L2 캐시에 배치 저장
        if self.redis_client:
            pipe = self.redis_client.pipeline()
            cache_ttl = ttl or self.l2_cache_ttl
            
            for key, data in data_dict.items():
                compressed_data = await self._compress_data(data, CompressionType.JSON)
                pipe.setex(f"kg:{key}", cache_ttl, compressed_data)
                success_count += 1
            
            await pipe.execute()
        
        logger.debug(f"Batch cached {success_count} entries")
        return success_count
    
    async def prefetch(self, keys: List[str], priority: int = 1):
        """프리페칭 요청"""
        
        if not self.enable_prefetching:
            return
        
        for key in keys:
            await self.prefetch_queue.put((key, priority))
    
    async def add_prefetch_pattern(self, pattern_name: str, key_templates: List[str]):
        """프리페칭 패턴 추가"""
        
        self.prefetch_patterns[pattern_name] = key_templates
        logger.info(f"Added prefetch pattern: {pattern_name}")
    
    async def warm_up(self, warm_up_data: Dict[str, Any]):
        """캐시 워밍업"""
        
        logger.info(f"Warming up cache with {len(warm_up_data)} entries")
        
        await self.batch_set(warm_up_data, ttl=self.l2_cache_ttl * 2)  # 더 긴 TTL
        
        logger.info("Cache warm-up completed")
    
    def get_stats(self) -> Dict[str, CacheStats]:
        """캐시 통계 조회"""
        
        return {
            "l1_cache": self.l1_stats,
            "l2_cache": self.l2_stats
        }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """캐시 정보 조회"""
        
        l1_info = self.l1_cache.currsize if hasattr(self.l1_cache, 'currsize') else len(self.l1_cache)
        
        return {
            "l1_cache_size": l1_info,
            "l1_cache_maxsize": self.l1_cache_size,
            "l2_cache_ttl": self.l2_cache_ttl,
            "total_entries": len(self.cache_metadata),
            "compression_enabled": self.enable_compression,
            "prefetching_enabled": self.enable_prefetching,
            "invalidation_tags": len(self.invalidation_tags)
        }
    
    async def cleanup_expired(self) -> int:
        """만료된 캐시 엔트리 정리"""
        
        expired_keys = []
        current_time = datetime.now()
        
        for key, entry in self.cache_metadata.items():
            if entry.ttl_seconds:
                expiry_time = entry.created_at + timedelta(seconds=entry.ttl_seconds)
                if current_time > expiry_time:
                    expired_keys.append(key)
        
        for key in expired_keys:
            await self.delete(key)
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    # ========================================================================
    # 내부 메서드들
    # ========================================================================
    
    def _determine_compression(self, data: Any, data_size: int) -> CompressionType:
        """압축 타입 결정"""
        
        if not self.enable_compression or data_size < self.compression_threshold:
            return CompressionType.NONE
        
        # 데이터 타입에 따른 최적 압축 방식 선택
        if isinstance(data, (dict, list)):
            return CompressionType.JSON
        elif isinstance(data, str) and data_size > 5000:
            return CompressionType.GZIP
        else:
            return CompressionType.PICKLE
    
    async def _compress_data(self, data: Any, compression: CompressionType) -> bytes:
        """데이터 압축"""
        
        if compression == CompressionType.NONE:
            return str(data).encode('utf-8')
        elif compression == CompressionType.JSON:
            return json.dumps(data, default=str).encode('utf-8')
        elif compression == CompressionType.GZIP:
            json_data = json.dumps(data, default=str).encode('utf-8')
            return gzip.compress(json_data)
        elif compression == CompressionType.PICKLE:
            return pickle.dumps(data)
        else:
            return str(data).encode('utf-8')
    
    async def _decompress_data(self, compressed_data: bytes, key: str) -> Any:
        """데이터 압축 해제"""
        
        try:
            # 메타데이터에서 압축 타입 확인
            if self.redis_client:
                metadata_json = await self.redis_client.get(f"kg:meta:{key}")
                if metadata_json:
                    metadata = json.loads(metadata_json)
                    compression = CompressionType(metadata.get("compression", "none"))
                else:
                    compression = CompressionType.JSON  # 기본값
            else:
                compression = CompressionType.JSON
            
            if compression == CompressionType.NONE:
                return compressed_data.decode('utf-8')
            elif compression == CompressionType.JSON:
                return json.loads(compressed_data.decode('utf-8'))
            elif compression == CompressionType.GZIP:
                decompressed = gzip.decompress(compressed_data)
                return json.loads(decompressed.decode('utf-8'))
            elif compression == CompressionType.PICKLE:
                return pickle.loads(compressed_data)
            else:
                return json.loads(compressed_data.decode('utf-8'))
                
        except Exception as e:
            logger.error(f"Decompression failed for key {key}: {e}")
            # 폴백: JSON으로 시도
            try:
                return json.loads(compressed_data.decode('utf-8'))
            except:
                return compressed_data.decode('utf-8')
    
    def _create_cache_entry(
        self,
        key: str,
        data: Any,
        size_bytes: int,
        compression: CompressionType,
        ttl: Optional[int],
        tags: Optional[Set[str]]
    ):
        """캐시 엔트리 메타데이터 생성"""
        
        self.cache_metadata[key] = CacheEntry(
            key=key,
            data=data,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            size_bytes=size_bytes,
            compression=compression,
            ttl_seconds=ttl,
            tags=tags or set()
        )
    
    def _update_access_metadata(self, key: str):
        """접근 메타데이터 업데이트"""
        
        if key in self.cache_metadata:
            entry = self.cache_metadata[key]
            entry.last_accessed = datetime.now()
            entry.access_count += 1
    
    def _update_l1_stats(self, hit: bool, access_time: float):
        """L1 캐시 통계 업데이트"""
        
        self.l1_stats.total_requests += 1
        if hit:
            self.l1_stats.cache_hits += 1
        else:
            self.l1_stats.cache_misses += 1
        
        # 평균 접근 시간 업데이트
        total_time = self.l1_stats.avg_access_time_ms * (self.l1_stats.total_requests - 1)
        self.l1_stats.avg_access_time_ms = (total_time + access_time * 1000) / self.l1_stats.total_requests
    
    def _update_l2_stats(self, hit: bool, access_time: float):
        """L2 캐시 통계 업데이트"""
        
        self.l2_stats.total_requests += 1
        if hit:
            self.l2_stats.cache_hits += 1
        else:
            self.l2_stats.cache_misses += 1
        
        # 평균 접근 시간 업데이트
        total_time = self.l2_stats.avg_access_time_ms * (self.l2_stats.total_requests - 1)
        self.l2_stats.avg_access_time_ms = (total_time + access_time * 1000) / self.l2_stats.total_requests
    
    async def _prefetch_worker(self):
        """프리페칭 워커"""
        
        logger.info("Prefetch worker started")
        
        while True:
            try:
                # 우선순위 큐에서 프리페칭 요청 처리
                key, priority = await asyncio.wait_for(
                    self.prefetch_queue.get(), 
                    timeout=1.0
                )
                
                # 이미 캐시에 있는지 확인
                if key not in self.l1_cache:
                    # 실제 데이터 로딩은 별도 콜백으로 처리
                    logger.debug(f"Prefetching key: {key} (priority: {priority})")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Prefetch worker error: {e}")
                await asyncio.sleep(1)


# 전역 캐시 매니저 인스턴스
_cache_manager: Optional[KGCacheManager] = None


async def get_cache_manager() -> KGCacheManager:
    """캐시 매니저 싱글톤 인스턴스 조회"""
    
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = KGCacheManager()
        await _cache_manager.initialize()
    
    return _cache_manager


async def invalidate_kg_cache(kg_id: str):
    """특정 KG의 모든 캐시 무효화"""
    
    cache_manager = await get_cache_manager()
    await cache_manager.invalidate_by_tags({f"kg:{kg_id}"})


async def warm_up_kg_cache(kg_id: str, common_data: Dict[str, Any]):
    """특정 KG의 캐시 워밍업"""
    
    cache_manager = await get_cache_manager()
    
    # KG 태그 추가
    tagged_data = {}
    for key, data in common_data.items():
        tagged_key = f"kg:{kg_id}:{key}"
        tagged_data[tagged_key] = data
    
    await cache_manager.warm_up(tagged_data)