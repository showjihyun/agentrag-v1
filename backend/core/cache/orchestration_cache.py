"""
Orchestration Cache Manager
오케스트레이션 결과 및 설정 캐싱 시스템
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self) -> None:
        """접근 기록 업데이트"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class OrchestrationCache:
    """
    오케스트레이션 캐싱 관리자
    
    L1 (메모리) + L2 (Redis) 다단계 캐싱 지원
    """
    
    def __init__(self, redis_client=None, max_memory_entries: int = 1000):
        """
        캐시 매니저 초기화
        
        Args:
            redis_client: Redis 클라이언트 (L2 캐시)
            max_memory_entries: 메모리 캐시 최대 엔트리 수
        """
        self.redis = redis_client
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_entries = max_memory_entries
        
        # 캐시 통계
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        캐시 키 생성
        
        Args:
            prefix: 키 접두사
            **kwargs: 키 생성에 사용할 파라미터들
            
        Returns:
            str: 생성된 캐시 키
        """
        # 파라미터를 정렬하여 일관된 키 생성
        sorted_params = sorted(kwargs.items())
        param_str = json.dumps(sorted_params, sort_keys=True, default=str)
        
        # SHA256 해시로 키 생성
        hash_obj = hashlib.sha256(param_str.encode())
        hash_key = hash_obj.hexdigest()[:16]  # 16자리로 단축
        
        return f"{prefix}:{hash_key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 조회
        
        Args:
            key: 캐시 키
            
        Returns:
            Optional[Any]: 캐시된 값 또는 None
        """
        try:
            # L1 캐시 (메모리) 확인
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                
                if entry.is_expired():
                    # 만료된 엔트리 제거
                    del self.memory_cache[key]
                else:
                    entry.access()
                    self.stats["l1_hits"] += 1
                    logger.debug(f"L1 cache hit: {key}")
                    return entry.value
            
            # L2 캐시 (Redis) 확인
            if self.redis:
                try:
                    cached_data = await self.redis.get(key)
                    if cached_data:
                        value = json.loads(cached_data)
                        
                        # L1 캐시에도 저장 (승격)
                        await self._set_memory_cache(key, value, ttl_seconds=300)  # 5분
                        
                        self.stats["l2_hits"] += 1
                        logger.debug(f"L2 cache hit: {key}")
                        return value
                        
                except Exception as e:
                    logger.warning(f"Redis cache error: {e}")
            
            # 캐시 미스
            self.stats["misses"] += 1
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None,
        l1_only: bool = False
    ) -> bool:
        """
        캐시에 값 저장
        
        Args:
            key: 캐시 키
            value: 저장할 값
            ttl_seconds: TTL (초)
            l1_only: L1 캐시에만 저장할지 여부
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # L1 캐시 (메모리) 저장
            await self._set_memory_cache(key, value, ttl_seconds)
            
            # L2 캐시 (Redis) 저장
            if not l1_only and self.redis:
                try:
                    serialized_value = json.dumps(value, default=str)
                    
                    if ttl_seconds:
                        await self.redis.setex(key, ttl_seconds, serialized_value)
                    else:
                        await self.redis.set(key, serialized_value)
                        
                except Exception as e:
                    logger.warning(f"Redis cache set error: {e}")
            
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def _set_memory_cache(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> None:
        """L1 메모리 캐시에 저장"""
        # 메모리 캐시 크기 제한 확인
        if len(self.memory_cache) >= self.max_memory_entries:
            await self._evict_memory_cache()
        
        # TTL 계산
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        # 엔트리 생성
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        self.memory_cache[key] = entry
    
    async def _evict_memory_cache(self) -> None:
        """메모리 캐시 제거 (LRU 방식)"""
        if not self.memory_cache:
            return
        
        # 가장 오래 전에 접근된 엔트리 찾기
        oldest_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k].last_accessed or self.memory_cache[k].created_at
        )
        
        del self.memory_cache[oldest_key]
        self.stats["evictions"] += 1
        logger.debug(f"Evicted from L1 cache: {oldest_key}")
    
    async def delete(self, key: str) -> bool:
        """
        캐시에서 키 삭제
        
        Args:
            key: 삭제할 캐시 키
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            deleted = False
            
            # L1 캐시에서 삭제
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted = True
            
            # L2 캐시에서 삭제
            if self.redis:
                try:
                    redis_deleted = await self.redis.delete(key)
                    deleted = deleted or redis_deleted > 0
                except Exception as e:
                    logger.warning(f"Redis cache delete error: {e}")
            
            if deleted:
                logger.debug(f"Cache deleted: {key}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """
        캐시 클리어
        
        Args:
            pattern: 삭제할 키 패턴 (None이면 전체 삭제)
            
        Returns:
            int: 삭제된 키 수
        """
        try:
            deleted_count = 0
            
            # L1 캐시 클리어
            if pattern:
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    deleted_count += 1
            else:
                deleted_count += len(self.memory_cache)
                self.memory_cache.clear()
            
            # L2 캐시 클리어
            if self.redis:
                try:
                    if pattern:
                        keys = await self.redis.keys(f"*{pattern}*")
                        if keys:
                            redis_deleted = await self.redis.delete(*keys)
                            deleted_count += redis_deleted
                    else:
                        await self.redis.flushdb()
                except Exception as e:
                    logger.warning(f"Redis cache clear error: {e}")
            
            logger.info(f"Cache cleared: {deleted_count} keys (pattern: {pattern})")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 조회
        
        Returns:
            Dict[str, Any]: 캐시 통계
        """
        total_requests = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["misses"]
        hit_rate = 0.0
        
        if total_requests > 0:
            hit_rate = (self.stats["l1_hits"] + self.stats["l2_hits"]) / total_requests
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "l1_size": len(self.memory_cache),
            "l1_max_size": self.max_memory_entries
        }
    
    async def cleanup_expired(self) -> int:
        """
        만료된 캐시 엔트리 정리
        
        Returns:
            int: 정리된 엔트리 수
        """
        try:
            cleaned_count = 0
            
            # L1 캐시 정리
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
                cleaned_count += 1
            
            if cleaned_count > 0:
                logger.debug(f"Cleaned up {cleaned_count} expired cache entries")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0


