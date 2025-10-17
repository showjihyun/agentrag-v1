# Maximal Marginal Relevance (MMR) for Result Diversity
import logging
import numpy as np
from typing import List, Dict, Any, Optional
import torch
from sentence_transformers import util

logger = logging.getLogger(__name__)


class MMRDiversifier:
    """
    Maximal Marginal Relevance for diverse search results.

    MMR balances:
    - Relevance: How well results match the query
    - Diversity: How different results are from each other

    Formula: MMR = λ * Relevance - (1-λ) * MaxSimilarity

    Benefits:
    - Avoid redundant results
    - Provide diverse perspectives
    - Better user experience
    """

    def __init__(self, embedding_service=None, lambda_param: float = 0.5):
        """
        Initialize MMR diversifier.

        Args:
            embedding_service: Service for generating embeddings
            lambda_param: Balance between relevance and diversity (0-1)
                         0 = max diversity, 1 = max relevance
        """
        self.embedding_service = embedding_service
        self.lambda_param = lambda_param

    async def diversify(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 10,
        lambda_param: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Apply MMR to diversify search results.

        Args:
            query: Search query
            results: Initial search results
            top_k: Number of diverse results to return
            lambda_param: Override default lambda

        Returns:
            Diversified results
        """
        if not results or len(results) <= top_k:
            return results[:top_k]

        lambda_val = lambda_param if lambda_param is not None else self.lambda_param

        try:
            # Get embeddings
            if self.embedding_service:
                query_emb = await self.embedding_service.embed(query)
                result_texts = [r.get("text", "") for r in results]
                result_embs = await self.embedding_service.embed_batch(result_texts)
            else:
                # Fallback: use scores only
                return self._diversify_by_scores(results, top_k, lambda_val)

            # Convert to tensors
            query_tensor = torch.tensor(query_emb).unsqueeze(0)
            result_tensors = torch.tensor(result_embs)

            # Calculate relevance scores
            relevance_scores = util.cos_sim(query_tensor, result_tensors)[0]

            # MMR selection
            selected_indices = []
            remaining_indices = list(range(len(results)))

            # Select first result (highest relevance)
            first_idx = int(torch.argmax(relevance_scores))
            selected_indices.append(first_idx)
            remaining_indices.remove(first_idx)

            # Select remaining results using MMR
            while len(selected_indices) < top_k and remaining_indices:
                mmr_scores = []

                for idx in remaining_indices:
                    # Relevance to query
                    relevance = float(relevance_scores[idx])

                    # Max similarity to already selected results
                    max_sim = 0.0
                    for selected_idx in selected_indices:
                        sim = float(
                            util.cos_sim(
                                result_tensors[idx].unsqueeze(0),
                                result_tensors[selected_idx].unsqueeze(0),
                            )[0][0]
                        )
                        max_sim = max(max_sim, sim)

                    # MMR score
                    mmr_score = lambda_val * relevance - (1 - lambda_val) * max_sim
                    mmr_scores.append((idx, mmr_score))

                # Select result with highest MMR score
                best_idx, best_score = max(mmr_scores, key=lambda x: x[1])
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)

            # Return selected results
            diversified = [results[idx] for idx in selected_indices]

            logger.info(
                f"MMR diversification: {len(results)} → {len(diversified)} results "
                f"(λ={lambda_val})"
            )

            return diversified

        except Exception as e:
            logger.error(f"MMR diversification failed: {e}")
            return results[:top_k]

    def _diversify_by_scores(
        self, results: List[Dict[str, Any]], top_k: int, lambda_param: float
    ) -> List[Dict[str, Any]]:
        """Fallback diversification using scores only"""
        # Simple strategy: alternate between high and medium scores
        sorted_results = sorted(
            results, key=lambda x: x.get("score", 0.0), reverse=True
        )

        selected = []
        high_idx = 0
        mid_idx = len(sorted_results) // 2

        while len(selected) < top_k:
            if high_idx < len(sorted_results):
                selected.append(sorted_results[high_idx])
                high_idx += 1

            if len(selected) < top_k and mid_idx < len(sorted_results):
                selected.append(sorted_results[mid_idx])
                mid_idx += 1

            if high_idx >= len(sorted_results) and mid_idx >= len(sorted_results):
                break

        return selected[:top_k]

    async def diversify_with_clustering(
        self, results: List[Dict[str, Any]], top_k: int = 10, num_clusters: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Diversify using clustering approach.

        Groups similar results and selects from each cluster.

        Args:
            results: Search results
            top_k: Number of results to return
            num_clusters: Number of clusters to create

        Returns:
            Diversified results from different clusters
        """
        if not results or len(results) <= top_k:
            return results[:top_k]

        try:
            if not self.embedding_service:
                return results[:top_k]

            # Get embeddings
            result_texts = [r.get("text", "") for r in results]
            result_embs = await self.embedding_service.embed_batch(result_texts)

            # Simple k-means clustering
            from sklearn.cluster import KMeans

            kmeans = KMeans(n_clusters=min(num_clusters, len(results)), random_state=42)
            clusters = kmeans.fit_predict(result_embs)

            # Select top results from each cluster
            selected = []
            results_per_cluster = top_k // num_clusters

            for cluster_id in range(num_clusters):
                cluster_results = [
                    r for i, r in enumerate(results) if clusters[i] == cluster_id
                ]

                # Sort by score within cluster
                cluster_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)

                # Take top from this cluster
                selected.extend(cluster_results[:results_per_cluster])

                if len(selected) >= top_k:
                    break

            # Fill remaining slots with highest scores
            if len(selected) < top_k:
                remaining = [r for r in results if r not in selected]
                remaining.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                selected.extend(remaining[: top_k - len(selected)])

            logger.info(
                f"Cluster-based diversification: {len(results)} → {len(selected)} results "
                f"({num_clusters} clusters)"
            )

            return selected[:top_k]

        except Exception as e:
            logger.error(f"Cluster diversification failed: {e}")
            return results[:top_k]

    def calculate_diversity_score(self, results: List[Dict[str, Any]]) -> float:
        """
        Calculate diversity score for a result set.

        Higher score = more diverse results

        Args:
            results: Search results

        Returns:
            Diversity score (0-1)
        """
        if len(results) <= 1:
            return 1.0

        try:
            # Simple diversity: average pairwise text difference
            texts = [r.get("text", "") for r in results]

            total_diff = 0.0
            count = 0

            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    # Word-level difference
                    words1 = set(texts[i].lower().split())
                    words2 = set(texts[j].lower().split())

                    if words1 or words2:
                        diff = 1.0 - (len(words1 & words2) / len(words1 | words2))
                        total_diff += diff
                        count += 1

            return total_diff / count if count > 0 else 0.0

        except Exception as e:
            logger.debug(f"Diversity calculation failed: {e}")
            return 0.0


# Global diversifier instance
_mmr_diversifier: Optional[MMRDiversifier] = None


def get_mmr_diversifier(
    embedding_service=None, lambda_param: float = 0.5
) -> MMRDiversifier:
    """Get global MMR diversifier instance"""
    global _mmr_diversifier
    if _mmr_diversifier is None:
        _mmr_diversifier = MMRDiversifier(embedding_service, lambda_param)
    return _mmr_diversifier
