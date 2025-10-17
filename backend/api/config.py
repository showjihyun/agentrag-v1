"""
Configuration API endpoints for viewing and managing system configuration.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["configuration"])


class AdaptiveRoutingConfig(BaseModel):
    """Adaptive routing configuration response model"""

    enabled: bool
    complexity_thresholds: Dict[str, float]
    mode_timeouts: Dict[str, float]
    mode_parameters: Dict[str, int]
    mode_cache_ttls: Dict[str, int]
    auto_tuning: Dict[str, Any]
    pattern_learning: Dict[str, Any]
    target_distribution: Dict[str, float]


class SystemConfig(BaseModel):
    """System configuration response model"""

    llm_provider: str
    llm_model: str
    embedding_model: str
    speculative_rag_enabled: bool
    hybrid_rag_enabled: bool
    adaptive_routing_enabled: bool


@router.get("/adaptive", response_model=AdaptiveRoutingConfig)
async def get_adaptive_routing_config():
    """
    Get adaptive routing configuration.

    Returns current configuration for:
    - Complexity thresholds
    - Mode timeouts and parameters
    - Caching configuration
    - Auto-tuning settings
    - Pattern learning settings
    - Target mode distribution

    **Example Response:**
    ```json
    {
        "enabled": true,
        "complexity_thresholds": {
            "simple": 0.35,
            "complex": 0.70
        },
        "mode_timeouts": {
            "fast": 1.0,
            "balanced": 3.0,
            "deep": 15.0
        },
        "mode_parameters": {
            "fast_top_k": 5,
            "balanced_top_k": 10,
            "deep_top_k": 15
        },
        "mode_cache_ttls": {
            "fast": 3600,
            "balanced": 1800,
            "deep": 7200
        },
        "auto_tuning": {
            "enabled": true,
            "interval_hours": 24,
            "min_samples": 1000,
            "dry_run": true
        },
        "pattern_learning": {
            "enabled": true,
            "min_samples": 100,
            "similarity_threshold": 0.8,
            "window_days": 30
        },
        "target_distribution": {
            "fast": 0.45,
            "balanced": 0.35,
            "deep": 0.20
        }
    }
    ```
    """
    try:
        config = AdaptiveRoutingConfig(
            enabled=settings.ADAPTIVE_ROUTING_ENABLED,
            complexity_thresholds={
                "simple": settings.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE,
                "complex": settings.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX,
            },
            mode_timeouts={
                "fast": settings.FAST_MODE_TIMEOUT,
                "balanced": settings.BALANCED_MODE_TIMEOUT,
                "deep": settings.DEEP_MODE_TIMEOUT,
            },
            mode_parameters={
                "fast_top_k": settings.FAST_MODE_TOP_K,
                "balanced_top_k": settings.BALANCED_MODE_TOP_K,
                "deep_top_k": settings.DEEP_MODE_TOP_K,
            },
            mode_cache_ttls={
                "fast": settings.FAST_MODE_CACHE_TTL,
                "balanced": settings.BALANCED_MODE_CACHE_TTL,
                "deep": settings.DEEP_MODE_CACHE_TTL,
            },
            auto_tuning={
                "enabled": settings.ENABLE_AUTO_THRESHOLD_TUNING,
                "interval_hours": settings.TUNING_INTERVAL_HOURS,
                "min_samples": settings.TUNING_MIN_SAMPLES,
                "dry_run": settings.TUNING_DRY_RUN,
            },
            pattern_learning={
                "enabled": settings.ENABLE_PATTERN_LEARNING,
                "min_samples": settings.MIN_SAMPLES_FOR_LEARNING,
                "similarity_threshold": settings.PATTERN_SIMILARITY_THRESHOLD,
                "window_days": settings.PATTERN_LEARNING_WINDOW_DAYS,
            },
            target_distribution={
                "fast": settings.TARGET_FAST_MODE_PERCENTAGE,
                "balanced": settings.TARGET_BALANCED_MODE_PERCENTAGE,
                "deep": settings.TARGET_DEEP_MODE_PERCENTAGE,
            },
        )

        logger.info("Adaptive routing configuration retrieved successfully")
        return config

    except Exception as e:
        logger.error(f"Error retrieving adaptive routing configuration: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.get("/system", response_model=SystemConfig)
async def get_system_config():
    """
    Get high-level system configuration.

    Returns basic system configuration including:
    - LLM provider and model
    - Embedding model
    - Feature flags (Speculative RAG, Hybrid RAG, Adaptive Routing)

    **Example Response:**
    ```json
    {
        "llm_provider": "ollama",
        "llm_model": "llama3.1",
        "embedding_model": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "speculative_rag_enabled": true,
        "hybrid_rag_enabled": true,
        "adaptive_routing_enabled": true
    }
    ```
    """
    try:
        config = SystemConfig(
            llm_provider=settings.LLM_PROVIDER,
            llm_model=settings.LLM_MODEL,
            embedding_model=settings.EMBEDDING_MODEL,
            speculative_rag_enabled=settings.ENABLE_SPECULATIVE_RAG,
            hybrid_rag_enabled=settings.HYBRID_RAG_ENABLED,
            adaptive_routing_enabled=settings.ADAPTIVE_ROUTING_ENABLED,
        )

        logger.info("System configuration retrieved successfully")
        return config

    except Exception as e:
        logger.error(f"Error retrieving system configuration: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.get("/all")
async def get_all_config():
    """
    Get all configuration settings (for debugging/admin purposes).

    Returns a comprehensive view of all configuration settings.

    **Note:** This endpoint exposes sensitive configuration details.
    In production, this should be protected with authentication.

    **Example Response:**
    ```json
    {
        "system": {...},
        "adaptive_routing": {...},
        "llm": {...},
        "database": {...},
        "caching": {...},
        "performance": {...}
    }
    ```
    """
    try:
        config = {
            "system": {
                "llm_provider": settings.LLM_PROVIDER,
                "llm_model": settings.LLM_MODEL,
                "embedding_model": settings.EMBEDDING_MODEL,
                "debug": settings.DEBUG,
                "log_level": settings.LOG_LEVEL,
            },
            "adaptive_routing": {
                "enabled": settings.ADAPTIVE_ROUTING_ENABLED,
                "complexity_thresholds": {
                    "simple": settings.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE,
                    "complex": settings.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX,
                },
                "mode_timeouts": {
                    "fast": settings.FAST_MODE_TIMEOUT,
                    "balanced": settings.BALANCED_MODE_TIMEOUT,
                    "deep": settings.DEEP_MODE_TIMEOUT,
                },
                "mode_parameters": {
                    "fast_top_k": settings.FAST_MODE_TOP_K,
                    "balanced_top_k": settings.BALANCED_MODE_TOP_K,
                    "deep_top_k": settings.DEEP_MODE_TOP_K,
                },
                "mode_cache_ttls": {
                    "fast": settings.FAST_MODE_CACHE_TTL,
                    "balanced": settings.BALANCED_MODE_CACHE_TTL,
                    "deep": settings.DEEP_MODE_CACHE_TTL,
                },
                "auto_tuning": {
                    "enabled": settings.ENABLE_AUTO_THRESHOLD_TUNING,
                    "interval_hours": settings.TUNING_INTERVAL_HOURS,
                    "min_samples": settings.TUNING_MIN_SAMPLES,
                    "dry_run": settings.TUNING_DRY_RUN,
                },
                "pattern_learning": {
                    "enabled": settings.ENABLE_PATTERN_LEARNING,
                    "min_samples": settings.MIN_SAMPLES_FOR_LEARNING,
                    "similarity_threshold": settings.PATTERN_SIMILARITY_THRESHOLD,
                    "window_days": settings.PATTERN_LEARNING_WINDOW_DAYS,
                },
                "target_distribution": {
                    "fast": settings.TARGET_FAST_MODE_PERCENTAGE,
                    "balanced": settings.TARGET_BALANCED_MODE_PERCENTAGE,
                    "deep": settings.TARGET_DEEP_MODE_PERCENTAGE,
                },
            },
            "llm": {
                "provider": settings.LLM_PROVIDER,
                "model": settings.LLM_MODEL,
                "timeout_local": settings.LLM_TIMEOUT_LOCAL,
                "timeout_cloud": settings.LLM_TIMEOUT_CLOUD,
                "fallback_providers": settings.get_fallback_providers(),
            },
            "database": {
                "milvus": {
                    "host": settings.MILVUS_HOST,
                    "port": settings.MILVUS_PORT,
                    "collection": settings.MILVUS_COLLECTION_NAME,
                    "ltm_collection": settings.MILVUS_LTM_COLLECTION_NAME,
                    "pool_size": settings.MILVUS_POOL_SIZE,
                },
                "redis": {
                    "host": settings.REDIS_HOST,
                    "port": settings.REDIS_PORT,
                    "db": settings.REDIS_DB,
                    "max_connections": settings.REDIS_MAX_CONNECTIONS,
                },
                "postgres": {
                    "host": settings.POSTGRES_HOST,
                    "port": settings.POSTGRES_PORT,
                    "database": settings.POSTGRES_DB,
                    "pool_size": settings.DB_POOL_SIZE,
                    "max_overflow": settings.DB_MAX_OVERFLOW,
                },
            },
            "caching": {
                "search_cache_enabled": settings.ENABLE_SEARCH_CACHE,
                "l1_ttl": settings.CACHE_L1_TTL,
                "l2_threshold": settings.CACHE_L2_THRESHOLD,
                "l2_max_size": settings.CACHE_L2_MAX_SIZE,
                "llm_cache_enabled": settings.ENABLE_LLM_CACHE,
                "llm_cache_ttl": settings.LLM_CACHE_TTL,
            },
            "performance": {
                "speculative_rag_enabled": settings.ENABLE_SPECULATIVE_RAG,
                "speculative_timeout": settings.SPECULATIVE_TIMEOUT,
                "agentic_timeout": settings.AGENTIC_TIMEOUT,
                "use_direct_agents": settings.USE_DIRECT_AGENTS,
                "use_optimized_react": settings.USE_OPTIMIZED_REACT,
                "background_tasks_enabled": settings.ENABLE_BACKGROUND_TASKS,
                "max_concurrent_tasks": settings.MAX_CONCURRENT_TASKS,
            },
            "document_processing": {
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "chunking_strategy": settings.CHUNKING_STRATEGY,
                "max_file_size": settings.MAX_FILE_SIZE,
                "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
                "max_batch_files": settings.MAX_BATCH_FILES,
                "max_batch_size_mb": settings.MAX_BATCH_SIZE_MB,
            },
            "hybrid_rag": {
                "enabled": settings.HYBRID_RAG_ENABLED,
                "complexity_thresholds": {
                    "simple": settings.COMPLEXITY_THRESHOLD_SIMPLE,
                    "complex": settings.COMPLEXITY_THRESHOLD_COMPLEX,
                },
                "confidence_thresholds": {
                    "high": settings.CONFIDENCE_THRESHOLD_HIGH,
                    "low": settings.CONFIDENCE_THRESHOLD_LOW,
                },
                "static_rag": {
                    "top_k": settings.STATIC_RAG_TOP_K,
                    "timeout": settings.STATIC_RAG_TIMEOUT,
                    "cache_enabled": settings.ENABLE_STATIC_RAG_CACHE,
                    "cache_ttl": settings.STATIC_RAG_CACHE_TTL,
                },
                "agentic_rag": {"max_iterations": settings.AGENTIC_RAG_MAX_ITERATIONS},
                "auto_escalation": settings.ENABLE_AUTO_ESCALATION,
            },
        }

        logger.info("All configuration retrieved successfully")
        return config

    except Exception as e:
        logger.error(f"Error retrieving all configuration: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve configuration: {str(e)}"
        )
