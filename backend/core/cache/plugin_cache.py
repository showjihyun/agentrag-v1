"""
Agent Plugin 캐싱 시스템
계층적 캐싱 (L1: 메모리, L2: Redis) 및 캐시 무효화 전략
"""
from typing import Dict, Any, Optional, List, Union
import asyncio
import json
import logging
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from backend.core.dependencies import get_redis_client
from backend.core.utils.circular_buffer import CircularBuffer

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """캐시 레벨"""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    BOTH = "both"

@dataclass
class CacheConfig:
    """캐시 설정"""
    ttl_seconds: int
    max_size: int = 1000
    enable_l1: bool = True
    enable_l2: bool = True
    compression: bool = False

class PluginCacheManager:
    """플러그인 캐시 관리자"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        
        # L1 캐시 (메모리)
        self.l1_cache: Dict[str, CircularBuffer] = {}
        
        # 캐시 설정
        self.cache_configs = {
            'plugin_list': CacheConfig(ttl_seconds=300, max_size=100),  # 5분
            'plugin_info': CacheConfig(ttl_seconds=600, max_size=500),  # 10분
            'execution_result': CacheConfig(ttl_seconds=3600, max_size=1000),  # 1시간
            'system_health': CacheConfig(ttl_seconds=60, max_size=10),  # 1분
            'user_plugins': CacheConfig(ttl_seconds=300, max_size=200),  # 5분
            'orchestration_patterns': CacheConfig(ttl_seconds=1800, max_size=50),  # 30분
        }
        
        # 캐시 통계
        self.cache_stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'invalidations': 0,
            'evictions': 0
        }
        
        # 캐시 의존성 맵 (캐시 무효화용)
        self.dependency_map = {
            'plugin_list': ['plugin_info', 'user_plugins'],
            'plugin_info': ['execution_result'],
            'system_health': ['plugin_list', 'plugin_info'],
        }
    
    def _get_cache_key(self, cache_type: str, identifier: str) -> str:
        """캐시 키 생성"""
        return f"plugin_cache:{cache_type}:{identifier}"
    
    def _hash_data(self, data: Any) -> str:
        """데이터 해시 생성"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def get(
        self, 
        cache_type: str, 
        identifier: str, 
        level: CacheLevel = CacheLevel.BOTH
    ) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        cache_key = self._get_cache_key(cache_type, identifier)
        config = self.cache_configs.get(cache_type)
        
        if not config:
            return None
        
        # L1 캐시 확인
        if level in [CacheLevel.L1_MEMORY, CacheLevel.BOTH] and config.enable_l1:
            l1_result = await self._get_from_l1(cache_type, identifier)
            if l1_result is not None:
                self.cache_stats['l1_hits'] += 1
                return l1_result
            else:
                self.cache_stats['l1_misses'] += 1
        
        # L2 캐시 확인
        if level in [CacheLevel.L2_REDIS, CacheLevel.BOTH] and config.enable_l2:
            l2_result = await self._get_from_l2(cache_key, config)
            if l2_result is not None:
                self.cache_stats['l2_hits'] += 1
                
                # L1 캐시에도 저장 (캐시 승격)
                if config.enable_l1:
                    await self._set_to_l1(cache_type, identifier, l2_result, config)
                
                return l2_result
            else:
                self.cache_stats['l2_misses'] += 1
        
        return None
    
    async def set(
        self, 
        cache_type: str, 
        identifier: str, 
        data: Any, 
        level: CacheLevel = CacheLevel.BOTH,
        ttl_override: Optional[int] = None
    ) -> bool:
        """캐시에 데이터 저장"""
        cache_key = self._get_cache_key(cache_type, identifier)
        config = self.cache_configs.get(cache_type)
        
        if not config:
            return False
        
        # TTL 오버라이드
        if ttl_override:
            config = CacheConfig(
                ttl_seconds=ttl_override,
                max_size=config.max_size,
                enable_l1=config.enable_l1,
                enable_l2=config.enable_l2,
                compression=config.compression
            )
        
        success = True
        
        # L1 캐시에 저장
        if level in [CacheLevel.L1_MEMORY, CacheLevel.BOTH] and config.enable_l1:
            success &= await self._set_to_l1(cache_type, identifier, data, config)
        
        # L2 캐시에 저장
        if level in [CacheLevel.L2_REDIS, CacheLevel.BOTH] and config.enable_l2:
            success &= await self._set_to_l2(cache_key, data, config)
        
        return success
    
    async def _get_from_l1(self, cache_type: str, identifier: str) -> Optional[Any]:
        """L1 캐시에서 데이터 조회"""
        try:
            if cache_type not in self.l1_cache:
                return None
            
            buffer = self.l1_cache[cache_type]
            
            # 순환 버퍼에서 해당 식별자의 최신 데이터 찾기
            for item in reversed(buffer.get_all()):
                if item.get('identifier') == identifier:
                    # TTL 확인
                    if self._is_expired(item.get('timestamp'), item.get('ttl')):
                        return None
                    return item.get('data')
            
            return None
            
        except Exception as e:
            logger.error(f"L1 cache get error: {e}")
            return None
    
    async def _set_to_l1(
        self, 
        cache_type: str, 
        identifier: str, 
        data: Any, 
        config: CacheConfig
    ) -> bool:
        """L1 캐시에 데이터 저장"""
        try:
            if cache_type not in self.l1_cache:
                self.l1_cache[cache_type] = CircularBuffer(config.max_size)
            
            cache_item = {
                'identifier': identifier,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'ttl': config.ttl_seconds,
                'hash': self._hash_data(data)
            }
            
            self.l1_cache[cache_type].add(cache_item)
            return True
            
        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
            return False
    
    async def _get_from_l2(self, cache_key: str, config: CacheConfig) -> Optional[Any]:
        """L2 캐시에서 데이터 조회"""
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            return None
    
    async def _set_to_l2(self, cache_key: str, data: Any, config: CacheConfig) -> bool:
        """L2 캐시에 데이터 저장"""
        try:
            cached_data = json.dumps(data, ensure_ascii=False)
            await self.redis_client.setex(
                cache_key, 
                config.ttl_seconds, 
                cached_data
            )
            return True
            
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
            return False
    
    def _is_expired(self, timestamp_str: str, ttl_seconds: int) -> bool:
        """캐시 만료 확인"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            expiry_time = timestamp + timedelta(seconds=ttl_seconds)
            return datetime.now() > expiry_time
        except Exception:
            return True
    
    async def invalidate(
        self, 
        cache_type: str, 
        identifier: Optional[str] = None,
        cascade: bool = True
    ) -> bool:
        """캐시 무효화"""
        try:
            success = True
            
            if identifier:
                # 특정 항목 무효화
                cache_key = self._get_cache_key(cache_type, identifier)
                
                # L1 캐시에서 제거 (실제로는 만료 표시)
                if cache_type in self.l1_cache:
                    # 새로운 만료 항목 추가
                    expired_item = {
                        'identifier': identifier,
                        'data': None,
                        'timestamp': datetime.now().isoformat(),
                        'ttl': 0,  # 즉시 만료
                        'expired': True
                    }
                    self.l1_cache[cache_type].add(expired_item)
                
                # L2 캐시에서 제거
                await self.redis_client.delete(cache_key)
            else:
                # 전체 캐시 타입 무효화
                if cache_type in self.l1_cache:
                    self.l1_cache[cache_type].clear()
                
                # Redis에서 패턴 매칭으로 삭제
                pattern = self._get_cache_key(cache_type, "*")
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            self.cache_stats['invalidations'] += 1
            
            # 연쇄 무효화
            if cascade and cache_type in self.dependency_map:
                for dependent_type in self.dependency_map[cache_type]:
                    await self.invalidate(dependent_type, cascade=False)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_requests = (
            self.cache_stats['l1_hits'] + self.cache_stats['l1_misses'] +
            self.cache_stats['l2_hits'] + self.cache_stats['l2_misses']
        )
        
        l1_hit_rate = (
            self.cache_stats['l1_hits'] / max(total_requests, 1) * 100
        )
        l2_hit_rate = (
            self.cache_stats['l2_hits'] / max(total_requests, 1) * 100
        )
        overall_hit_rate = (
            (self.cache_stats['l1_hits'] + self.cache_stats['l2_hits']) / 
            max(total_requests, 1) * 100
        )
        
        # L1 캐시 크기 정보
        l1_sizes = {
            cache_type: buffer.size() 
            for cache_type, buffer in self.l1_cache.items()
        }
        
        return {
            'hit_rates': {
                'l1_hit_rate': round(l1_hit_rate, 2),
                'l2_hit_rate': round(l2_hit_rate, 2),
                'overall_hit_rate': round(overall_hit_rate, 2)
            },
            'request_counts': {
                'l1_hits': self.cache_stats['l1_hits'],
                'l1_misses': self.cache_stats['l1_misses'],
                'l2_hits': self.cache_stats['l2_hits'],
                'l2_misses': self.cache_stats['l2_misses'],
                'total_requests': total_requests
            },
            'cache_sizes': {
                'l1_sizes': l1_sizes,
                'total_l1_items': sum(l1_sizes.values())
            },
            'operations': {
                'invalidations': self.cache_stats['invalidations'],
                'evictions': self.cache_stats['evictions']
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def warm_cache(self, cache_type: str, data_loader_func) -> bool:
        """캐시 워밍"""
        try:
            logger.info(f"Warming cache for type: {cache_type}")
            
            # 데이터 로더 함수 실행
            data_items = await data_loader_func()
            
            # 각 항목을 캐시에 저장
            for identifier, data in data_items.items():
                await self.set(cache_type, identifier, data)
            
            logger.info(f"Cache warmed for {cache_type}: {len(data_items)} items")
            return True
            
        except Exception as e:
            logger.error(f"Cache warming error for {cache_type}: {e}")
            return False
    
    async def cleanup_expired(self) -> int:
        """만료된 캐시 정리"""
        cleaned_count = 0
        
        try:
            # L1 캐시 정리는 CircularBuffer가 자동으로 처리
            # L2 캐시는 Redis TTL이 자동으로 처리
            
            # 통계 업데이트
            self.cache_stats['evictions'] += cleaned_count
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
        
        return cleaned_count

# 전역 인스턴스
plugin_cache_manager = PluginCacheManager()