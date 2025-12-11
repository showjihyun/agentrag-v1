"""
Enhanced Agent Executor with Circuit Breaker and Multi-Level Cache

Demonstrates integration of Phase 1 architecture improvements.
"""

from typing import Dict, Any, AsyncGenerator, Optional
import asyncio
from datetime import datetime
import logging

from backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    get_circuit_breaker_registry
)
from backend.core.advanced_cache import MultiLevelCache, cache_key
from backend.core.enhanced_logging import get_logger, log_execution_time, log_error

logger = get_logger(__name__)


class EnhancedAgentExecutor:
    """
    Agent executor with circuit breakers and multi-level caching.
    
    Features:
    - Circuit breakers for LLM and Milvus calls
    - Multi-level caching for responses
    - Structured logging with context
    - Automatic fallback strategies
    """
    
    def __init__(
        self,
        llm_manager,
        milvus_manager,
        redis_client,
        embedding_service
    ):
        self.llm_manager = llm_manager
        self.milvus_manager = milvus_manager
        self.embedding_service = embedding_service
        
        # Initialize multi-level cache
        self.cache = MultiLevelCache(
            redis_client=redis_client,
            l1_max_size=1000,
            l1_ttl=300,  # 5 minutes
            l2_ttl=3600,  # 1 hour
        )
        
        # Register circuit breakers
        registry = get_circuit_breaker_registry()
        
        self.llm_breaker = registry.register(
            name="llm_service",
            failure_threshold=3,
            timeout=30,
            fallback=self._llm_fallback
        )
        
        self.milvus_breaker = registry.register(
            name="milvus_service",
            failure_threshold=5,
            timeout=60,
            fallback=self._milvus_fallback
        )
        
        logger.info("Enhanced agent executor initialized")
    
    async def execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        use_cache: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute agent with circuit breakers and caching.
        
        Args:
            agent_id: Agent ID
            input_data: Input data
            use_cache: Whether to use cache
            
        Yields:
            Execution steps
        """
        start_time = datetime.utcnow()
        
        try:
            # Generate cache key
            cache_key_str = cache_key(
                "agent_execution",
                agent_id=agent_id,
                input_hash=hash(str(input_data))
            )
            
            # Try cache first
            if use_cache:
                cached_result = await self.cache.get(cache_key_str)
                if cached_result:
                    logger.info(
                        "Cache hit for agent execution",
                        extra={
                            "agent_id": agent_id,
                            "cache_key": cache_key_str
                        }
                    )
                    
                    # Yield cached steps
                    for step in cached_result:
                        yield step
                    return
            
            # Execute agent
            steps = []
            async for step in self._execute_with_circuit_breakers(
                agent_id,
                input_data
            ):
                steps.append(step)
                yield step
            
            # Cache result
            if use_cache and steps:
                await self.cache.set(
                    cache_key_str,
                    steps,
                    ttl=3600  # 1 hour
                )
            
            # Log execution time
            duration_ms = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000
            
            log_execution_time(
                "execute_agent",
                duration_ms,
                agent_id=agent_id,
                steps_count=len(steps)
            )
            
        except Exception as e:
            log_error(
                e,
                context={
                    "agent_id": agent_id,
                    "input_data": input_data
                }
            )
            raise
    
    async def _execute_with_circuit_breakers(
        self,
        agent_id: str,
        input_data: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute agent with circuit breaker protection"""
        
        # Step 1: Retrieve context with Milvus circuit breaker
        try:
            context = await self.milvus_breaker.call(
                self._retrieve_context,
                input_data.get("query", "")
            )
            
            yield {
                "type": "context_retrieved",
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except CircuitBreakerOpenError as e:
            logger.warning(f"Milvus circuit breaker open: {e}")
            context = []
            
            yield {
                "type": "context_retrieved",
                "context": context,
                "fallback": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Step 2: Generate response with LLM circuit breaker
        try:
            response = await self.llm_breaker.call(
                self._generate_response,
                input_data.get("query", ""),
                context
            )
            
            yield {
                "type": "response_generated",
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except CircuitBreakerOpenError as e:
            logger.warning(f"LLM circuit breaker open: {e}")
            
            yield {
                "type": "response_generated",
                "response": "Service temporarily unavailable. Please try again later.",
                "fallback": True,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _retrieve_context(self, query: str) -> list:
        """Retrieve context from Milvus"""
        # Simulate Milvus call
        embedding = await self.embedding_service.embed_text(query)
        results = await self.milvus_manager.search(
            embedding,
            top_k=5
        )
        return results
    
    async def _generate_response(
        self,
        query: str,
        context: list
    ) -> str:
        """Generate response with LLM"""
        # Simulate LLM call
        prompt = self._build_prompt(query, context)
        response = await self.llm_manager.generate(prompt)
        return response
    
    def _build_prompt(self, query: str, context: list) -> str:
        """Build prompt from query and context"""
        context_str = "\n".join([
            doc.get("text", "") for doc in context
        ])
        
        return f"""Context:
{context_str}

Question: {query}

Answer:"""
    
    async def _llm_fallback(self, *args, **kwargs) -> str:
        """Fallback when LLM circuit is open"""
        logger.info("Using LLM fallback")
        return "I'm currently experiencing high load. Please try again in a moment."
    
    async def _milvus_fallback(self, *args, **kwargs) -> list:
        """Fallback when Milvus circuit is open"""
        logger.info("Using Milvus fallback")
        return []  # Return empty context
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all components"""
        registry = get_circuit_breaker_registry()
        
        return {
            "circuit_breakers": registry.get_all_states(),
            "cache_stats": self.cache.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
