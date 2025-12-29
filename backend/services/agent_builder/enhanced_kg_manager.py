"""
Enhanced Knowledge Graph Manager

모든 KG 컴포넌트를 통합 관리하는 고성능 매니저
- 쿼리 엔진 통합
- 캐시 관리
- 배치 처리
- 실시간 처리
- 성능 모니터링
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import json

from sqlalchemy.orm import Session
import redis

from backend.db.models.knowledge_graph import KnowledgeGraph, KGEntity, KGRelationship
from backend.services.agent_builder.optimized_kg_query_engine import (
    OptimizedKGQueryEngine, QueryType, QueryResult
)
from backend.services.agent_builder.kg_cache_manager import (
    KGCacheManager, get_cache_manager
)
from backend.services.agent_builder.kg_batch_processor import (
    KGBatchProcessor, BatchConfig, get_batch_processor
)
from backend.services.agent_builder.kg_realtime_processor import (
    KGRealtimeProcessor, get_realtime_processor, ChangeType, ProcessingPriority
)
from backend.services.agent_builder.advanced_kg_extraction_service import (
    AdvancedKGExtractionService
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class KGPerformanceMetrics:
    """KG 성능 메트릭"""
    # 쿼리 성능
    total_queries: int = 0
    avg_query_time: float = 0.0
    cache_hit_rate: float = 0.0
    
    # 처리 성능
    documents_processed: int = 0
    entities_extracted: int = 0
    relationships_extracted: int = 0
    
    # 실시간 처리
    realtime_events: int = 0
    realtime_processing_time: float = 0.0
    
    # 시스템 리소스
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    # 오류율
    error_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_performance": {
                "total_queries": self.total_queries,
                "avg_query_time_ms": self.avg_query_time * 1000,
                "cache_hit_rate_percent": self.cache_hit_rate
            },
            "processing_performance": {
                "documents_processed": self.documents_processed,
                "entities_extracted": self.entities_extracted,
                "relationships_extracted": self.relationships_extracted
            },
            "realtime_performance": {
                "events_processed": self.realtime_events,
                "avg_processing_time_ms": self.realtime_processing_time * 1000
            },
            "system_resources": {
                "memory_usage_mb": self.memory_usage_mb,
                "cpu_usage_percent": self.cpu_usage_percent
            },
            "reliability": {
                "error_rate_percent": self.error_rate
            }
        }


@dataclass
class KGConfiguration:
    """KG 설정"""
    # 캐시 설정
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    max_cache_size: int = 1000
    
    # 배치 처리 설정
    batch_size: int = 100
    max_workers: int = 4
    
    # 실시간 처리 설정
    enable_realtime: bool = True
    realtime_queue_size: int = 1000
    
    # 성능 설정
    query_timeout_seconds: int = 30
    max_concurrent_queries: int = 50
    
    # 모니터링 설정
    enable_metrics: bool = True
    metrics_collection_interval: int = 60


class EnhancedKGManager:
    """향상된 지식 그래프 매니저"""
    
    def __init__(
        self, 
        db: Session,
        config: Optional[KGConfiguration] = None,
        redis_client: Optional[redis.Redis] = None
    ):
        self.db = db
        self.config = config or KGConfiguration()
        self.redis_client = redis_client
        
        # 핵심 컴포넌트들
        self.query_engine: Optional[OptimizedKGQueryEngine] = None
        self.cache_manager: Optional[KGCacheManager] = None
        self.batch_processor: Optional[KGBatchProcessor] = None
        self.realtime_processor: Optional[KGRealtimeProcessor] = None
        self.extraction_service: Optional[AdvancedKGExtractionService] = None
        
        # 성능 메트릭
        self.metrics = KGPerformanceMetrics()
        self.metrics_history: List[Tuple[datetime, KGPerformanceMetrics]] = []
        
        # 동시성 제어
        self.query_semaphore = asyncio.Semaphore(self.config.max_concurrent_queries)
        
        # 상태 관리
        self.is_initialized = False
        self.is_running = False
        
        logger.info("Enhanced KG Manager created")
    
    async def initialize(self):
        """KG 매니저 초기화"""
        
        if self.is_initialized:
            return
        
        logger.info("Initializing Enhanced KG Manager")
        
        try:
            # 1. 캐시 매니저 초기화
            if self.config.enable_caching:
                self.cache_manager = await get_cache_manager()
                logger.info("Cache manager initialized")
            
            # 2. 쿼리 엔진 초기화
            self.query_engine = OptimizedKGQueryEngine(
                db=self.db,
                redis_client=self.redis_client,
                enable_caching=self.config.enable_caching,
                max_workers=self.config.max_workers
            )
            logger.info("Query engine initialized")
            
            # 3. 배치 처리기 초기화
            self.batch_processor = get_batch_processor(self.db)
            logger.info("Batch processor initialized")
            
            # 4. 실시간 처리기 초기화
            if self.config.enable_realtime:
                self.realtime_processor = await get_realtime_processor(self.db)
                logger.info("Realtime processor initialized")
            
            # 5. 추출 서비스 초기화
            self.extraction_service = AdvancedKGExtractionService(self.db)
            logger.info("Extraction service initialized")
            
            # 6. 메트릭 수집 시작
            if self.config.enable_metrics:
                asyncio.create_task(self._metrics_collector())
                logger.info("Metrics collection started")
            
            self.is_initialized = True
            self.is_running = True
            
            logger.info("Enhanced KG Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"KG Manager initialization failed: {e}", exc_info=True)
            raise
    
    async def shutdown(self):
        """KG 매니저 종료"""
        
        if not self.is_running:
            return
        
        logger.info("Shutting down Enhanced KG Manager")
        
        try:
            # 실시간 처리기 종료
            if self.realtime_processor:
                await self.realtime_processor.stop()
            
            # 기타 정리 작업
            self.is_running = False
            
            logger.info("Enhanced KG Manager shut down successfully")
            
        except Exception as e:
            logger.error(f"KG Manager shutdown failed: {e}", exc_info=True)
    
    # ========================================================================
    # 쿼리 인터페이스
    # ========================================================================
    
    async def search_entities(
        self,
        kg_id: str,
        query: str,
        **kwargs
    ) -> QueryResult:
        """엔티티 검색 (최적화된)"""
        
        await self._ensure_initialized()
        
        async with self.query_semaphore:
            start_time = time.time()
            
            try:
                result = await self.query_engine.search_entities(
                    kg_id=kg_id,
                    query=query,
                    **kwargs
                )
                
                # 메트릭 업데이트
                self._update_query_metrics(time.time() - start_time, True)
                
                return result
                
            except Exception as e:
                self._update_query_metrics(time.time() - start_time, False)
                logger.error(f"Entity search failed: {e}")
                raise
    
    async def find_shortest_path(
        self,
        kg_id: str,
        source_entity_id: str,
        target_entity_id: str,
        **kwargs
    ) -> QueryResult:
        """최단 경로 찾기 (최적화된)"""
        
        await self._ensure_initialized()
        
        async with self.query_semaphore:
            start_time = time.time()
            
            try:
                result = await self.query_engine.find_shortest_path(
                    kg_id=kg_id,
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                    **kwargs
                )
                
                self._update_query_metrics(time.time() - start_time, True)
                return result
                
            except Exception as e:
                self._update_query_metrics(time.time() - start_time, False)
                logger.error(f"Path finding failed: {e}")
                raise
    
    async def extract_subgraph(
        self,
        kg_id: str,
        center_entity_id: str,
        **kwargs
    ) -> QueryResult:
        """서브그래프 추출 (최적화된)"""
        
        await self._ensure_initialized()
        
        async with self.query_semaphore:
            start_time = time.time()
            
            try:
                result = await self.query_engine.extract_subgraph(
                    kg_id=kg_id,
                    center_entity_id=center_entity_id,
                    **kwargs
                )
                
                self._update_query_metrics(time.time() - start_time, True)
                return result
                
            except Exception as e:
                self._update_query_metrics(time.time() - start_time, False)
                logger.error(f"Subgraph extraction failed: {e}")
                raise
    
    async def compute_analytics(
        self,
        kg_id: str,
        metrics: Optional[List[str]] = None
    ) -> QueryResult:
        """그래프 분석 메트릭 계산"""
        
        await self._ensure_initialized()
        
        async with self.query_semaphore:
            start_time = time.time()
            
            try:
                result = await self.query_engine.compute_graph_analytics(
                    kg_id=kg_id,
                    metrics=metrics
                )
                
                self._update_query_metrics(time.time() - start_time, True)
                return result
                
            except Exception as e:
                self._update_query_metrics(time.time() - start_time, False)
                logger.error(f"Analytics computation failed: {e}")
                raise
    
    async def batch_query(
        self,
        queries: List[Tuple[QueryType, Dict[str, Any], str]],
        max_concurrent: int = 10
    ) -> List[QueryResult]:
        """배치 쿼리 실행"""
        
        await self._ensure_initialized()
        
        start_time = time.time()
        
        try:
            results = await self.query_engine.batch_execute_queries(
                queries=queries,
                max_concurrent=max_concurrent
            )
            
            # 배치 쿼리 메트릭 업데이트
            for result in results:
                if result:
                    self._update_query_metrics(result.execution_time, True)
                else:
                    self._update_query_metrics(0.0, False)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch query failed: {e}")
            raise
    
    # ========================================================================
    # 배치 처리 인터페이스
    # ========================================================================
    
    async def submit_batch_extraction(
        self,
        kg_id: str,
        user_id: str,
        document_ids: List[str],
        config: Optional[BatchConfig] = None
    ) -> str:
        """배치 추출 작업 제출"""
        
        await self._ensure_initialized()
        
        job_id = await self.batch_processor.submit_batch_job(
            kg_id=kg_id,
            user_id=user_id,
            document_ids=document_ids,
            config=config
        )
        
        # 자동 시작
        await self.batch_processor.start_batch_job(job_id)
        
        return job_id
    
    async def get_batch_job_status(self, job_id: str):
        """배치 작업 상태 조회"""
        
        await self._ensure_initialized()
        return self.batch_processor.get_job_status(job_id)
    
    async def cancel_batch_job(self, job_id: str) -> bool:
        """배치 작업 취소"""
        
        await self._ensure_initialized()
        return await self.batch_processor.cancel_batch_job(job_id)
    
    # ========================================================================
    # 실시간 처리 인터페이스
    # ========================================================================
    
    async def process_document_change(
        self,
        kg_id: str,
        document_id: str,
        change_type: ChangeType,
        priority: ProcessingPriority = ProcessingPriority.NORMAL
    ):
        """문서 변경 실시간 처리"""
        
        await self._ensure_initialized()
        
        if self.realtime_processor:
            await self.realtime_processor.process_document_change(
                kg_id=kg_id,
                document_id=document_id,
                change_type=change_type,
                priority=priority
            )
    
    async def add_realtime_notification_callback(self, callback):
        """실시간 알림 콜백 추가"""
        
        await self._ensure_initialized()
        
        if self.realtime_processor:
            self.realtime_processor.add_notification_callback(callback)
    
    # ========================================================================
    # 캐시 관리 인터페이스
    # ========================================================================
    
    async def warm_up_cache(self, kg_id: str, common_queries: List[Dict[str, Any]]):
        """캐시 워밍업"""
        
        await self._ensure_initialized()
        
        if self.query_engine:
            await self.query_engine.warm_up_cache(kg_id, common_queries)
    
    async def invalidate_cache(self, kg_id: str):
        """캐시 무효화"""
        
        await self._ensure_initialized()
        
        if self.cache_manager:
            await self.cache_manager.invalidate_by_tags({f"kg:{kg_id}"})
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        
        await self._ensure_initialized()
        
        if self.cache_manager:
            return self.cache_manager.get_stats()
        
        return {}
    
    # ========================================================================
    # 성능 모니터링 인터페이스
    # ========================================================================
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        
        return self.metrics.to_dict()
    
    def get_metrics_history(
        self, 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """메트릭 히스토리 조회"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            {
                "timestamp": timestamp.isoformat(),
                "metrics": metrics.to_dict()
            }
            for timestamp, metrics in self.metrics_history
            if timestamp >= cutoff_time
        ]
    
    async def get_system_health(self) -> Dict[str, Any]:
        """시스템 건강 상태 조회"""
        
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # 각 컴포넌트 상태 확인
        try:
            # 쿼리 엔진 상태
            if self.query_engine:
                query_metrics = self.query_engine.get_performance_metrics()
                health_status["components"]["query_engine"] = {
                    "status": "healthy" if query_metrics.error_rate < 0.05 else "degraded",
                    "cache_hit_rate": query_metrics.cache_hit_rate(),
                    "avg_response_time": query_metrics.avg_response_time
                }
            
            # 배치 처리기 상태
            if self.batch_processor:
                active_jobs = await self.batch_processor.get_active_jobs()
                health_status["components"]["batch_processor"] = {
                    "status": "healthy",
                    "active_jobs": len(active_jobs)
                }
            
            # 실시간 처리기 상태
            if self.realtime_processor:
                rt_stats = self.realtime_processor.get_processing_stats()
                health_status["components"]["realtime_processor"] = {
                    "status": "healthy" if rt_stats["queue_size"] < 1000 else "degraded",
                    "queue_size": rt_stats["queue_size"],
                    "active_workers": rt_stats["active_workers"]
                }
            
            # 캐시 매니저 상태
            if self.cache_manager:
                cache_info = self.cache_manager.get_cache_info()
                health_status["components"]["cache_manager"] = {
                    "status": "healthy",
                    "l1_cache_usage": f"{cache_info['l1_cache_size']}/{cache_info['l1_cache_maxsize']}"
                }
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    # ========================================================================
    # 고급 기능
    # ========================================================================
    
    @asynccontextmanager
    async def transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        
        transaction = self.db.begin()
        try:
            yield self.db
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
        finally:
            transaction.close()
    
    async def optimize_kg(self, kg_id: str) -> Dict[str, Any]:
        """KG 최적화 (인덱스, 중복 제거 등)"""
        
        await self._ensure_initialized()
        
        optimization_results = {
            "duplicates_removed": 0,
            "indexes_created": 0,
            "cache_optimized": False,
            "processing_time": 0.0
        }
        
        start_time = time.time()
        
        try:
            # 1. 중복 엔티티 제거
            duplicates_removed = await self._remove_duplicate_entities(kg_id)
            optimization_results["duplicates_removed"] = duplicates_removed
            
            # 2. 인덱스 최적화
            indexes_created = await self._optimize_indexes(kg_id)
            optimization_results["indexes_created"] = indexes_created
            
            # 3. 캐시 최적화
            if self.cache_manager:
                await self.cache_manager.cleanup_expired()
                optimization_results["cache_optimized"] = True
            
            optimization_results["processing_time"] = time.time() - start_time
            
            logger.info(f"KG optimization completed for {kg_id}: {optimization_results}")
            
        except Exception as e:
            logger.error(f"KG optimization failed for {kg_id}: {e}")
            raise
        
        return optimization_results
    
    async def backup_kg(self, kg_id: str, backup_path: str) -> Dict[str, Any]:
        """KG 백업"""
        
        await self._ensure_initialized()
        
        backup_info = {
            "kg_id": kg_id,
            "backup_path": backup_path,
            "timestamp": datetime.now().isoformat(),
            "entities_count": 0,
            "relationships_count": 0,
            "file_size_mb": 0.0
        }
        
        try:
            # 엔티티 및 관계 데이터 추출
            entities_data = await self._export_entities(kg_id)
            relationships_data = await self._export_relationships(kg_id)
            
            backup_data = {
                "kg_id": kg_id,
                "timestamp": backup_info["timestamp"],
                "entities": entities_data,
                "relationships": relationships_data
            }
            
            # 파일로 저장
            import aiofiles
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write(json.dumps(backup_data, indent=2, default=str))
            
            # 백업 정보 업데이트
            backup_info["entities_count"] = len(entities_data)
            backup_info["relationships_count"] = len(relationships_data)
            
            # 파일 크기 계산
            import os
            backup_info["file_size_mb"] = os.path.getsize(backup_path) / (1024 * 1024)
            
            logger.info(f"KG backup completed: {backup_info}")
            
        except Exception as e:
            logger.error(f"KG backup failed: {e}")
            raise
        
        return backup_info
    
    # ========================================================================
    # 내부 메서드들
    # ========================================================================
    
    async def _ensure_initialized(self):
        """초기화 확인"""
        
        if not self.is_initialized:
            await self.initialize()
    
    def _update_query_metrics(self, execution_time: float, success: bool):
        """쿼리 메트릭 업데이트"""
        
        self.metrics.total_queries += 1
        
        if success:
            # 평균 쿼리 시간 업데이트
            total_time = self.metrics.avg_query_time * (self.metrics.total_queries - 1)
            self.metrics.avg_query_time = (total_time + execution_time) / self.metrics.total_queries
        else:
            # 오류율 업데이트
            error_count = self.metrics.error_rate * (self.metrics.total_queries - 1) + 1
            self.metrics.error_rate = error_count / self.metrics.total_queries
    
    async def _metrics_collector(self):
        """메트릭 수집기"""
        
        while self.is_running:
            try:
                # 현재 메트릭 스냅샷 저장
                current_metrics = KGPerformanceMetrics(
                    total_queries=self.metrics.total_queries,
                    avg_query_time=self.metrics.avg_query_time,
                    cache_hit_rate=self.metrics.cache_hit_rate,
                    documents_processed=self.metrics.documents_processed,
                    entities_extracted=self.metrics.entities_extracted,
                    relationships_extracted=self.metrics.relationships_extracted,
                    realtime_events=self.metrics.realtime_events,
                    realtime_processing_time=self.metrics.realtime_processing_time,
                    memory_usage_mb=self.metrics.memory_usage_mb,
                    cpu_usage_percent=self.metrics.cpu_usage_percent,
                    error_rate=self.metrics.error_rate
                )
                
                self.metrics_history.append((datetime.now(), current_metrics))
                
                # 오래된 메트릭 정리 (24시간 이상)
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.metrics_history = [
                    (timestamp, metrics) 
                    for timestamp, metrics in self.metrics_history
                    if timestamp >= cutoff_time
                ]
                
                # 캐시 히트율 업데이트
                if self.query_engine:
                    engine_metrics = self.query_engine.get_performance_metrics()
                    self.metrics.cache_hit_rate = engine_metrics.cache_hit_rate()
                
                await asyncio.sleep(self.config.metrics_collection_interval)
                
            except Exception as e:
                logger.error(f"Metrics collection failed: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 대기
    
    async def _remove_duplicate_entities(self, kg_id: str) -> int:
        """중복 엔티티 제거"""
        
        # 중복 엔티티 찾기 및 제거 로직
        # 실제 구현에서는 더 정교한 중복 감지 알고리즘 필요
        
        return 0  # 제거된 중복 엔티티 수
    
    async def _optimize_indexes(self, kg_id: str) -> int:
        """인덱스 최적화"""
        
        # 인덱스 생성 및 최적화 로직
        # 실제 구현에서는 쿼리 패턴 분석 후 최적 인덱스 생성
        
        return 0  # 생성된 인덱스 수
    
    async def _export_entities(self, kg_id: str) -> List[Dict[str, Any]]:
        """엔티티 데이터 내보내기"""
        
        entities = self.db.query(KGEntity).filter(
            KGEntity.knowledge_graph_id == kg_id
        ).all()
        
        return [
            {
                "id": str(entity.id),
                "name": entity.name,
                "entity_type": entity.entity_type,
                "description": entity.description,
                "properties": entity.properties,
                "confidence_score": entity.confidence_score,
                "created_at": entity.created_at.isoformat() if entity.created_at else None
            }
            for entity in entities
        ]
    
    async def _export_relationships(self, kg_id: str) -> List[Dict[str, Any]]:
        """관계 데이터 내보내기"""
        
        relationships = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id
        ).all()
        
        return [
            {
                "id": str(rel.id),
                "source_entity_id": str(rel.source_entity_id),
                "target_entity_id": str(rel.target_entity_id),
                "relation_type": rel.relation_type,
                "description": rel.description,
                "properties": rel.properties,
                "confidence_score": rel.confidence_score,
                "created_at": rel.created_at.isoformat() if rel.created_at else None
            }
            for rel in relationships
        ]


# 전역 KG 매니저 인스턴스
_kg_manager: Optional[EnhancedKGManager] = None


async def get_kg_manager(
    db: Session,
    config: Optional[KGConfiguration] = None,
    redis_client: Optional[redis.Redis] = None
) -> EnhancedKGManager:
    """KG 매니저 싱글톤 인스턴스 조회"""
    
    global _kg_manager
    
    if _kg_manager is None:
        _kg_manager = EnhancedKGManager(db, config, redis_client)
        await _kg_manager.initialize()
    
    return _kg_manager


async def shutdown_kg_manager():
    """KG 매니저 종료"""
    
    global _kg_manager
    
    if _kg_manager:
        await _kg_manager.shutdown()
        _kg_manager = None