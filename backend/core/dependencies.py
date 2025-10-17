"""
Dependency Injection Container for FastAPI.

Provides centralized dependency management with proper lifecycle handling.
"""

import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as redis

from backend.config import settings
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.services.llm_manager import LLMManager, LLMProvider
from backend.services.document_processor import DocumentProcessor
from backend.memory.stm import ShortTermMemory
from backend.memory.ltm import LongTermMemory
from backend.memory.manager import MemoryManager
from backend.mcp.manager import MCPServerManager
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.local_data import LocalDataAgent
from backend.agents.web_search import WebSearchAgent
from backend.agents.aggregator import AggregatorAgent
from backend.services.hybrid_search import (
    HybridSearchService,
    get_hybrid_search_service,
)
from backend.services.search_cache import SearchCacheManager
from backend.services.query_expansion import QueryExpansionService
from backend.services.reranker import RerankerService
from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.response_coordinator import ResponseCoordinator
from backend.services.hybrid_query_router import HybridQueryRouter
from backend.services.performance_monitor import PerformanceMonitor
from backend.services.intelligent_mode_router import IntelligentModeRouter
from backend.services.adaptive_rag_service import AdaptiveRAGService

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Dependency Injection Container for managing service lifecycle.

    Provides singleton instances of services with proper initialization
    and cleanup. Supports testing by allowing service replacement.
    """

    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._embedding_service: Optional[EmbeddingService] = None
        self._milvus_manager: Optional[MilvusManager] = None
        self._llm_manager: Optional[LLMManager] = None
        self._document_processor: Optional[DocumentProcessor] = None
        self._memory_manager: Optional[MemoryManager] = None
        self._mcp_manager: Optional[MCPServerManager] = None
        self._aggregator_agent: Optional[AggregatorAgent] = None
        self._hybrid_search_manager: Optional[HybridSearchService] = None
        self._search_cache_manager: Optional[SearchCacheManager] = None
        self._query_expansion_service: Optional[QueryExpansionService] = None
        self._reranker_service: Optional[RerankerService] = None
        self._speculative_processor: Optional[SpeculativeProcessor] = None
        self._response_coordinator: Optional[ResponseCoordinator] = None
        self._hybrid_query_router: Optional[HybridQueryRouter] = None
        self._performance_monitor: Optional[PerformanceMonitor] = None
        self._adaptive_rag_service: Optional[AdaptiveRAGService] = None
        self._intelligent_mode_router: Optional[IntelligentModeRouter] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all services."""
        if self._initialized:
            logger.warning("ServiceContainer already initialized")
            return

        logger.info("Initializing ServiceContainer...")

        try:
            # Initialize Redis with connection pool
            logger.info("Connecting to Redis...")
            from backend.core.connection_pool import get_redis_pool

            redis_pool = get_redis_pool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
            )
            self._redis_client = redis_pool.get_client()
            await self._redis_client.ping()
            logger.info(
                f"Redis connected successfully with connection pool (max_connections={settings.REDIS_MAX_CONNECTIONS})"
            )

            # Initialize Embedding Service
            logger.info("Initializing Embedding Service...")
            self._embedding_service = EmbeddingService(
                model_name=settings.EMBEDDING_MODEL
            )
            logger.info(
                f"Embedding Service initialized with model: {settings.EMBEDDING_MODEL}"
            )

            # Initialize Milvus Manager
            logger.info("Connecting to Milvus...")
            self._milvus_manager = MilvusManager(
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                collection_name=settings.MILVUS_COLLECTION_NAME,
                embedding_dim=self._embedding_service.dimension,
            )
            self._milvus_manager.connect()
            logger.info("Milvus connected successfully")

            # Initialize LLM Manager
            logger.info("Initializing LLM Manager...")
            self._llm_manager = LLMManager(
                provider=LLMProvider(settings.LLM_PROVIDER), model=settings.LLM_MODEL
            )
            logger.info(
                f"LLM Manager initialized with provider: {settings.LLM_PROVIDER}"
            )

            # Initialize Document Processor
            logger.info("Initializing Document Processor...")
            self._document_processor = DocumentProcessor(
                chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
            )
            logger.info("Document Processor initialized")

            # Initialize Memory System
            logger.info("Initializing Memory System...")
            stm = ShortTermMemory(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                ttl=3600,
            )

            # Initialize LTM with separate Milvus collection
            logger.info("Initializing LTM with separate Milvus collection...")
            ltm_milvus = MilvusManager(
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                collection_name="long_term_memory",  # Separate collection for LTM
                embedding_dim=self._embedding_service.dimension,
            )
            ltm_milvus.connect()

            # Create LTM collection with appropriate schema
            from backend.models.milvus_schema import get_ltm_collection_schema

            ltm_schema = get_ltm_collection_schema(self._embedding_service.dimension)
            ltm_milvus.create_collection(schema=ltm_schema, drop_existing=False)
            logger.info("LTM Milvus collection initialized")

            ltm = LongTermMemory(
                milvus_manager=ltm_milvus, embedding_service=self._embedding_service
            )
            self._memory_manager = MemoryManager(stm=stm, ltm=ltm)
            logger.info("Memory System initialized")

            # Initialize advanced search services
            logger.info("Initializing advanced search services...")

            # Hybrid Search Manager
            if settings.ENABLE_HYBRID_SEARCH:
                self._hybrid_search_manager = get_hybrid_search_service(
                    vector_weight=settings.VECTOR_SEARCH_WEIGHT,
                    bm25_weight=settings.KEYWORD_SEARCH_WEIGHT,
                )
                logger.info("HybridSearchService initialized")

            # Search Cache Manager
            if settings.ENABLE_SEARCH_CACHE:
                self._search_cache_manager = SearchCacheManager(
                    redis_client=self._redis_client,
                    l1_ttl=settings.CACHE_L1_TTL,
                    l2_threshold=settings.CACHE_L2_THRESHOLD,
                    max_l2_size=settings.CACHE_L2_MAX_SIZE,
                )
                logger.info("SearchCacheManager initialized")

            # Query Expansion Service
            if settings.ENABLE_QUERY_EXPANSION:
                self._query_expansion_service = QueryExpansionService(
                    llm_manager=self._llm_manager,
                    embedding_service=self._embedding_service,
                )
                logger.info("QueryExpansionService initialized")

            # Reranker Service
            if settings.ENABLE_RERANKING:
                self._reranker_service = RerankerService(
                    cross_encoder_model=settings.CROSS_ENCODER_MODEL,
                    use_cross_encoder=True,
                )
                logger.info("RerankerService initialized")

            # Initialize MCP Manager and Agents
            logger.info("Initializing MCP Manager and Agents...")
            self._mcp_manager = MCPServerManager()

            # Connect to MCP servers with graceful degradation
            await self._initialize_mcp_servers()

            # Initialize ColPali for image search
            colpali_processor = None
            colpali_milvus = None
            if settings.ENABLE_COLPALI:
                try:
                    from backend.services.colpali_processor import get_colpali_processor
                    from backend.services.colpali_milvus_service import get_colpali_milvus_service
                    
                    colpali_processor = get_colpali_processor(
                        model_name=settings.COLPALI_MODEL,
                        enable_binarization=settings.COLPALI_ENABLE_BINARIZATION,
                        enable_pooling=settings.COLPALI_ENABLE_POOLING,
                        pooling_factor=settings.COLPALI_POOLING_FACTOR
                    )
                    
                    colpali_milvus = get_colpali_milvus_service(
                        host=settings.MILVUS_HOST,
                        port=str(settings.MILVUS_PORT)
                    )
                    
                    logger.info("ColPali image search initialized")
                except Exception as e:
                    logger.warning(f"ColPali initialization failed: {e}")
            
            # Initialize specialized agents with advanced services
            # Add direct Milvus fallback for VectorSearchAgent
            vector_agent = VectorSearchAgent(
                mcp_manager=self._mcp_manager,
                hybrid_search_manager=self._hybrid_search_manager,
                query_expansion_service=self._query_expansion_service,
                reranker_service=self._reranker_service,
                cache_manager=self._search_cache_manager,
                milvus_manager=self._milvus_manager,  # Direct Milvus fallback
                embedding_service=self._embedding_service,  # For direct search
                colpali_processor=colpali_processor,  # ColPali image search
                colpali_milvus=colpali_milvus,  # ColPali Milvus service
                enable_colpali_search=settings.ENABLE_COLPALI,  # Enable ColPali
            )
            local_agent = LocalDataAgent(mcp_manager=self._mcp_manager)
            search_agent = WebSearchAgent(mcp_manager=self._mcp_manager)

            # Initialize Aggregator Agent
            self._aggregator_agent = AggregatorAgent(
                llm_manager=self._llm_manager,
                memory_manager=self._memory_manager,
                vector_agent=vector_agent,
                local_agent=local_agent,
                search_agent=search_agent,
            )
            logger.info("Aggregator Agent initialized")

            # Initialize Performance Monitor
            logger.info("Initializing Performance Monitor...")
            self._performance_monitor = PerformanceMonitor(
                redis_client=self._redis_client,
                metrics_ttl=getattr(settings, "METRICS_TTL", 86400 * 7),
                alert_threshold_error_rate=getattr(
                    settings, "ALERT_THRESHOLD_ERROR_RATE", 0.1
                ),
                alert_threshold_slow_response=getattr(
                    settings, "ALERT_THRESHOLD_SLOW_RESPONSE", 5.0
                ),
            )
            logger.info("Performance Monitor initialized")

            # Initialize Hybrid Query System (Speculative RAG)
            if settings.ENABLE_SPECULATIVE_RAG:
                logger.info("Initializing Hybrid Query System (Speculative RAG)...")

                # Initialize Speculative Processor
                self._speculative_processor = SpeculativeProcessor(
                    embedding_service=self._embedding_service,
                    milvus_manager=self._milvus_manager,
                    llm_manager=self._llm_manager,
                    redis_client=self._redis_client,
                    stm=self._memory_manager.stm if self._memory_manager else None,
                    semantic_cache=None,  # Will be initialized separately if needed
                )
                logger.info("SpeculativeProcessor initialized")

                # Initialize Response Coordinator
                self._response_coordinator = ResponseCoordinator()
                logger.info("ResponseCoordinator initialized")

                # Initialize Hybrid Query Router
                self._hybrid_query_router = HybridQueryRouter(
                    speculative_processor=self._speculative_processor,
                    agentic_processor=self._aggregator_agent,
                    response_coordinator=self._response_coordinator,
                    default_speculative_timeout=settings.SPECULATIVE_TIMEOUT,
                    default_agentic_timeout=settings.AGENTIC_TIMEOUT,
                )
                logger.info("HybridQueryRouter initialized")

                # Initialize Adaptive RAG Service
                self._adaptive_rag_service = AdaptiveRAGService()
                logger.info("AdaptiveRAGService initialized")

                # Initialize Intelligent Mode Router
                self._intelligent_mode_router = IntelligentModeRouter(
                    adaptive_service=self._adaptive_rag_service, settings=settings
                )
                logger.info("IntelligentModeRouter initialized")

            self._initialized = True
            logger.info("ServiceContainer initialization complete!")

        except Exception as e:
            logger.error(f"ServiceContainer initialization failed: {e}", exc_info=True)
            await self.cleanup()
            raise

    async def _initialize_mcp_servers(self) -> None:
        """Initialize MCP servers with error handling."""
        mcp_servers = [
            ("vector_server", "python", ["mcp_servers/vector_server.py"]),
            ("local_data_server", "python", ["mcp_servers/local_data_server.py"]),
            ("search_server", "python", ["mcp_servers/search_server.py"]),
        ]

        for server_name, command, args in mcp_servers:
            try:
                await self._mcp_manager.connect_server(server_name, command, args)
                logger.info(f"{server_name} connected")
            except Exception as e:
                logger.warning(f"{server_name} unavailable: {e}")

    async def cleanup(self) -> None:
        """Cleanup all services."""
        logger.info("Cleaning up ServiceContainer...")

        if self._redis_client:
            try:
                await self._redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

        if self._milvus_manager:
            try:
                self._milvus_manager.disconnect()
                logger.info("Milvus connection closed")
            except Exception as e:
                logger.error(f"Error closing Milvus: {e}")

        if self._mcp_manager:
            try:
                await self._mcp_manager.disconnect_all()
                logger.info("MCP servers disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting MCP servers: {e}")

        self._initialized = False
        logger.info("ServiceContainer cleanup complete")

    # Getters with validation
    def get_redis_client(self) -> redis.Redis:
        if not self._initialized or self._redis_client is None:
            raise RuntimeError("Redis client not initialized")
        return self._redis_client

    def get_embedding_service(self) -> EmbeddingService:
        if not self._initialized or self._embedding_service is None:
            raise RuntimeError("EmbeddingService not initialized")
        return self._embedding_service

    def get_milvus_manager(self) -> MilvusManager:
        if not self._initialized or self._milvus_manager is None:
            raise RuntimeError("MilvusManager not initialized")
        return self._milvus_manager

    def get_llm_manager(self) -> LLMManager:
        if not self._initialized or self._llm_manager is None:
            raise RuntimeError("LLMManager not initialized")
        return self._llm_manager

    def get_document_processor(self) -> DocumentProcessor:
        if not self._initialized or self._document_processor is None:
            raise RuntimeError("DocumentProcessor not initialized")
        return self._document_processor

    def get_memory_manager(self) -> MemoryManager:
        if not self._initialized or self._memory_manager is None:
            raise RuntimeError("MemoryManager not initialized")
        return self._memory_manager

    def get_aggregator_agent(self) -> AggregatorAgent:
        if not self._initialized or self._aggregator_agent is None:
            raise RuntimeError("AggregatorAgent not initialized")
        return self._aggregator_agent

    def get_hybrid_search_manager(self) -> Optional[HybridSearchService]:
        """Get HybridSearchService (may be None if disabled)."""
        return self._hybrid_search_manager

    def get_search_cache_manager(self) -> Optional[SearchCacheManager]:
        """Get SearchCacheManager (may be None if disabled)."""
        return self._search_cache_manager

    def get_query_expansion_service(self) -> Optional[QueryExpansionService]:
        """Get QueryExpansionService (may be None if disabled)."""
        return self._query_expansion_service

    def get_reranker_service(self) -> Optional[RerankerService]:
        """Get RerankerService (may be None if disabled)."""
        return self._reranker_service

    def get_speculative_processor(self) -> Optional[SpeculativeProcessor]:
        """Get SpeculativeProcessor (may be None if disabled)."""
        return self._speculative_processor

    def get_response_coordinator(self) -> Optional[ResponseCoordinator]:
        """Get ResponseCoordinator (may be None if disabled)."""
        return self._response_coordinator

    def get_hybrid_query_router(self) -> Optional[HybridQueryRouter]:
        """Get HybridQueryRouter (may be None if disabled)."""
        return self._hybrid_query_router

    def get_performance_monitor(self) -> PerformanceMonitor:
        """Get PerformanceMonitor."""
        if not self._initialized or self._performance_monitor is None:
            raise RuntimeError("PerformanceMonitor not initialized")
        return self._performance_monitor

    def get_adaptive_rag_service(self) -> Optional[AdaptiveRAGService]:
        """Get AdaptiveRAGService (may be None if disabled)."""
        return self._adaptive_rag_service

    def get_intelligent_mode_router(self) -> Optional[IntelligentModeRouter]:
        """Get IntelligentModeRouter (may be None if disabled)."""
        return self._intelligent_mode_router

    # Setters for testing
    def set_embedding_service(self, service: EmbeddingService) -> None:
        """Override embedding service (for testing)."""
        self._embedding_service = service

    def set_milvus_manager(self, manager: MilvusManager) -> None:
        """Override Milvus manager (for testing)."""
        self._milvus_manager = manager

    def set_llm_manager(self, manager: LLMManager) -> None:
        """Override LLM manager (for testing)."""
        self._llm_manager = manager


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        raise RuntimeError(
            "ServiceContainer not initialized. Call initialize_container() first."
        )
    return _container


