"""
Application startup handlers.
"""

from backend.config import settings
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


async def startup_handler():
    """
    Application startup handler.
    
    Initializes all services and connections.
    """
    logger.info("Starting up Agentic RAG System...")

    try:
        # Initialize Sentry error tracking
        await _initialize_sentry()
        
        # Initialize service container
        await _initialize_service_container()
        
        # Initialize connection pools
        await _initialize_connection_pools()
        
        # Initialize cache manager
        await _initialize_cache_manager()
        
        # Initialize embedding configuration
        await _initialize_embedding_config()
        
        # Initialize background task manager
        _initialize_task_manager()
        
        # Initialize health checks
        await _initialize_health_checks()
        
        # Initialize ColPali processor
        await _initialize_colpali()
        
        # Initialize cache warmer
        await _initialize_cache_warmer()
        
        # Initialize tool integrations
        await _initialize_tools()
        
        # Start background scheduler
        _start_scheduler()
        
        # Start KB cache scheduler
        _start_kb_scheduler()
        
        # Initialize Agent Plugin System
        await _initialize_agent_plugins()

        logger.info(
            "Startup complete!", system_version="1.0.0", debug_mode=settings.DEBUG
        )

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise


async def _initialize_sentry():
    """Initialize Sentry error tracking."""
    try:
        from backend.services.sentry_service import initialize_sentry
        sentry_initialized = initialize_sentry(
            environment="production" if not settings.DEBUG else "development",
            enable_tracing=not settings.DEBUG,
        )
        if sentry_initialized:
            logger.info("Sentry error tracking initialized")
    except Exception as e:
        logger.warning(f"Sentry initialization failed: {e}")


async def _initialize_service_container():
    """Initialize service container."""
    from backend.core.dependencies import initialize_container
    await initialize_container()
    logger.info("Service container initialized")


async def _initialize_connection_pools():
    """Initialize connection pools."""
    from backend.core.connection_pool import get_redis_pool
    from backend.core.milvus_pool import get_milvus_pool

    # Redis pool
    redis_pool = get_redis_pool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )
    logger.info("Redis connection pool initialized")

    # Milvus pool
    milvus_pool = get_milvus_pool(
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
        pool_size=settings.MILVUS_POOL_SIZE,
    )
    await milvus_pool.initialize()
    logger.info("Milvus connection pool initialized")


async def _initialize_cache_manager():
    """Initialize cache manager."""
    from backend.core.cache_manager import get_cache_manager
    from backend.core.connection_pool import get_redis_pool

    redis_pool = get_redis_pool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )
    redis_client = redis_pool.get_client()
    cache_manager = get_cache_manager(redis_client)
    await cache_manager.start_cleanup_task()
    logger.info("Cache manager initialized")


async def _initialize_embedding_config():
    """Initialize embedding configuration."""
    try:
        from backend.services.system_config_service import SystemConfigService
        await SystemConfigService.initialize_embedding_config()
        logger.info("Embedding configuration initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize embedding config: {e}")


def _initialize_task_manager():
    """Initialize background task manager."""
    from backend.core.background_tasks import get_task_manager
    get_task_manager()
    logger.info("Background task manager initialized")


async def _initialize_health_checks():
    """Initialize health checks."""
    from backend.core.health_check import initialize_health_checks
    from backend.core.dependencies import get_container

    container = get_container()
    await initialize_health_checks(container)
    logger.info("Health checks initialized")


async def _initialize_colpali():
    """Initialize ColPali processor."""
    try:
        logger.info("Initializing ColPali processor...")
        from backend.services.colpali_processor import get_colpali_processor
        
        colpali = get_colpali_processor()
        if colpali:
            logger.info(f"✅ ColPali initialized: model={colpali.model_name}, device={colpali.device}")
        else:
            logger.warning("⚠️  ColPali not available")
    except Exception as e:
        logger.warning(f"ColPali initialization failed: {e}")


async def _initialize_cache_warmer():
    """Initialize cache warmer."""
    try:
        import asyncio
        from backend.services.cache_warmer import get_cache_warmer
        from backend.services.speculative_processor import SpeculativeProcessor
        from backend.services.embedding import EmbeddingService
        from backend.services.milvus import MilvusManager
        from backend.services.llm_manager import LLMManager
        from backend.core.connection_pool import get_redis_pool
        
        redis_pool = get_redis_pool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )
        redis_client = redis_pool.get_client()
        
        # Get services
        embedding_service = EmbeddingService()
        milvus_manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION_NAME,
            embedding_dim=embedding_service.dimension,
        )
        llm_manager = LLMManager()
        
        # Create speculative processor
        speculative_processor = SpeculativeProcessor(
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            llm_manager=llm_manager,
            redis_client=redis_client
        )
        
        # Initialize cache warmer
        cache_warmer = get_cache_warmer(
            speculative_processor=speculative_processor,
            redis_client=redis_client
        )
        
        # Warm cache on startup (non-blocking)
        asyncio.create_task(cache_warmer.warm_cache_on_startup())
        logger.info("Cache warming scheduled")
        
    except Exception as e:
        logger.warning(f"Failed to initialize cache warmer: {e}")


async def _initialize_tools():
    """Initialize tool integrations."""
    try:
        from backend.core.tools.init_tools import initialize_tools, get_tool_summary
        
        tool_count = initialize_tools()
        tool_summary = get_tool_summary()
        
        logger.info(
            f"Tool integrations initialized: {tool_count} tools across "
            f"{len(tool_summary['categories'])} categories"
        )
        
        for category, count in tool_summary['by_category'].items():
            logger.info(f"  - {category}: {count} tools")
        
        # Sync tools to database
        try:
            from backend.core.tools.sync_tools_to_db import sync_tools_to_database
            from backend.db.database import SessionLocal
            
            db = SessionLocal()
            try:
                synced_count = sync_tools_to_database(db)
                logger.info(f"✅ Synced {synced_count} tools to database")
            finally:
                db.close()
        except Exception as sync_error:
            logger.warning(f"Failed to sync tools to database: {sync_error}")
            
    except Exception as e:
        logger.warning(f"Failed to initialize tool integrations: {e}")


def _start_scheduler():
    """Start background scheduler."""
    try:
        from backend.core.scheduler import start_scheduler
        start_scheduler()
        logger.info("Background scheduler started (memory cleanup at 3 AM daily)")
    except Exception as e:
        logger.warning(f"Failed to start background scheduler: {e}")


def _start_kb_scheduler():
    """Start KB cache scheduler."""
    try:
        from backend.core.kb_scheduler import start_kb_scheduler
        start_kb_scheduler()
        logger.info("KB cache scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start KB cache scheduler: {e}")


async def _initialize_agent_plugins():
    """Initialize Agent Plugin System."""
    try:
        from backend.app.lifecycle.agent_plugin_startup import initialize_agent_plugins
        
        success = await initialize_agent_plugins()
        if success:
            logger.info("✅ Agent Plugin System initialized successfully")
        else:
            logger.warning("⚠️  Agent Plugin System initialization failed - continuing without agent features")
            
    except Exception as e:
        logger.warning(f"Failed to initialize Agent Plugin System: {e} - continuing without agent features")
