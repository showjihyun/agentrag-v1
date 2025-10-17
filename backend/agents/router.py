"""
Smart Agent Router for optimal agent selection.

This router analyzes queries and determines which agents should be used,
reducing unnecessary LLM calls and improving response time.
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Smart router for selecting optimal agents based on query analysis.

    Features:
    - Rule-based routing (fast)
    - LLM-based routing (accurate)
    - Query type caching
    - Parallel agent detection
    """

    def __init__(self, llm_manager=None):
        """
        Initialize AgentRouter.

        Args:
            llm_manager: Optional LLM manager for complex routing
        """
        self.llm = llm_manager
        self.cache = {}  # Query type cache

        # Routing rules: query patterns -> required agents
        self.routing_rules = {
            "document_query": ["vector_search"],
            "file_access": ["local_data"],
            "current_info": ["web_search"],
            "comprehensive": ["vector_search", "web_search"],
            "comparison": ["vector_search", "web_search"],
            "local_file": ["local_data"],
            "database_query": ["local_data"],
        }

        # Keywords for quick classification
        self.keywords = {
            "document_query": ["document", "pdf", "file", "text", "내용", "문서"],
            "current_info": [
                "latest",
                "recent",
                "current",
                "news",
                "today",
                "최신",
                "최근",
            ],
            "comparison": ["compare", "versus", "vs", "difference", "비교", "차이"],
            "local_file": ["read file", "open file", "파일 읽기"],
            "database_query": ["database", "query", "sql", "데이터베이스"],
        }

        logger.info("AgentRouter initialized")

    async def route(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Determine which agents should be used for the query.

        Args:
            query: User query
            context: Optional context information
            use_cache: Whether to use cached results

        Returns:
            Dict with:
                - agents: List of agent names
                - parallel: Whether agents can run in parallel
                - reasoning: Why these agents were selected
        """
        if not query or not query.strip():
            return {
                "agents": ["vector_search"],
                "parallel": False,
                "reasoning": "Default to vector search for empty query",
            }

        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(query)
            if cache_key in self.cache:
                logger.debug(f"Cache hit for query routing: {query[:50]}...")
                return self.cache[cache_key]

        # Try quick rule-based routing first
        quick_result = self._quick_route(query)
        if quick_result:
            if use_cache:
                self.cache[cache_key] = quick_result
            return quick_result

        # Fall back to LLM-based routing for complex queries
        if self.llm:
            llm_result = await self._llm_route(query, context)
            if use_cache:
                self.cache[cache_key] = llm_result
            return llm_result

        # Default fallback
        default_result = {
            "agents": ["vector_search"],
            "parallel": False,
            "reasoning": "Default routing (no LLM available)",
        }

        if use_cache:
            self.cache[cache_key] = default_result

        return default_result

    def _quick_route(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Fast rule-based routing using keyword matching.

        Args:
            query: User query

        Returns:
            Routing result or None if no clear match
        """
        query_lower = query.lower()

        # Check for each query type
        matches = {}
        for query_type, keywords in self.keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in query_lower)
            if match_count > 0:
                matches[query_type] = match_count

        # No clear match
        if not matches:
            return None

        # Get best match
        best_type = max(matches, key=matches.get)
        agents = self.routing_rules.get(best_type, ["vector_search"])

        # Determine if parallel execution is possible
        parallel = len(agents) > 1 and best_type in ["comprehensive", "comparison"]

        logger.info(f"Quick route: {best_type} -> {agents} " f"(parallel={parallel})")

        return {
            "agents": agents,
            "parallel": parallel,
            "reasoning": f"Rule-based: detected {best_type} query",
            "query_type": best_type,
        }

    async def _llm_route(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        LLM-based routing for complex queries.

        Args:
            query: User query
            context: Optional context

        Returns:
            Routing result
        """
        try:
            # Create routing prompt
            prompt = f"""Analyze this query and determine which agents to use.

Query: {query}

Available agents:
1. vector_search: Search in document database (semantic search)
2. local_data: Access local files or databases
3. web_search: Search the web for current information

Determine:
1. Which agents are needed? (can be multiple)
2. Can they run in parallel? (yes/no)
3. Why these agents?

Respond in JSON format:
{{
    "agents": ["agent1", "agent2"],
    "parallel": true/false,
    "reasoning": "explanation"
}}
"""

            # Get LLM response
            response = await self.llm.generate(
                [
                    {
                        "role": "system",
                        "content": "You are an expert at query analysis and agent selection.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            # Parse JSON response
            result = json.loads(response)

            # Validate agents
            valid_agents = ["vector_search", "local_data", "web_search"]
            result["agents"] = [
                agent for agent in result.get("agents", []) if agent in valid_agents
            ]

            # Ensure at least one agent
            if not result["agents"]:
                result["agents"] = ["vector_search"]

            logger.info(
                f"LLM route: {result['agents']} "
                f"(parallel={result.get('parallel', False)})"
            )

            return result

        except Exception as e:
            logger.error(f"LLM routing failed: {e}")
            # Fallback to default
            return {
                "agents": ["vector_search"],
                "parallel": False,
                "reasoning": f"LLM routing failed: {str(e)}",
            }

    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        # Normalize query
        normalized = query.lower().strip()
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()

    def clear_cache(self) -> None:
        """Clear routing cache."""
        self.cache.clear()
        logger.info("Routing cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            "cache_size": len(self.cache),
            "routing_rules": len(self.routing_rules),
            "keyword_patterns": len(self.keywords),
        }

    def __repr__(self) -> str:
        return f"AgentRouter(cache_size={len(self.cache)})"
