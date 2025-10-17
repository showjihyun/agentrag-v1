#!/usr/bin/env python3
"""
Vector Search MCP Server

This MCP server provides vector similarity search capabilities using Milvus.
It integrates with the EmbeddingService for query embedding and MilvusManager
for vector search operations.
"""

import asyncio
import logging
import sys
import os
from typing import Any, Dict, List

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("ERROR: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vector_server")


class VectorSearchServer:
    """MCP Server for vector similarity search."""
    
    def __init__(self):
        """Initialize the Vector Search Server."""
        self.server = Server("vector-search-server")
        self.embedding_service: EmbeddingService = None
        self.milvus_manager: MilvusManager = None
        
        # Register tools
        self._register_tools()
        
        logger.info("VectorSearchServer initialized")
    
    def _register_tools(self):
        """Register available tools with the MCP server."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="vector_search",
                    description=(
                        "Perform vector similarity search to find relevant document chunks. "
                        "Converts the query text to an embedding and searches the vector database "
                        "for the most similar documents."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query text"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return (default: 10)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100
                            },
                            "filters": {
                                "type": "string",
                                "description": (
                                    "Optional Milvus filter expression "
                                    "(e.g., 'document_id == \"doc123\"')"
                                ),
                                "default": None
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            if name == "vector_search":
                return await self._handle_vector_search(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_vector_search(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle vector search tool call.
        
        Args:
            arguments: Tool arguments containing query, top_k, and optional filters
        
        Returns:
            List of TextContent with search results
        """
        try:
            # Extract arguments
            query = arguments.get("query")
            top_k = arguments.get("top_k", 10)
            filters = arguments.get("filters")
            
            if not query:
                raise ValueError("query parameter is required")
            
            logger.info(f"Vector search request: query='{query[:50]}...', top_k={top_k}")
            
            # Initialize services if not already done
            if self.embedding_service is None:
                logger.info("Initializing EmbeddingService...")
                self.embedding_service = EmbeddingService(
                    model_name=settings.EMBEDDING_MODEL
                )
            
            if self.milvus_manager is None:
                logger.info("Initializing MilvusManager...")
                self.milvus_manager = MilvusManager(
                    host=settings.MILVUS_HOST,
                    port=settings.MILVUS_PORT,
                    collection_name=settings.MILVUS_COLLECTION_NAME,
                    embedding_dim=self.embedding_service.dimension
                )
                self.milvus_manager.connect()
            
            # Generate query embedding
            logger.info("Generating query embedding...")
            query_embedding = self.embedding_service.embed_text(query)
            
            # Perform vector search
            logger.info("Performing vector search...")
            search_results = await self.milvus_manager.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters
            )
            
            # Format results
            if not search_results:
                return [TextContent(
                    type="text",
                    text="No results found for the query."
                )]
            
            # Build response text
            response_parts = [f"Found {len(search_results)} results:\n"]
            
            for i, result in enumerate(search_results, 1):
                response_parts.append(
                    f"\n{i}. Document: {result.document_name} "
                    f"(Score: {result.score:.4f})\n"
                    f"   Chunk {result.chunk_index}: {result.text[:200]}...\n"
                    f"   Document ID: {result.document_id}\n"
                )
            
            response_text = "".join(response_parts)
            
            logger.info(f"Vector search completed: {len(search_results)} results")
            
            return [TextContent(
                type="text",
                text=response_text
            )]
            
        except Exception as e:
            error_msg = f"Vector search failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return [TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up VectorSearchServer...")
        
        if self.milvus_manager:
            self.milvus_manager.disconnect()
        
        logger.info("Cleanup complete")
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Vector Search MCP Server...")
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    server = VectorSearchServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)
