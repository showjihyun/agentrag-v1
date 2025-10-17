"""
Comprehensive Health Check System

Provides detailed health checks for all system components:
- Database connections
- Redis cache
- Milvus vector database
- LLM providers
- File storage
- Background tasks
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import time

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentHealth:
    """Health status for a single component."""

    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None,
    ):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.response_time_ms = response_time_ms
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "status": self.status.value,
            "timestamp": self.timestamp,
        }

        if self.message:
            result["message"] = self.message

        if self.details:
            result["details"] = self.details

        if self.response_time_ms is not None:
            result["response_time_ms"] = round(self.response_time_ms, 2)

        return result


class HealthChecker:
    """
    Comprehensive health checker for all system components.
    """

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_check_time: Optional[datetime] = None
        self.last_results: Dict[str, ComponentHealth] = {}
        self._lock = asyncio.Lock()

    def register_check(
        self, name: str, check_func: Callable, critical: bool = True
    ) -> None:
        """
        Register a health check.

        Args:
            name: Component name
            check_func: Async function that returns ComponentHealth
            critical: Whether this component is critical for system health
        """
        self.checks[name] = {"func": check_func, "critical": critical}
        logger.info(f"Registered health check: {name} (critical={critical})")

    async def check_component(self, name: str, timeout: float = 5.0) -> ComponentHealth:
        """
        Check health of a single component.

        Args:
            name: Component name
            timeout: Timeout in seconds

        Returns:
            ComponentHealth instance
        """
        if name not in self.checks:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"No health check registered for {name}",
            )

        check_info = self.checks[name]
        check_func = check_info["func"]

        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(check_func(), timeout=timeout)

            response_time = (time.time() - start_time) * 1000
            result.response_time_ms = response_time

            return result

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {timeout}s",
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Health check failed for {name}: {e}")
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=response_time,
            )

    async def check_all(self, timeout_per_check: float = 5.0) -> Dict[str, Any]:
        """
        Check health of all registered components.

        Args:
            timeout_per_check: Timeout per component check

        Returns:
            Dictionary with overall health status and component details
        """
        async with self._lock:
            start_time = time.time()

            # Run all checks concurrently
            check_tasks = {
                name: self.check_component(name, timeout_per_check)
                for name in self.checks.keys()
            }

            results = await asyncio.gather(
                *check_tasks.values(), return_exceptions=True
            )

            # Process results
            component_results = {}
            critical_failures = []
            degraded_components = []

            for name, result in zip(check_tasks.keys(), results):
                if isinstance(result, Exception):
                    result = ComponentHealth(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Check failed: {str(result)}",
                    )

                component_results[name] = result

                # Track failures
                if result.status == HealthStatus.UNHEALTHY:
                    if self.checks[name]["critical"]:
                        critical_failures.append(name)
                elif result.status == HealthStatus.DEGRADED:
                    degraded_components.append(name)

            # Determine overall status
            if critical_failures:
                overall_status = HealthStatus.UNHEALTHY
            elif degraded_components:
                overall_status = HealthStatus.DEGRADED
            else:
                overall_status = HealthStatus.HEALTHY

            # Calculate total response time
            total_response_time = (time.time() - start_time) * 1000

            # Store results
            self.last_check_time = datetime.utcnow()
            self.last_results = component_results

            # Build response
            response = {
                "status": overall_status.value,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "response_time_ms": round(total_response_time, 2),
                "components": {
                    name: result.to_dict() for name, result in component_results.items()
                },
            }

            if critical_failures:
                response["critical_failures"] = critical_failures

            if degraded_components:
                response["degraded_components"] = degraded_components

            return response

    async def get_last_results(self) -> Optional[Dict[str, Any]]:
        """Get results from last health check."""
        if not self.last_results:
            return None

        return {
            "timestamp": (
                self.last_check_time.isoformat() + "Z" if self.last_check_time else None
            ),
            "components": {
                name: result.to_dict() for name, result in self.last_results.items()
            },
        }


# Health check implementations


async def check_database_health(db_session_factory) -> ComponentHealth:
    """Check PostgreSQL database health."""
    try:
        from sqlalchemy import text

        start_time = time.time()

        # Test connection
        async with db_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()

        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection successful",
            details={"type": "PostgreSQL", "query_time_ms": round(response_time, 2)},
        )

    except Exception as e:
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}",
        )


async def check_redis_health(redis_client) -> ComponentHealth:
    """Check Redis health."""
    try:
        start_time = time.time()

        # Test ping
        await redis_client.ping()

        # Get info
        info = await redis_client.info("memory")

        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Redis connection successful",
            details={
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", "N/A"),
                "ping_time_ms": round(response_time, 2),
            },
        )

    except Exception as e:
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=f"Redis connection failed: {str(e)}",
        )


async def check_milvus_health(milvus_manager) -> ComponentHealth:
    """Check Milvus vector database health."""
    try:
        start_time = time.time()

        # Get health info
        health_info = milvus_manager.health_check()

        response_time = (time.time() - start_time) * 1000

        if health_info.get("status") == "healthy":
            status = HealthStatus.HEALTHY
            message = "Milvus connection successful"
        else:
            status = HealthStatus.DEGRADED
            message = health_info.get("error", "Milvus connection degraded")

        return ComponentHealth(
            name="milvus",
            status=status,
            message=message,
            details={
                "host": health_info.get("host"),
                "port": health_info.get("port"),
                "collection_exists": health_info.get("collection_exists"),
                "num_entities": health_info.get("num_entities", "N/A"),
                "check_time_ms": round(response_time, 2),
            },
        )

    except Exception as e:
        return ComponentHealth(
            name="milvus",
            status=HealthStatus.UNHEALTHY,
            message=f"Milvus health check failed: {str(e)}",
        )


async def check_llm_health(llm_manager) -> ComponentHealth:
    """Check LLM provider health."""
    try:
        start_time = time.time()

        # Simple test - just check if manager is initialized
        provider = llm_manager.provider.value
        model = llm_manager.model

        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name="llm",
            status=HealthStatus.HEALTHY,
            message="LLM provider available",
            details={
                "provider": provider,
                "model": model,
                "check_time_ms": round(response_time, 2),
            },
        )

    except Exception as e:
        return ComponentHealth(
            name="llm",
            status=HealthStatus.UNHEALTHY,
            message=f"LLM provider check failed: {str(e)}",
        )


async def check_embedding_health(embedding_service) -> ComponentHealth:
    """Check embedding service health."""
    try:
        start_time = time.time()

        # Test with simple text
        test_text = "health check"
        embedding = await embedding_service.embed_text(test_text)

        response_time = (time.time() - start_time) * 1000

        if embedding and len(embedding) == embedding_service.dimension:
            status = HealthStatus.HEALTHY
            message = "Embedding service operational"
        else:
            status = HealthStatus.DEGRADED
            message = "Embedding service returned unexpected result"

        return ComponentHealth(
            name="embedding",
            status=status,
            message=message,
            details={
                "model": embedding_service.model_name,
                "dimension": embedding_service.dimension,
                "test_time_ms": round(response_time, 2),
            },
        )

    except Exception as e:
        return ComponentHealth(
            name="embedding",
            status=HealthStatus.UNHEALTHY,
            message=f"Embedding service check failed: {str(e)}",
        )


async def check_cache_health(cache_manager) -> ComponentHealth:
    """Check cache system health."""
    try:
        start_time = time.time()

        # Get cache stats
        stats = await cache_manager.get_stats()

        response_time = (time.time() - start_time) * 1000

        # Check if L1 and L2 are operational
        l1_ok = stats.get("enabled", {}).get("l1", False)
        l2_ok = stats.get("l2", {}).get("connected", False) if "l2" in stats else False

        if l1_ok and l2_ok:
            status = HealthStatus.HEALTHY
            message = "Cache system operational"
        elif l1_ok or l2_ok:
            status = HealthStatus.DEGRADED
            message = "Cache system partially operational"
        else:
            status = HealthStatus.UNHEALTHY
            message = "Cache system unavailable"

        return ComponentHealth(
            name="cache",
            status=status,
            message=message,
            details={
                "l1_enabled": l1_ok,
                "l2_enabled": l2_ok,
                "l1_stats": stats.get("l1", {}),
                "check_time_ms": round(response_time, 2),
            },
        )

    except Exception as e:
        return ComponentHealth(
            name="cache",
            status=HealthStatus.DEGRADED,
            message=f"Cache check failed: {str(e)}",
        )


async def check_storage_health(file_storage_service) -> ComponentHealth:
    """Check file storage health."""
    try:
        start_time = time.time()

        # Check storage backend
        backend = file_storage_service.backend

        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name="storage",
            status=HealthStatus.HEALTHY,
            message="File storage operational",
            details={"backend": backend, "check_time_ms": round(response_time, 2)},
        )

    except Exception as e:
        return ComponentHealth(
            name="storage",
            status=HealthStatus.UNHEALTHY,
            message=f"Storage check failed: {str(e)}",
        )


async def check_background_tasks_health(task_manager) -> ComponentHealth:
    """Check background task system health."""
    try:
        start_time = time.time()

        # Get task stats
        stats = task_manager.get_stats()

        response_time = (time.time() - start_time) * 1000

        # Check if task manager is healthy
        active_tasks = stats.get("active_tasks", 0)
        max_tasks = stats.get("max_concurrent_tasks", 0)

        if active_tasks < max_tasks:
            status = HealthStatus.HEALTHY
            message = "Background task system operational"
        else:
            status = HealthStatus.DEGRADED
            message = "Background task system at capacity"

        return ComponentHealth(
            name="background_tasks",
            status=status,
            message=message,
            details={
                "active_tasks": active_tasks,
                "max_tasks": max_tasks,
                "total_processed": stats.get("total_processed", 0),
                "check_time_ms": round(response_time, 2),
            },
        )

    except Exception as e:
        return ComponentHealth(
            name="background_tasks",
            status=HealthStatus.DEGRADED,
            message=f"Background tasks check failed: {str(e)}",
        )


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get or create global health checker."""
    global _health_checker

    if _health_checker is None:
        _health_checker = HealthChecker()

    return _health_checker


