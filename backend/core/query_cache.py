"""
Query Result Caching
쿼리 결과 캐싱을 위한 데코레이터 및 유틸리티
"""

from functools import wraps
import hashlib
import json
import pickle
from typing import Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


def cache_query(ttl: int = 3600, key_prefix: str = "query"):
    """
    쿼리 결과 캐싱 데코레이터
    
    Redis를 사용하여 쿼리 결과를 캐싱합니다.
    
    Args:
        ttl: 캐시 유효 시간 (초)
        key_prefix: 캐시 키 접두사
        
    Example:
        @cache_query(ttl=3600)
        def get_tool_by_id(db: Session, tool_id: str):
            return db.query(Tool).filter(Tool.id == tool_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Redis 연결 가져오기
            try:
                from backend.core.connection_pool import get_redis_connection
                redis = get_redis_connection()
            except Exception as e:
                logger.warning(f"Redis not available, skipping cache: {e}")
                return func(*args, **kwargs)
            
            # 캐시 키 생성
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)
            
            # 캐시 확인
            try:
                cached = redis.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {cache_key}")
                    return pickle.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # 캐시 미스 - 함수 실행
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # 결과 캐싱
            try:
                redis.setex(cache_key, ttl, pickle.dumps(result))
                logger.debug(f"Cached result: {cache_key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
            
        # 캐시 무효화 함수 추가
        def invalidate(*args, **kwargs):
            """캐시 무효화"""
            try:
                from backend.core.connection_pool import get_redis_connection
                redis = get_redis_connection()
                cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)
                redis.delete(cache_key)
                logger.info(f"Cache invalidated: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache invalidation error: {e}")
        
        wrapper.invalidate = invalidate
        return wrapper
    return decorator


def cache_query_list(ttl: int = 3600, key_prefix: str = "query_list"):
    """
    리스트 쿼리 결과 캐싱 데코레이터
    
    여러 항목을 반환하는 쿼리에 최적화
    
    Example:
        @cache_query_list(ttl=1800)
        def get_all_tools(db: Session):
            return db.query(Tool).all()
    """
    return cache_query(ttl=ttl, key_prefix=key_prefix)


def invalidate_cache_pattern(pattern: str):
    """
    패턴에 맞는 모든 캐시 무효화
    
    Args:
        pattern: Redis 키 패턴 (예: "query:get_tool_*")
        
    Example:
        # 모든 tool 관련 캐시 무효화
        invalidate_cache_pattern("query:get_tool_*")
    """
    try:
        from backend.core.connection_pool import get_redis_connection
        redis = get_redis_connection()
        
        # 패턴에 맞는 키 찾기
        keys = redis.keys(pattern)
        
        if keys:
            # 키 삭제
            redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching: {pattern}")
        else:
            logger.debug(f"No cache keys found matching: {pattern}")
            
    except Exception as e:
        logger.warning(f"Cache pattern invalidation error: {e}")


def _generate_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """
    캐시 키 생성
    
    함수 이름과 인자를 기반으로 고유한 캐시 키 생성
    """
    # 인자를 문자열로 변환
    args_str = str(args)
    kwargs_str = str(sorted(kwargs.items()))
    
    # 해시 생성
    key_data = f"{func_name}:{args_str}:{kwargs_str}"
    key_hash = hashlib.md5(key_data.encode()).hexdigest()
    
    return f"{prefix}:{func_name}:{key_hash}"


class CacheManager:
    """캐시 관리 클래스"""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        try:
            from backend.core.connection_pool import get_redis_connection
            redis = get_redis_connection()
            cached = redis.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = 3600):
        """캐시에 값 저장"""
        try:
            from backend.core.connection_pool import get_redis_connection
            redis = get_redis_connection()
            redis.setex(key, ttl, pickle.dumps(value))
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    @staticmethod
    def delete(key: str):
        """캐시에서 값 삭제"""
        try:
            from backend.core.connection_pool import get_redis_connection
            redis = get_redis_connection()
            redis.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
    
    @staticmethod
    def clear_all():
        """모든 캐시 삭제"""
        try:
            from backend.core.connection_pool import get_redis_connection
            redis = get_redis_connection()
            redis.flushdb()
            logger.warning("All cache cleared!")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
    
    @staticmethod
    def get_stats() -> dict:
        """캐시 통계 조회"""
        try:
            from backend.core.connection_pool import get_redis_connection
            redis = get_redis_connection()
            info = redis.info('stats')
            return {
                'total_keys': redis.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / 
                           (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {}
