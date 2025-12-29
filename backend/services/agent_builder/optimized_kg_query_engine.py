"""
Optimized Knowledge Graph Query Engine

고성능 그래프 쿼리 엔진 with 다층 캐싱, 쿼리 최적화, 병렬 처리
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json

from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
import redis
from cachetools import TTLCache, LRUCache

from backend.db.models.knowledge_graph import (
    KnowledgeGraph, KGEntity, KGRelationship, EntityType, RelationType
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class QueryType(Enum):
    """쿼리 타입 분류"""
    ENTITY_SEARCH = "entity_search"
    RELATIONSHIP_SEARCH = "relationship_search"
    PATH_FINDING = "path_finding"
    SUBGRAPH_EXTRACTION = "subgraph_extraction"
    ANALYTICS = "analytics"
    SIMILARITY_SEARCH = "similarity_search"


class CacheLevel(Enum):
    """캐시 레벨 정의"""
    L1_MEMORY = "l1_memory"      # 인메모리 캐시 (가장 빠름)
    L2_REDIS = "l2_redis"        # Redis 분산 캐시
    L3_DATABASE = "l3_database"  # DB 쿼리 결과 캐시


@dataclass
class QueryPlan:
    """쿼리 실행 계획"""
    query_id: str
    query_type: QueryType
    estimated_cost: float
    execution_steps: List[str]
    cache_strategy: CacheLevel
    parallel_execution: bool = False
    index_hints: List[str] = field(default_factory=list)
    optimization_flags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """쿼리 결과"""
    data: Any
    execution_time: float
    cache_hit: bool
    cache_level: Optional[CacheLevel]
    query_plan: QueryPlan
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    total_queries: int = 0
    cache_hits: int = 0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    error_rate: float = 0.0
    throughput_qps: float = 0.0
    
    def cache_hit_rate(self) -> float:
        return (self.cache_hits / self.total_queries * 100) if self.total_queries > 0 else 0.0


class OptimizedKGQueryEngine:
    """최적화된 지식 그래프 쿼리 엔진"""
    
    def __init__(
        self, 
        db: Session,
        redis_client: Optional[redis.Redis] = None,
        enable_caching: bool = True,
        max_workers: int = 4
    ):
        self.db = db
        self.redis_client = redis_client
        self.enable_caching = enable_caching
        self.max_workers = max_workers
        
        # 다층 캐시 시스템
        self.l1_cache = LRUCache(maxsize=1000)  # 메모리 캐시
        self.l2_cache_ttl = 3600  # Redis 캐시 TTL (1시간)
        
        # 성능 메트릭
        self.metrics = PerformanceMetrics()
        self.query_history: List[Tuple[str, float]] = []
        
        # 쿼리 최적화기
        self.query_optimizer = QueryOptimizer()
        
        # 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info("Optimized KG Query Engine initialized")
    
    async def execute_query(
        self,
        query_type: QueryType,
        parameters: Dict[str, Any],
        kg_id: str,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> QueryResult:
        """최적화된 쿼리 실행"""
        
        start_time = time.time()
        query_id = self._generate_query_id(query_type, parameters, kg_id)
        
        try:
            # 1. 쿼리 계획 생성
            query_plan = await self.query_optimizer.create_plan(
                query_type, parameters, kg_id
            )
            
            # 2. 캐시 확인 (force_refresh가 아닌 경우)
            if use_cache and not force_refresh:
                cached_result = await self._get_from_cache(query_id, query_plan.cache_strategy)
                if cached_result:
                    execution_time = time.time() - start_time
                    self._update_metrics(execution_time, cache_hit=True)
                    
                    return QueryResult(
                        data=cached_result,
                        execution_time=execution_time,
                        cache_hit=True,
                        cache_level=query_plan.cache_strategy,
                        query_plan=query_plan
                    )
            
            # 3. 쿼리 실행
            if query_plan.parallel_execution:
                result_data = await self._execute_parallel_query(query_plan, parameters, kg_id)
            else:
                result_data = await self._execute_sequential_query(query_plan, parameters, kg_id)
            
            # 4. 결과 캐싱
            if use_cache:
                await self._store_in_cache(query_id, result_data, query_plan.cache_strategy)
            
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, cache_hit=False)
            
            return QueryResult(
                data=result_data,
                execution_time=execution_time,
                cache_hit=False,
                cache_level=None,
                query_plan=query_plan,
                metadata={
                    "query_id": query_id,
                    "optimization_applied": True
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e}", exc_info=True)
            self._update_metrics(execution_time, cache_hit=False, error=True)
            raise
    
    async def batch_execute_queries(
        self,
        queries: List[Tuple[QueryType, Dict[str, Any], str]],
        max_concurrent: int = 10
    ) -> List[QueryResult]:
        """배치 쿼리 실행 (병렬 처리)"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single(query_info):
            async with semaphore:
                query_type, parameters, kg_id = query_info
                return await self.execute_query(query_type, parameters, kg_id)
        
        tasks = [execute_single(query_info) for query_info in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch query failed: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def search_entities(
        self,
        kg_id: str,
        query: str,
        entity_types: Optional[List[EntityType]] = None,
        limit: int = 50,
        similarity_threshold: float = 0.7
    ) -> QueryResult:
        """엔티티 검색 (최적화된)"""
        
        parameters = {
            "query": query,
            "entity_types": entity_types,
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }
        
        return await self.execute_query(
            QueryType.ENTITY_SEARCH,
            parameters,
            kg_id
        )
    
    async def find_shortest_path(
        self,
        kg_id: str,
        source_entity_id: str,
        target_entity_id: str,
        max_depth: int = 6,
        relation_types: Optional[List[RelationType]] = None
    ) -> QueryResult:
        """최단 경로 찾기 (최적화된)"""
        
        parameters = {
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "max_depth": max_depth,
            "relation_types": relation_types
        }
        
        return await self.execute_query(
            QueryType.PATH_FINDING,
            parameters,
            kg_id
        )
    
    async def extract_subgraph(
        self,
        kg_id: str,
        center_entity_id: str,
        radius: int = 2,
        max_nodes: int = 100,
        include_relation_types: Optional[List[RelationType]] = None
    ) -> QueryResult:
        """서브그래프 추출 (최적화된)"""
        
        parameters = {
            "center_entity_id": center_entity_id,
            "radius": radius,
            "max_nodes": max_nodes,
            "include_relation_types": include_relation_types
        }
        
        return await self.execute_query(
            QueryType.SUBGRAPH_EXTRACTION,
            parameters,
            kg_id
        )
    
    async def compute_graph_analytics(
        self,
        kg_id: str,
        metrics: List[str] = None
    ) -> QueryResult:
        """그래프 분석 메트릭 계산"""
        
        if metrics is None:
            metrics = ["centrality", "clustering", "communities", "density"]
        
        parameters = {"metrics": metrics}
        
        return await self.execute_query(
            QueryType.ANALYTICS,
            parameters,
            kg_id
        )
    
    # ========================================================================
    # 내부 메서드들
    # ========================================================================
    
    def _generate_query_id(
        self, 
        query_type: QueryType, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> str:
        """쿼리 ID 생성 (캐시 키로 사용)"""
        
        # 파라미터를 정규화하여 일관된 해시 생성
        normalized_params = json.dumps(parameters, sort_keys=True, default=str)
        query_string = f"{query_type.value}:{kg_id}:{normalized_params}"
        
        return hashlib.md5(query_string.encode()).hexdigest()
    
    async def _get_from_cache(
        self, 
        query_id: str, 
        cache_level: CacheLevel
    ) -> Optional[Any]:
        """캐시에서 결과 조회"""
        
        if not self.enable_caching:
            return None
        
        # L1 캐시 (메모리) 확인
        if cache_level in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]:
            if query_id in self.l1_cache:
                logger.debug(f"L1 cache hit for query: {query_id}")
                return self.l1_cache[query_id]
        
        # L2 캐시 (Redis) 확인
        if cache_level == CacheLevel.L2_REDIS and self.redis_client:
            try:
                cached_data = self.redis_client.get(f"kg_query:{query_id}")
                if cached_data:
                    result = json.loads(cached_data)
                    # L1 캐시에도 저장
                    self.l1_cache[query_id] = result
                    logger.debug(f"L2 cache hit for query: {query_id}")
                    return result
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
        
        return None
    
    async def _store_in_cache(
        self, 
        query_id: str, 
        data: Any, 
        cache_level: CacheLevel
    ):
        """캐시에 결과 저장"""
        
        if not self.enable_caching:
            return
        
        # L1 캐시 (메모리) 저장
        if cache_level in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]:
            self.l1_cache[query_id] = data
        
        # L2 캐시 (Redis) 저장
        if cache_level == CacheLevel.L2_REDIS and self.redis_client:
            try:
                serialized_data = json.dumps(data, default=str)
                self.redis_client.setex(
                    f"kg_query:{query_id}",
                    self.l2_cache_ttl,
                    serialized_data
                )
                logger.debug(f"Stored in L2 cache: {query_id}")
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
    
    async def _execute_parallel_query(
        self, 
        query_plan: QueryPlan, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> Any:
        """병렬 쿼리 실행"""
        
        if query_plan.query_type == QueryType.SUBGRAPH_EXTRACTION:
            return await self._parallel_subgraph_extraction(parameters, kg_id)
        elif query_plan.query_type == QueryType.ANALYTICS:
            return await self._parallel_analytics_computation(parameters, kg_id)
        else:
            # 기본적으로 순차 실행으로 폴백
            return await self._execute_sequential_query(query_plan, parameters, kg_id)
    
    async def _execute_sequential_query(
        self, 
        query_plan: QueryPlan, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> Any:
        """순차 쿼리 실행"""
        
        if query_plan.query_type == QueryType.ENTITY_SEARCH:
            return await self._execute_entity_search(parameters, kg_id)
        elif query_plan.query_type == QueryType.PATH_FINDING:
            return await self._execute_path_finding(parameters, kg_id)
        elif query_plan.query_type == QueryType.SUBGRAPH_EXTRACTION:
            return await self._execute_subgraph_extraction(parameters, kg_id)
        elif query_plan.query_type == QueryType.ANALYTICS:
            return await self._execute_analytics(parameters, kg_id)
        else:
            raise ValueError(f"Unsupported query type: {query_plan.query_type}")
    
    async def _execute_entity_search(
        self, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> List[Dict[str, Any]]:
        """엔티티 검색 실행"""
        
        query = parameters["query"]
        entity_types = parameters.get("entity_types", [])
        limit = parameters.get("limit", 50)
        similarity_threshold = parameters.get("similarity_threshold", 0.7)
        
        # 최적화된 SQL 쿼리
        sql_query = text("""
            SELECT 
                e.id,
                e.name,
                e.entity_type,
                e.properties,
                e.confidence_score,
                ts_rank(to_tsvector('english', e.name || ' ' || COALESCE(e.description, '')), 
                        plainto_tsquery('english', :query)) as relevance_score
            FROM kg_entities e
            WHERE e.knowledge_graph_id = :kg_id
                AND (:entity_types_empty OR e.entity_type = ANY(:entity_types))
                AND (
                    e.name ILIKE :query_pattern 
                    OR to_tsvector('english', e.name || ' ' || COALESCE(e.description, '')) 
                       @@ plainto_tsquery('english', :query)
                )
                AND e.confidence_score >= :similarity_threshold
            ORDER BY relevance_score DESC, e.confidence_score DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(sql_query, {
            "kg_id": kg_id,
            "query": query,
            "query_pattern": f"%{query}%",
            "entity_types": entity_types if entity_types else [],
            "entity_types_empty": len(entity_types) == 0,
            "similarity_threshold": similarity_threshold,
            "limit": limit
        })
        
        return [dict(row) for row in result.fetchall()]
    
    async def _execute_path_finding(
        self, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> Dict[str, Any]:
        """최단 경로 찾기 실행 (BFS 알고리즘)"""
        
        source_id = parameters["source_entity_id"]
        target_id = parameters["target_entity_id"]
        max_depth = parameters.get("max_depth", 6)
        relation_types = parameters.get("relation_types", [])
        
        # BFS를 사용한 최단 경로 찾기
        visited = set()
        queue = [(source_id, [source_id], 0)]
        
        while queue:
            current_id, path, depth = queue.pop(0)
            
            if current_id == target_id:
                return {
                    "path": path,
                    "length": len(path) - 1,
                    "depth": depth
                }
            
            if depth >= max_depth or current_id in visited:
                continue
            
            visited.add(current_id)
            
            # 인접 노드 찾기
            neighbors_query = text("""
                SELECT DISTINCT 
                    CASE 
                        WHEN r.source_entity_id = :current_id THEN r.target_entity_id
                        ELSE r.source_entity_id
                    END as neighbor_id
                FROM kg_relationships r
                WHERE (r.source_entity_id = :current_id OR r.target_entity_id = :current_id)
                    AND (:relation_types_empty OR r.relation_type = ANY(:relation_types))
                    AND r.knowledge_graph_id = :kg_id
            """)
            
            neighbors = self.db.execute(neighbors_query, {
                "current_id": current_id,
                "kg_id": kg_id,
                "relation_types": relation_types if relation_types else [],
                "relation_types_empty": len(relation_types) == 0
            }).fetchall()
            
            for neighbor in neighbors:
                neighbor_id = neighbor.neighbor_id
                if neighbor_id not in visited:
                    queue.append((neighbor_id, path + [neighbor_id], depth + 1))
        
        return {"path": None, "length": -1, "depth": -1}
    
    async def _parallel_subgraph_extraction(
        self, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> Dict[str, Any]:
        """병렬 서브그래프 추출"""
        
        center_entity_id = parameters["center_entity_id"]
        radius = parameters.get("radius", 2)
        max_nodes = parameters.get("max_nodes", 100)
        
        # 병렬로 각 레벨의 노드들을 가져옴
        tasks = []
        for level in range(1, radius + 1):
            task = asyncio.create_task(
                self._get_nodes_at_distance(kg_id, center_entity_id, level)
            )
            tasks.append(task)
        
        level_results = await asyncio.gather(*tasks)
        
        # 결과 병합
        all_nodes = {center_entity_id}
        for nodes in level_results:
            all_nodes.update(nodes)
            if len(all_nodes) >= max_nodes:
                break
        
        # 노드 간 관계 조회
        relationships = await self._get_relationships_between_nodes(
            kg_id, list(all_nodes)
        )
        
        return {
            "nodes": list(all_nodes)[:max_nodes],
            "relationships": relationships,
            "center_entity": center_entity_id,
            "radius": radius
        }
    
    def _update_metrics(
        self, 
        execution_time: float, 
        cache_hit: bool = False, 
        error: bool = False
    ):
        """성능 메트릭 업데이트"""
        
        self.metrics.total_queries += 1
        if cache_hit:
            self.metrics.cache_hits += 1
        if error:
            self.metrics.error_rate = (
                (self.metrics.error_rate * (self.metrics.total_queries - 1) + 1) 
                / self.metrics.total_queries
            )
        
        # 응답 시간 업데이트
        self.query_history.append((datetime.now().isoformat(), execution_time))
        
        # 최근 100개 쿼리만 유지
        if len(self.query_history) > 100:
            self.query_history = self.query_history[-100:]
        
        # 평균 응답 시간 계산
        recent_times = [t for _, t in self.query_history[-50:]]
        self.metrics.avg_response_time = sum(recent_times) / len(recent_times)
        
        # P95 응답 시간 계산
        sorted_times = sorted(recent_times)
        p95_index = int(len(sorted_times) * 0.95)
        self.metrics.p95_response_time = sorted_times[p95_index] if sorted_times else 0.0
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭 조회"""
        return self.metrics
    
    async def warm_up_cache(self, kg_id: str, common_queries: List[Dict[str, Any]]):
        """캐시 워밍업 (자주 사용되는 쿼리들을 미리 실행)"""
        
        logger.info(f"Warming up cache for KG {kg_id} with {len(common_queries)} queries")
        
        for query_info in common_queries:
            try:
                await self.execute_query(
                    QueryType(query_info["type"]),
                    query_info["parameters"],
                    kg_id,
                    use_cache=True
                )
            except Exception as e:
                logger.warning(f"Cache warmup failed for query: {e}")
        
        logger.info("Cache warmup completed")


class QueryOptimizer:
    """쿼리 최적화기"""
    
    def __init__(self):
        self.optimization_rules = {
            QueryType.ENTITY_SEARCH: self._optimize_entity_search,
            QueryType.PATH_FINDING: self._optimize_path_finding,
            QueryType.SUBGRAPH_EXTRACTION: self._optimize_subgraph_extraction,
            QueryType.ANALYTICS: self._optimize_analytics,
        }
    
    async def create_plan(
        self, 
        query_type: QueryType, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> QueryPlan:
        """쿼리 실행 계획 생성"""
        
        optimizer_func = self.optimization_rules.get(query_type)
        if optimizer_func:
            return await optimizer_func(parameters, kg_id)
        
        # 기본 계획
        return QueryPlan(
            query_id=f"{query_type.value}_{kg_id}",
            query_type=query_type,
            estimated_cost=1.0,
            execution_steps=["execute_query"],
            cache_strategy=CacheLevel.L1_MEMORY
        )
    
    async def _optimize_entity_search(
        self, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> QueryPlan:
        """엔티티 검색 최적화"""
        
        limit = parameters.get("limit", 50)
        entity_types = parameters.get("entity_types", [])
        
        # 비용 추정
        estimated_cost = 0.5 if entity_types else 1.0
        estimated_cost *= min(limit / 50, 2.0)
        
        return QueryPlan(
            query_id=f"entity_search_{kg_id}",
            query_type=QueryType.ENTITY_SEARCH,
            estimated_cost=estimated_cost,
            execution_steps=["build_search_query", "execute_with_index"],
            cache_strategy=CacheLevel.L2_REDIS if limit <= 100 else CacheLevel.L1_MEMORY,
            index_hints=["idx_kg_entities_name", "idx_kg_entities_type"]
        )
    
    async def _optimize_path_finding(
        self, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> QueryPlan:
        """경로 찾기 최적화"""
        
        max_depth = parameters.get("max_depth", 6)
        
        # 깊이가 클수록 비용 증가
        estimated_cost = min(max_depth / 3, 5.0)
        
        return QueryPlan(
            query_id=f"path_finding_{kg_id}",
            query_type=QueryType.PATH_FINDING,
            estimated_cost=estimated_cost,
            execution_steps=["bidirectional_bfs", "path_reconstruction"],
            cache_strategy=CacheLevel.L2_REDIS,
            parallel_execution=False,  # BFS는 순차적으로 실행
            index_hints=["idx_kg_relationships_source", "idx_kg_relationships_target"]
        )
    
    async def _optimize_subgraph_extraction(
        self, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> QueryPlan:
        """서브그래프 추출 최적화"""
        
        radius = parameters.get("radius", 2)
        max_nodes = parameters.get("max_nodes", 100)
        
        # 반경과 노드 수에 따른 비용 추정
        estimated_cost = radius * (max_nodes / 100)
        
        return QueryPlan(
            query_id=f"subgraph_{kg_id}",
            query_type=QueryType.SUBGRAPH_EXTRACTION,
            estimated_cost=estimated_cost,
            execution_steps=["parallel_level_expansion", "relationship_gathering"],
            cache_strategy=CacheLevel.L1_MEMORY,
            parallel_execution=True,  # 레벨별 병렬 처리 가능
            optimization_flags={"use_parallel_expansion": True}
        )
    
    async def _optimize_analytics(
        self, 
        parameters: Dict[str, Any], 
        kg_id: str
    ) -> QueryPlan:
        """분석 쿼리 최적화"""
        
        metrics = parameters.get("metrics", [])
        
        # 메트릭 수에 따른 비용 추정
        estimated_cost = len(metrics) * 2.0
        
        return QueryPlan(
            query_id=f"analytics_{kg_id}",
            query_type=QueryType.ANALYTICS,
            estimated_cost=estimated_cost,
            execution_steps=["parallel_metric_computation", "result_aggregation"],
            cache_strategy=CacheLevel.L2_REDIS,
            parallel_execution=True,
            optimization_flags={"cache_intermediate_results": True}
        )