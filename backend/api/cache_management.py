"""
Cache Management API
캐시 관리 및 모니터링 API
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.core.query_cache import CacheManager, invalidate_cache_pattern
from backend.services.cached_queries import (
    invalidate_tool_cache,
    invalidate_template_cache,
    invalidate_user_cache
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/cache",
    tags=["cache-management"]
)


@router.get("/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    캐시 통계 조회
    
    - 총 키 수
    - 히트율
    - 미스율
    """
    # 관리자 권한 확인
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )
    
    try:
        stats = CacheManager.get_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.post("/invalidate/tools")
async def invalidate_tools_cache(
    tool_id: str = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Tool 캐시 무효화
    
    Args:
        tool_id: 특정 Tool ID (선택, 없으면 전체 무효화)
    """
    # 관리자 권한 확인
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )
    
    try:
        invalidate_tool_cache(tool_id)
        
        return {
            "success": True,
            "message": f"Tool cache invalidated" + (f" for {tool_id}" if tool_id else " (all)")
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate tool cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.post("/invalidate/templates")
async def invalidate_templates_cache(
    template_id: str = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Template 캐시 무효화
    
    Args:
        template_id: 특정 Template ID (선택, 없으면 전체 무효화)
    """
    # 관리자 권한 확인
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )
    
    try:
        invalidate_template_cache(template_id)
        
        return {
            "success": True,
            "message": f"Template cache invalidated" + (f" for {template_id}" if template_id else " (all)")
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate template cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.post("/invalidate/pattern")
async def invalidate_cache_by_pattern(
    pattern: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    패턴으로 캐시 무효화
    
    Args:
        pattern: Redis 키 패턴 (예: "query:get_tool_*")
    """
    # 관리자 권한 확인
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )
    
    try:
        invalidate_cache_pattern(pattern)
        
        return {
            "success": True,
            "message": f"Cache invalidated for pattern: {pattern}"
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.post("/clear")
async def clear_all_cache(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    모든 캐시 삭제 (주의!)
    
    관리자 전용
    """
    # 관리자 권한 확인
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )
    
    try:
        CacheManager.clear_all()
        
        return {
            "success": True,
            "message": "All cache cleared"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
