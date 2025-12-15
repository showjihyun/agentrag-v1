"""
Batch Video Processing Service
여러 비디오를 동시에 처리하는 배치 처리 시스템
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import logging

from backend.services.multimodal.video_processor import get_video_processor, VideoAnalysisRequest
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class BatchStatus(Enum):
    """배치 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchJobItem:
    """배치 작업 항목"""
    
    def __init__(self, item_id: str, video_data: bytes, analysis_request: VideoAnalysisRequest):
        self.item_id = item_id
        self.video_data = video_data
        self.analysis_request = analysis_request
        self.status = BatchStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.processing_time_seconds: float = 0.0
    
    def start_processing(self):
        """처리 시작"""
        self.status = BatchStatus.PROCESSING
        self.start_time = datetime.now()
    
    def complete_processing(self, result: Dict[str, Any]):
        """처리 완료"""
        self.status = BatchStatus.COMPLETED
        self.result = result
        self.end_time = datetime.now()
        if self.start_time:
            self.processing_time_seconds = (self.end_time - self.start_time).total_seconds()
    
    def fail_processing(self, error: str):
        """처리 실패"""
        self.status = BatchStatus.FAILED
        self.error = error
        self.end_time = datetime.now()
        if self.start_time:
            self.processing_time_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "item_id": self.item_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "processing_time_seconds": self.processing_time_seconds,
            "analysis_config": self.analysis_request.get_analysis_config()
        }

class BatchJob:
    """배치 작업"""
    
    def __init__(self, job_id: str, job_name: str = ""):
        self.job_id = job_id
        self.job_name = job_name or f"Batch Job {job_id[:8]}"
        self.items: List[BatchJobItem] = []
        self.status = BatchStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress_callback: Optional[Callable] = None
        
        # 통계
        self.total_items = 0
        self.completed_items = 0
        self.failed_items = 0
        self.total_processing_time = 0.0
    
    def add_item(self, item: BatchJobItem):
        """작업 항목 추가"""
        self.items.append(item)
        self.total_items = len(self.items)
    
    def get_progress(self) -> Dict[str, Any]:
        """진행률 정보 반환"""
        processed_items = sum(1 for item in self.items if item.status in [BatchStatus.COMPLETED, BatchStatus.FAILED])
        
        return {
            "job_id": self.job_id,
            "job_name": self.job_name,
            "status": self.status.value,
            "total_items": self.total_items,
            "processed_items": processed_items,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "progress_percentage": (processed_items / self.total_items * 100) if self.total_items > 0 else 0,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_remaining_time": self._estimate_remaining_time(),
            "average_processing_time": self.total_processing_time / max(self.completed_items, 1)
        }
    
    def get_results(self) -> List[Dict[str, Any]]:
        """모든 결과 반환"""
        return [item.to_dict() for item in self.items]
    
    def _estimate_remaining_time(self) -> Optional[float]:
        """남은 시간 추정"""
        if self.completed_items == 0:
            return None
        
        avg_time = self.total_processing_time / self.completed_items
        remaining_items = self.total_items - (self.completed_items + self.failed_items)
        
        return avg_time * remaining_items
    
    def update_statistics(self):
        """통계 업데이트"""
        self.completed_items = sum(1 for item in self.items if item.status == BatchStatus.COMPLETED)
        self.failed_items = sum(1 for item in self.items if item.status == BatchStatus.FAILED)
        self.total_processing_time = sum(item.processing_time_seconds for item in self.items if item.processing_time_seconds > 0)

