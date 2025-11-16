"""
Knowledgebase Result Reranker.

Advanced reranking for KB search results using multiple signals.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RerankingSignal:
    """Signals used for reranking"""
    vector_score: float  # Original vector similarity score
    kb_priority: float  # KB vs general source priority
    recency: float  # Document recency score
    relevance: float  # Semantic relevance score
    diversity: float  # Result diversity score


class KBReranker:
    """
    Advanced reranker for KB search results.
    
    Features:
    - Multi-signal reranking
    - KB priority boosting
    - Diversity promotion
    - Configurable weights
    """
    
    def __init__(
        self,
        kb_weight: float = 0.3,
        vector_weight: float = 0.4,
        recency_weight: float = 0.1,
        relevance_weight: float = 0.1,
        diversity_weight: float = 0.1
    ):
        """
        Initialize reranker with weights.
        
        Args:
            kb_weight: Weight for KB priority (default: 0.3)
            vector_weight: Weight for vector score (default: 0.4)
            recency_weight: Weight for recency (default: 0.1)
            relevance_weight: Weight for relevance (default: 0.1)
            diversity_weight: Weight for diversity (default: 0.1)
        """
        self.kb_weight = kb_weight
        self.vector_weight = vector_weight
        self.recency_weight = recency_weight
        self.relevance_weight = relevance_weight
        self.diversity_weight = diversity_weight
        
        # Normalize weights
        total = sum([
            kb_weight, vector_weight, recency_weight,
            relevance_weight, diversity_weight
        ])
        
        if total > 0:
            self.kb_weight /= total
            self.vector_weight /= total
            self.recency_weight /= total
            self.relevance_weight /= total
            self.diversity_weight /= total
        
        logger.info(
            f"KBReranker initialized with weights: "
            f"kb={self.kb_weight:.2f}, vector={self.vector_weight:.2f}, "
            f"recency={self.recency_weight:.2f}, relevance={self.relevance_weight:.2f}, "
            f"diversity={self.diversity_weight:.2f}"
        )
    
    def rerank(
        self,
        results: List[Any],
        query: str,
        top_k: int = 5
    ) -> List[Any]:
        """
        Rerank search results using multiple signals.
        
        Args:
            results: List of search results
            query: Original query
            top_k: Number of results to return
            
        Returns:
            Reranked results
        """
        if not results:
            return []
        
        logger.debug(f"Reranking {len(results)} results")
        
        # Calculate signals for each result
        scored_results = []
        for i, result in enumerate(results):
            signals = self._calculate_signals(result, i, results, query)
            final_score = self._combine_signals(signals)
            
            scored_results.append({
                'result': result,
                'signals': signals,
                'final_score': final_score,
                'original_rank': i
            })
        
        # Sort by final score
        scored_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Log reranking changes
        significant_changes = sum(
            1 for sr in scored_results[:top_k]
            if abs(sr['original_rank'] - scored_results.index(sr)) > 2
        )
        
        if significant_changes > 0:
            logger.info(
                f"Reranking changed {significant_changes}/{top_k} positions significantly"
            )
        
        # Return top-k results
        return [sr['result'] for sr in scored_results[:top_k]]
    
    def _calculate_signals(
        self,
        result: Any,
        position: int,
        all_results: List[Any],
        query: str
    ) -> RerankingSignal:
        """
        Calculate reranking signals for a result.
        
        Args:
            result: Search result
            position: Position in original results
            all_results: All results for diversity calculation
            query: Original query
            
        Returns:
            RerankingSignal with all scores
        """
        # Vector score (original similarity)
        vector_score = getattr(result, 'score', 0.5)
        
        # KB priority (is it from KB?)
        metadata = getattr(result, 'metadata', {}) or {}
        source = metadata.get('source', '')
        kb_priority = 1.0 if source.startswith('kb:') else 0.5
        
        # Recency (if available)
        recency = self._calculate_recency(metadata)
        
        # Relevance (query-specific)
        relevance = self._calculate_relevance(result, query)
        
        # Diversity (different from other results)
        diversity = self._calculate_diversity(result, all_results, position)
        
        return RerankingSignal(
            vector_score=vector_score,
            kb_priority=kb_priority,
            recency=recency,
            relevance=relevance,
            diversity=diversity
        )
    
    def _combine_signals(self, signals: RerankingSignal) -> float:
        """
        Combine signals into final score.
        
        Args:
            signals: RerankingSignal
            
        Returns:
            Final combined score
        """
        final_score = (
            signals.vector_score * self.vector_weight +
            signals.kb_priority * self.kb_weight +
            signals.recency * self.recency_weight +
            signals.relevance * self.relevance_weight +
            signals.diversity * self.diversity_weight
        )
        
        return final_score
    
    def _calculate_recency(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate recency score from metadata.
        
        Args:
            metadata: Result metadata
            
        Returns:
            Recency score (0-1)
        """
        # TODO: Implement based on document timestamp
        # For now, return neutral score
        return 0.5
    
    def _calculate_relevance(self, result: Any, query: str) -> float:
        """
        Calculate semantic relevance score.
        
        Args:
            result: Search result
            query: Query text
            
        Returns:
            Relevance score (0-1)
        """
        # Simple keyword matching for now
        content = getattr(result, 'content', '')
        if not content:
            return 0.5
        
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Count query word matches
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        
        if not query_words:
            return 0.5
        
        matches = len(query_words & content_words)
        relevance = matches / len(query_words)
        
        return min(relevance, 1.0)
    
    def _calculate_diversity(
        self,
        result: Any,
        all_results: List[Any],
        position: int
    ) -> float:
        """
        Calculate diversity score (how different from other results).
        
        Args:
            result: Current result
            all_results: All results
            position: Position in results
            
        Returns:
            Diversity score (0-1)
        """
        # Simple diversity: prefer results from different sources
        metadata = getattr(result, 'metadata', {}) or {}
        source = metadata.get('source', '')
        
        # Count how many results before this one have the same source
        same_source_count = 0
        for i in range(position):
            other_metadata = getattr(all_results[i], 'metadata', {}) or {}
            other_source = other_metadata.get('source', '')
            if other_source == source:
                same_source_count += 1
        
        # Penalize if many results from same source
        diversity = 1.0 - (same_source_count * 0.2)
        return max(diversity, 0.0)


# Global reranker instance
_reranker: Optional[KBReranker] = None


def get_kb_reranker(
    kb_weight: float = 0.3,
    vector_weight: float = 0.4,
    recency_weight: float = 0.1,
    relevance_weight: float = 0.1,
    diversity_weight: float = 0.1
) -> KBReranker:
    """
    Get or create global KB reranker.
    
    Args:
        kb_weight: Weight for KB priority
        vector_weight: Weight for vector score
        recency_weight: Weight for recency
        relevance_weight: Weight for relevance
        diversity_weight: Weight for diversity
        
    Returns:
        KBReranker instance
    """
    global _reranker
    
    if _reranker is None:
        _reranker = KBReranker(
            kb_weight=kb_weight,
            vector_weight=vector_weight,
            recency_weight=recency_weight,
            relevance_weight=relevance_weight,
            diversity_weight=diversity_weight
        )
    
    return _reranker
