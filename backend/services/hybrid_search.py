# Hybrid Search Service (Vector + BM25)
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with score"""

    doc_id: str
    content: str
    score: float
    source: str  # 'vector', 'bm25', or 'hybrid'
    metadata: Optional[Dict] = None


class HybridSearchService:
    """
    Combines vector similarity search with BM25 keyword search.

    Uses Reciprocal Rank Fusion (RRF) to merge results from both methods.
    """

    def __init__(
        self, vector_weight: float = 0.7, bm25_weight: float = 0.3, rrf_k: int = 60
    ):
        """
        Initialize hybrid search.

        Args:
            vector_weight: Weight for vector search (0.0 - 1.0)
            bm25_weight: Weight for BM25 search (0.0 - 1.0)
            rrf_k: RRF constant (default: 60)
        """
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k

        # Normalize weights
        total_weight = vector_weight + bm25_weight
        self.vector_weight = vector_weight / total_weight
        self.bm25_weight = bm25_weight / total_weight

    def reciprocal_rank_fusion(
        self,
        vector_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Merge results using Reciprocal Rank Fusion.

        RRF formula: score = sum(1 / (k + rank))

        Args:
            vector_results: List of (doc_id, score) from vector search
            bm25_results: List of (doc_id, score) from BM25 search
            top_k: Number of results to return

        Returns:
            Merged list of (doc_id, score) tuples
        """
        rrf_scores = {}

        # Add vector search scores
        for rank, (doc_id, _) in enumerate(vector_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (
                self.vector_weight / (self.rrf_k + rank)
            )

        # Add BM25 scores
        for rank, (doc_id, _) in enumerate(bm25_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (
                self.bm25_weight / (self.rrf_k + rank)
            )

        # Sort by RRF score
        merged = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        return merged[:top_k]

    def weighted_score_fusion(
        self,
        vector_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Merge results using weighted score fusion.

        Normalizes scores from each method and combines with weights.

        Args:
            vector_results: List of (doc_id, score) from vector search
            bm25_results: List of (doc_id, score) from BM25 search
            top_k: Number of results to return

        Returns:
            Merged list of (doc_id, score) tuples
        """
        combined_scores = {}

        # Normalize vector scores
        if vector_results:
            max_vector_score = max(score for _, score in vector_results)
            if max_vector_score > 0:
                for doc_id, score in vector_results:
                    normalized_score = score / max_vector_score
                    combined_scores[doc_id] = (
                        combined_scores.get(doc_id, 0.0)
                        + self.vector_weight * normalized_score
                    )

        # Normalize BM25 scores
        if bm25_results:
            max_bm25_score = max(score for _, score in bm25_results)
            if max_bm25_score > 0:
                for doc_id, score in bm25_results:
                    normalized_score = score / max_bm25_score
                    combined_scores[doc_id] = (
                        combined_scores.get(doc_id, 0.0)
                        + self.bm25_weight * normalized_score
                    )

        # Sort by combined score
        merged = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        return merged[:top_k]

    async def search(
        self,
        query: str,
        vector_search_fn,
        bm25_search_fn,
        top_k: int = 10,
        fusion_method: str = "rrf",
    ) -> List[SearchResult]:
        """
        Perform hybrid search.

        Args:
            query: Search query
            vector_search_fn: Async function for vector search
            bm25_search_fn: Async function for BM25 search
            top_k: Number of results to return
            fusion_method: 'rrf' or 'weighted'

        Returns:
            List of SearchResult objects
        """
        # Perform both searches
        vector_results = await vector_search_fn(query, top_k * 2)
        bm25_results = await bm25_search_fn(query, top_k * 2)

        logger.info(
            f"Hybrid search: vector={len(vector_results)}, " f"bm25={len(bm25_results)}"
        )

        # Merge results
        if fusion_method == "rrf":
            merged = self.reciprocal_rank_fusion(vector_results, bm25_results, top_k)
        else:
            merged = self.weighted_score_fusion(vector_results, bm25_results, top_k)

        # Convert to SearchResult objects
        # Note: You'll need to fetch actual document content
        results = []
        for doc_id, score in merged:
            results.append(
                SearchResult(
                    doc_id=doc_id, content="", score=score, source="hybrid"
                )  # To be filled by caller
            )

        logger.info(f"Hybrid search completed: {len(results)} results")

        return results


# Global hybrid search service
_hybrid_search_service: HybridSearchService = None


def get_hybrid_search_service(
    vector_weight: float = 0.7, bm25_weight: float = 0.3
) -> HybridSearchService:
    """Get global hybrid search service instance"""
    global _hybrid_search_service
    if _hybrid_search_service is None:
        _hybrid_search_service = HybridSearchService(
            vector_weight=vector_weight, bm25_weight=bm25_weight
        )
    return _hybrid_search_service


# Alias for backward compatibility with tests
HybridSearchManager = HybridSearchService
