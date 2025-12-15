"""
Gemini Batch Video Processing API
대량 비디오 파일을 동시에 처리하는 배치 처리 API
"""

import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.multimodal.batch_processor import (
    get_batch_processor, 
    VideoAnalysisRequest,
    BatchStatus
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/gemini-batch", tags=["Gemini Batch Processing"])

# ============================================================================
# Request/Response Models
# ============================================================================

class BatchJobCreateRequest(BaseModel):
    """배치 작업 생성 요청"""
    job_name: str = Field(..., description="배치 작업 이름")
    analysis_type: str = Field(default="comprehensive", description="분석 유형")
    model: str = Field(default="gemini-1.5-pro", description="사용할 Gemini 모델")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="창의성 수준")
    max_tokens: int = Field(default=4096, ge=1, le=8192, description="최대 토큰 수")
    frame_sampling: str = Field(default="auto", description="프레임 샘플링 방법")
    max_frames: int = Field(default=30, ge=1, le=100, description="최대 프레임 수")
    include_audio: bool = Field(default=True, description="오디오 포함 여부")

class BatchJobResponse(BaseModel):
    """배치 작업 응답"""
    job_id: str
    job_name: str
    status: str
    total_items: int
    processed_items: int
    completed_items: int
    failed_items: int
    progress_percentage: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_remaining_time: Optional[float] = None
    average_processing_time: float

class BatchItemResponse(BaseModel):
    """배치 항목 응답"""
    item_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_seconds: float
    analysis_config: Dict[str, Any]

# ============================================================================
# Batch Job Management
# ============================================================================

