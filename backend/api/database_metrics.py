"""
Database Metrics API

Provides endpoints for monitoring PostgreSQL and Milvus database health.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

from backend.db.database import engine
from backend.db.pool_monitor import get_pool_monitor
from backend.db.monitoring import get_pool_status
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics/database", tags=["Database Metrics"])


@router.get("/postgresql/pool")
async def get_postgresql_pool_stats() -> Dict[str, Any]:
    """
    Get PostgreSQL connection pool statistics.

    Returns comprehensive metrics including:
    - Pool configuration
    - Current utilization
    - Connection statistics
    - Health status
    """
    try:
        # Get basic pool status
        basic_stats = get_pool_status(engine)

        # Get detailed monitoring stats if available
        try:
            monitor = get_pool_monitor()
            detailed_stats = monitor.get_pool_stats()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "basic": basic_stats,
                "detailed": detailed_stats,
                "monitoring_enabled": True,
            }
        except RuntimeError:
            # Monitoring not setup, return basic stats only
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "basic": basic_stats,
                "monitoring_enabled": False,
                "message": "Advanced monitoring not enabled. Call setup_pool_monitoring() to enable.",
            }

    except Exception as e:
        logger.error(f"Failed to get PostgreSQL pool stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve pool statistics: {str(e)}"
        )


@router.get("/postgresql/health")
async def get_postgresql_health() -> Dict[str, Any]:
    """
    Get PostgreSQL database health status.

    Returns:
    - Connection status
    - Pool health
    - Recent warnings
    """
    try:
        # Test connection
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            connection_ok = result == 1

        # Get pool stats
        pool_stats = get_pool_status(engine)
        utilization = (
            pool_stats["checked_out"] / pool_stats["max_connections"] * 100
            if pool_stats["max_connections"] > 0
            else 0
        )

        # Determine health status
        if not connection_ok:
            status = "critical"
            message = "Database connection failed"
        elif utilization > 90:
            status = "warning"
            message = f"High pool utilization: {utilization:.1f}%"
        elif utilization > 75:
            status = "degraded"
            message = f"Elevated pool utilization: {utilization:.1f}%"
        else:
            status = "healthy"
            message = "All systems operational"

        # Get monitoring data if available
        warnings = []
        try:
            monitor = get_pool_monitor()
            recent_long_connections = monitor.get_recent_long_connections(limit=5)
            potential_leaks = monitor.get_potential_leaks()

            if recent_long_connections:
                warnings.append(
                    {
                        "type": "long_connections",
                        "count": len(recent_long_connections),
                        "recent": recent_long_connections,
                    }
                )

            if potential_leaks:
                warnings.append(
                    {
                        "type": "potential_leaks",
                        "count": len(potential_leaks),
                        "leaks": potential_leaks,
                    }
                )
                status = "critical"
                message = f"Potential connection leaks detected: {len(potential_leaks)}"

        except RuntimeError:
            pass  # Monitoring not enabled

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "message": message,
            "connection_ok": connection_ok,
            "pool_utilization_percent": utilization,
            "warnings": warnings,
            "config": {
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_recycle": settings.DB_POOL_RECYCLE,
            },
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "critical",
            "message": f"Health check failed: {str(e)}",
            "connection_ok": False,
        }


@router.get("/milvus/pool")
async def get_milvus_pool_stats() -> Dict[str, Any]:
    """
    Get Milvus connection pool statistics.

    Returns:
    - Pool configuration
    - Connection status
    - Utilization metrics
    """
    try:
        from backend.core.milvus_pool import get_milvus_pool

        pool = get_milvus_pool(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            pool_size=settings.MILVUS_POOL_SIZE,
        )

        stats = await pool.get_stats()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
            "config": {
                "host": settings.MILVUS_HOST,
                "port": settings.MILVUS_PORT,
                "pool_size": settings.MILVUS_POOL_SIZE,
                "max_idle_time": settings.MILVUS_MAX_IDLE_TIME,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get Milvus pool stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve Milvus pool statistics: {str(e)}",
        )


@router.get("/milvus/collection")
async def get_milvus_collection_stats() -> Dict[str, Any]:
    """
    Get Milvus collection statistics.

    Returns:
    - Collection info
    - Entity count
    - Schema details
    """
    try:
        from backend.services.milvus import MilvusManager

        manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION_NAME,
        )

        manager.connect()

        try:
            stats = manager.get_collection_stats()
            health = manager.health_check()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "collection_stats": stats,
                "health": health,
            }
        finally:
            manager.disconnect()

    except Exception as e:
        logger.error(f"Failed to get Milvus collection stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve collection statistics: {str(e)}",
        )


@router.get("/milvus/health")
async def get_milvus_health() -> Dict[str, Any]:
    """
    Get Milvus database health status.

    Returns:
    - Connection status
    - Collection status
    - Performance metrics
    """
    try:
        from backend.services.milvus import MilvusManager

        manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION_NAME,
        )

        manager.connect()

        try:
            health = manager.health_check()

            # Determine status
            if health["status"] == "healthy":
                status = "healthy"
                message = "Milvus is operational"
            elif health["status"] == "disconnected":
                status = "critical"
                message = "Milvus connection failed"
            else:
                status = "degraded"
                message = health.get("error", "Unknown issue")

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "message": message,
                "details": health,
                "config": {
                    "host": settings.MILVUS_HOST,
                    "port": settings.MILVUS_PORT,
                    "collection": settings.MILVUS_COLLECTION_NAME,
                },
            }
        finally:
            manager.disconnect()

    except Exception as e:
        logger.error(f"Milvus health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "critical",
            "message": f"Health check failed: {str(e)}",
            "details": {"error": str(e)},
        }


@router.get("/summary")
async def get_database_summary() -> Dict[str, Any]:
    """
    Get summary of all database metrics.

    Returns:
    - PostgreSQL status
    - Milvus status
    - Overall health
    """
    try:
        # Get PostgreSQL health
        pg_health = await get_postgresql_health()

        # Get Milvus health
        milvus_health = await get_milvus_health()

        # Determine overall status
        statuses = [pg_health["status"], milvus_health["status"]]

        if "critical" in statuses:
            overall_status = "critical"
        elif "warning" in statuses or "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "postgresql": {
                "status": pg_health["status"],
                "message": pg_health["message"],
                "utilization": pg_health.get("pool_utilization_percent", 0),
            },
            "milvus": {
                "status": milvus_health["status"],
                "message": milvus_health["message"],
            },
        }

    except Exception as e:
        logger.error(f"Failed to get database summary: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "critical",
            "error": str(e),
        }