async def initialize_health_checks(container) -> None:
    """
    Initialize all health checks with service container.

    Args:
        container: Service container with all dependencies
    """
    checker = get_health_checker()

    # Register all health checks
    checker.register_check(
        "database",
        lambda: check_database_health(container.get_db_session),
        critical=True,
    )

    checker.register_check(
        "redis", lambda: check_redis_health(container.get_redis_client()), critical=True
    )

    checker.register_check(
        "milvus",
        lambda: check_milvus_health(container.get_milvus_manager()),
        critical=True,
    )

    checker.register_check(
        "llm", lambda: check_llm_health(container.get_llm_manager()), critical=True
    )

    checker.register_check(
        "embedding",
        lambda: check_embedding_health(container.get_embedding_service()),
        critical=True,
    )

    checker.register_check(
        "cache",
        lambda: check_cache_health(container.get_cache_manager()),
        critical=False,  # Non-critical, system can work without cache
    )

    try:
        checker.register_check(
            "storage",
            lambda: check_storage_health(container.get_file_storage_service()),
            critical=True,
        )
    except:
        pass  # Storage service might not be available

    try:
        checker.register_check(
            "background_tasks",
            lambda: check_background_tasks_health(container.get_task_manager()),
            critical=False,
        )
    except:
        pass  # Background tasks might not be available

    logger.info(f"Initialized {len(checker.checks)} health checks")
