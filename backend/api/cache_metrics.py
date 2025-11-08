"""
Cache Metrics API

Provides endpoints for monitoring cache performance and hit rates.
"""

import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache-metrics", tags=["Cache Metrics"])


@router.get("/semantic")
async def get_semantic_cache_metrics():
    """
    Get semantic cache performance metrics.
    
    Returns detailed statistics about semantic cache including:
    - Hit/miss rates
    - Exact vs semantic matches
    - Cache utilization
    - Popular queries
    """
    try:
        from backend.services.semantic_cache import get_semantic_cache
        
        cache = get_semantic_cache()
        stats = cache.get_stats()
        
        # Get popular queries
        popular_queries = cache.get_popular_queries(top_n=10)
        
        return {
            "service": "semantic_cache",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": stats,
            "popular_queries": [
                {
                    "query": query[:100],  # Truncate for display
                    "access_count": count,
                    "popularity_score": round(score, 3)
                }
                for query, count, score in popular_queries
            ],
            "health": {
                "is_healthy": stats["hit_rate"] > 0.3,  # 30% threshold
                "status": "good" if stats["hit_rate"] > 0.5 else "degraded" if stats["hit_rate"] > 0.3 else "poor"
            }
        }
        
    except RuntimeError as e:
        # Cache not initialized
        return {
            "service": "semantic_cache",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Cache not initialized",
            "metrics": None
        }
    except Exception as e:
        logger.error(f"Failed to get semantic cache metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get semantic cache metrics: {str(e)}"
        )


