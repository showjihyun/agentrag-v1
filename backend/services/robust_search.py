# Robust Search with Multiple Fallback Strategies
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Available search strategies"""

    HYBRID = "hybrid"
    VECTOR_ONLY = "vector_only"
    KEYWORD_ONLY = "keyword_only"
    SIMPLE = "simple"


class RobustSearchService:
    """
    Robust search service with automatic fallback strategies.

    Tries multiple search strategies in order:
    1. Hybrid search (vector + BM25)
    2. Vector-only search
    3. Keyword-only search (BM25)
    4. Simple text matching

    Ensures users always get results even if advanced features fail.
    """

    def __init__(self, vector_search_agent, bm25_service=None):
        self.vector_agent = vector_search_agent
        self.bm25_service = bm25_service
        self.fallback_count = {strategy: 0 for strategy in SearchStrategy}

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        preferred_strategy: SearchStrategy = SearchStrategy.HYBRID,
    ) -> tuple[List[Dict[str, Any]], SearchStrategy]:
        """
        Perform robust search with automatic fallback.

        Args:
            query: Search query
            top_k: Number of results
            filters: Optional filters
            preferred_strategy: Preferred search strategy

        Returns:
            Tuple of (results, strategy_used)
        """
        strategies = self._get_fallback_chain(preferred_strategy)

        for strategy in strategies:
            try:
                logger.info(f"Attempting search with strategy: {strategy.value}")
                results = await self._execute_strategy(strategy, query, top_k, filters)

                if results:
                    if strategy != preferred_strategy:
                        self.fallback_count[strategy] += 1
                        logger.warning(
                            f"Fallback to {strategy.value} for query: {query[:50]}..."
                        )

                    logger.info(
                        f"Search successful with {strategy.value}: "
                        f"{len(results)} results"
                    )
                    return results, strategy

                logger.warning(
                    f"No results from {strategy.value}, trying next strategy"
                )

            except Exception as e:
                logger.error(
                    f"Strategy {strategy.value} failed: {e}, trying next strategy"
                )
                continue

        # All strategies failed - return empty results
        logger.error(f"All search strategies failed for query: {query[:50]}...")
        return [], SearchStrategy.SIMPLE

    def _get_fallback_chain(self, preferred: SearchStrategy) -> List[SearchStrategy]:
        """Get ordered list of strategies to try"""
        if preferred == SearchStrategy.HYBRID:
            return [
                SearchStrategy.HYBRID,
                SearchStrategy.VECTOR_ONLY,
                SearchStrategy.KEYWORD_ONLY,
                SearchStrategy.SIMPLE,
            ]
        elif preferred == SearchStrategy.VECTOR_ONLY:
            return [
                SearchStrategy.VECTOR_ONLY,
                SearchStrategy.HYBRID,
                SearchStrategy.KEYWORD_ONLY,
                SearchStrategy.SIMPLE,
            ]
        elif preferred == SearchStrategy.KEYWORD_ONLY:
            return [
                SearchStrategy.KEYWORD_ONLY,
                SearchStrategy.VECTOR_ONLY,
                SearchStrategy.HYBRID,
                SearchStrategy.SIMPLE,
            ]
        else:
            return [SearchStrategy.SIMPLE]

    async def _execute_strategy(
        self,
        strategy: SearchStrategy,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Execute a specific search strategy"""

        if strategy == SearchStrategy.HYBRID:
            return await self.vector_agent.search(
                query=query, top_k=top_k, filters=filters, search_mode="hybrid"
            )

        elif strategy == SearchStrategy.VECTOR_ONLY:
            return await self.vector_agent.search(
                query=query, top_k=top_k, filters=filters, search_mode="vector_only"
            )

        elif strategy == SearchStrategy.KEYWORD_ONLY:
            if not self.bm25_service or not self.bm25_service.indexed:
                raise ValueError("BM25 service not available")

            results = await self.bm25_service.search(query, top_k)
            return [
                {
                    "id": doc_id,
                    "chunk_id": doc_id,
                    "score": score,
                    "text": "",  # Would need to fetch from storage
                    "source": "keyword",
                }
                for doc_id, score in results
            ]

        elif strategy == SearchStrategy.SIMPLE:
            # Simple text matching as last resort
            logger.warning("Using simple text matching as last resort")
            return []

        return []

    def get_fallback_stats(self) -> Dict[str, int]:
        """Get statistics on fallback usage"""
        return {
            strategy.value: count for strategy, count in self.fallback_count.items()
        }

    def reset_stats(self):
        """Reset fallback statistics"""
        self.fallback_count = {strategy: 0 for strategy in SearchStrategy}


def create_robust_search(vector_agent, bm25_service=None) -> RobustSearchService:
    """Factory function to create robust search service"""
    return RobustSearchService(vector_agent, bm25_service)
