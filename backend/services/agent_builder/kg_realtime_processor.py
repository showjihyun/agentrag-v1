"""
Knowledge Graph Real-time Processing System

실시간 문서 변경 감지 및 증분 업데이트 시스템
- 문서 변경 감지
- 증분 KG 업데이트
- 실시간 동기화
- WebSocket 알림
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Set, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import text, event
import aiofiles
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.db.models.knowledge_graph import (
    KnowledgeGraph, KGEntity, KGRelationship, KGChangeLog
)
from backend.db.models.agent_builder import Knowledgebase, KnowledgebaseDocument
from backend.services.agent_builder.advanced_kg_extraction_service import AdvancedKGExtractionService
from backend.services.agent_builder.kg_cache_manager import get_cache_manager, invalidate_kg_cache
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class ChangeType(Enum):
    """변경 타입"""
    DOCUMENT_ADDED = "document_added"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    ENTITY_ADDED = "entity_added"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_UPDATED = "relationship_updated"
    RELATIONSHIP_DELETED = "relationship_deleted"


class ProcessingPriority(Enum):
    """처리 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ChangeEvent:
    """변경 이벤트"""
    event_id: str
    kg_id: str
    change_type: ChangeType
    entity_id: Optional[str] = None
    document_id: Optional[str] = None
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """처리 결과"""
    event_id: str
    success: bool
    processing_time: float
    entities_affected: int = 0
    relationships_affected: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentWatcher(FileSystemEventHandler):
    """문서 파일 변경 감지"""
    
    def __init__(self, processor: 'KGRealtimeProcessor'):
        self.processor = processor
        super().__init__()
    
    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(
                self.processor._handle_file_change(event.src_path, ChangeType.DOCUMENT_UPDATED)
            )
    
    def on_created(self, event):
        if not event.is_directory:
            asyncio.create_task(
                self.processor._handle_file_change(event.src_path, ChangeType.DOCUMENT_ADDED)
            )
    
    def on_deleted(self, event):
        if not event.is_directory:
            asyncio.create_task(
                self.processor._handle_file_change(event.src_path, ChangeType.DOCUMENT_DELETED)
            )


