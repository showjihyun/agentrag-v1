"""
Application shutdown handlers.
"""

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


async def shutdown_handler():
    """
    Application shutdown handler.
    
    Cleans up all services and connections.
    """
    logger.info("Shutting down...")

    # Stop schedulers
    _stop_schedulers()
    
    # Cleanup connection pools
    await _cleanup_connection_pools()
    
    # Cleanup cache manager
    await _cleanup_cache_manager()
    
    # Cleanup task manager
    _cleanup_task_manager()
    
    # Cleanup service container
    await _cleanup_service_container()
    
    # Shutdown Agent Plugin System
    await _shutdown_agent_plugins()

    logger.info("Shutdown complete")


def _stop_schedulers():
    """Stop all schedulers."""
    # Stop background scheduler
    try:
        from backend.core.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop scheduler: {e}")
    
    # Stop KB cache scheduler
    try:
        from backend.core.kb_scheduler import stop_kb_scheduler
        stop_kb_scheduler()
        logger.info("KB cache scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop KB cache scheduler: {e}")


async def _cleanup_connection_pools():
    """Cleanup connection pools."""
    # Redis pool
    try:
        from backend.core.connection_pool import cleanup_redis_pool
        await cleanup_redis_pool()
        logger.info("Redis connection pool closed")
    except Exception as e:
        logger.warning(f"Failed to cleanup Redis pool: {e}")

    # Milvus pool
    try:
        from backend.core.milvus_pool import cleanup_milvus_pool
        await cleanup_milvus_pool()
        logger.info("Milvus connection pool closed")
    except Exception as e:
        logger.warning(f"Failed to cleanup Milvus pool: {e}")


async def _cleanup_cache_manager():
    """Cleanup cache manager."""
    try:
        from backend.core.cache_manager import cleanup_cache_manager
        await cleanup_cache_manager()
        logger.info("Cache manager cleaned up")
    except Exception as e:
        logger.warning(f"Failed to cleanup cache manager: {e}")


def _cleanup_task_manager():
    """Cleanup task manager."""
    try:
        from backend.core.background_tasks import cleanup_task_manager
        cleanup_task_manager()
        logger.info("Background task manager cleaned up")
    except Exception as e:
        logger.warning(f"Failed to cleanup task manager: {e}")


async def _cleanup_service_container():
    """Cleanup service container."""
    try:
        from backend.core.dependencies import cleanup_container
        await cleanup_container()
        logger.info("Service container cleaned up")
    except Exception as e:
        logger.warning(f"Failed to cleanup service container: {e}")


async def _shutdown_agent_plugins():
    """Shutdown Agent Plugin System."""
    try:
        from backend.app.lifecycle.agent_plugin_startup import shutdown_agent_plugins
        await shutdown_agent_plugins()
        logger.info("✅ Agent Plugin System shutdown completed")
    except Exception as e:
        logger.warning(f"Failed to shutdown Agent Plugin System: {e}")
