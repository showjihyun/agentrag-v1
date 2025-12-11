"""
Advanced Health Checks API

Kubernetes-ready health checks with dependency monitoring.
"""

from fastapi import APIRouter, status, Response
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import time

from backend.core.structured_logging import get_logger
from backend.db.database import get_db
from backend.core.cache_manager import get_cache_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


class HealthChecker:
    """Comprehensive health checking for all dependencies"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL database connectivity"""
        start_time = time.time()
        
        try:
            # Try to execute a simple query
            db = next(get_db())
            result = db.execute("SELECT 1").scalar()
            
            latency_ms = (time.time() - start_time) * 1000
            
            if result == 1:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency_ms, 2),
                    "message": "Database connection successful"
                }
            else:
                return {
                    "status": "unhealthy",
                    "latency_ms": round(latency_ms, 2),
                    "error": "Unexpected query result"
                }
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.logger.error("database_health_check_failed", error=str(e))
            
            return {
                "status": "unhealthy",
                "latency_ms": round(latency_ms, 2),
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        start_time = time.time()
        
        try:
            cache_manager = get_cache_manager()
            
            # Try to ping Redis
            await cache_manager.redis.ping()
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = await cache_manager.redis.info()
            
            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "message": "Redis connection successful",
                "info": {
                    "version": info.get("redis_version"),
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients")
                }
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.logger.error("redis_health_check_failed", error=str(e))
            
            return {
                "status": "unhealthy",
                "latency_ms": round(latency_ms, 2),
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def check_milvus(self) -> Dict[str, Any]:
        """Check Milvus vector database connectivity"""
        start_time = time.time()
        
        try:
            from backend.core.milvus_pool import get_milvus_pool
            
            pool = get_milvus_pool()
            
            # Try to list collections
            async with pool.acquire() as client:
                collections = await client.list_collections()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "message": "Milvus connection successful",
                "info": {
                    "collections_count": len(collections)
                }
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.logger.error("milvus_health_check_failed", error=str(e))
            
            return {
                "status": "unhealthy",
                "latency_ms": round(latency_ms, 2),
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage("/")
            
            # Convert to GB
            total_gb = total / (1024 ** 3)
            used_gb = used / (1024 ** 3)
            free_gb = free / (1024 ** 3)
            usage_percent = (used / total) * 100
            
            # Consider unhealthy if less than 10% free
            is_healthy = usage_percent < 90
            
            return {
                "status": "healthy" if is_healthy else "degraded",
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "usage_percent": round(usage_percent, 2),
                "message": "Sufficient disk space" if is_healthy else "Low disk space warning"
            }
            
        except Exception as e:
            self.logger.error("disk_space_check_failed", error=str(e))
            
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    async def check_memory(self) -> Dict[str, Any]:
        """Check available memory"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            # Convert to GB
            total_gb = memory.total / (1024 ** 3)
            available_gb = memory.available / (1024 ** 3)
            used_gb = memory.used / (1024 ** 3)
            usage_percent = memory.percent
            
            # Consider unhealthy if more than 90% used
            is_healthy = usage_percent < 90
            
            return {
                "status": "healthy" if is_healthy else "degraded",
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "available_gb": round(available_gb, 2),
                "usage_percent": round(usage_percent, 2),
                "message": "Sufficient memory" if is_healthy else "High memory usage warning"
            }
            
        except Exception as e:
            self.logger.error("memory_check_failed", error=str(e))
            
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        start_time = time.time()
        
        # Run checks in parallel
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_milvus(),
            self.check_disk_space(),
            self.check_memory(),
            return_exceptions=True
        )
        
        # Process results
        results = {
            "database": checks[0] if not isinstance(checks[0], Exception) else {"status": "error", "error": str(checks[0])},
            "redis": checks[1] if not isinstance(checks[1], Exception) else {"status": "error", "error": str(checks[1])},
            "milvus": checks[2] if not isinstance(checks[2], Exception) else {"status": "error", "error": str(checks[2])},
            "disk": checks[3] if not isinstance(checks[3], Exception) else {"status": "error", "error": str(checks[3])},
            "memory": checks[4] if not isinstance(checks[4], Exception) else {"status": "error", "error": str(checks[4])},
        }
        
        # Determine overall status
        statuses = [check.get("status") for check in results.values()]
        
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        duration_ms = (time.time() - start_time) * 1000
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "duration_ms": round(duration_ms, 2),
            "checks": results
        }


# Initialize health checker
health_checker = HealthChecker()


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Kubernetes liveness probe - checks if application is running",
    status_code=status.HTTP_200_OK
)
async def liveness():
    """
    Liveness probe for Kubernetes
    
    Returns 200 if the application is alive.
    This should only fail if the application is completely broken.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Kubernetes readiness probe - checks if application can serve traffic",
    responses={
        200: {"description": "Application is ready"},
        503: {"description": "Application is not ready"}
    }
)
async def readiness():
    """
    Readiness probe for Kubernetes
    
    Returns 200 if the application is ready to serve traffic.
    Returns 503 if any critical dependency is unavailable.
    """
    result = await health_checker.check_all()
    
    if result["status"] == "healthy":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=result
        )


@router.get(
    "/startup",
    summary="Startup Probe",
    description="Kubernetes startup probe - checks if application has started",
    responses={
        200: {"description": "Application has started"},
        503: {"description": "Application is still starting"}
    }
)
async def startup():
    """
    Startup probe for Kubernetes
    
    Returns 200 once the application has fully started.
    This allows for slow-starting applications.
    """
    # Check critical dependencies only
    db_check = await health_checker.check_database()
    
    if db_check["status"] == "healthy":
        return {
            "status": "started",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "starting",
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "message": "Application is still starting"
            }
        )


@router.get(
    "/detailed",
    summary="Detailed Health Check",
    description="Comprehensive health check with all dependency details"
)
async def detailed_health():
    """
    Detailed health check with all dependency information
    
    Useful for monitoring dashboards and debugging.
    """
    return await health_checker.check_all()


@router.get(
    "/database",
    summary="Database Health",
    description="Check PostgreSQL database health"
)
async def database_health():
    """Check database health only"""
    return await health_checker.check_database()


@router.get(
    "/redis",
    summary="Redis Health",
    description="Check Redis cache health"
)
async def redis_health():
    """Check Redis health only"""
    return await health_checker.check_redis()


@router.get(
    "/milvus",
    summary="Milvus Health",
    description="Check Milvus vector database health"
)
async def milvus_health():
    """Check Milvus health only"""
    return await health_checker.check_milvus()


@router.get(
    "/resources",
    summary="Resource Usage",
    description="Check system resource usage (disk, memory)"
)
async def resource_health():
    """Check system resources"""
    disk = await health_checker.check_disk_space()
    memory = await health_checker.check_memory()
    
    return {
        "disk": disk,
        "memory": memory,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