class KGRealtimeProcessor:
    """지식 그래프 실시간 처리기"""
    
    def __init__(self, db: Session):
        self.db = db
        self.extraction_service = AdvancedKGExtractionService(db)
        
        # 이벤트 큐
        self.event_queue: asyncio.Queue[ChangeEvent] = asyncio.Queue()
        self.high_priority_queue: asyncio.Queue[ChangeEvent] = asyncio.Queue()
        
        # 처리 워커들
        self.workers: List[asyncio.Task] = []
        self.num_workers = 4
        
        # 파일 시스템 감시
        self.file_observer: Optional[Observer] = None
        self.watched_directories: Set[str] = set()
        
        # 변경 로그
        self.change_logs: List[KGChangeLog] = []
        
        # 실시간 알림 콜백
        self.notification_callbacks: List[Callable] = []
        
        # 처리 통계
        self.processing_stats = {
            "total_events": 0,
            "processed_events": 0,
            "failed_events": 0,
            "avg_processing_time": 0.0
        }
        
        # 중복 처리 방지
        self.processing_locks: Dict[str, asyncio.Lock] = {}
        
        logger.info("KG Realtime Processor initialized")
    
    async def start(self):
        """실시간 처리기 시작"""
        
        logger.info("Starting KG realtime processor")
        
        # 워커 시작
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._event_worker(f"worker-{i}"))
            self.workers.append(worker)
        
        # 고우선순위 워커 시작
        priority_worker = asyncio.create_task(self._priority_event_worker())
        self.workers.append(priority_worker)
        
        # 파일 시스템 감시 시작
        await self._start_file_watching()
        
        # DB 변경 감지 설정
        self._setup_db_change_detection()
        
        logger.info("KG realtime processor started")
    
    async def stop(self):
        """실시간 처리기 중지"""
        
        logger.info("Stopping KG realtime processor")
        
        # 워커 중지
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        # 파일 감시 중지
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
        
        logger.info("KG realtime processor stopped")
    
    async def add_change_event(self, event: ChangeEvent):
        """변경 이벤트 추가"""
        
        # 우선순위에 따라 큐 선택
        if event.priority in [ProcessingPriority.HIGH, ProcessingPriority.CRITICAL]:
            await self.high_priority_queue.put(event)
        else:
            await self.event_queue.put(event)
        
        self.processing_stats["total_events"] += 1
        
        logger.debug(f"Change event added: {event.event_id} ({event.change_type.value})")
    
    async def process_document_change(
        self,
        kg_id: str,
        document_id: str,
        change_type: ChangeType,
        priority: ProcessingPriority = ProcessingPriority.NORMAL
    ):
        """문서 변경 처리"""
        
        event = ChangeEvent(
            event_id=str(uuid.uuid4()),
            kg_id=kg_id,
            change_type=change_type,
            document_id=document_id,
            priority=priority
        )
        
        await self.add_change_event(event)
    
    async def process_entity_change(
        self,
        kg_id: str,
        entity_id: str,
        change_type: ChangeType,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        priority: ProcessingPriority = ProcessingPriority.NORMAL
    ):
        """엔티티 변경 처리"""
        
        event = ChangeEvent(
            event_id=str(uuid.uuid4()),
            kg_id=kg_id,
            change_type=change_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            priority=priority
        )
        
        await self.add_change_event(event)
    
    def add_notification_callback(self, callback: Callable):
        """실시간 알림 콜백 추가"""
        
        self.notification_callbacks.append(callback)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """처리 통계 조회"""
        
        return {
            **self.processing_stats,
            "queue_size": self.event_queue.qsize(),
            "priority_queue_size": self.high_priority_queue.qsize(),
            "active_workers": len([w for w in self.workers if not w.done()])
        }
    
    async def get_recent_changes(
        self, 
        kg_id: str, 
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """최근 변경 내역 조회"""
        
        query = text("""
            SELECT 
                cl.id,
                cl.change_type,
                cl.entity_id,
                cl.old_data,
                cl.new_data,
                cl.created_at,
                cl.metadata
            FROM kg_change_logs cl
            WHERE cl.knowledge_graph_id = :kg_id
                AND (:since IS NULL OR cl.created_at >= :since)
            ORDER BY cl.created_at DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(query, {
            "kg_id": kg_id,
            "since": since,
            "limit": limit
        })
        
        return [dict(row) for row in result.fetchall()]
    
    # ========================================================================
    # 내부 메서드들
    # ========================================================================
    
    async def _event_worker(self, worker_name: str):
        """이벤트 처리 워커"""
        
        logger.info(f"Event worker started: {worker_name}")
        
        while True:
            try:
                # 이벤트 대기
                event = await self.event_queue.get()
                
                # 처리
                result = await self._process_change_event(event)
                
                # 통계 업데이트
                self.processing_stats["processed_events"] += 1
                if not result.success:
                    self.processing_stats["failed_events"] += 1
                
                # 평균 처리 시간 업데이트
                total_time = (
                    self.processing_stats["avg_processing_time"] * 
                    (self.processing_stats["processed_events"] - 1)
                )
                self.processing_stats["avg_processing_time"] = (
                    (total_time + result.processing_time) / 
                    self.processing_stats["processed_events"]
                )
                
                # 알림 전송
                await self._send_notifications(event, result)
                
                # 큐 작업 완료 표시
                self.event_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event worker error ({worker_name}): {e}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.info(f"Event worker stopped: {worker_name}")
    
    async def _priority_event_worker(self):
        """고우선순위 이벤트 처리 워커"""
        
        logger.info("Priority event worker started")
        
        while True:
            try:
                # 고우선순위 이벤트 대기
                event = await self.high_priority_queue.get()
                
                # 즉시 처리
                result = await self._process_change_event(event)
                
                # 알림 전송
                await self._send_notifications(event, result)
                
                # 큐 작업 완료 표시
                self.high_priority_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Priority event worker error: {e}", exc_info=True)
                await asyncio.sleep(0.1)
        
        logger.info("Priority event worker stopped")
    
    async def _process_change_event(self, event: ChangeEvent) -> ProcessingResult:
        """변경 이벤트 처리"""
        
        start_time = time.time()
        
        try:
            # 중복 처리 방지
            lock_key = f"{event.kg_id}:{event.document_id or event.entity_id}"
            
            if lock_key not in self.processing_locks:
                self.processing_locks[lock_key] = asyncio.Lock()
            
            async with self.processing_locks[lock_key]:
                
                if event.change_type == ChangeType.DOCUMENT_ADDED:
                    result = await self._process_document_added(event)
                elif event.change_type == ChangeType.DOCUMENT_UPDATED:
                    result = await self._process_document_updated(event)
                elif event.change_type == ChangeType.DOCUMENT_DELETED:
                    result = await self._process_document_deleted(event)
                elif event.change_type in [
                    ChangeType.ENTITY_ADDED, 
                    ChangeType.ENTITY_UPDATED, 
                    ChangeType.ENTITY_DELETED
                ]:
                    result = await self._process_entity_change(event)
                else:
                    result = ProcessingResult(
                        event_id=event.event_id,
                        success=False,
                        processing_time=0.0,
                        error_message=f"Unsupported change type: {event.change_type}"
                    )
                
                # 변경 로그 저장
                await self._save_change_log(event, result)
                
                # 캐시 무효화
                await self._invalidate_related_cache(event)
                
                processing_time = time.time() - start_time
                result.processing_time = processing_time
                
                logger.debug(
                    f"Change event processed: {event.event_id} "
                    f"({processing_time:.3f}s, success: {result.success})"
                )
                
                return result
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Change event processing failed: {event.event_id} - {e}", exc_info=True)
            
            return ProcessingResult(
                event_id=event.event_id,
                success=False,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def _process_document_added(self, event: ChangeEvent) -> ProcessingResult:
        """문서 추가 처리"""
        
        try:
            # 문서 내용 조회
            document_content = await self._get_document_content(event.document_id)
            
            if not document_content:
                return ProcessingResult(
                    event_id=event.event_id,
                    success=False,
                    processing_time=0.0,
                    error_message="Document content not found"
                )
            
            # 엔티티 및 관계 추출
            extraction_result = await self.extraction_service.extract_from_text(
                text=document_content["text"],
                kg_id=event.kg_id,
                document_id=event.document_id,
                language=document_content.get("language", "auto")
            )
            
            # KG에 추가
            entities_added = await self._add_entities_to_kg(
                event.kg_id, extraction_result.entities
            )
            relationships_added = await self._add_relationships_to_kg(
                event.kg_id, extraction_result.relationships
            )
            
            return ProcessingResult(
                event_id=event.event_id,
                success=True,
                processing_time=0.0,
                entities_affected=entities_added,
                relationships_affected=relationships_added
            )
            
        except Exception as e:
            return ProcessingResult(
                event_id=event.event_id,
                success=False,
                processing_time=0.0,
                error_message=str(e)
            )
    
    async def _process_document_updated(self, event: ChangeEvent) -> ProcessingResult:
        """문서 업데이트 처리"""
        
        try:
            # 기존 엔티티/관계 제거
            await self._remove_document_entities(event.kg_id, event.document_id)
            
            # 새로운 내용으로 재추출
            return await self._process_document_added(event)
            
        except Exception as e:
            return ProcessingResult(
                event_id=event.event_id,
                success=False,
                processing_time=0.0,
                error_message=str(e)
            )
    
    async def _process_document_deleted(self, event: ChangeEvent) -> ProcessingResult:
        """문서 삭제 처리"""
        
        try:
            # 관련 엔티티/관계 제거
            entities_removed = await self._remove_document_entities(event.kg_id, event.document_id)
            relationships_removed = await self._remove_document_relationships(event.kg_id, event.document_id)
            
            return ProcessingResult(
                event_id=event.event_id,
                success=True,
                processing_time=0.0,
                entities_affected=entities_removed,
                relationships_affected=relationships_removed
            )
            
        except Exception as e:
            return ProcessingResult(
                event_id=event.event_id,
                success=False,
                processing_time=0.0,
                error_message=str(e)
            )
    
    async def _process_entity_change(self, event: ChangeEvent) -> ProcessingResult:
        """엔티티 변경 처리"""
        
        try:
            # 관련 관계 업데이트
            relationships_affected = await self._update_entity_relationships(
                event.kg_id, event.entity_id, event.new_data
            )
            
            return ProcessingResult(
                event_id=event.event_id,
                success=True,
                processing_time=0.0,
                entities_affected=1,
                relationships_affected=relationships_affected
            )
            
        except Exception as e:
            return ProcessingResult(
                event_id=event.event_id,
                success=False,
                processing_time=0.0,
                error_message=str(e)
            )
    
    async def _get_document_content(self, document_id: str) -> Optional[Dict[str, Any]]:
        """문서 내용 조회"""
        
        query = text("""
            SELECT d.id, d.filename, d.content_text
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
    
    async def _add_entities_to_kg(self, kg_id: str, entities: List[Dict[str, Any]]) -> int:
        """KG에 엔티티 추가"""
        
        added_count = 0
        
        for entity_data in entities:
            try:
                # 중복 확인
                existing_entity = self.db.query(KGEntity).filter(
                    KGEntity.knowledge_graph_id == kg_id,
                    KGEntity.name == entity_data["name"],
                    KGEntity.entity_type == entity_data["type"]
                ).first()
                
                if not existing_entity:
                    entity = KGEntity(
                        knowledge_graph_id=kg_id,
                        name=entity_data["name"],
                        entity_type=entity_data["type"],
                        description=entity_data.get("description"),
                        properties=entity_data.get("properties", {}),
                        confidence_score=entity_data.get("confidence", 0.8)
                    )
                    self.db.add(entity)
                    added_count += 1
                
            except Exception as e:
                logger.error(f"Failed to add entity: {e}")
        
        self.db.commit()
        return added_count
    
    async def _add_relationships_to_kg(self, kg_id: str, relationships: List[Dict[str, Any]]) -> int:
        """KG에 관계 추가"""
        
        added_count = 0
        
        for rel_data in relationships:
            try:
                # 중복 확인
                existing_rel = self.db.query(KGRelationship).filter(
                    KGRelationship.knowledge_graph_id == kg_id,
                    KGRelationship.source_entity_id == rel_data["source_entity_id"],
                    KGRelationship.target_entity_id == rel_data["target_entity_id"],
                    KGRelationship.relation_type == rel_data["type"]
                ).first()
                
                if not existing_rel:
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
                    added_count += 1
                
            except Exception as e:
                logger.error(f"Failed to add relationship: {e}")
        
        self.db.commit()
        return added_count
    
    async def _remove_document_entities(self, kg_id: str, document_id: str) -> int:
        """문서 관련 엔티티 제거"""
        
        # 문서에서 추출된 엔티티들 조회 및 삭제
        query = text("""
            DELETE FROM kg_entities 
            WHERE knowledge_graph_id = :kg_id 
                AND id IN (
                    SELECT entity_id FROM kg_entity_mentions 
                    WHERE document_id = :document_id
                )
        """)
        
        result = self.db.execute(query, {
            "kg_id": kg_id,
            "document_id": document_id
        })
        
        self.db.commit()
        return result.rowcount
    
    async def _remove_document_relationships(self, kg_id: str, document_id: str) -> int:
        """문서 관련 관계 제거"""
        
        # 문서에서 추출된 관계들 조회 및 삭제
        query = text("""
            DELETE FROM kg_relationships 
            WHERE knowledge_graph_id = :kg_id 
                AND (source_entity_id IN (
                    SELECT entity_id FROM kg_entity_mentions 
                    WHERE document_id = :document_id
                ) OR target_entity_id IN (
                    SELECT entity_id FROM kg_entity_mentions 
                    WHERE document_id = :document_id
                ))
        """)
        
        result = self.db.execute(query, {
            "kg_id": kg_id,
            "document_id": document_id
        })
        
        self.db.commit()
        return result.rowcount
    
    async def _update_entity_relationships(
        self, 
        kg_id: str, 
        entity_id: str, 
        new_data: Optional[Dict[str, Any]]
    ) -> int:
        """엔티티 관련 관계 업데이트"""
        
        # 엔티티 이름이 변경된 경우 관련 관계들의 캐시 무효화
        if new_data and "name" in new_data:
            await invalidate_kg_cache(kg_id)
        
        return 0  # 실제 업데이트된 관계 수 반환
    
    async def _save_change_log(self, event: ChangeEvent, result: ProcessingResult):
        """변경 로그 저장"""
        
        try:
            change_log = KGChangeLog(
                knowledge_graph_id=event.kg_id,
                change_type=event.change_type.value,
                entity_id=event.entity_id,
                old_data=event.old_data,
                new_data=event.new_data,
                success=result.success,
                error_message=result.error_message,
                processing_time_ms=int(result.processing_time * 1000),
                metadata={
                    "event_id": event.event_id,
                    "document_id": event.document_id,
                    "priority": event.priority.value,
                    "entities_affected": result.entities_affected,
                    "relationships_affected": result.relationships_affected
                }
            )
            
            self.db.add(change_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save change log: {e}")
    
    async def _invalidate_related_cache(self, event: ChangeEvent):
        """관련 캐시 무효화"""
        
        try:
            cache_manager = await get_cache_manager()
            
            # KG 전체 캐시 무효화
            await cache_manager.invalidate_by_tags({f"kg:{event.kg_id}"})
            
            # 특정 엔티티/문서 캐시 무효화
            if event.entity_id:
                await cache_manager.invalidate_by_tags({f"entity:{event.entity_id}"})
            
            if event.document_id:
                await cache_manager.invalidate_by_tags({f"document:{event.document_id}"})
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
    
    async def _send_notifications(self, event: ChangeEvent, result: ProcessingResult):
        """실시간 알림 전송"""
        
        notification_data = {
            "event_id": event.event_id,
            "kg_id": event.kg_id,
            "change_type": event.change_type.value,
            "success": result.success,
            "processing_time": result.processing_time,
            "entities_affected": result.entities_affected,
            "relationships_affected": result.relationships_affected,
            "timestamp": event.timestamp.isoformat()
        }
        
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification_data)
                else:
                    callback(notification_data)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
    
    async def _start_file_watching(self):
        """파일 시스템 감시 시작"""
        
        try:
            self.file_observer = Observer()
            
            # 업로드 디렉토리 감시
            upload_dirs = ["uploads"]  # 실제 업로드 디렉토리 경로
            
            for upload_dir in upload_dirs:
                if Path(upload_dir).exists():
                    event_handler = DocumentWatcher(self)
                    self.file_observer.schedule(
                        event_handler, 
                        upload_dir, 
                        recursive=True
                    )
                    self.watched_directories.add(upload_dir)
            
            self.file_observer.start()
            logger.info(f"File watching started for directories: {self.watched_directories}")
            
        except Exception as e:
            logger.error(f"Failed to start file watching: {e}")
    
    async def _handle_file_change(self, file_path: str, change_type: ChangeType):
        """파일 변경 처리"""
        
        try:
            # 파일 경로에서 문서 ID 추출 (실제 구현에서는 더 정교한 매핑 필요)
            # 예: uploads/kb_123/doc_456.pdf -> document_id: doc_456
            
            path_parts = Path(file_path).parts
            if len(path_parts) >= 3 and path_parts[0] == "uploads":
                kb_dir = path_parts[1]  # kb_123
                filename = path_parts[-1]  # doc_456.pdf
                
                # KB ID 추출
                if kb_dir.startswith("kb_"):
                    kg_id = kb_dir[3:]  # 123
                    
                    # 문서 ID 조회 (파일명으로)
                    document_id = await self._get_document_id_by_filename(filename)
                    
                    if document_id:
                        await self.process_document_change(
                            kg_id=kg_id,
                            document_id=document_id,
                            change_type=change_type,
                            priority=ProcessingPriority.HIGH
                        )
            
        except Exception as e:
            logger.error(f"File change handling failed: {file_path} - {e}")
    
    async def _get_document_id_by_filename(self, filename: str) -> Optional[str]:
        """파일명으로 문서 ID 조회"""
        
        query = text("""
            SELECT id FROM documents 
            WHERE filename = :filename OR original_filename = :filename
            LIMIT 1
        """)
        
        result = self.db.execute(query, {"filename": filename}).fetchone()
        
        return str(result.id) if result else None
    
    def _setup_db_change_detection(self):
        """DB 변경 감지 설정"""
        
        # SQLAlchemy 이벤트 리스너 설정
        @event.listens_for(KGEntity, 'after_insert')
        def entity_inserted(mapper, connection, target):
            asyncio.create_task(self.process_entity_change(
                kg_id=target.knowledge_graph_id,
                entity_id=str(target.id),
                change_type=ChangeType.ENTITY_ADDED,
                new_data={"name": target.name, "type": target.entity_type}
            ))
        
        @event.listens_for(KGEntity, 'after_update')
        def entity_updated(mapper, connection, target):
            asyncio.create_task(self.process_entity_change(
                kg_id=target.knowledge_graph_id,
                entity_id=str(target.id),
                change_type=ChangeType.ENTITY_UPDATED,
                new_data={"name": target.name, "type": target.entity_type}
            ))
        
        @event.listens_for(KGEntity, 'after_delete')
        def entity_deleted(mapper, connection, target):
            asyncio.create_task(self.process_entity_change(
                kg_id=target.knowledge_graph_id,
                entity_id=str(target.id),
                change_type=ChangeType.ENTITY_DELETED,
                old_data={"name": target.name, "type": target.entity_type}
            ))


# 전역 실시간 처리기 인스턴스
_realtime_processor: Optional[KGRealtimeProcessor] = None


async def get_realtime_processor(db: Session) -> KGRealtimeProcessor:
    """실시간 처리기 인스턴스 조회"""
    
    global _realtime_processor
    
    if _realtime_processor is None:
        _realtime_processor = KGRealtimeProcessor(db)
        await _realtime_processor.start()
    
    return _realtime_processor


async def shutdown_realtime_processor():
    """실시간 처리기 종료"""
    
    global _realtime_processor
    
    if _realtime_processor:
        await _realtime_processor.stop()
        _realtime_processor = None