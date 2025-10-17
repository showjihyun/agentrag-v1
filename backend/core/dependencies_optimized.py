"""
Optimized Dependency Injection with Direct Agent Integration.

This module provides dependency injection for the optimized agent architecture
that removes MCP overhead for 50-70% latency reduction.
"""

import logging
from typing import Optional
from functools import lru_cache

from backend.config import settings
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.services.llm_manager import LLMManager
from backend.services.document_processor import DocumentProcessor
from backend.memory.stm import ShortTermMemory
from backend.memory.ltm import LongTermMemory
from backend.memory.manager import MemoryManager

# Import optimized direct agents
from backend.agents.vector_search_direct import VectorSearchAgentDirect
from backend.agents.local_data_direct import LocalDataAgentDirect
from backend.agents.web_search_direct import WebSearchAgentDirect

logger = logging.getLogger(__name__)


# ============================================================================
# Core Services (Singleton Pattern)
# ============================================================================


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """
    Get or create EmbeddingService singleton.

    Returns:
        EmbeddingService instance
    """
    logger.info(f"Initializing EmbeddingService: {settings.EMBEDDING_MODEL}")
    return EmbeddingService(model_name=settings.EMBEDDING_MODEL)


@lru_cache()
def get_milvus_manager() -> MilvusManager:
    """
    Get or create MilvusManager singleton.

    Returns:
        MilvusManager instance
    """
    embedding_service = get_embedding_service()

    logger.info(
        f"Initializing MilvusManager: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
    )

    manager = MilvusManager(
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
        collection_name=settings.MILVUS_COLLECTION_NAME,
        embedding_dim=embedding_service.dimension,
    )

    # Connect and ensure collection exists
    manager.connect()
    manager.create_collection()

    return manager


@lru_cache()
def get_llm_manager() -> LLMManager:
    """
    Get or create LLMManager singleton.

    Returns:
        LLMManager instance
    """
    logger.info(
        f"Initializing LLMManager: {settings.LLM_PROVIDER}/{settings.LLM_MODEL}"
    )

    return LLMManager(
        provider=None, model=settings.LLM_MODEL, enable_fallback=True
    )  # Will use settings.LLM_PROVIDER


@lru_cache()
def get_document_processor() -> DocumentProcessor:
    """
    Get or create DocumentProcessor singleton.

    Returns:
        DocumentProcessor instance
    """
    logger.info("Initializing DocumentProcessor")

    return DocumentProcessor(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        max_file_size=settings.MAX_FILE_SIZE,
    )


# ============================================================================
# Memory System
# ============================================================================


@lru_cache()
def get_short_term_memory() -> ShortTermMemory:
    """
    Get or create ShortTermMemory singleton.

    Returns:
        ShortTermMemory instance
    """
    logger.info(
        f"Initializing ShortTermMemory: {settings.REDIS_HOST}:{settings.REDIS_PORT}"
    )

    return ShortTermMemory(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        ttl=settings.STM_TTL,
    )


@lru_cache()
def get_long_term_memory() -> LongTermMemory:
    """
    Get or create LongTermMemory singleton.

    Returns:
        LongTermMemory instance
    """
    embedding_service = get_embedding_service()

    logger.info("Initializing LongTermMemory")

    return LongTermMemory(
        milvus_host=settings.MILVUS_HOST,
        milvus_port=settings.MILVUS_PORT,
        collection_name=settings.MILVUS_LTM_COLLECTION_NAME,
        embedding_service=embedding_service,
    )


@lru_cache()
def get_memory_manager() -> MemoryManager:
    """
    Get or create MemoryManager singleton.

    Returns:
        MemoryManager instance
    """
    stm = get_short_term_memory()
    ltm = get_long_term_memory()

    logger.info("Initializing MemoryManager")

    return MemoryManager(
        stm=stm, ltm=ltm, max_history_length=settings.MAX_CONVERSATION_HISTORY
    )


# ============================================================================
# Optimized Direct Agents
# ============================================================================


