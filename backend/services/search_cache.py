"""
계층적 검색 캐싱 시스템 (STM/LTM 개념 활용)

이 모듈은 검색 결과를 두 계층으로 캐싱합니다:
- L1 Cache (STM): 최근 검색 결과 (빠른 접근, 짧은 TTL)
- L2 Cache (LTM): 인기 검색 결과 (영구 저장, 빈도 기반)
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class SearchCacheManager:
    """
    계층적 검색 캐싱 관리자

    Features:
    - L1 Cache (STM): 최근 검색 결과 (1시간 TTL)
    - L2 Cache (LTM): 인기 검색 결과 (영구, 빈도 기반)
    - 임베딩 캐싱: 동일 텍스트 재사용
    - 통계 추적: 캐시 히트율, 인기 쿼리
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        l1_ttl: int = 3600,  # 1시간
        l2_threshold: int = 3,  # 3회 이상 검색 시 L2로 승격
        max_l2_size: int = 1000,  # L2 캐시 최대 크기
    ):
        """
        Initialize SearchCacheManager.

        Args:
            redis_client: Redis client instance
            l1_ttl: L1 cache TTL in seconds
            l2_threshold: Minimum query count for L2 promotion
            max_l2_size: Maximum number of entries in L2 cache
        """
        self.redis = redis_client
        self.l1_ttl = l1_ttl
        self.l2_threshold = l2_threshold
        self.max_l2_size = max_l2_size

        logger.info(
            f"SearchCacheManager initialized: "
            f"L1_TTL={l1_ttl}s, L2_threshold={l2_threshold}, "
            f"max_L2_size={max_l2_size}"
        )

    def _get_query_hash(
        self,
        query: str,
        top_k: int,
        filters: Optional[dict] = None,
        search_mode: str = "hybrid",
    ) -> str:
        """쿼리 해시 생성"""
        cache_data = {
            "query": query.lower().strip(),
            "top_k": top_k,
            "filters": filters or {},
            "search_mode": search_mode,
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_l1_key(self, query_hash: str) -> str:
        """L1 캐시 키"""
        return f"search:l1:{query_hash}"

    def _get_l2_key(self, query_hash: str) -> str:
        """L2 캐시 키"""
        return f"search:l2:{query_hash}"

    def _get_frequency_key(self) -> str:
        """쿼리 빈도 추적 키"""
        return "search:frequency"

    def _get_embedding_key(self, text: str) -> str:
        """임베딩 캐시 키"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{text_hash}"

    async def get_cached_results(
        self,
        query: str,
        top_k: int,
        filters: Optional[dict] = None,
        search_mode: str = "hybrid",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        캐시된 검색 결과 가져오기 (L1 → L2 순서)

        Returns:
            캐시된 결과 또는 None
        """
        try:
            query_hash = self._get_query_hash(query, top_k, filters, search_mode)

            # 1. L1 캐시 확인 (STM - 최근 검색)
            l1_key = self._get_l1_key(query_hash)
            l1_data = await self.redis.get(l1_key)

            if l1_data:
                logger.debug(f"L1 cache hit for query: {query[:50]}...")
                await self._record_cache_hit("l1")

                # 빈도 증가
                await self._increment_query_frequency(query_hash, query)

                return json.loads(l1_data)

            # 2. L2 캐시 확인 (LTM - 인기 검색)
            l2_key = self._get_l2_key(query_hash)
            l2_data = await self.redis.get(l2_key)

            if l2_data:
                logger.debug(f"L2 cache hit for query: {query[:50]}...")
                await self._record_cache_hit("l2")

                # L1으로 승격 (자주 사용되는 L2 항목)
                await self.redis.setex(l1_key, self.l1_ttl, l2_data)

                # 빈도 증가
                await self._increment_query_frequency(query_hash, query)

                return json.loads(l2_data)

            # 캐시 미스
            logger.debug(f"Cache miss for query: {query[:50]}...")
            await self._record_cache_miss()

            return None

        except RedisError as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected cache error: {e}")
            return None

    async def cache_results(
        self,
        query: str,
        top_k: int,
        filters: Optional[dict],
        search_mode: str,
        results: List[Dict[str, Any]],
    ):
        """
        검색 결과 캐싱 (L1에 저장, 빈도에 따라 L2로 승격)
        """
        try:
            query_hash = self._get_query_hash(query, top_k, filters, search_mode)
            results_json = json.dumps(results)

            # 1. L1 캐시에 저장 (STM)
            l1_key = self._get_l1_key(query_hash)
            await self.redis.setex(l1_key, self.l1_ttl, results_json)

            logger.debug(f"Cached results in L1 for query: {query[:50]}...")

            # 2. 빈도 증가
            frequency = await self._increment_query_frequency(query_hash, query)

            # 3. 빈도가 임계값 이상이면 L2로 승격 (LTM)
            if frequency >= self.l2_threshold:
                await self._promote_to_l2(query_hash, results_json, frequency)

        except RedisError as e:
            logger.error(f"Cache storage error: {e}")
        except Exception as e:
            logger.error(f"Unexpected cache storage error: {e}")

    async def _promote_to_l2(self, query_hash: str, results_json: str, frequency: int):
        """L2 캐시로 승격 (인기 검색)"""
        try:
            l2_key = self._get_l2_key(query_hash)

            # L2에 영구 저장
            await self.redis.set(l2_key, results_json)

            # L2 크기 관리 (LRU 방식)
            l2_size_key = "search:l2:size"
            current_size = await self.redis.incr(l2_size_key)

            if current_size > self.max_l2_size:
                # 가장 오래된 항목 제거
                await self._evict_l2_entries()

            logger.info(
                f"Promoted to L2 cache (frequency={frequency}): " f"{query_hash[:8]}..."
            )

        except RedisError as e:
            logger.error(f"L2 promotion error: {e}")

    async def _evict_l2_entries(self):
        """L2 캐시에서 오래된 항목 제거"""
        try:
            # 빈도가 낮은 항목부터 제거
            freq_key = self._get_frequency_key()

            # 빈도가 가장 낮은 항목 찾기
            lowest_freq_items = await self.redis.zrange(freq_key, 0, 9)  # 하위 10개

            for query_hash in lowest_freq_items:
                l2_key = self._get_l2_key(
                    query_hash.decode() if isinstance(query_hash, bytes) else query_hash
                )
                await self.redis.delete(l2_key)

            # 크기 카운터 감소
            await self.redis.decrby("search:l2:size", len(lowest_freq_items))

            logger.info(f"Evicted {len(lowest_freq_items)} entries from L2 cache")

        except RedisError as e:
            logger.error(f"L2 eviction error: {e}")

    async def _increment_query_frequency(self, query_hash: str, query: str) -> int:
        """쿼리 빈도 증가 및 반환"""
        try:
            freq_key = self._get_frequency_key()

            # Sorted Set에 저장 (score = frequency)
            new_freq = await self.redis.zincrby(freq_key, 1, query_hash)

            # 쿼리 텍스트도 저장 (분석용)
            query_text_key = f"search:query_text:{query_hash}"
            if not await self.redis.exists(query_text_key):
                await self.redis.setex(query_text_key, 86400 * 7, query)  # 7일 보관

            return int(new_freq)

        except RedisError as e:
            logger.error(f"Frequency increment error: {e}")
            return 0

    async def _record_cache_hit(self, cache_level: str):
        """캐시 히트 기록"""
        try:
            key = f"search:stats:hit:{cache_level}"
            await self.redis.incr(key)
            await self.redis.expire(key, 86400)  # 24시간 보관
        except RedisError:
            pass

    async def _record_cache_miss(self):
        """캐시 미스 기록"""
        try:
            key = "search:stats:miss"
            await self.redis.incr(key)
            await self.redis.expire(key, 86400)
        except RedisError:
            pass

    async def get_embedding_cache(self, text: str) -> Optional[List[float]]:
        """임베딩 캐시 가져오기"""
        try:
            key = self._get_embedding_key(text)
            cached = await self.redis.get(key)

            if cached:
                logger.debug(f"Embedding cache hit for text: {text[:30]}...")
                return json.loads(cached)

            return None

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Embedding cache retrieval error: {e}")
            return None

    async def cache_embedding(self, text: str, embedding: List[float]):
        """임베딩 캐싱 (영구 저장)"""
        try:
            key = self._get_embedding_key(text)

            # 영구 저장 (임베딩은 변하지 않음)
            await self.redis.set(key, json.dumps(embedding))

            logger.debug(f"Cached embedding for text: {text[:30]}...")

        except (RedisError, TypeError) as e:
            logger.error(f"Embedding cache storage error: {e}")

    async def get_popular_queries(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """인기 검색어 조회"""
        try:
            freq_key = self._get_frequency_key()

            # 빈도가 높은 순으로 조회
            top_hashes = self.redis.zrevrange(freq_key, 0, top_n - 1, withscores=True)

            popular_queries = []
            for query_hash, frequency in top_hashes:
                if isinstance(query_hash, bytes):
                    query_hash = query_hash.decode()

                # 쿼리 텍스트 가져오기
                query_text_key = f"search:query_text:{query_hash}"
                query_text = await self.redis.get(query_text_key)

                if query_text:
                    if isinstance(query_text, bytes):
                        query_text = query_text.decode()

                    popular_queries.append(
                        {
                            "query": query_text,
                            "frequency": int(frequency),
                            "hash": query_hash,
                        }
                    )

            return popular_queries

        except RedisError as e:
            logger.error(f"Popular queries retrieval error: {e}")
            return []

    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        try:
            l1_hits = int(await self.redis.get("search:stats:hit:l1") or 0)
            l2_hits = int(await self.redis.get("search:stats:hit:l2") or 0)
            misses = int(await self.redis.get("search:stats:miss") or 0)

            total_requests = l1_hits + l2_hits + misses
            hit_rate = (
                (l1_hits + l2_hits) / total_requests * 100 if total_requests > 0 else 0
            )

            l2_size = int(await self.redis.get("search:l2:size") or 0)

            return {
                "l1_hits": l1_hits,
                "l2_hits": l2_hits,
                "total_hits": l1_hits + l2_hits,
                "misses": misses,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "l2_cache_size": l2_size,
                "l2_cache_max": self.max_l2_size,
            }

        except RedisError as e:
            logger.error(f"Cache stats retrieval error: {e}")
            return {}

    async def clear_cache(self, cache_level: Optional[str] = None):
        """
        캐시 초기화

        Args:
            cache_level: "l1", "l2", or None (both)
        """
        try:
            if cache_level == "l1" or cache_level is None:
                # L1 캐시 초기화
                keys = self.redis.keys("search:l1:*")
                if keys:
                    self.redis.delete(*keys)
                logger.info(f"Cleared L1 cache ({len(keys)} entries)")

            if cache_level == "l2" or cache_level is None:
                # L2 캐시 초기화
                keys = self.redis.keys("search:l2:*")
                if keys:
                    self.redis.delete(*keys)
                self.redis.delete("search:l2:size")
                logger.info(f"Cleared L2 cache ({len(keys)} entries)")

            if cache_level is None:
                # 통계도 초기화
                self.redis.delete(
                    "search:stats:hit:l1", "search:stats:hit:l2", "search:stats:miss"
                )
                logger.info("Cleared cache statistics")

        except RedisError as e:
            logger.error(f"Cache clear error: {e}")

    def __repr__(self) -> str:
        return (
            f"SearchCacheManager(L1_TTL={self.l1_ttl}s, "
            f"L2_threshold={self.l2_threshold}, max_L2={self.max_l2_size})"
        )
