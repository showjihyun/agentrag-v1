"""
Connection Pool Metrics API

Provides endpoints for monitoring connection pool health and performance.
"""

import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pool-metrics", tags=["Pool Metrics"])


@router.get("/redis")
async def get_redis_pool_metrics():
    """
    Get Redis connection pool metrics.
    
    Returns comprehensive statistics about Redis connection pool including:
    - Pool configuration
    - Redis server stats
    - Custom metrics (checkouts, timeouts, etc.)
    - Health status
    - Performance warnings
    """
    try:
        from backend.core.connection_pool import get_redis_pool
        from backend.config import settings
        
        pool = get_redis_pool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )
        
        stats = await pool.get_pool_stats()
        
        return {
            "service": "redis",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": stats,
        }
        
    except Exception as e:
        logger.error(f"Failed to get Redis pool metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Redis pool metrics: {str(e)}"
        )


@router.get("/milvus")
async def get_milvus_pool_metrics():
    """
    Get Milvus connection pool metrics.
    
    Returns comprehensive statistics about Milvus connection pool including:
    - Pool configuration
    - Connection usage
    - Custom metrics (acquisitions, wait times, etc.)
    - Health status
    - Performance warnings
    """
    try:
        from backend.core.milvus_pool import get_milvus_pool
        from backend.config import settings
        
        pool = get_milvus_pool(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            pool_size=settings.MILVUS_POOL_SIZE,
        )
        
        # Get pool stats
        stats = {
            "pool_config": {
                "host": pool.host,
                "port": pool.port,
                "pool_size": pool.pool_size,
                "max_idle_time": pool.max_idle_time,
            },
            "connections": {
                "total": len(pool._connections),
                "in_use": sum(1 for c in pool._connections if c["in_use"]),
                "available": sum(1 for c in pool._connections if not c["in_use"]),
            },
            "custom_metrics": pool.metrics.get_metrics(),
            "health": {
                "is_healthy": pool._initialized,
                "last_check": datetime.utcnow().isoformat(),
            },
        }
        
        # Check for warnings
        warnings = []
        active = stats["connections"]["in_use"]
        total = stats["connections"]["total"]
        
        if active > total * 0.8:
            warnings.append(f"High connection usage: {active}/{total}")
        
        if pool.metrics.avg_wait_time > 100:  # 100ms threshold
            warnings.append(f"Slow acquisition time: {pool.metrics.avg_wait_time:.2f}ms")
        
        if pool.metrics.total_timeouts > 0:
            warnings.append(f"Connection timeouts detected: {pool.metrics.total_timeouts}")
        
        if warnings:
            stats["warnings"] = warnings
            logger.warning(f"Milvus pool warnings: {warnings}")
        
        return {
            "service": "milvus",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": stats,
        }
        
    except Exception as e:
        logger.error(f"Failed to get Milvus pool metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Milvus pool metrics: {str(e)}"
        )


@router.get("/all")
async def get_all_pool_metrics():
    """
    Get metrics for all connection pools.
    
    Returns combined metrics from Redis and Milvus pools.
    """
    try:
        redis_metrics = await get_redis_pool_metrics()
        milvus_metrics = await get_milvus_pool_metrics()
        
        # Aggregate warnings
        all_warnings = []
        if "warnings" in redis_metrics.get("metrics", {}):
            all_warnings.extend([f"Redis: {w}" for w in redis_metrics["metrics"]["warnings"]])
        if "warnings" in milvus_metrics.get("metrics", {}):
            all_warnings.extend([f"Milvus: {w}" for w in milvus_metrics["metrics"]["warnings"]])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "pools": {
                "redis": redis_metrics["metrics"],
                "milvus": milvus_metrics["metrics"],
            },
            "overall_health": "healthy" if not all_warnings else "degraded",
            "warnings": all_warnings if all_warnings else None,
        }
        
    except Exception as e:
        logger.error(f"Failed to get all pool metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all pool metrics: {str(e)}"
        )


@router.get("/summary")
async def get_pool_metrics_summary():
    """
    Get a summary of connection pool health.
    
    Returns a simplified view suitable for dashboards.
    """
    try:
        all_metrics = await get_all_pool_metrics()
        
        redis = all_metrics["pools"]["redis"]
        milvus = all_metrics["pools"]["milvus"]
        
        # Calculate utilization percentages
        redis_utilization = 0
        if "custom_metrics" in redis:
            active = redis["custom_metrics"].get("active_connections", 0)
            max_conn = redis["pool_config"].get("max_connections", 1)
            redis_utilization = (active / max_conn) * 100 if max_conn > 0 else 0
        
        milvus_utilization = 0
        if "connections" in milvus:
            in_use = milvus["connections"].get("in_use", 0)
            total = milvus["connections"].get("total", 1)
            milvus_utilization = (in_use / total) * 100 if total > 0 else 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": all_metrics["overall_health"],
            "summary": {
                "redis": {
                    "utilization_percent": round(redis_utilization, 1),
                    "avg_checkout_time_ms": redis.get("custom_metrics", {}).get("avg_checkout_time_ms", 0),
                    "total_errors": redis.get("custom_metrics", {}).get("total_errors", 0),
                },
                "milvus": {
                    "utilization_percent": round(milvus_utilization, 1),
                    "avg_wait_time_ms": milvus.get("custom_metrics", {}).get("avg_wait_time_ms", 0),
                    "total_errors": milvus.get("custom_metrics", {}).get("total_errors", 0),
                },
            },
            "warnings": all_metrics.get("warnings"),
        }
        
    except Exception as e:
        logger.error(f"Failed to get pool metrics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pool metrics summary: {str(e)}"
        )
