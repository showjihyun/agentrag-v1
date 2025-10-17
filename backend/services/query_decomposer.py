# Query Decomposition and Routing
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries"""

    FACTUAL = "factual"  # Simple fact lookup
    ANALYTICAL = "analytical"  # Requires analysis
    COMPARATIVE = "comparative"  # Comparison between items
    TEMPORAL = "temporal"  # Time-based queries
    AGGREGATION = "aggregation"  # Requires aggregation
    COMPLEX = "complex"  # Multiple sub-queries


class QueryDecomposer:
    """
    Decompose complex queries into simpler sub-queries.

    Handles:
    - Multi-part questions
    - Comparative queries
    - Temporal queries
    - Aggregation queries

    Benefits:
    - Better handling of complex questions
    - More accurate results
    - Structured approach
    """

    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.decomposition_cache = {}

    async def decompose(self, query: str, max_sub_queries: int = 5) -> Dict[str, Any]:
        """
        Decompose a complex query into sub-queries.

        Args:
            query: Complex query
            max_sub_queries: Maximum number of sub-queries

        Returns:
            Dictionary with query type and sub-queries
        """
        # Check cache
        if query in self.decomposition_cache:
            logger.info(f"Using cached decomposition for: {query[:50]}...")
            return self.decomposition_cache[query]

        try:
            # Classify query type
            query_type = await self._classify_query(query)

            # Decompose based on type
            if query_type == QueryType.COMPLEX:
                sub_queries = await self._decompose_complex(query, max_sub_queries)
            elif query_type == QueryType.COMPARATIVE:
                sub_queries = await self._decompose_comparative(query)
            elif query_type == QueryType.TEMPORAL:
                sub_queries = await self._decompose_temporal(query)
            elif query_type == QueryType.AGGREGATION:
                sub_queries = await self._decompose_aggregation(query)
            else:
                # Simple query - no decomposition needed
                sub_queries = [{"query": query, "type": "main"}]

            result = {
                "original_query": query,
                "query_type": query_type.value,
                "sub_queries": sub_queries,
                "needs_synthesis": len(sub_queries) > 1,
            }

            # Cache result
            self.decomposition_cache[query] = result

            logger.info(
                f"Decomposed query into {len(sub_queries)} sub-queries "
                f"(type: {query_type.value})"
            )

            return result

        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            # Fallback: treat as simple query
            return {
                "original_query": query,
                "query_type": QueryType.FACTUAL.value,
                "sub_queries": [{"query": query, "type": "main"}],
                "needs_synthesis": False,
            }

    async def _classify_query(self, query: str) -> QueryType:
        """Classify query type"""
        try:
            prompt = f"""Classify the following query into one of these types:
- factual: Simple fact lookup
- analytical: Requires analysis or reasoning
- comparative: Compares two or more things
- temporal: Involves time periods or dates
- aggregation: Requires combining multiple pieces of information
- complex: Multiple questions or parts

Query: {query}

Classification (one word):"""

            response = await self.llm_manager.generate(
                prompt=prompt, max_tokens=20, temperature=0.1
            )

            classification = response.strip().lower()

            # Map to QueryType
            for qtype in QueryType:
                if qtype.value in classification:
                    return qtype

            # Default to factual
            return QueryType.FACTUAL

        except Exception as e:
            logger.debug(f"Query classification failed: {e}")
            return QueryType.FACTUAL

    async def _decompose_complex(
        self, query: str, max_sub_queries: int
    ) -> List[Dict[str, str]]:
        """Decompose complex query"""
        try:
            prompt = f"""Break down the following complex query into {max_sub_queries} or fewer simpler sub-queries.
Each sub-query should be answerable independently.

Complex Query: {query}

Sub-queries (one per line, numbered):"""

            response = await self.llm_manager.generate(
                prompt=prompt, max_tokens=300, temperature=0.3
            )

            # Parse sub-queries
            sub_queries = []
            for line in response.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Remove numbering
                import re

                cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)

                if cleaned and len(cleaned) > 10:
                    sub_queries.append({"query": cleaned, "type": "sub_query"})

            if not sub_queries:
                return [{"query": query, "type": "main"}]

            return sub_queries[:max_sub_queries]

        except Exception as e:
            logger.debug(f"Complex decomposition failed: {e}")
            return [{"query": query, "type": "main"}]

    async def _decompose_comparative(self, query: str) -> List[Dict[str, str]]:
        """Decompose comparative query"""
        try:
            prompt = f"""This is a comparative query. Break it into:
1. Query for first item
2. Query for second item
3. Comparison criteria

