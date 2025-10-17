"""
Local Data Agent for accessing local files and databases via MCP Local Server.

This agent specializes in local data access operations, interfacing with
the MCP Local Data Server to read files and query databases.
"""

import logging
from typing import List, Dict, Any, Optional

from backend.mcp.manager import MCPServerManager

logger = logging.getLogger(__name__)


class LocalDataAgent:
    """
    Agent specialized in local data access.

    This agent communicates with the MCP Local Data Server to perform
    file system operations and database queries.

    Features:
    - File reading via MCP
    - Database querying via MCP
    - Result formatting and error handling
    - Security validation for file paths
    """

    def __init__(
        self, mcp_manager: MCPServerManager, server_name: str = "local_data_server"
    ):
        """
        Initialize the Local Data Agent.

        Args:
            mcp_manager: MCPServerManager instance for server communication
            server_name: Name of the MCP local data server (default: "local_data_server")
        """
        self.mcp = mcp_manager
        self.server_name = server_name

        logger.info(f"LocalDataAgent initialized with server: {server_name}")

    async def read_file(self, file_path: str) -> str:
        """
        Read a local file via MCP Local Data Server.

        Args:
            file_path: Path to the file to read

        Returns:
            str: File content as text

        Raises:
            ValueError: If file_path is empty or invalid
            RuntimeError: If MCP server call fails or file cannot be read
        """
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")

        # Basic path validation
        file_path = file_path.strip()

        try:
            logger.info(f"Reading file via MCP: {file_path}")

            # Call the read_file tool via MCP
            result = await self.mcp.call_tool(
                server_name=self.server_name,
                tool_name="read_file",
                arguments={"path": file_path},
            )

            # Extract content from result
            content = self._extract_content(result)

            logger.info(
                f"Successfully read file: {file_path} " f"({len(content)} characters)"
            )

            return content

        except ValueError as e:
            # Re-raise validation errors
            raise

        except Exception as e:
            error_msg = f"Failed to read file '{file_path}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def query_database(
        self, query: str, db_name: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Query a local database via MCP Local Data Server.

        Args:
            query: SQL query to execute
            db_name: Name of the database to query (default: "default")

        Returns:
            List of dictionaries representing query results (rows)

        Raises:
            ValueError: If query is empty or invalid
            RuntimeError: If MCP server call fails or query execution fails
        """
        if not query or not query.strip():
            raise ValueError("query cannot be empty")

        if not db_name or not db_name.strip():
            raise ValueError("db_name cannot be empty")

        query = query.strip()
        db_name = db_name.strip()

        try:
            logger.info(f"Querying database '{db_name}' via MCP: {query[:100]}...")

            # Call the query_database tool via MCP
            result = await self.mcp.call_tool(
                server_name=self.server_name,
                tool_name="query_database",
                arguments={"query": query, "database": db_name},
            )

            # Parse and format results
            rows = self._parse_query_results(result)

            logger.info(f"Database query completed: returned {len(rows)} rows")

            return rows

        except ValueError as e:
            # Re-raise validation errors
            raise

        except Exception as e:
            error_msg = f"Database query failed for '{db_name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _extract_content(self, mcp_result: Any) -> str:
        """
        Extract text content from MCP tool result.

        Args:
            mcp_result: Raw result from MCP tool call

        Returns:
            str: Extracted content

        Raises:
            ValueError: If content cannot be extracted
        """
        try:
            # Handle different result formats from MCP
            if hasattr(mcp_result, "content"):
                content = mcp_result.content
            elif isinstance(mcp_result, dict):
                content = mcp_result.get("content", mcp_result.get("text", ""))
            elif isinstance(mcp_result, str):
                content = mcp_result
            else:
                content = str(mcp_result)

            # Handle list of content items (MCP can return multiple content blocks)
            if isinstance(content, list):
                # Join all text content
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        text_parts.append(item.get("text", str(item)))
                    elif hasattr(item, "text"):
                        text_parts.append(item.text)
                    else:
                        text_parts.append(str(item))
                content = "\n".join(text_parts)

            return str(content)

        except Exception as e:
            logger.error(f"Failed to extract content from MCP result: {str(e)}")
            raise ValueError(f"Invalid content format: {str(e)}") from e

    def _parse_query_results(self, mcp_result: Any) -> List[Dict[str, Any]]:
        """
        Parse database query results from MCP tool result.

        Args:
            mcp_result: Raw result from MCP tool call

        Returns:
            List of dictionaries representing rows

        Raises:
            ValueError: If results cannot be parsed
        """
        try:
            # Handle different result formats from MCP
            if hasattr(mcp_result, "content"):
                results_data = mcp_result.content
            elif isinstance(mcp_result, dict):
                results_data = mcp_result.get(
                    "rows", mcp_result.get("results", mcp_result)
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
                if isinstance(results_data, dict):
                    # Single row result
                    results_data = [results_data]
                else:
                    results_data = []

            # Convert each row to dictionary
            rows = []
            for item in results_data:
                if isinstance(item, dict):
                    rows.append(item)
                elif hasattr(item, "__dict__"):
                    rows.append(item.__dict__)
                else:
                    # Try to convert to dict
                    try:
                        rows.append(dict(item))
                    except (TypeError, ValueError):
                        logger.warning(f"Could not convert row to dict: {item}")
                        continue

            return rows

        except Exception as e:
            logger.error(f"Failed to parse query results: {str(e)}")
            # Return empty list rather than failing completely
            return []

    async def list_files(self, directory: str = ".") -> List[str]:
        """
        List files in a directory via MCP Local Data Server.

        Note: This method requires the MCP server to support a list_files tool.

        Args:
            directory: Directory path to list (default: current directory)

        Returns:
            List of file paths

        Raises:
            RuntimeError: If MCP server call fails or tool is not available
        """
        try:
            logger.info(f"Listing files in directory: {directory}")

            # Call the list_files tool via MCP (if available)
            result = await self.mcp.call_tool(
                server_name=self.server_name,
                tool_name="list_files",
                arguments={"directory": directory},
            )

            # Extract file list from result
            files = self._extract_file_list(result)

            logger.info(f"Found {len(files)} files in {directory}")

            return files

        except Exception as e:
            error_msg = f"Failed to list files in '{directory}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _extract_file_list(self, mcp_result: Any) -> List[str]:
        """
        Extract file list from MCP tool result.

        Args:
            mcp_result: Raw result from MCP tool call

        Returns:
            List of file paths
        """
        try:
            # Handle different result formats
            if hasattr(mcp_result, "content"):
                files_data = mcp_result.content
            elif isinstance(mcp_result, dict):
                files_data = mcp_result.get("files", mcp_result.get("content", []))
            elif isinstance(mcp_result, list):
                files_data = mcp_result
            else:
                files_data = []

            # Convert to list of strings
            if isinstance(files_data, str):
                import json

                try:
                    files_data = json.loads(files_data)
                except json.JSONDecodeError:
                    # Split by newlines if it's a text list
                    files_data = [
                        f.strip() for f in files_data.split("\n") if f.strip()
                    ]

            # Ensure we have a list of strings
            if not isinstance(files_data, list):
                files_data = [str(files_data)]

            return [str(f) for f in files_data if f]

        except Exception as e:
            logger.error(f"Failed to extract file list: {str(e)}")
            return []

    async def health_check(self) -> bool:
        """
        Check if the MCP Local Data Server is available and responsive.

        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            # Check if server is connected
            if not self.mcp.is_connected(self.server_name):
                logger.warning(
                    f"Local data server '{self.server_name}' is not connected"
                )
                return False

            # Try to list tools to verify server is responsive
            tools = await self.mcp.list_tools(self.server_name)

            # Check if required tools are available
            tool_names = [tool["name"] for tool in tools]
            required_tools = ["read_file", "query_database"]

            missing_tools = [t for t in required_tools if t not in tool_names]
            if missing_tools:
                logger.warning(
                    f"Missing tools on server '{self.server_name}': {missing_tools}"
                )
                return False

            logger.info(f"Local data server '{self.server_name}' is healthy")
            return True

        except Exception as e:
            logger.error(
                f"Health check failed for local data server '{self.server_name}': {str(e)}"
            )
            return False

    def __repr__(self) -> str:
        return f"LocalDataAgent(server={self.server_name})"
