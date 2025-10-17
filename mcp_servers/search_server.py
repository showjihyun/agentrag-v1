#!/usr/bin/env python3
"""
Web Search MCP Server

This MCP server provides web search capabilities using DuckDuckGo.
It includes result parsing, formatting, and rate limiting.
"""

import asyncio
import logging
import sys
import os
import time
from typing import Any, Dict, List
from collections import deque

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("ERROR: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("WARNING: duckduckgo-search not installed. Install with: pip install duckduckgo-search", file=sys.stderr)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("search_server")


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int = 10, time_window: float = 60.0):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
    
    async def acquire(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        
        # Remove old calls outside the time window
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()
        
        # If at limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.time_window - now
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                # Retry after waiting
                return await self.acquire()
        
        # Record this call
        self.calls.append(now)


class WebSearchServer:
    """MCP Server for web search capabilities."""
    
    def __init__(self, max_calls_per_minute: int = 10):
        """
        Initialize the Web Search Server.
        
        Args:
            max_calls_per_minute: Maximum search calls per minute
        """
        self.server = Server("web-search-server")
        self.rate_limiter = RateLimiter(max_calls=max_calls_per_minute, time_window=60.0)
        
        if not DDGS_AVAILABLE:
            logger.warning(
                "DuckDuckGo search not available. "
                "Install with: pip install duckduckgo-search"
            )
        
        # Register tools
        self._register_tools()
        
        logger.info("WebSearchServer initialized")
    
    def _register_tools(self):
        """Register available tools with the MCP server."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="web_search",
                    description=(
                        "Search the web using DuckDuckGo. "
                        "Returns relevant web pages with titles, URLs, and snippets."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of results to return (default: 5)",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            },
                            "region": {
                                "type": "string",
                                "description": "Region for search results (e.g., 'us-en', 'uk-en')",
                                "default": "wt-wt"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            if name == "web_search":
                return await self._handle_web_search(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_web_search(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle web_search tool call.
        
        Args:
            arguments: Tool arguments containing query, num_results, and region
        
        Returns:
            List of TextContent with search results
        """
        try:
            query = arguments.get("query")
            num_results = arguments.get("num_results", 5)
            region = arguments.get("region", "wt-wt")
            
            if not query:
                raise ValueError("query parameter is required")
            
            if not DDGS_AVAILABLE:
                error_msg = (
                    "Web search is not available. "
                    "Install duckduckgo-search: pip install duckduckgo-search"
                )
                logger.error(error_msg)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]
            
            logger.info(f"Web search request: query='{query}', num_results={num_results}")
            
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Perform search
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(
                        keywords=query,
                        region=region,
                        max_results=num_results
                    ))
                
                if not results:
                    return [TextContent(
                        type="text",
                        text=f"No results found for query: {query}"
                    )]
                
                # Format results
                response_parts = [
                    f"Web Search Results for: {query}\n",
                    f"Found {len(results)} results:\n\n"
                ]
                
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'No title')
                    url = result.get('href', result.get('link', 'No URL'))
                    snippet = result.get('body', result.get('snippet', 'No description'))
                    
                    response_parts.append(
                        f"{i}. {title}\n"
                        f"   URL: {url}\n"
                        f"   {snippet}\n\n"
                    )
                
                response_text = "".join(response_parts)
                
                logger.info(f"Web search completed: {len(results)} results")
                
                return [TextContent(
                    type="text",
                    text=response_text
                )]
                
            except Exception as search_error:
                error_msg = f"Search failed: {str(search_error)}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]
            
        except Exception as e:
            error_msg = f"Web search request failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return [TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Web Search MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    # Get rate limit from environment variable if set
    max_calls = int(os.getenv("MAX_CALLS_PER_MINUTE", "10"))
    logger.info(f"Rate limit: {max_calls} calls per minute")
    
    server = WebSearchServer(max_calls_per_minute=max_calls)
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)
