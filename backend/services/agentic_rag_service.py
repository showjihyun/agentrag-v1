"""
Agentic RAG Service

High-level service for agentic RAG operations with intelligent retrieval.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.core.blocks.agentic.agentic_rag_block import (
    AgenticRAGBlock,
    QueryComplexity,
    RetrievalStrategy,
)
from backend.services.llm_manager import LLMManager
from backend.services.embedding_service import EmbeddingService
from backend.services.milvus import MilvusManager


logger = logging.getLogger(__name__)


class AgenticRAGService:
    """
    High-level service for agentic RAG operations.
    
    Provides a simplified interface for executing agentic RAG queries
    with intelligent retrieval, query decomposition, and reflection.
    """
    
    def __init__(
        self,
        llm_manager: LLMManager,
        embedding_service: EmbeddingService,
        milvus_manager: MilvusManager,
    ):
        """
        Initialize the agentic RAG service.
        
        Args:
            llm_manager: LLM manager for text generation
            embedding_service: Embedding service for vector search
            milvus_manager: Milvus manager for vector search
        """
        self.llm_manager = llm_manager
        self.embedding_service = embedding_service
        self.milvus_manager = milvus_manager
        self.agentic_rag_block = AgenticRAGBlock(
            llm_manager=llm_manager,
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            enable_query_decomposition=True,
            enable_reflection=True,
            enable_web_search=True,
            max_retrieval_iterations=3,
            relevance_threshold=0.7,
        )
        
    async def execute_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        strategy: str = "adaptive",
        top_k: int = 10,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute an agentic RAG query with intelligent retrieval.
        
        Args:
            query: User query
            user_id: Optional user ID for context
            strategy: Retrieval strategy (adaptive, hybrid, vector_only, web_only)
            top_k: Number of sources to retrieve
            context: Additional context
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Executing agentic RAG query: {query[:100]}...")
        
        # Map strategy string to enum
        strategy_map = {
            "adaptive": RetrievalStrategy.ADAPTIVE,
            "hybrid": RetrievalStrategy.HYBRID,
            "vector_only": RetrievalStrategy.VECTOR_ONLY,
            "web_only": RetrievalStrategy.WEB_ONLY,
        }
        retrieval_strategy = strategy_map.get(strategy, RetrievalStrategy.ADAPTIVE)
        
        # Prepare context
        query_context = context or {}
        if user_id:
            query_context["user_id"] = user_id
        
        # Execute the agentic RAG block
        result = await self.agentic_rag_block.execute(
            query=query,
            context=query_context,
            strategy=retrieval_strategy,
            top_k=top_k,
        )
        
        logger.info(
            f"Query completed - Complexity: {result.get('query_complexity')}, "
            f"Confidence: {result.get('confidence_score', 0):.2f}, "
            f"Sources: {result.get('total_sources', 0)}"
        )
        
        return result
    
    async def analyze_complexity(self, query: str) -> Dict[str, Any]:
        """
        Analyze query complexity without executing full retrieval.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with complexity analysis
        """
        complexity = await self.agentic_rag_block._analyze_query_complexity(
            query=query,
            context={},
        )
        
        complexity_str = complexity.value if isinstance(complexity, QueryComplexity) else str(complexity)
        
        # Estimate execution time based on complexity
        execution_time_map = {
            "simple": 1.0,
            "moderate": 3.0,
            "complex": 5.0,
        }
        estimated_time = execution_time_map.get(complexity_str.lower(), 2.0)
        
        return {
            "query": query,
            "complexity": complexity_str,
            "recommended_strategy": self._recommend_strategy(complexity),
            "estimated_execution_time": estimated_time,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def decompose_query(self, query: str) -> Dict[str, Any]:
        """
        Decompose a complex query into sub-queries.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with sub-queries
        """
        sub_queries = await self.agentic_rag_block._decompose_query(
            query=query,
            context={},
        )
        
        sub_query_list = [
            {
                "id": sq.id,
                "query": sq.query,
                "dependencies": sq.dependencies,
            }
            for sq in sub_queries
        ]
        
        return {
            "original_query": query,
            "sub_queries": sub_query_list,
            "total_sub_queries": len(sub_query_list),
            "timestamp": datetime.now().isoformat(),
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics for agentic RAG.
        
        Returns:
            Dictionary with statistics
        """
        # For now, return basic statistics
        # In production, this would query from database
        return {
            "total_queries": 0,
            "average_complexity": {
                "simple": 0,
                "moderate": 0,
                "complex": 0,
            },
            "average_confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _recommend_strategy(self, complexity) -> str:
        """
        Recommend a retrieval strategy based on query complexity.
        
        Args:
            complexity: Query complexity
            
        Returns:
            Recommended strategy
        """
        if isinstance(complexity, QueryComplexity):
            if complexity == QueryComplexity.SIMPLE:
                return "vector_only"
            elif complexity == QueryComplexity.MODERATE:
                return "hybrid"
            else:
                return "adaptive"
        
        # String-based fallback
        complexity_str = str(complexity).lower()
        if "simple" in complexity_str:
            return "vector_only"
        elif "moderate" in complexity_str:
            return "hybrid"
        else:
            return "adaptive"
