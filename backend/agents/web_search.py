"""
Web Search Agent for performing web searches via MCP Search Server.

This agent specializes in web search operations, interfacing with
the MCP Search Server to query external web sources.
"""

import logging
from typing import List, Dict, Any, Optional

from backend.mcp.manager import MCPServerManager

logger = logging.getLogger(__name__)


class WebSearchResult:
    """Represents a single web search result."""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a web search result.

        Args:
            title: Title of the web page
            url: URL of the web page
            snippet: Text snippet/description
            score: Relevance score (0-1)
            metadata: Additional metadata
        """
        self.title = title
        self.url = url
        self.snippet = snippet
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "score": self.score,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"WebSearchResult(title='{self.title[:50]}...', url='{self.url}')"


class WebSearchAgent:
    """
    Agent specialized in web search.

    This agent communicates with the MCP Search Server to perform
    web searches and retrieve information from external sources.

    Features:
    - Web search via MCP
    - Result parsing and formatting
    - Relevance scoring
    - Error handling for MCP failures
    """

    def __init__(
        self, mcp_manager: MCPServerManager = None, server_name: str = "search_server"
    ):
        """
        Initialize the Web Search Agent.

        Args:
            mcp_manager: MCPServerManager instance for server communication (optional)
            server_name: Name of the MCP search server (default: "search_server")
        """
        self.mcp = mcp_manager
        self.server_name = server_name

        logger.info(f"WebSearchAgent initialized with server: {server_name}")

    async def search_web(
        self, query: str, num_results: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[WebSearchResult]:
        """
        Perform a web search via MCP Search Server.

        Args:
            query: The search query text
            num_results: Number of results to retrieve (default: 5)
            filters: Optional filters for search (e.g., date range, domain)

        Returns:
            List of WebSearchResult objects

        Raises:
            ValueError: If query is empty or parameters are invalid
            RuntimeError: If MCP server call fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if num_results < 1 or num_results > 50:
            raise ValueError("num_results must be between 1 and 50")

        try:
            if not self.mcp:
                raise ValueError("MCP manager not available - cannot perform web search")
                
            logger.info(
                f"Performing web search: query='{query[:50]}...', "
                f"num_results={num_results}"
            )

            # Prepare arguments for MCP tool call
            arguments = {"query": query, "num_results": num_results}

            # Add filters if provided
            if filters:
                arguments.update(filters)

            # Call the web_search tool via MCP
            result = await self.mcp.call_tool(
                server_name=self.server_name,
                tool_name="web_search",
                arguments=arguments,
            )

            # Parse and format results
            search_results = self._parse_results(result)

            # Apply relevance scoring
            search_results = self._score_results(search_results, query)

            logger.info(f"Web search completed: found {len(search_results)} results")

            return search_results

        except ValueError as e:
            # Re-raise validation errors
            raise

        except Exception as e:
            error_msg = f"Web search failed for query '{query[:50]}...': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _parse_results(self, mcp_result: Any) -> List[WebSearchResult]:
        """
        Parse MCP tool result and convert to WebSearchResult objects.

        Args:
            mcp_result: Raw result from MCP tool call

        Returns:
            List of WebSearchResult objects
        """
        try:
            # Handle different result formats from MCP
            if hasattr(mcp_result, "content"):
                results_data = mcp_result.content
            elif isinstance(mcp_result, dict):
                results_data = mcp_result.get(
                    "results", mcp_result.get("content", mcp_result)
                )
            elif isinstance(mcp_result, list):
                results_data = mcp_result
            else:
                results_data = []

            # Convert to list if needed
            if isinstance(results_data, str):
                # If content is a string, try to parse as JSON
                import json

                try:
                    results_data = json.loads(results_data)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Could not parse MCP result as JSON: {results_data[:100]}"
                    )
                    results_data = []

            # Ensure we have a list
            if not isinstance(results_data, list):
                if isinstance(results_data, dict) and "results" in results_data:
                    results_data = results_data["results"]
                else:
                    results_data = [results_data] if results_data else []

            # Convert each result to WebSearchResult
            search_results = []
            for idx, item in enumerate(results_data):
                try:
                    search_result = self._convert_to_web_search_result(item, idx)
                    if search_result:
                        search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Failed to convert result item {idx}: {str(e)}")
                    continue

            return search_results

        except Exception as e:
            logger.error(f"Failed to parse MCP results: {str(e)}")
            # Return empty list rather than failing completely
            return []

    def _convert_to_web_search_result(
        self, item: Dict[str, Any], index: int
    ) -> Optional[WebSearchResult]:
        """
        Convert a single result item to WebSearchResult object.

        Args:
            item: Result item from MCP response
            index: Index of the item in results list

        Returns:
            WebSearchResult object or None if conversion fails
        """
        try:
            # Handle different field naming conventions
            title = item.get("title") or item.get("name") or f"Result {index + 1}"

            url = item.get("url") or item.get("link") or item.get("href") or ""

            snippet = (
                item.get("snippet")
                or item.get("description")
                or item.get("content")
                or item.get("text")
                or ""
            )

            score = float(item.get("score", 0.0))

            # Extract metadata
            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            # Add any additional fields to metadata
            for key, value in item.items():
                if key not in [
                    "title",
                    "name",
                    "url",
                    "link",
                    "href",
                    "snippet",
                    "description",
                    "content",
                    "text",
                    "score",
                    "metadata",
                ]:
                    metadata[key] = value

            return WebSearchResult(
                title=title, url=url, snippet=snippet, score=score, metadata=metadata
            )

        except Exception as e:
            logger.warning(
                f"Failed to convert item to WebSearchResult: {str(e)}, item: {item}"
            )
            return None

    def _score_results(
        self, results: List[WebSearchResult], query: str
    ) -> List[WebSearchResult]:
        """
        Apply relevance scoring to search results.

        This method enhances the scoring by analyzing how well each result
        matches the query based on title and snippet content.

        Args:
            results: List of WebSearchResult objects
            query: Original search query

        Returns:
            List of WebSearchResult objects with updated scores
        """
        try:
            query_lower = query.lower()
            query_terms = set(query_lower.split())

            for result in results:
                # If result already has a score, use it as base
                base_score = result.score if result.score > 0 else 0.5

                # Calculate term overlap in title and snippet
                title_lower = result.title.lower()
                snippet_lower = result.snippet.lower()

                # Count matching terms
                title_matches = sum(1 for term in query_terms if term in title_lower)
                snippet_matches = sum(
                    1 for term in query_terms if term in snippet_lower
                )

                # Calculate relevance boost
                title_boost = (
                    (title_matches / len(query_terms)) * 0.3 if query_terms else 0
                )
                snippet_boost = (
                    (snippet_matches / len(query_terms)) * 0.2 if query_terms else 0
                )

                # Update score (capped at 1.0)
                result.score = min(1.0, base_score + title_boost + snippet_boost)

            # Sort by score (highest first)
            results.sort(key=lambda x: x.score, reverse=True)

            return results

        except Exception as e:
            logger.warning(f"Failed to score results: {str(e)}")
            # Return original results if scoring fails
            return results

    async def search_with_context(
        self, query: str, context: str, num_results: int = 5
    ) -> List[WebSearchResult]:
        """
        Perform a web search with additional context.

        This method enhances the query with context to get more relevant results.

        Args:
            query: The search query text
            context: Additional context to inform the search
            num_results: Number of results to retrieve

        Returns:
            List of WebSearchResult objects
        """
        # Enhance query with context (simple approach)
        enhanced_query = f"{query} {context[:100]}"

        logger.info(
            f"Performing context-aware search: query='{query}', "
            f"context_length={len(context)}"
        )

        return await self.search_web(enhanced_query, num_results)

    async def health_check(self) -> bool:
        """
        Check if the MCP Search Server is available and responsive.

        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            # Check if server is connected
            if not self.mcp.is_connected(self.server_name):
                logger.warning(f"Search server '{self.server_name}' is not connected")
                return False

            # Try to list tools to verify server is responsive
            tools = await self.mcp.list_tools(self.server_name)

            # Check if web_search tool is available
            tool_names = [tool["name"] for tool in tools]
            if "web_search" not in tool_names:
                logger.warning(
                    f"web_search tool not found on server '{self.server_name}'"
                )
                return False

            logger.info(f"Search server '{self.server_name}' is healthy")
            return True

        except Exception as e:
            logger.error(
                f"Health check failed for search server '{self.server_name}': {str(e)}"
            )
            return False

    def format_results_as_text(self, results: List[WebSearchResult]) -> str:
        """
        Format search results as readable text.

        Args:
            results: List of WebSearchResult objects

        Returns:
            Formatted text string
        """
        if not results:
            return "No search results found."

        formatted = []
        for idx, result in enumerate(results, 1):
            formatted.append(
                f"{idx}. {result.title}\n"
                f"   URL: {result.url}\n"
                f"   {result.snippet}\n"
                f"   Relevance: {result.score:.2f}\n"
            )

        return "\n".join(formatted)

    def __repr__(self) -> str:
        return f"WebSearchAgent(server={self.server_name})"