Query: {query}

Breakdown (one per line):"""

            response = await self.llm_manager.generate(
                prompt=prompt, max_tokens=200, temperature=0.3
            )

            lines = [l.strip() for l in response.split("\n") if l.strip()]

            sub_queries = []
            for i, line in enumerate(lines[:3]):
                import re

                cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)

                query_type = (
                    "item_1" if i == 0 else "item_2" if i == 1 else "comparison"
                )

                sub_queries.append({"query": cleaned, "type": query_type})

            return sub_queries if sub_queries else [{"query": query, "type": "main"}]

        except Exception as e:
            logger.debug(f"Comparative decomposition failed: {e}")
            return [{"query": query, "type": "main"}]

    async def _decompose_temporal(self, query: str) -> List[Dict[str, str]]:
        """Decompose temporal query"""
        try:
            # Extract time periods
            import re

            years = re.findall(r"\b(19|20)\d{2}\b", query)

            if len(years) >= 2:
                # Create sub-queries for each time period
                sub_queries = []
                for year in years[:3]:  # Max 3 years
                    sub_query = (
                        query.replace(years[0], year)
                        if years[0] in query
                        else f"{query} in {year}"
                    )
                    sub_queries.append({"query": sub_query, "type": f"temporal_{year}"})

                return sub_queries

            return [{"query": query, "type": "main"}]

        except Exception as e:
            logger.debug(f"Temporal decomposition failed: {e}")
            return [{"query": query, "type": "main"}]

    async def _decompose_aggregation(self, query: str) -> List[Dict[str, str]]:
        """Decompose aggregation query"""
        # Aggregation queries often need the full context
        # But we can identify key aspects
        return [
            {"query": query, "type": "aggregation_main"},
            {"query": f"Key facts about: {query}", "type": "aggregation_facts"},
        ]


class QueryRouter:
    """
    Route queries to appropriate search strategies.

    Routes based on:
    - Query type
    - Query complexity
    - Available resources
    """

    def __init__(self, vector_search_agent, agentic_processor=None):
        self.vector_agent = vector_search_agent
        self.agentic_processor = agentic_processor

    async def route_and_execute(
        self, decomposed_query: Dict[str, Any], top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Route and execute decomposed query.

        Args:
            decomposed_query: Output from QueryDecomposer
            top_k: Number of results per sub-query

        Returns:
            Aggregated results
        """
        try:
            query_type = decomposed_query["query_type"]
            sub_queries = decomposed_query["sub_queries"]

            # Execute sub-queries
            if len(sub_queries) == 1:
                # Simple query - direct search
                results = await self._execute_simple(sub_queries[0]["query"], top_k)
            else:
                # Multiple sub-queries - execute in parallel
                results = await self._execute_multiple(sub_queries, top_k)

            return {
                "original_query": decomposed_query["original_query"],
                "query_type": query_type,
                "results": results,
                "sub_query_count": len(sub_queries),
            }

        except Exception as e:
            logger.error(f"Query routing failed: {e}")
            return {
                "original_query": decomposed_query["original_query"],
                "query_type": "error",
                "results": [],
                "error": str(e),
            }

    async def _execute_simple(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Execute simple query"""
        return await self.vector_agent.search(
            query=query, top_k=top_k, search_mode="hybrid"
        )

    async def _execute_multiple(
        self, sub_queries: List[Dict[str, str]], top_k: int
    ) -> List[Dict[str, Any]]:
        """Execute multiple sub-queries in parallel"""
        # Execute all sub-queries
        tasks = [
            self.vector_agent.search(
                query=sq["query"], top_k=top_k, search_mode="hybrid"
            )
            for sq in sub_queries
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        all_results = []
        for i, results in enumerate(results_list):
            if isinstance(results, Exception):
                logger.warning(f"Sub-query {i} failed: {results}")
                continue

            # Tag with sub-query info
            for result in results:
                result["sub_query_index"] = i
                result["sub_query_type"] = sub_queries[i]["type"]

            all_results.extend(results)

        # Deduplicate and sort
        seen_ids = set()
        unique_results = []

        for result in sorted(
            all_results, key=lambda x: x.get("score", 0.0), reverse=True
        ):
            result_id = result.get("chunk_id") or result.get("id")
            if result_id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result_id)

        return unique_results


def create_query_decomposer(llm_manager) -> QueryDecomposer:
    """Factory function"""
    return QueryDecomposer(llm_manager)


def create_query_router(vector_agent, agentic_processor=None) -> QueryRouter:
    """Factory function"""
    return QueryRouter(vector_agent, agentic_processor)