@lru_cache()
def get_vector_search_agent() -> VectorSearchAgentDirect:
    """
    Get or create VectorSearchAgentDirect singleton (optimized).

    Returns:
        VectorSearchAgentDirect instance
    """
    milvus = get_milvus_manager()
    embedding = get_embedding_service()

    logger.info("Initializing VectorSearchAgentDirect (optimized)")

    # Optional: Get cache manager if available
    cache_manager = None
    try:
        from backend.core.cache_manager import get_cache_manager
        from backend.core.connection_pool import get_redis_pool

        redis_pool = get_redis_pool()
        redis_client = redis_pool.get_client()
        cache_manager = get_cache_manager(redis_client)
    except Exception as e:
        logger.warning(f"Cache manager not available: {e}")

    return VectorSearchAgentDirect(
        milvus_manager=milvus, embedding_service=embedding, cache_manager=cache_manager
    )


@lru_cache()
def get_local_data_agent() -> LocalDataAgentDirect:
    """
    Get or create LocalDataAgentDirect singleton (optimized).

    Returns:
        LocalDataAgentDirect instance
    """
    logger.info("Initializing LocalDataAgentDirect (optimized)")

    # Configure allowed paths
    import os

    allowed_paths = [
        os.getcwd(),
        os.path.join(os.getcwd(), "backend", "uploads"),
        settings.LOCAL_STORAGE_PATH,
    ]

    return LocalDataAgentDirect(allowed_paths=allowed_paths)


@lru_cache()
def get_web_search_agent() -> WebSearchAgentDirect:
    """
    Get or create WebSearchAgentDirect singleton (optimized).

    Returns:
        WebSearchAgentDirect instance
    """
    logger.info("Initializing WebSearchAgentDirect (optimized)")

    # Optional: Get cache manager if available
    cache_manager = None
    try:
        from backend.core.cache_manager import get_cache_manager
        from backend.core.connection_pool import get_redis_pool

        redis_pool = get_redis_pool()
        redis_client = redis_pool.get_client()
        cache_manager = get_cache_manager(redis_client)
    except Exception as e:
        logger.warning(f"Cache manager not available: {e}")

    return WebSearchAgentDirect(
        max_calls_per_minute=10, timeout=10.0, cache_manager=cache_manager
    )


@lru_cache()
def get_aggregator_agent():
    """
    Get or create AggregatorAgent with optimized direct agents.

    Returns:
        AggregatorAgent instance
    """
    from backend.agents.aggregator import AggregatorAgent

    llm = get_llm_manager()
    memory = get_memory_manager()
    vector_agent = get_vector_search_agent()
    local_agent = get_local_data_agent()
    search_agent = get_web_search_agent()

    logger.info("Initializing AggregatorAgent with optimized direct agents")

    return AggregatorAgent(
        llm_manager=llm,
        memory_manager=memory,
        vector_agent=vector_agent,
        local_agent=local_agent,
        search_agent=search_agent,
        max_iterations=10,
    )


# ============================================================================
# Hybrid Query System (Speculative RAG)
# ============================================================================


@lru_cache()
def get_hybrid_query_router():
    """
    Get or create HybridQueryRouter for speculative RAG.

    Returns:
        HybridQueryRouter instance
    """
    from backend.core.hybrid_query_router import HybridQueryRouter

    aggregator = get_aggregator_agent()
    vector_agent = get_vector_search_agent()
    llm = get_llm_manager()

    logger.info("Initializing HybridQueryRouter (Speculative RAG)")

    return HybridQueryRouter(
        aggregator_agent=aggregator,
        vector_agent=vector_agent,
        llm_manager=llm,
        speculative_timeout=settings.SPECULATIVE_TIMEOUT,
        agentic_timeout=settings.AGENTIC_TIMEOUT,
    )


# ============================================================================
# Cleanup Functions
# ============================================================================


