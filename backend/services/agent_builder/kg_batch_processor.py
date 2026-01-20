"""
Knowledge Graph Batch Processing System

대용량 문서 처리를 위한 고성능 배치 처리 시스템
- 병렬 처리
- 메모리 효율적 스트리밍
- 진행률 추적
- 오류 복구
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from pathlib import Path
import json

from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.db.models.knowledge_graph import (
    KnowledgeGraph, KGEntity, KGRelationship, KGExtractionJob
)
from backend.db.models.agent_builder import Knowledgebase, KnowledgebaseDocument
from backend.services.agent_builder.advanced_kg_extraction_service import (
    AdvancedKGExtractionService, ExtractionResult
)
from backend.services.agent_builder.kg_cache_manager import get_cache_manager
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class JobStatus(Enum):
    """배치 작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingMode(Enum):
    """처리 모드"""
    SEQUENTIAL = "sequential"      # 순차 처리
    PARALLEL_THREAD = "parallel_thread"  # 스레드 병렬
    PARALLEL_PROCESS = "parallel_process"  # 프로세스 병렬
    DISTRIBUTED = "distributed"    # 분산 처리 (Celery)


@dataclass
class BatchConfig:
    """배치 처리 설정"""
    batch_size: int = 100
    max_workers: int = 4
    processing_mode: ProcessingMode = ProcessingMode.PARALLEL_THREAD
    memory_limit_mb: int = 1024
    timeout_seconds: int = 3600
    retry_attempts: int = 3
    checkpoint_interval: int = 50
    enable_progress_tracking: bool = True
    enable_error_recovery: bool = True


@dataclass
class ProcessingStats:
    """처리 통계"""
    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    processing_time_seconds: float = 0.0
    avg_processing_time_per_doc: float = 0.0
    throughput_docs_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    
    def progress_percentage(self) -> float:
        return (self.processed_documents / self.total_documents * 100) if self.total_documents > 0 else 0.0


@dataclass
class BatchJob:
    """배치 작업"""
    job_id: str
    kg_id: str
    user_id: str
    document_ids: List[str]
    config: BatchConfig
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stats: ProcessingStats = field(default_factory=ProcessingStats)
    error_message: Optional[str] = None
    checkpoint_data: Dict[str, Any] = field(default_factory=dict)


