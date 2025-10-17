# RAG Fusion - Multiple Query Perspectives
import logging
from typing import List, Dict, Any, Optional
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class RAGFusion:
    """
    RAG Fusion: Search with multiple query perspectives.

    Strategy:
    1. Rewrite query from multiple perspectives
    2. Search with each perspective
    3. Fuse results using Reciprocal Rank Fusion (RRF)

    Benefits:
    - 30-40% better recall
    - More robust to query phrasing
    - Captures different aspects
    """

    def __init__(self, llm_manager, vector_search_agent, rrf_k: int = 60):
        self.llm_manager = llm_manager
        self.vector_agent = vector_search_agent
        self.rrf_k = rrf_k

    async def fused_search(
        self,
        original_query: str,
        top_k: int = 10,
        num_perspectives: int = 5,
        perspective_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform RAG Fusion search.

        Args:
            original_query: Original user query
            top_k: Number of final results
            num_perspectives: Number of query perspectives
            perspective_types: Specific perspectives to use

        Returns:
            Fused search results
        """
        try:
            # Step 1: Generate query perspectives
            perspectives = await self.generate_perspectives(
                original_query, num_perspectives, perspective_types
            )

            logger.info(
                f"Generated {len(perspectives)} query perspectives "
                f"for: {original_query[:50]}..."
            )

            # Step 2: Search with each perspective
            all_results = await self._search_all_perspectives(
                perspectives, top_k * 2
            )  # Get more for fusion

            # Step 3: Fuse results using RRF
            fused_results = self._reciprocal_rank_fusion(all_results, top_k)

            logger.info(
                f"RAG Fusion: {sum(len(r) for r in all_results)} total results → "
                f"{len(fused_results)} fused results"
            )

            return fused_results

        except Exception as e:
            logger.error(f"RAG Fusion failed: {e}")
            # Fallback to original query
            return await self.vector_agent.search(query=original_query, top_k=top_k)

    async def generate_perspectives(
        self,
        query: str,
        num_perspectives: int = 5,
        perspective_types: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """
        Generate multiple query perspectives.

        Args:
            query: Original query
            num_perspectives: Number of perspectives
            perspective_types: Specific types (technical, business, etc.)

        Returns:
            List of query perspectives
        """
        # Default perspective types
        if not perspective_types:
            perspective_types = [
                "technical",
                "business",
                "user-focused",
                "detailed",
                "high-level",
            ]

        try:
            prompt = f"""Rewrite the following query from {num_perspectives} different perspectives.
Each perspective should capture a different aspect or angle of the question.

Perspectives to use: {', '.join(perspective_types[:num_perspectives])}

Original Query: {query}

Rewritten queries (one per line, labeled with perspective):"""

            response = await self.llm_manager.generate(
                prompt=prompt,
                max_tokens=400,
                temperature=0.7,  # Higher temperature for diversity
            )

            # Parse perspectives
            perspectives = [{"query": query, "perspective": "original"}]

            for line in response.split("\n"):
                line = line.strip()
                if not line or len(line) < 10:
                    continue

                # Try to extract perspective label
                import re

                match = re.match(r"^(\w+[-\w]*)\s*:\s*(.+)$", line)

                if match:
                    perspective_name = match.group(1)
                    rewritten_query = match.group(2)
                else:
                    # No label, use line as is
                    perspective_name = f"perspective_{len(perspectives)}"
                    rewritten_query = line

                perspectives.append(
                    {"query": rewritten_query, "perspective": perspective_name}
                )

            # Limit to requested number
            return perspectives[: num_perspectives + 1]  # +1 for original

        except Exception as e:
            logger.error(f"Perspective generation failed: {e}")
            # Fallback: return original query only
            return [{"query": query, "perspective": "original"}]

    async def _search_all_perspectives(
        self, perspectives: List[Dict[str, str]], top_k: int
    ) -> List[List[Dict[str, Any]]]:
        """Search with all perspectives in parallel"""
        tasks = [
            self.vector_agent.search(
                query=p["query"], top_k=top_k, search_mode="hybrid"
            )
            for p in perspectives
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    f"Search failed for perspective '{perspectives[i]['perspective']}': {result}"
                )
            else:
                # Tag results with perspective
                for r in result:
                    r["perspective"] = perspectives[i]["perspective"]
                valid_results.append(result)

        return valid_results

    def _reciprocal_rank_fusion(
        self, results_lists: List[List[Dict[str, Any]]], top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Fuse multiple result lists using Reciprocal Rank Fusion.

        RRF formula: score = sum(1 / (k + rank))

        Args:
            results_lists: List of result lists from different perspectives
            top_k: Number of results to return

        Returns:
            Fused and ranked results
        """
        rrf_scores = defaultdict(float)
        result_data = {}

        # Calculate RRF scores
        for results in results_lists:
            for rank, result in enumerate(results, start=1):
                result_id = result.get("chunk_id") or result.get("id")

                # RRF score
                rrf_score = 1.0 / (self.rrf_k + rank)
                rrf_scores[result_id] += rrf_score

                # Store result data (keep highest scoring version)
                if result_id not in result_data or rrf_scores[result_id] > result_data[
                    result_id
                ].get("rrf_score", 0):
                    result_data[result_id] = {
                        **result,
                        "rrf_score": rrf_scores[result_id],
                        "fusion_count": 1,
                    }
                else:
                    result_data[result_id]["fusion_count"] += 1

        # Sort by RRF score
        sorted_results = sorted(
            result_data.values(), key=lambda x: x["rrf_score"], reverse=True
        )

        return sorted_results[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG Fusion statistics"""
        return {"enabled": True, "rrf_k": self.rrf_k, "default_perspectives": 5}


class AdaptiveRAGFusion(RAGFusion):
    """
    Adaptive RAG Fusion that adjusts based on query complexity.

    - Simple queries: 2-3 perspectives
    - Medium queries: 4-5 perspectives
    - Complex queries: 6-7 perspectives
    """

    async def fused_search(
        self,
        original_query: str,
        top_k: int = 10,
        num_perspectives: Optional[int] = None,
        perspective_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Adaptive fused search"""

        # Determine query complexity
        if num_perspectives is None:
            num_perspectives = await self._determine_perspectives_count(original_query)

        return await super().fused_search(
            original_query, top_k, num_perspectives, perspective_types
        )

    async def _determine_perspectives_count(self, query: str) -> int:
        """Determine optimal number of perspectives based on query"""
        query_length = len(query.split())

        # Simple heuristic
        if query_length < 5:
            return 2  # Simple query
        elif query_length < 15:
            return 4  # Medium query
        else:
            return 6  # Complex query


def create_rag_fusion(llm_manager, vector_agent, adaptive: bool = False) -> RAGFusion:
    """Factory function to create RAG Fusion"""
    if adaptive:
        return AdaptiveRAGFusion(llm_manager, vector_agent)
    else:
        return RAGFusion(llm_manager, vector_agent)