def cleanup_services():
    """
    Cleanup all services and close connections.

    Call this during application shutdown.
    """
    logger.info("Cleaning up services...")

    try:
        # Disconnect Milvus
        milvus = get_milvus_manager()
        milvus.disconnect()
        logger.info("Milvus disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting Milvus: {e}")

    try:
        # Close Redis connections
        stm = get_short_term_memory()
        stm.close()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

    # Clear LRU caches
    get_embedding_service.cache_clear()
    get_milvus_manager.cache_clear()
    get_llm_manager.cache_clear()
    get_document_processor.cache_clear()
    get_short_term_memory.cache_clear()
    get_long_term_memory.cache_clear()
    get_memory_manager.cache_clear()
    get_vector_search_agent.cache_clear()
    get_local_data_agent.cache_clear()
    get_web_search_agent.cache_clear()
    get_aggregator_agent.cache_clear()
    get_hybrid_query_router.cache_clear()

    logger.info("Service cleanup complete")


# ============================================================================
# Health Check
# ============================================================================


async def check_all_services_health() -> dict:
    """
    Check health of all services.

    Returns:
        Dictionary with health status of each service
    """
    health_status = {"overall": "healthy", "services": {}}

    # Check Milvus
    try:
        milvus = get_milvus_manager()
        milvus_health = milvus.health_check()
        health_status["services"]["milvus"] = milvus_health
        if milvus_health.get("status") != "healthy":
            health_status["overall"] = "degraded"
    except Exception as e:
        health_status["services"]["milvus"] = {"status": "unhealthy", "error": str(e)}
        health_status["overall"] = "unhealthy"

    # Check Redis
    try:
        stm = get_short_term_memory()
        redis_health = stm.health_check()
        health_status["services"]["redis"] = redis_health
        if redis_health.get("status") != "healthy":
            health_status["overall"] = "degraded"
    except Exception as e:
        health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["overall"] = "unhealthy"

    # Check Vector Search Agent
    try:
        vector_agent = get_vector_search_agent()
        vector_health = await vector_agent.health_check()
        health_status["services"]["vector_agent"] = {
            "status": "healthy" if vector_health else "unhealthy"
        }
        if not vector_health:
            health_status["overall"] = "degraded"
    except Exception as e:
        health_status["services"]["vector_agent"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["overall"] = "degraded"

    # Check Local Data Agent
    try:
        local_agent = get_local_data_agent()
        local_health = await local_agent.health_check()
        health_status["services"]["local_agent"] = {
            "status": "healthy" if local_health else "unhealthy"
        }
        if not local_health:
            health_status["overall"] = "degraded"
    except Exception as e:
        health_status["services"]["local_agent"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["overall"] = "degraded"

    # Check Web Search Agent
    try:
        search_agent = get_web_search_agent()
        search_health = await search_agent.health_check()
        health_status["services"]["search_agent"] = {
            "status": "healthy" if search_health else "unhealthy"
        }
        if not search_health:
            health_status["overall"] = "degraded"
    except Exception as e:
        health_status["services"]["search_agent"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["overall"] = "degraded"

    return health_status


# ============================================================================
# Service Information
# ============================================================================


def get_services_info() -> dict:
    """
    Get information about all initialized services.

    Returns:
        Dictionary with service information
    """
    info = {
        "optimization": "direct_integration",
        "mcp_removed": True,
        "expected_latency_improvement": "50-70%",
        "services": {},
    }

    try:
        vector_agent = get_vector_search_agent()
        info["services"]["vector_agent"] = vector_agent.get_agent_info()
    except:
        pass

    try:
        local_agent = get_local_data_agent()
        info["services"]["local_agent"] = local_agent.get_agent_info()
    except:
        pass

    try:
        search_agent = get_web_search_agent()
        info["services"]["search_agent"] = search_agent.get_agent_info()
    except:
        pass

    try:
        llm = get_llm_manager()
        info["services"]["llm"] = llm.get_provider_info()
    except:
        pass

    try:
        embedding = get_embedding_service()
        info["services"]["embedding"] = embedding.get_model_info()
    except:
        pass

    return info