class BatchVideoProcessor:
    """배치 비디오 처리기"""
    
    def __init__(self, max_concurrent_jobs: int = 3):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_history: Dict[str, BatchJob] = {}
        self.video_processor = get_video_processor()
        self._processing_semaphore = asyncio.Semaphore(max_concurrent_jobs)
    
    def create_batch_job(self, job_name: str = "") -> str:
        """새 배치 작업 생성"""
        job_id = str(uuid.uuid4())
        job = BatchJob(job_id, job_name)
        self.active_jobs[job_id] = job
        
        logger.info(f"Created batch job: {job_id}")
        return job_id
    
    def add_video_to_batch(
        self,
        job_id: str,
        video_data: bytes,
        analysis_request: VideoAnalysisRequest,
        item_name: str = ""
    ) -> str:
        """배치에 비디오 추가"""
        if job_id not in self.active_jobs:
            raise ValueError(f"Batch job {job_id} not found")
        
        job = self.active_jobs[job_id]
        if job.status != BatchStatus.PENDING:
            raise ValueError(f"Cannot add items to job in {job.status.value} status")
        
        item_id = str(uuid.uuid4())
        if item_name:
            analysis_request.metadata["item_name"] = item_name
        
        item = BatchJobItem(item_id, video_data, analysis_request)
        job.add_item(item)
        
        logger.info(f"Added video to batch {job_id}: {item_id}")
        return item_id
    
    async def process_batch(
        self,
        job_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """배치 처리 실행"""
        if job_id not in self.active_jobs:
            raise ValueError(f"Batch job {job_id} not found")
        
        job = self.active_jobs[job_id]
        if job.status != BatchStatus.PENDING:
            raise ValueError(f"Job {job_id} is already {job.status.value}")
        
        if len(job.items) == 0:
            raise ValueError(f"No items in batch job {job_id}")
        
        job.status = BatchStatus.PROCESSING
        job.started_at = datetime.now()
        job.progress_callback = progress_callback
        
        logger.info(f"Starting batch processing: {job_id} ({len(job.items)} items)")
        
        try:
            # 병렬 처리 실행
            tasks = []
            for item in job.items:
                task = asyncio.create_task(self._process_item(job, item))
                tasks.append(task)
            
            # 모든 작업 완료 대기
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 최종 상태 업데이트
            job.update_statistics()
            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.now()
            
            # 작업을 히스토리로 이동
            self.job_history[job_id] = job
            del self.active_jobs[job_id]
            
            logger.info(f"Batch processing completed: {job_id}")
            
            return job.get_progress()
            
        except Exception as e:
            job.status = BatchStatus.FAILED
            job.completed_at = datetime.now()
            logger.error(f"Batch processing failed: {job_id} - {str(e)}")
            raise
    
    async def _process_item(self, job: BatchJob, item: BatchJobItem):
        """개별 항목 처리"""
        async with self._processing_semaphore:
            try:
                item.start_processing()
                
                # 비디오 분석 실행
                result = await self.video_processor.analyze_video(
                    request=item.analysis_request,
                    model=item.analysis_request.metadata.get("model", "gemini-1.5-pro"),
                    temperature=item.analysis_request.metadata.get("temperature", 0.7),
                    max_tokens=item.analysis_request.metadata.get("max_tokens", 4096)
                )
                
                item.complete_processing(result)
                
                # 진행률 콜백 호출
                if job.progress_callback:
                    try:
                        job.update_statistics()
                        await job.progress_callback(job.get_progress())
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {e}")
                
                logger.info(f"Processed batch item: {item.item_id}")
                
            except Exception as e:
                item.fail_processing(str(e))
                logger.error(f"Failed to process batch item {item.item_id}: {e}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """작업 상태 조회"""
        # 활성 작업에서 찾기
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.update_statistics()
            return job.get_progress()
        
        # 히스토리에서 찾기
        if job_id in self.job_history:
            return self.job_history[job_id].get_progress()
        
        raise ValueError(f"Job {job_id} not found")
    
    def get_job_results(self, job_id: str) -> List[Dict[str, Any]]:
        """작업 결과 조회"""
        # 활성 작업에서 찾기
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].get_results()
        
        # 히스토리에서 찾기
        if job_id in self.job_history:
            return self.job_history[job_id].get_results()
        
        raise ValueError(f"Job {job_id} not found")
    
    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        if job.status == BatchStatus.PROCESSING:
            job.status = BatchStatus.CANCELLED
            job.completed_at = datetime.now()
            
            # 히스토리로 이동
            self.job_history[job_id] = job
            del self.active_jobs[job_id]
            
            logger.info(f"Cancelled batch job: {job_id}")
            return True
        
        return False
    
    def list_jobs(self, include_history: bool = False) -> List[Dict[str, Any]]:
        """작업 목록 조회"""
        jobs = []
        
        # 활성 작업
        for job in self.active_jobs.values():
            job.update_statistics()
            jobs.append(job.get_progress())
        
        # 히스토리 (요청시)
        if include_history:
            for job in self.job_history.values():
                jobs.append(job.get_progress())
        
        return sorted(jobs, key=lambda x: x["created_at"], reverse=True)
    
    def cleanup_old_jobs(self, max_history_size: int = 100):
        """오래된 작업 정리"""
        if len(self.job_history) > max_history_size:
            # 가장 오래된 작업들 제거
            sorted_jobs = sorted(
                self.job_history.items(),
                key=lambda x: x[1].completed_at or x[1].created_at
            )
            
            jobs_to_remove = sorted_jobs[:-max_history_size]
            for job_id, _ in jobs_to_remove:
                del self.job_history[job_id]
            
            logger.info(f"Cleaned up {len(jobs_to_remove)} old batch jobs")
    
    async def health_check(self) -> Dict[str, Any]:
        """배치 처리기 상태 확인"""
        return {
            "status": "healthy",
            "service": "batch_video_processor",
            "active_jobs": len(self.active_jobs),
            "history_jobs": len(self.job_history),
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "available_slots": self.max_concurrent_jobs - len(self.active_jobs),
            "timestamp": datetime.now().isoformat()
        }

# 싱글톤 인스턴스
_batch_processor = None

def get_batch_processor() -> BatchVideoProcessor:
    """배치 프로세서 싱글톤 인스턴스 반환"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchVideoProcessor()
    return _batch_processor