class OrchestrationCacheManager:
    """오케스트레이션 전용 캐시 매니저"""
    
    def __init__(self, cache: OrchestrationCache):
        self.cache = cache
    
    async def get_validation_result(
        self, 
        pattern_type: str, 
        config_hash: str
    ) -> Optional[Dict[str, Any]]:
        """설정 검증 결과 조회"""
        key = self.cache._generate_cache_key(
            "validation", 
            pattern_type=pattern_type, 
            config_hash=config_hash
        )
        return await self.cache.get(key)
    
    async def cache_validation_result(
        self, 
        pattern_type: str, 
        config_hash: str, 
        result: Dict[str, Any]
    ) -> bool:
        """설정 검증 결과 캐싱"""
        key = self.cache._generate_cache_key(
            "validation", 
            pattern_type=pattern_type, 
            config_hash=config_hash
        )
        return await self.cache.set(key, result, ttl_seconds=3600)  # 1시간
    
    async def get_execution_result(
        self, 
        pattern_type: str, 
        config_hash: str, 
        input_hash: str
    ) -> Optional[Dict[str, Any]]:
        """실행 결과 조회"""
        key = self.cache._generate_cache_key(
            "execution", 
            pattern_type=pattern_type, 
            config_hash=config_hash, 
            input_hash=input_hash
        )
        return await self.cache.get(key)
    
    async def cache_execution_result(
        self, 
        pattern_type: str, 
        config_hash: str, 
        input_hash: str, 
        result: Dict[str, Any]
    ) -> bool:
        """실행 결과 캐싱"""
        key = self.cache._generate_cache_key(
            "execution", 
            pattern_type=pattern_type, 
            config_hash=config_hash, 
            input_hash=input_hash
        )
        return await self.cache.set(key, result, ttl_seconds=1800)  # 30분
    
    async def get_pattern_metadata(self, pattern_type: str) -> Optional[Dict[str, Any]]:
        """패턴 메타데이터 조회"""
        key = self.cache._generate_cache_key("pattern_meta", pattern_type=pattern_type)
        return await self.cache.get(key)
    
    async def cache_pattern_metadata(
        self, 
        pattern_type: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """패턴 메타데이터 캐싱"""
        key = self.cache._generate_cache_key("pattern_meta", pattern_type=pattern_type)
        return await self.cache.set(key, metadata, ttl_seconds=7200)  # 2시간
    
    def generate_config_hash(self, config: Dict[str, Any]) -> str:
        """설정 해시 생성"""
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def generate_input_hash(self, input_data: Dict[str, Any]) -> str:
        """입력 데이터 해시 생성"""
        input_str = json.dumps(input_data, sort_keys=True, default=str)
        return hashlib.sha256(input_str.encode()).hexdigest()[:16]


# 전역 캐시 인스턴스 (의존성 주입으로 교체 가능)
_cache_instance: Optional[OrchestrationCache] = None
_cache_manager_instance: Optional[OrchestrationCacheManager] = None


def get_orchestration_cache() -> OrchestrationCache:
    """오케스트레이션 캐시 인스턴스 조회"""
    global _cache_instance
    
    if _cache_instance is None:
        # Redis 클라이언트는 실제 환경에서 주입
        _cache_instance = OrchestrationCache(redis_client=None)
    
    return _cache_instance


def get_orchestration_cache_manager() -> OrchestrationCacheManager:
    """오케스트레이션 캐시 매니저 인스턴스 조회"""
    global _cache_manager_instance
    
    if _cache_manager_instance is None:
        cache = get_orchestration_cache()
        _cache_manager_instance = OrchestrationCacheManager(cache)
    
    return _cache_manager_instance


def set_orchestration_cache(cache: OrchestrationCache) -> None:
    """오케스트레이션 캐시 인스턴스 설정 (테스트용)"""
    global _cache_instance, _cache_manager_instance
    _cache_instance = cache
    _cache_manager_instance = OrchestrationCacheManager(cache)