#!/usr/bin/env python3
"""
Local Data MCP Server

This MCP server provides access to local file system and SQLite databases.
It includes security checks to prevent unauthorized file access.
"""

import asyncio
import logging
import sys
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("ERROR: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("local_data_server")


class LocalDataServer:
    """MCP Server for local file and database access."""
    
    def __init__(self, allowed_paths: List[str] = None):
        """
        Initialize the Local Data Server.
        
        Args:
            allowed_paths: List of allowed base paths for file access.
                          If None, defaults to current working directory.
        """
        self.server = Server("local-data-server")
        
        # Set allowed paths for security
        if allowed_paths is None:
            # Default to current working directory and uploads folder
            self.allowed_paths = [
                os.getcwd(),
                os.path.join(os.getcwd(), "backend", "uploads")
            ]
        else:
            self.allowed_paths = [os.path.abspath(p) for p in allowed_paths]
        
        logger.info(f"Allowed paths: {self.allowed_paths}")
        
        # Register tools
        self._register_tools()
        
        logger.info("LocalDataServer initialized")
    
    def _is_path_allowed(self, file_path: str) -> bool:
        """
        Check if a file path is within allowed directories.
        
        Args:
            file_path: Path to check
        
        Returns:
            bool: True if path is allowed, False otherwise
        """
        try:
            abs_path = os.path.abspath(file_path)
            
            for allowed_path in self.allowed_paths:
                if abs_path.startswith(allowed_path):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking path: {str(e)}")
            return False
    
    def _register_tools(self):
        """Register available tools with the MCP server."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="read_file",
                    description=(
                        "Read contents of a local file. "
                        "Only files within allowed directories can be accessed."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to read"
                            },
                            "encoding": {
                                "type": "string",
                                "description": "File encoding (default: utf-8)",
                                "default": "utf-8"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="query_database",
                    description=(
                        "Execute a SELECT query on a SQLite database. "
                        "Only SELECT queries are allowed for security."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "string",
                                "description": "Path to the SQLite database file"
                            },
                            "query": {
                                "type": "string",
                                "description": "SQL SELECT query to execute"
                            },
                            "params": {
                                "type": "array",
                                "description": "Optional query parameters for parameterized queries",
                                "items": {"type": "string"},
                                "default": []
                            }
                        },
                        "required": ["database", "query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            if name == "read_file":
                return await self._handle_read_file(arguments)
            elif name == "query_database":
                return await self._handle_query_database(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_read_file(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle read_file tool call.
        
        Args:
            arguments: Tool arguments containing path and encoding
        
        Returns:
            List of TextContent with file contents
        """
        try:
            file_path = arguments.get("path")
            encoding = arguments.get("encoding", "utf-8")
            
            if not file_path:
                raise ValueError("path parameter is required")
            
            logger.info(f"Read file request: {file_path}")
            
            # Security check
            if not self._is_path_allowed(file_path):
                error_msg = (
                    f"Access denied: Path '{file_path}' is outside allowed directories. "
                    f"Allowed paths: {self.allowed_paths}"
                )
                logger.warning(error_msg)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]
            
            # Check if file exists
            if not os.path.exists(file_path):
                error_msg = f"File not found: {file_path}"
                logger.warning(error_msg)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]
            
            # Check if it's a file (not a directory)
            if not os.path.isfile(file_path):
                error_msg = f"Path is not a file: {file_path}"
                logger.warning(error_msg)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]
            
            # Read file
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                logger.info(f"Successfully read file: {file_path} ({len(content)} chars)")
                
                return [TextContent(
                    type="text",
                    text=f"File: {file_path}\n\n{content}"
                )]
                
            except UnicodeDecodeError:
                # Try with different encoding
                logger.warning(f"Failed to read with {encoding}, trying latin-1")
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                
                return [TextContent(
                    type="text",
                    text=f"File: {file_path} (read with latin-1 encoding)\n\n{content}"
                )]
            
        except Exception as e:
            error_msg = f"Failed to read file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return [TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]
    
    async def _handle_query_database(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle query_database tool call.
        
        Args:
            arguments: Tool arguments containing database, query, and params
        
        Returns:
            List of TextContent with query results
        """
        try:
            db_path = arguments.get("database")
            query = arguments.get("query")
            params = arguments.get("params", [])
            
            if not db_path:
                raise ValueError("database parameter is required")
            if not query:
                raise ValueError("query parameter is required")
            
            logger.info(f"Database query request: {db_path}")
            logger.debug(f"Query: {query}")
            
            # Security check - only allow SELECT queries
            query_upper = query.strip().upper()
            if not query_upper.startswith("SELECT"):
                error_msg = "Only SELECT queries are allowed for security reasons"
                logger.warning(error_msg)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]
            
            # Security check - path validation
            if not self._is_path_allowed(db_path):
                error_msg = (
                    f"Access denied: Database path '{db_path}' is outside allowed directories. "
                    f"Allowed paths: {self.allowed_paths}"
                )
                logger.warning(error_msg)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]
            
            # Check if database exists
            if not os.path.exists(db_path):
                error_msg = f"Database not found: {db_path}"
                logger.warning(error_msg)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]
            
            # Execute query
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            try:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                if not rows:
                    return [TextContent(
                        type="text",
                        text="Query executed successfully. No results returned."
                    )]
                
                # Format results
                columns = rows[0].keys()
                response_parts = [
                    f"Query Results ({len(rows)} rows):\n",
                    f"Columns: {', '.join(columns)}\n\n"
                ]
                
                for i, row in enumerate(rows[:100], 1):  # Limit to 100 rows
                    row_data = {col: row[col] for col in columns}
                    response_parts.append(f"{i}. {row_data}\n")
                
                if len(rows) > 100:
                    response_parts.append(f"\n... and {len(rows) - 100} more rows")
                
                response_text = "".join(response_parts)
                
                logger.info(f"Query executed successfully: {len(rows)} rows returned")
                
                return [TextContent(
                    type="text",
                    text=response_text
                )]
                
            finally:
                cursor.close()
                conn.close()
            
        except sqlite3.Error as e:
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return [TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]
        except Exception as e:
            error_msg = f"Failed to query database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return [TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Local Data MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    # Get allowed paths from environment variable if set
    allowed_paths_env = os.getenv("ALLOWED_PATHS")
    allowed_paths = None
    
    if allowed_paths_env:
        allowed_paths = [p.strip() for p in allowed_paths_env.split(",")]
        logger.info(f"Using allowed paths from environment: {allowed_paths}")
    
    server = LocalDataServer(allowed_paths=allowed_paths)
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)