@router.post("/create-job", response_model=Dict[str, str])
async def create_batch_job(
    request: BatchJobCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    새로운 배치 처리 작업 생성
    
    여러 비디오를 동시에 처리할 수 있는 배치 작업을 생성합니다.
    작업 생성 후 비디오 파일들을 추가하고 처리를 시작할 수 있습니다.
    """
    try:
        batch_processor = get_batch_processor()
        job_id = batch_processor.create_batch_job(request.job_name)
        
        logger.info(
            f"Created batch job",
            extra={
                'user_id': current_user.id,
                'job_id': job_id,
                'job_name': request.job_name,
                'analysis_type': request.analysis_type
            }
        )
        
        return {
            "job_id": job_id,
            "message": f"Batch job '{request.job_name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create batch job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/add-videos")
async def add_videos_to_batch(
    job_id: str,
    analysis_type: str = Form(default="comprehensive"),
    model: str = Form(default="gemini-1.5-pro"),
    temperature: float = Form(default=0.7),
    frame_sampling: str = Form(default="auto"),
    max_frames: int = Form(default=30),
    include_audio: bool = Form(default=True),
    video_files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    배치 작업에 비디오 파일들 추가
    
    여러 비디오 파일을 한 번에 업로드하여 배치 작업에 추가합니다.
    모든 파일은 동일한 분석 설정을 사용합니다.
    """
    try:
        batch_processor = get_batch_processor()
        
        # 파일 검증 및 추가
        added_items = []
        
        for video_file in video_files:
            # 파일 형식 검증
            if not video_file.content_type or not video_file.content_type.startswith('video/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid video format: {video_file.filename}"
                )
            
            # 파일 크기 제한 (100MB)
            video_content = await video_file.read()
            if len(video_content) > 100 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"Video file too large: {video_file.filename} (max 100MB)"
                )
            
            # VideoAnalysisRequest 생성
            analysis_request = VideoAnalysisRequest()
            analysis_request.analysis_type = analysis_type
            analysis_request.frame_sampling = frame_sampling
            analysis_request.max_frames = max_frames
            analysis_request.include_audio = include_audio
            analysis_request.metadata = {
                "filename": video_file.filename,
                "content_type": video_file.content_type,
                "size_bytes": len(video_content),
                "model": model,
                "temperature": temperature
            }
            
            # 비디오 데이터 설정
            analysis_request.set_video_data(video_content)
            
            # 배치에 추가
            item_id = batch_processor.add_video_to_batch(
                job_id=job_id,
                video_data=video_content,
                analysis_request=analysis_request,
                item_name=video_file.filename or f"video_{len(added_items) + 1}"
            )
            
            added_items.append({
                "item_id": item_id,
                "filename": video_file.filename,
                "size_bytes": len(video_content)
            })
        
        logger.info(
            f"Added videos to batch",
            extra={
                'user_id': current_user.id,
                'job_id': job_id,
                'video_count': len(added_items)
            }
        )
        
        return {
            "job_id": job_id,
            "added_items": added_items,
            "total_added": len(added_items),
            "message": f"Successfully added {len(added_items)} videos to batch"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add videos to batch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/start")
async def start_batch_processing(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    배치 처리 시작
    
    배치 작업에 추가된 모든 비디오의 분석을 시작합니다.
    처리는 백그라운드에서 실행되며, 상태는 별도 API로 확인할 수 있습니다.
    """
    try:
        batch_processor = get_batch_processor()
        
        # 백그라운드에서 배치 처리 실행
        background_tasks.add_task(
            _process_batch_background,
            batch_processor,
            job_id,
            current_user.id
        )
        
        logger.info(
            f"Started batch processing",
            extra={
                'user_id': current_user.id,
                'job_id': job_id
            }
        )
        
        return {
            "job_id": job_id,
            "message": "Batch processing started in background",
            "status_endpoint": f"/api/agent-builder/gemini-batch/jobs/{job_id}/status"
        }
        
    except Exception as e:
        logger.error(f"Failed to start batch processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def _process_batch_background(batch_processor, job_id: str, user_id: int):
    """백그라운드 배치 처리 함수"""
    try:
        # 진행률 콜백 함수
        async def progress_callback(progress_info):
            logger.info(
                f"Batch progress update",
                extra={
                    'user_id': user_id,
                    'job_id': job_id,
                    'progress': progress_info['progress_percentage']
                }
            )
        
        # 배치 처리 실행
        result = await batch_processor.process_batch(job_id, progress_callback)
        
        logger.info(
            f"Batch processing completed",
            extra={
                'user_id': user_id,
                'job_id': job_id,
                'completed_items': result['completed_items'],
                'failed_items': result['failed_items']
            }
        )
        
    except Exception as e:
        logger.error(
            f"Background batch processing failed",
            extra={
                'user_id': user_id,
                'job_id': job_id,
                'error': str(e)
            }
        )

# ============================================================================
# Job Status and Results
# ============================================================================

@router.get("/jobs/{job_id}/status", response_model=BatchJobResponse)
async def get_batch_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    배치 작업 상태 조회
    
    배치 작업의 현재 진행 상황과 통계를 조회합니다.
    실시간으로 업데이트되는 진행률과 예상 완료 시간을 확인할 수 있습니다.
    """
    try:
        batch_processor = get_batch_processor()
        status = batch_processor.get_job_status(job_id)
        
        return BatchJobResponse(**status)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get batch job status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/results")
async def get_batch_job_results(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    배치 작업 결과 조회
    
    배치 작업의 모든 항목별 분석 결과를 조회합니다.
    성공한 항목의 분석 결과와 실패한 항목의 오류 정보를 포함합니다.
    """
    try:
        batch_processor = get_batch_processor()
        results = batch_processor.get_job_results(job_id)
        
        return {
            "job_id": job_id,
            "total_items": len(results),
            "results": results
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get batch job results: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}")
async def cancel_batch_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    배치 작업 취소
    
    진행 중인 배치 작업을 취소합니다.
    이미 완료된 항목의 결과는 유지되며, 처리 중인 항목들이 중단됩니다.
    """
    try:
        batch_processor = get_batch_processor()
        cancelled = batch_processor.cancel_job(job_id)
        
        if cancelled:
            logger.info(
                f"Cancelled batch job",
                extra={
                    'user_id': current_user.id,
                    'job_id': job_id
                }
            )
            return {"job_id": job_id, "message": "Batch job cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel batch job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Job Management
# ============================================================================

@router.get("/jobs")
async def list_batch_jobs(
    include_history: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    배치 작업 목록 조회
    
    사용자의 모든 배치 작업 목록을 조회합니다.
    활성 작업과 완료된 작업을 포함할 수 있습니다.
    """
    try:
        batch_processor = get_batch_processor()
        jobs = batch_processor.list_jobs(include_history)
        
        return {
            "jobs": jobs,
            "total": len(jobs),
            "active_jobs": len([job for job in jobs if job["status"] in ["pending", "processing"]]),
            "completed_jobs": len([job for job in jobs if job["status"] == "completed"])
        }
        
    except Exception as e:
        logger.error(f"Failed to list batch jobs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_batch_processing_stats(
    current_user: User = Depends(get_current_user)
):
    """
    배치 처리 통계
    
    전체 배치 처리 시스템의 통계와 성능 지표를 조회합니다.
    """
    try:
        batch_processor = get_batch_processor()
        health = await batch_processor.health_check()
        
        jobs = batch_processor.list_jobs(include_history=True)
        
        # 통계 계산
        total_jobs = len(jobs)
        completed_jobs = len([job for job in jobs if job["status"] == "completed"])
        failed_jobs = len([job for job in jobs if job["status"] == "failed"])
        
        total_items = sum(job["total_items"] for job in jobs)
        completed_items = sum(job["completed_items"] for job in jobs)
        
        avg_processing_time = 0
        if completed_jobs > 0:
            total_time = sum(job["average_processing_time"] * job["completed_items"] for job in jobs if job["status"] == "completed")
            avg_processing_time = total_time / max(completed_items, 1)
        
        return {
            "system_health": health,
            "statistics": {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": (completed_jobs / max(total_jobs, 1)) * 100,
                "total_items_processed": total_items,
                "completed_items": completed_items,
                "average_processing_time_seconds": avg_processing_time,
                "throughput_items_per_hour": (completed_items / max(avg_processing_time / 3600, 1)) if avg_processing_time > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get batch processing stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    배치 처리 서비스 상태 확인
    """
    try:
        batch_processor = get_batch_processor()
        health_status = await batch_processor.health_check()
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "gemini_batch_processor"
        }