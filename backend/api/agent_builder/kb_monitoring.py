"""
Knowledgebase Monitoring API.

Provides endpoints for monitoring KB search performance and optimization.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.core.dependencies import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/kb",
    tags=["kb-monitoring"],
)


class OptimizerStats(BaseModel):
    """Optimizer statistics response"""
    total_searches: int
    avg_search_time: float
    cache_hit_rate: float
    error_rate: float
    kb_profiles: int


class WarmerStats(BaseModel):
    """Cache warmer statistics response"""
    total_warmed: int
    last_warming: Optional[str]
    errors: int


class KBPerformanceMetrics(BaseModel):
    """KB performance metrics"""
    kb_id: str
    document_count: int
    avg_search_time: float
    collection_size: int
    last_updated: str


@router.get(
    "/optimizer/stats",
    response_model=OptimizerStats,
    summary="Get optimizer statistics",
    description="Retrieve KB search optimizer performance statistics"
)
async def get_optimizer_stats(
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    """
    Get KB search optimizer statistics.
    
    **Returns**:
    - total_searches: Total number of searches performed
    - avg_search_time: Average search time in seconds
    - cache_hit_rate: Cache hit rate (0-1)
    - error_rate: Error rate (0-1)
    - kb_profiles: Number of KB profiles
    
    **Requires**: Authentication
    """
    try:
        from backend.services.kb_search_optimizer import get_kb_search_optimizer
        
        optimizer = get_kb_search_optimizer(redis_client)
        stats = optimizer.get_search_stats()
        
        return OptimizerStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get optimizer stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve optimizer statistics"
        )


@router.get(
    "/warmer/stats",
    response_model=WarmerStats,
    summary="Get cache warmer statistics",
    description="Retrieve cache warmer performance statistics"
)
async def get_warmer_stats(
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    """
    Get cache warmer statistics.
    
    **Returns**:
    - total_warmed: Total queries warmed
    - last_warming: Last warming timestamp
    - errors: Number of errors
    
    **Requires**: Authentication
    """
    try:
        from backend.services.kb_cache_warmer import KBCacheWarmer
        from backend.services.speculative_processor import SpeculativeProcessor
        from backend.core.dependencies import (
            get_embedding_service,
            get_milvus_manager,
            get_llm_manager
        )
        
        # Note: In production, use a singleton or dependency injection
        # This is a simplified version
        embedding_service = await get_embedding_service()
        milvus_manager = await get_milvus_manager()
        llm_manager = await get_llm_manager()
        
        processor = SpeculativeProcessor(
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            llm_manager=llm_manager,
            redis_client=redis_client
        )
        
        warmer = KBCacheWarmer(processor)
        stats = warmer.get_warming_stats()
        
        return WarmerStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get warmer stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve warmer statistics"
        )


@router.get(
    "/profiles",
    summary="Get KB profiles",
    description="Retrieve performance profiles for all knowledgebases"
)
async def get_kb_profiles(
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    """
    Get KB performance profiles.
    
    **Returns**:
    - List of KB profiles with performance metrics
    
    **Requires**: Authentication
    """
    try:
        from backend.services.kb_search_optimizer import get_kb_search_optimizer
        
        optimizer = get_kb_search_optimizer(redis_client)
        
        profiles = []
        for kb_id, profile in optimizer.kb_profiles.items():
            profiles.append({
                'kb_id': kb_id,
                'document_count': profile.document_count,
                'avg_search_time': profile.avg_search_time,
                'collection_size': profile.collection_size,
                'last_updated': profile.last_updated.isoformat()
            })
        
        return {
            'total_profiles': len(profiles),
            'profiles': profiles
        }
        
    except Exception as e:
        logger.error(f"Failed to get KB profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KB profiles"
        )


@router.post(
    "/warm/{agent_id}",
    summary="Warm agent cache",
    description="Manually trigger cache warming for an agent"
)
async def warm_agent_cache(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
):
    """
    Manually warm cache for an agent.
    
    **Args**:
    - agent_id: Agent ID to warm
    
    **Returns**:
    - Warming result with statistics
    
    **Requires**: Authentication and agent ownership
    """
    try:
        from backend.db.models.agent_builder import Agent
        from sqlalchemy.orm import joinedload
        from backend.services.kb_cache_warmer import KBCacheWarmer
        from backend.services.speculative_processor import SpeculativeProcessor
        from backend.core.dependencies import (
            get_embedding_service,
            get_milvus_manager,
            get_llm_manager
        )
        
        # Check agent access
        agent = db.query(Agent).options(
            joinedload(Agent.knowledgebases)
        ).filter(
            Agent.id == agent_id,
            Agent.deleted_at.is_(None)
        ).first()
        
        if not agent:
            raise HTTPException(404, "Agent not found")
        
        if str(agent.user_id) != str(current_user.id):
            raise HTTPException(403, "No permission to warm this agent")
        
        # Get KB IDs
        kb_ids = [str(kb.knowledgebase_id) for kb in agent.knowledgebases]
        
        if not kb_ids:
            return {
                'agent_id': agent_id,
                'message': 'No knowledgebases to warm',
                'queries_warmed': 0
            }
        
        # Initialize processor and warmer
        embedding_service = await get_embedding_service()
        milvus_manager = await get_milvus_manager()
        llm_manager = await get_llm_manager()
        
        processor = SpeculativeProcessor(
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            llm_manager=llm_manager,
            redis_client=redis_client
        )
        
        warmer = KBCacheWarmer(processor)
        
        # Warm cache
        result = await warmer.warm_agent_cache(agent_id, kb_ids)
        
        return {
            'agent_id': agent_id,
            'agent_name': agent.name,
            'kb_count': len(kb_ids),
            'queries_warmed': result['queries_warmed'],
            'errors': result['errors'],
            'duration_seconds': result['duration_seconds']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to warm agent cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warm cache: {str(e)}"
        )


@router.delete(
    "/cache/clear",
    summary="Clear KB cache",
    description="Clear all KB-related cache entries"
)
async def clear_kb_cache(
    pattern: str = Query("kb_search:*", description="Cache key pattern to clear"),
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    """
    Clear KB cache entries.
    
    **Query Parameters**:
    - pattern: Redis key pattern to clear (default: "kb_search:*")
    
    **Returns**:
    - Number of keys cleared
    
    **Requires**: Authentication (admin only in production)
    """
    try:
        # In production, add admin check
        # if current_user.role != 'admin':
        #     raise HTTPException(403, "Admin only")
        
        # Find matching keys
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        # Delete keys
        if keys:
            await redis_client.delete(*keys)
        
        logger.info(f"Cleared {len(keys)} cache keys with pattern: {pattern}")
        
        return {
            'pattern': pattern,
            'keys_cleared': len(keys),
            'message': f'Cleared {len(keys)} cache entries'
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


@router.get(
    "/health",
    summary="KB system health check",
    description="Check health of KB search system"
)
async def kb_health_check(
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    """
    Check KB system health.
    
    **Returns**:
    - Health status of various components
    
    **Requires**: Authentication
    """
    try:
        health = {
            'status': 'healthy',
            'components': {}
        }
        
        # Check Redis
        try:
            await redis_client.ping()
            health['components']['redis'] = 'healthy'
        except Exception as e:
            health['components']['redis'] = f'unhealthy: {str(e)}'
            health['status'] = 'degraded'
        
        # Check Optimizer
        try:
            from backend.services.kb_search_optimizer import get_kb_search_optimizer
            optimizer = get_kb_search_optimizer(redis_client)
            stats = optimizer.get_search_stats()
            health['components']['optimizer'] = {
                'status': 'healthy',
                'cache_hit_rate': stats['cache_hit_rate'],
                'error_rate': stats['error_rate']
            }
        except Exception as e:
            health['components']['optimizer'] = f'unhealthy: {str(e)}'
            health['status'] = 'degraded'
        
        return health
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