async def initialize_container() -> ServiceContainer:
    """Initialize the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer()
        await _container.initialize()
    return _container


async def cleanup_container() -> None:
    """Cleanup the global service container."""
    global _container
    if _container is not None:
        await _container.cleanup()
        _container = None


# FastAPI dependency functions
async def get_redis_client() -> redis.Redis:
    """FastAPI dependency for Redis client."""
    return get_container().get_redis_client()


async def get_embedding_service() -> EmbeddingService:
    """FastAPI dependency for EmbeddingService."""
    return get_container().get_embedding_service()


async def get_milvus_manager() -> MilvusManager:
    """FastAPI dependency for MilvusManager."""
    return get_container().get_milvus_manager()


async def get_llm_manager() -> LLMManager:
    """FastAPI dependency for LLMManager."""
    return get_container().get_llm_manager()


async def get_document_processor() -> DocumentProcessor:
    """FastAPI dependency for DocumentProcessor."""
    return get_container().get_document_processor()


async def get_memory_manager() -> MemoryManager:
    """FastAPI dependency for MemoryManager."""
    return get_container().get_memory_manager()


async def get_aggregator_agent() -> AggregatorAgent:
    """FastAPI dependency for AggregatorAgent."""
    return get_container().get_aggregator_agent()


async def get_hybrid_search_manager() -> Optional[HybridSearchService]:
    """FastAPI dependency for HybridSearchService."""
    return get_container().get_hybrid_search_manager()


async def get_search_cache_manager() -> Optional[SearchCacheManager]:
    """FastAPI dependency for SearchCacheManager."""
    return get_container().get_search_cache_manager()


async def get_query_expansion_service() -> Optional[QueryExpansionService]:
    """FastAPI dependency for QueryExpansionService."""
    return get_container().get_query_expansion_service()


async def get_reranker_service() -> Optional[RerankerService]:
    """FastAPI dependency for RerankerService."""
    return get_container().get_reranker_service()


async def get_speculative_processor() -> Optional[SpeculativeProcessor]:
    """FastAPI dependency for SpeculativeProcessor."""
    return get_container().get_speculative_processor()


async def get_response_coordinator() -> Optional[ResponseCoordinator]:
    """FastAPI dependency for ResponseCoordinator."""
    return get_container().get_response_coordinator()


async def get_hybrid_query_router() -> Optional[HybridQueryRouter]:
    """FastAPI dependency for HybridQueryRouter."""
    return get_container().get_hybrid_query_router()


async def get_performance_monitor() -> PerformanceMonitor:
    """FastAPI dependency for PerformanceMonitor."""
    return get_container().get_performance_monitor()


async def get_adaptive_rag_service() -> Optional[AdaptiveRAGService]:
    """FastAPI dependency for AdaptiveRAGService."""
    return get_container().get_adaptive_rag_service()


async def get_intelligent_mode_router() -> Optional[IntelligentModeRouter]:
    """FastAPI dependency for IntelligentModeRouter."""
    return get_container().get_intelligent_mode_router()