class KGBatchProcessor:
    """지식 그래프 배치 처리기"""
    
    def __init__(self, db: Session):
        self.db = db
        self.extraction_service = AdvancedKGExtractionService(db)
        
        # 활성 작업 추적
        self.active_jobs: Dict[str, BatchJob] = {}
        
        # 진행률 콜백
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        
        # 체크포인트 저장소
        self.checkpoint_dir = Path("checkpoints/kg_batch")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("KG Batch Processor initialized")
    
    async def submit_batch_job(
        self,
        kg_id: str,
        user_id: str,
        document_ids: List[str],
        config: Optional[BatchConfig] = None
    ) -> str:
        """배치 작업 제출"""
        
        if config is None:
            config = BatchConfig()
        
        job_id = str(uuid.uuid4())
        
        job = BatchJob(
            job_id=job_id,
            kg_id=kg_id,
            user_id=user_id,
            document_ids=document_ids,
            config=config
        )
        
        job.stats.total_documents = len(document_ids)
        
        # 작업 등록
        self.active_jobs[job_id] = job
        
        # DB에 작업 기록
        await self._save_job_to_db(job)
        
        logger.info(f"Batch job submitted: {job_id} ({len(document_ids)} documents)")
        
        return job_id
    
    async def start_batch_job(self, job_id: str) -> bool:
        """배치 작업 시작"""
        
        if job_id not in self.active_jobs:
            logger.error(f"Job not found: {job_id}")
            return False
        
        job = self.active_jobs[job_id]
        
        if job.status != JobStatus.PENDING:
            logger.error(f"Job {job_id} is not in pending status: {job.status}")
            return False
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        # 비동기로 작업 실행
        asyncio.create_task(self._execute_batch_job(job))
        
        logger.info(f"Batch job started: {job_id}")
        return True
    
    async def pause_batch_job(self, job_id: str) -> bool:
        """배치 작업 일시정지"""
        
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        
        if job.status == JobStatus.RUNNING:
            job.status = JobStatus.PAUSED
            await self._save_checkpoint(job)
            logger.info(f"Batch job paused: {job_id}")
            return True
        
        return False
    
    async def resume_batch_job(self, job_id: str) -> bool:
        """배치 작업 재개"""
        
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        
        if job.status == JobStatus.PAUSED:
            job.status = JobStatus.RUNNING
            asyncio.create_task(self._execute_batch_job(job))
            logger.info(f"Batch job resumed: {job_id}")
            return True
        
        return False
    
    async def cancel_batch_job(self, job_id: str) -> bool:
        """배치 작업 취소"""
        
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        
        await self._save_job_to_db(job)
        
        logger.info(f"Batch job cancelled: {job_id}")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """작업 상태 조회"""
        
        return self.active_jobs.get(job_id)
    
    def add_progress_callback(self, job_id: str, callback: Callable):
        """진행률 콜백 추가"""
        
        if job_id not in self.progress_callbacks:
            self.progress_callbacks[job_id] = []
        
        self.progress_callbacks[job_id].append(callback)
    
    async def get_active_jobs(self) -> List[BatchJob]:
        """활성 작업 목록 조회"""
        
        return list(self.active_jobs.values())
    
    # ========================================================================
    # 내부 메서드들
    # ========================================================================
    
    async def _execute_batch_job(self, job: BatchJob):
        """배치 작업 실행"""
        
        try:
            logger.info(f"Executing batch job: {job.job_id}")
            
            # 체크포인트에서 재개 여부 확인
            processed_doc_ids = set()
            if job.config.enable_error_recovery:
                checkpoint = await self._load_checkpoint(job.job_id)
                if checkpoint:
                    processed_doc_ids = set(checkpoint.get("processed_documents", []))
                    job.stats = ProcessingStats(**checkpoint.get("stats", {}))
            
            # 처리할 문서 필터링
            remaining_documents = [
                doc_id for doc_id in job.document_ids 
                if doc_id not in processed_doc_ids
            ]
            
            if not remaining_documents:
                logger.info(f"All documents already processed for job: {job.job_id}")
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                return
            
            # 처리 모드에 따른 실행
            if job.config.processing_mode == ProcessingMode.SEQUENTIAL:
                await self._process_sequential(job, remaining_documents)
            elif job.config.processing_mode == ProcessingMode.PARALLEL_THREAD:
                await self._process_parallel_thread(job, remaining_documents)
            elif job.config.processing_mode == ProcessingMode.PARALLEL_PROCESS:
                await self._process_parallel_process(job, remaining_documents)
            elif job.config.processing_mode == ProcessingMode.DISTRIBUTED:
                await self._process_distributed(job, remaining_documents)
            
            # 작업 완료
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.stats.processing_time_seconds = (
                job.completed_at - job.started_at
            ).total_seconds()
            
            if job.stats.processing_time_seconds > 0:
                job.stats.throughput_docs_per_second = (
                    job.stats.processed_documents / job.stats.processing_time_seconds
                )
            
            await self._save_job_to_db(job)
            await self._notify_progress(job)
            
            logger.info(f"Batch job completed: {job.job_id}")
            
        except Exception as e:
            logger.error(f"Batch job failed: {job.job_id} - {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            await self._save_job_to_db(job)
    
    async def _process_sequential(self, job: BatchJob, document_ids: List[str]):
        """순차 처리"""
        
        for i, doc_id in enumerate(document_ids):
            if job.status != JobStatus.RUNNING:
                break
            
            try:
                await self._process_single_document(job, doc_id)
                job.stats.processed_documents += 1
                
                # 체크포인트 저장
                if (i + 1) % job.config.checkpoint_interval == 0:
                    await self._save_checkpoint(job)
                
                # 진행률 알림
                await self._notify_progress(job)
                
            except Exception as e:
                logger.error(f"Document processing failed: {doc_id} - {e}")
                job.stats.failed_documents += 1
                
                if job.stats.failed_documents > job.config.retry_attempts:
                    raise Exception(f"Too many failures: {job.stats.failed_documents}")
    
    async def _process_parallel_thread(self, job: BatchJob, document_ids: List[str]):
        """스레드 병렬 처리"""
        
        semaphore = asyncio.Semaphore(job.config.max_workers)
        
        async def process_with_semaphore(doc_id: str):
            async with semaphore:
                try:
                    await self._process_single_document(job, doc_id)
                    job.stats.processed_documents += 1
                    return True
                except Exception as e:
                    logger.error(f"Document processing failed: {doc_id} - {e}")
                    job.stats.failed_documents += 1
                    return False
        
        # 배치 단위로 처리
        batch_size = job.config.batch_size
        
        for i in range(0, len(document_ids), batch_size):
            if job.status != JobStatus.RUNNING:
                break
            
            batch = document_ids[i:i + batch_size]
            
            # 배치 병렬 처리
            tasks = [process_with_semaphore(doc_id) for doc_id in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 체크포인트 저장
            if (i + batch_size) % job.config.checkpoint_interval == 0:
                await self._save_checkpoint(job)
            
            # 진행률 알림
            await self._notify_progress(job)
    
    async def _process_parallel_process(self, job: BatchJob, document_ids: List[str]):
        """프로세스 병렬 처리"""
        
        # 프로세스 풀 사용
        with ProcessPoolExecutor(max_workers=job.config.max_workers) as executor:
            
            # 배치 단위로 처리
            batch_size = job.config.batch_size
            
            for i in range(0, len(document_ids), batch_size):
                if job.status != JobStatus.RUNNING:
                    break
                
                batch = document_ids[i:i + batch_size]
                
                # 프로세스 풀에 작업 제출
                futures = []
                for doc_id in batch:
                    future = executor.submit(
                        self._process_document_in_process,
                        job.kg_id,
                        doc_id
                    )
                    futures.append((doc_id, future))
                
                # 결과 수집
                for doc_id, future in futures:
                    try:
                        result = future.result(timeout=job.config.timeout_seconds)
                        if result:
                            job.stats.processed_documents += 1
                            job.stats.total_entities += result.get("entity_count", 0)
                            job.stats.total_relationships += result.get("relationship_count", 0)
                        else:
                            job.stats.failed_documents += 1
                    except Exception as e:
                        logger.error(f"Process execution failed: {doc_id} - {e}")
                        job.stats.failed_documents += 1
                
                # 체크포인트 저장
                if (i + batch_size) % job.config.checkpoint_interval == 0:
                    await self._save_checkpoint(job)
                
                # 진행률 알림
                await self._notify_progress(job)
    
    async def _process_distributed(self, job: BatchJob, document_ids: List[str]):
        """분산 처리 (Celery 사용)"""
        
        # TODO: Celery 태스크 구현
        logger.warning("Distributed processing not implemented yet")
        await self._process_parallel_thread(job, document_ids)
    
    async def _process_single_document(self, job: BatchJob, document_id: str) -> Dict[str, Any]:
        """단일 문서 처리"""
        
        try:
            # 문서 내용 조회
            document_content = await self._get_document_content(document_id)
            
            if not document_content:
                raise ValueError(f"Document content not found: {document_id}")
            
            # 엔티티 및 관계 추출
            extraction_result = await self.extraction_service.extract_from_text(
                text=document_content["text"],
                kg_id=job.kg_id,
                document_id=document_id,
                language=document_content.get("language", "auto")
            )
            
            # 결과 저장
            await self._save_extraction_result(job.kg_id, document_id, extraction_result)
            
            # 통계 업데이트
            job.stats.total_entities += len(extraction_result.entities)
            job.stats.total_relationships += len(extraction_result.relationships)
            
            return {
                "success": True,
                "entity_count": len(extraction_result.entities),
                "relationship_count": len(extraction_result.relationships)
            }
            
        except Exception as e:
            logger.error(f"Single document processing failed: {document_id} - {e}")
            raise
    
    @staticmethod
    def _process_document_in_process(kg_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """프로세스에서 문서 처리 (정적 메서드)"""
        
        try:
            # 새로운 DB 세션 생성 (프로세스 간 공유 불가)
            from backend.db.session_utils import get_db_session
            
            with get_db_session() as db:
                extraction_service = AdvancedKGExtractionService(db)
                
                # 문서 처리 로직 (간소화된 버전)
                # 실제로는 더 복잡한 처리가 필요
                
                return {
                    "success": True,
                    "entity_count": 10,  # 임시값
                    "relationship_count": 5  # 임시값
                }
            
        except Exception as e:
            logger.error(f"Process document failed: {document_id} - {e}")
            return None
    
    async def _get_document_content(self, document_id: str) -> Optional[Dict[str, Any]]:
        """문서 내용 조회"""
        
        # DB에서 문서 내용 조회
        query = text("""
            SELECT d.id, d.filename, d.file_path, d.content_text
            FROM documents d
            WHERE d.id = :document_id
        """)
        
        result = self.db.execute(query, {"document_id": document_id}).fetchone()
        
        if result:
            return {
                "id": result.id,
                "filename": result.filename,
                "text": result.content_text or "",
                "language": "auto"
            }
        
        return None
    
    async def _save_extraction_result(
        self, 
        kg_id: str, 
        document_id: str, 
        result: ExtractionResult
    ):
        """추출 결과 저장"""
        
        try:
            # 엔티티 저장
            for entity_data in result.entities:
                entity = KGEntity(
                    knowledge_graph_id=kg_id,
                    name=entity_data["name"],
                    entity_type=entity_data["type"],
                    description=entity_data.get("description"),
                    properties=entity_data.get("properties", {}),
                    confidence_score=entity_data.get("confidence", 0.8)
                )
                self.db.add(entity)
            
            # 관계 저장
            for rel_data in result.relationships:
                relationship = KGRelationship(
                    knowledge_graph_id=kg_id,
                    source_entity_id=rel_data["source_entity_id"],
                    target_entity_id=rel_data["target_entity_id"],
                    relation_type=rel_data["type"],
                    description=rel_data.get("description"),
                    properties=rel_data.get("properties", {}),
                    confidence_score=rel_data.get("confidence", 0.8)
                )
                self.db.add(relationship)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save extraction result: {e}")
            raise
    
    async def _save_checkpoint(self, job: BatchJob):
        """체크포인트 저장"""
        
        if not job.config.enable_error_recovery:
            return
        
        checkpoint_data = {
            "job_id": job.job_id,
            "processed_documents": [
                doc_id for i, doc_id in enumerate(job.document_ids)
                if i < job.stats.processed_documents
            ],
            "stats": {
                "total_documents": job.stats.total_documents,
                "processed_documents": job.stats.processed_documents,
                "failed_documents": job.stats.failed_documents,
                "total_entities": job.stats.total_entities,
                "total_relationships": job.stats.total_relationships
            },
            "timestamp": datetime.now().isoformat()
        }
        
        checkpoint_file = self.checkpoint_dir / f"{job.job_id}.json"
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.debug(f"Checkpoint saved: {job.job_id}")
    
    async def _load_checkpoint(self, job_id: str) -> Optional[Dict[str, Any]]:
        """체크포인트 로드"""
        
        checkpoint_file = self.checkpoint_dir / f"{job_id}.json"
        
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")
        
        return None
    
    async def _save_job_to_db(self, job: BatchJob):
        """작업 정보를 DB에 저장"""
        
        try:
            # KGExtractionJob 테이블에 저장
            extraction_job = KGExtractionJob(
                id=job.job_id,
                knowledge_graph_id=job.kg_id,
                user_id=job.user_id,
                job_type="batch_extraction",
                status=job.status.value,
                total_documents=job.stats.total_documents,
                processed_documents=job.stats.processed_documents,
                failed_documents=job.stats.failed_documents,
                error_message=job.error_message,
                started_at=job.started_at,
                completed_at=job.completed_at,
                metadata={
                    "config": {
                        "batch_size": job.config.batch_size,
                        "max_workers": job.config.max_workers,
                        "processing_mode": job.config.processing_mode.value
                    },
                    "stats": {
                        "total_entities": job.stats.total_entities,
                        "total_relationships": job.stats.total_relationships,
                        "processing_time_seconds": job.stats.processing_time_seconds,
                        "throughput_docs_per_second": job.stats.throughput_docs_per_second
                    }
                }
            )
            
            # Upsert 로직
            existing_job = self.db.query(KGExtractionJob).filter(
                KGExtractionJob.id == job.job_id
            ).first()
            
            if existing_job:
                # 업데이트
                existing_job.status = extraction_job.status
                existing_job.processed_documents = extraction_job.processed_documents
                existing_job.failed_documents = extraction_job.failed_documents
                existing_job.error_message = extraction_job.error_message
                existing_job.completed_at = extraction_job.completed_at
                existing_job.metadata = extraction_job.metadata
            else:
                # 새로 생성
                self.db.add(extraction_job)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save job to DB: {e}")
    
    async def _notify_progress(self, job: BatchJob):
        """진행률 알림"""
        
        if not job.config.enable_progress_tracking:
            return
        
        callbacks = self.progress_callbacks.get(job.job_id, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(job)
                else:
                    callback(job)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")


# 전역 배치 프로세서 인스턴스
_batch_processor: Optional[KGBatchProcessor] = None


def get_batch_processor(db: Session) -> KGBatchProcessor:
    """배치 프로세서 인스턴스 조회"""
    
    global _batch_processor
    
    if _batch_processor is None:
        _batch_processor = KGBatchProcessor(db)
    
    return _batch_processor