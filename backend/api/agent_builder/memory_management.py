"""
Memory Management API
메모리 정리 및 통계 조회 API
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.memory_cleanup_service import MemoryCleanupService
from backend.core.scheduler import get_scheduler_status

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/memory",
    tags=["memory-management"]
)


@router.post("/cleanup")
async def cleanup_memories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    메모리 수동 정리 (관리자 전용)
    
    - STM: 24시간 이상 경과한 메모리 삭제
    - LTM: 90일 이상 경과하고 중요도가 낮은 메모리 삭제
    - Episodic: 30일 이상 경과하고 중요도가 낮은 메모리 삭제
    """
    
    # 관리자 권한 확인
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )
    
    try:
        service = MemoryCleanupService(db)
        stats = service.cleanup_expired_memories()
        
        return {
            "success": True,
            "message": "Memory cleanup completed",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Memory cleanup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Memory cleanup failed: {str(e)}"
        )


@router.post("/consolidate/{agent_id}")
async def consolidate_agent_memories(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    특정 에이전트의 메모리 통합 (STM → LTM 승격)
    
    자주 접근되는 STM을 LTM으로 승격시킵니다.
    """
    
    try:
        service = MemoryCleanupService(db)
        consolidated_count = service.consolidate_memories(agent_id)
        
        return {
            "success": True,
            "message": f"Consolidated {consolidated_count} memories",
            "agent_id": agent_id,
            "consolidated_count": consolidated_count
        }
        
    except Exception as e:
        logger.error(f"Memory consolidation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Memory consolidation failed: {str(e)}"
        )


@router.get("/stats")
async def get_memory_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    메모리 통계 조회
    
    - 타입별 메모리 수
    - 중요도별 메모리 수
    - 정리 대상 메모리 수
    """
    
    try:
        service = MemoryCleanupService(db)
        stats = service.get_memory_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory stats: {str(e)}"
        )


@router.get("/scheduler/status")
async def get_scheduler_status_api(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    스케줄러 상태 조회
    
    - 실행 중인 작업 목록
    - 다음 실행 시간
    """
    
    # 관리자 권한 확인
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )
    
    try:
        status = get_scheduler_status()
        
        return {
            "success": True,
            "scheduler": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scheduler status: {str(e)}"
        )