@router.get("/llm")
async def get_llm_cache_metrics():
    """
    Get LLM response cache performance metrics.
    
    Returns statistics about LLM response caching including:
    - Hit/miss rates
    - Total requests
    - Cache effectiveness
    """
    try:
        from backend.core.dependencies import get_llm_cache
        
        cache = await get_llm_cache()
        stats = cache.get_stats()
        
        return {
            "service": "llm_cache",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": stats,
            "health": {
                "is_healthy": stats["hit_rate"] > 20,  # 20% threshold
                "status": "good" if stats["hit_rate"] > 40 else "degraded" if stats["hit_rate"] > 20 else "poor"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get LLM cache metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get LLM cache metrics: {str(e)}"
        )


@router.get("/warmer")
async def get_cache_warmer_stats():
    """
    Get cache warmer statistics.
    
    Returns information about cache warming operations.
    """
    try:
        from backend.services.cache_warmer import _cache_warmer
        
        if _cache_warmer is None:
            return {
                "service": "cache_warmer",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Cache warmer not initialized",
                "stats": None
            }
        
        stats = _cache_warmer.get_stats()
        
        return {
            "service": "cache_warmer",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
            "health": {
                "is_healthy": not stats["is_warming"],
                "status": "warming" if stats["is_warming"] else "idle"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache warmer stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache warmer stats: {str(e)}"
        )


@router.get("/all")
async def get_all_cache_metrics():
    """
    Get metrics for all cache systems.
    
    Returns combined metrics from semantic cache, LLM cache, and cache warmer.
    """
    try:
        semantic_metrics = await get_semantic_cache_metrics()
        llm_metrics = await get_llm_cache_metrics()
        warmer_stats = await get_cache_warmer_stats()
        
        # Calculate overall health
        health_scores = []
        
        if semantic_metrics.get("metrics"):
            health_scores.append(semantic_metrics["metrics"]["hit_rate"])
        
        if llm_metrics.get("metrics"):
            health_scores.append(llm_metrics["metrics"]["hit_rate"] / 100)  # Normalize to 0-1
        
        overall_health = "healthy" if health_scores and sum(health_scores) / len(health_scores) > 0.3 else "degraded"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "caches": {
                "semantic": semantic_metrics,
                "llm": llm_metrics,
                "warmer": warmer_stats,
            },
            "overall_health": overall_health,
            "summary": {
                "semantic_hit_rate": semantic_metrics.get("metrics", {}).get("hit_rate", 0),
                "llm_hit_rate": llm_metrics.get("metrics", {}).get("hit_rate", 0),
                "cache_warmer_status": warmer_stats.get("health", {}).get("status", "unknown"),
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get all cache metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all cache metrics: {str(e)}"
        )


@router.post("/semantic/clear")
async def clear_semantic_cache():
    """
    Clear all semantic cache entries.
    
    Use with caution - this will remove all cached responses.
    """
    try:
        from backend.services.semantic_cache import get_semantic_cache
        
        cache = get_semantic_cache()
        cache.clear()
        
        return {
            "success": True,
            "message": "Semantic cache cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear semantic cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear semantic cache: {str(e)}"
        )


@router.post("/llm/clear")
async def clear_llm_cache():
    """
    Clear all LLM response cache entries.
    
    Use with caution - this will remove all cached LLM responses.
    """
    try:
        from backend.core.dependencies import get_llm_cache
        
        cache = await get_llm_cache()
        deleted = await cache.clear_all()
        
        return {
            "success": True,
            "message": f"LLM cache cleared ({deleted} entries)",
            "deleted_count": deleted,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear LLM cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear LLM cache: {str(e)}"
        )


@router.post("/semantic/cleanup")
async def cleanup_expired_semantic_cache():
    """
    Remove expired entries from semantic cache.
    
    This is a maintenance operation that removes stale cache entries.
    """
    try:
        from backend.services.semantic_cache import get_semantic_cache
        
        cache = get_semantic_cache()
        cache.cleanup_expired()
        
        return {
            "success": True,
            "message": "Expired entries cleaned up",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup semantic cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup semantic cache: {str(e)}"
        )


@router.get("/summary")
async def get_cache_metrics_summary():
    """
    Get a summary of cache performance.
    
    Returns a simplified view suitable for dashboards.
    """
    try:
        all_metrics = await get_all_cache_metrics()
        
        semantic = all_metrics["caches"]["semantic"]
        llm = all_metrics["caches"]["llm"]
        
        # Extract key metrics
        semantic_metrics = semantic.get("metrics", {})
        llm_metrics = llm.get("metrics", {})
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": all_metrics["overall_health"],
            "summary": {
                "semantic_cache": {
                    "hit_rate": semantic_metrics.get("hit_rate", 0),
                    "cache_size": semantic_metrics.get("cache_size", 0),
                    "utilization": semantic_metrics.get("utilization", 0),
                    "status": semantic.get("health", {}).get("status", "unknown"),
                },
                "llm_cache": {
                    "hit_rate": llm_metrics.get("hit_rate", 0),
                    "total_requests": llm_metrics.get("total_requests", 0),
                    "status": llm.get("health", {}).get("status", "unknown"),
                },
            },
            "recommendations": _generate_recommendations(semantic_metrics, llm_metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache metrics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache metrics summary: {str(e)}"
        )


def _generate_recommendations(semantic_metrics: dict, llm_metrics: dict) -> list:
    """Generate recommendations based on cache metrics."""
    recommendations = []
    
    # Semantic cache recommendations
    semantic_hit_rate = semantic_metrics.get("hit_rate", 0)
    if semantic_hit_rate < 0.3:
        recommendations.append({
            "type": "warning",
            "cache": "semantic",
            "message": f"Low semantic cache hit rate ({semantic_hit_rate:.1%}). Consider warming cache with common queries.",
            "action": "POST /api/cache-metrics/semantic/warm"
        })
    
    utilization = semantic_metrics.get("utilization", 0)
    if utilization > 0.9:
        recommendations.append({
            "type": "warning",
            "cache": "semantic",
            "message": f"High cache utilization ({utilization:.1%}). Consider increasing max_size.",
            "action": "Update CACHE_L2_MAX_SIZE in config"
        })
    
    # LLM cache recommendations
    llm_hit_rate = llm_metrics.get("hit_rate", 0)
    if llm_hit_rate < 20:
        recommendations.append({
            "type": "info",
            "cache": "llm",
            "message": f"Low LLM cache hit rate ({llm_hit_rate:.1f}%). This is normal for diverse queries.",
            "action": None
        })
    
    if not recommendations:
        recommendations.append({
            "type": "success",
            "cache": "all",
            "message": "Cache performance is optimal",
            "action": None
        })
    
    return recommendations
