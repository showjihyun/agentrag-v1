"""
MCP Server Manager for managing connections to MCP servers and executing tools.

This manager handles stdio-based communication with MCP servers, tool discovery,
and tool execution with error handling and reconnection logic.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning(
        "MCP SDK not available. Install with: pip install mcp\n"
        "MCP server functionality will be disabled."
    )

logger = logging.getLogger(__name__)


class MCPServerManager:
    """
    Manager for MCP (Model Context Protocol) server connections.

    Features:
    - Connect to multiple MCP servers via stdio transport
    - Tool discovery and listing
    - Tool execution with error handling
    - Connection management and reconnection logic
    - Session lifecycle management
    """

    def __init__(self):
        """Initialize the MCP Server Manager."""
        if not MCP_AVAILABLE:
            logger.warning(
                "MCP SDK is not installed. MCP functionality will be disabled. "
                "Install with: pip install mcp"
            )
            self.servers: Dict[str, StdioServerParameters] = {}
            self.sessions: Dict[str, ClientSession] = {}
            self.read_streams: Dict[str, Any] = {}
            self.write_streams: Dict[str, Any] = {}
            return

        self.servers: Dict[str, StdioServerParameters] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.read_streams: Dict[str, Any] = {}
        self.write_streams: Dict[str, Any] = {}
        self._connected_servers: set = set()

        logger.info("MCPServerManager initialized")

    async def connect_server(
        self,
        server_name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Connect to an MCP server using stdio transport.

        Args:
            server_name: Unique identifier for the server
            command: Command to execute (e.g., "uvx", "python")
            args: Command arguments (e.g., ["mcp-server-package"])
            env: Optional environment variables for the server process

        Raises:
            ValueError: If server_name is already connected
            RuntimeError: If connection fails
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP SDK not available, skipping server connection")
            return
            
        if not server_name:
            raise ValueError("server_name cannot be empty")
        if not command:
            raise ValueError("command cannot be empty")

        if server_name in self._connected_servers:
            logger.warning(f"Server '{server_name}' is already connected")
            return

        try:
            logger.info(
                f"Connecting to MCP server '{server_name}' "
                f"with command: {command} {' '.join(args)}"
            )

            # Create server parameters
            server_params = StdioServerParameters(
                command=command, args=args, env=env or {}
            )

            # Establish stdio connection
            read_stream, write_stream = await stdio_client(server_params)

            # Create client session
            session = ClientSession(read_stream, write_stream)

            # Initialize the session
            await session.initialize()

            # Store connection details
            self.servers[server_name] = server_params
            self.sessions[server_name] = session
            self.read_streams[server_name] = read_stream
            self.write_streams[server_name] = write_stream
            self._connected_servers.add(server_name)

            logger.info(f"Successfully connected to MCP server: {server_name}")

        except Exception as e:
            error_msg = f"Failed to connect to MCP server '{server_name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def disconnect_server(self, server_name: str) -> None:
        """
        Disconnect from an MCP server.

        Args:
            server_name: Name of the server to disconnect
        """
        if server_name not in self._connected_servers:
            logger.warning(f"Server '{server_name}' is not connected")
            return

        try:
            logger.info(f"Disconnecting from MCP server: {server_name}")

            # Close the session
            if server_name in self.sessions:
                session = self.sessions[server_name]
                # MCP sessions don't have explicit close, cleanup happens on context exit
                del self.sessions[server_name]

            # Clean up streams
            if server_name in self.read_streams:
                del self.read_streams[server_name]
            if server_name in self.write_streams:
                del self.write_streams[server_name]

            # Remove from tracking
            self._connected_servers.discard(server_name)

            if server_name in self.servers:
                del self.servers[server_name]

            logger.info(f"Disconnected from MCP server: {server_name}")

        except Exception as e:
            logger.error(f"Error disconnecting from server '{server_name}': {str(e)}")

    async def reconnect_server(self, server_name: str) -> None:
        """
        Reconnect to an MCP server.

        Args:
            server_name: Name of the server to reconnect

        Raises:
            ValueError: If server was never connected
            RuntimeError: If reconnection fails
        """
        if server_name not in self.servers:
            raise ValueError(
                f"Server '{server_name}' was never connected. "
                "Use connect_server() instead."
            )

        logger.info(f"Reconnecting to MCP server: {server_name}")

        # Get original connection parameters
        server_params = self.servers[server_name]

        # Disconnect if currently connected
        if server_name in self._connected_servers:
            await self.disconnect_server(server_name)

        # Reconnect with original parameters
        await self.connect_server(
            server_name=server_name,
            command=server_params.command,
            args=server_params.args,
            env=server_params.env,
        )

    def is_connected(self, server_name: str) -> bool:
        """
        Check if a server is connected.

        Args:
            server_name: Name of the server to check

        Returns:
            bool: True if connected, False otherwise
        """
        return server_name in self._connected_servers

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        retry_on_failure: bool = True,
    ) -> Any:
        """
        Call a tool on an MCP server.

        Args:
            server_name: Name of the server hosting the tool
            tool_name: Name of the tool to call
            arguments: Tool arguments as a dictionary
            retry_on_failure: Whether to retry with reconnection on failure

        Returns:
            Tool execution result

        Raises:
            ValueError: If server is not connected or tool doesn't exist
            RuntimeError: If tool execution fails
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP SDK not available, cannot call tool")
            return {"error": "MCP SDK not installed"}
            
        if server_name not in self._connected_servers:
            raise ValueError(
                f"Server '{server_name}' is not connected. "
                "Call connect_server() first."
            )

        if not tool_name:
            raise ValueError("tool_name cannot be empty")

        session = self.sessions[server_name]
        arguments = arguments or {}

        try:
            logger.info(
                f"Calling tool '{tool_name}' on server '{server_name}' "
                f"with arguments: {arguments}"
            )

            # Call the tool
            result = await session.call_tool(tool_name, arguments)

            logger.info(f"Tool '{tool_name}' executed successfully")
            logger.debug(f"Tool result: {result}")

            return result

        except Exception as e:
            error_msg = (
                f"Failed to call tool '{tool_name}' on server '{server_name}': {str(e)}"
            )
            logger.error(error_msg)

            # Attempt reconnection and retry if enabled
            if retry_on_failure:
                try:
                    logger.info(f"Attempting to reconnect and retry tool call...")
                    await self.reconnect_server(server_name)

                    # Retry the tool call (without retry to avoid infinite loop)
                    return await self.call_tool(
                        server_name=server_name,
                        tool_name=tool_name,
                        arguments=arguments,
                        retry_on_failure=False,
                    )

                except Exception as retry_error:
                    logger.error(f"Retry after reconnection failed: {str(retry_error)}")
                    raise RuntimeError(error_msg) from e

            raise RuntimeError(error_msg) from e

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """
        List all available tools on an MCP server.

        Args:
            server_name: Name of the server to query

        Returns:
            List of tool definitions with name, description, and schema

        Raises:
            ValueError: If server is not connected
            RuntimeError: If listing fails
        """
        if server_name not in self._connected_servers:
            raise ValueError(
                f"Server '{server_name}' is not connected. "
                "Call connect_server() first."
            )

        try:
            logger.info(f"Listing tools for server: {server_name}")

            session = self.sessions[server_name]
            tools_response = await session.list_tools()

            # Extract tool information
            tools = []
            for tool in tools_response.tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                tools.append(tool_info)

            logger.info(f"Found {len(tools)} tools on server '{server_name}'")

            return tools

        except Exception as e:
            error_msg = f"Failed to list tools for server '{server_name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def get_connected_servers(self) -> List[str]:
        """
        Get list of currently connected server names.

        Returns:
            List of connected server names
        """
        return list(self._connected_servers)

    def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Dictionary with server information or None if not found
        """
        if server_name not in self.servers:
            return None

        server_params = self.servers[server_name]

        return {
            "name": server_name,
            "command": server_params.command,
            "args": server_params.args,
            "connected": server_name in self._connected_servers,
            "env_vars": list(server_params.env.keys()) if server_params.env else [],
        }

    async def disconnect_all(self) -> None:
        """Disconnect from all connected servers."""
        logger.info("Disconnecting from all MCP servers")

        server_names = list(self._connected_servers)
        for server_name in server_names:
            await self.disconnect_server(server_name)

        logger.info("All MCP servers disconnected")

    @asynccontextmanager
    async def server_connection(
        self,
        server_name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
    ):
        """
        Context manager for temporary server connection.

        Usage:
            async with manager.server_connection("my_server", "uvx", ["package"]) as session:
                result = await manager.call_tool("my_server", "tool_name", {})

        Args:
            server_name: Unique identifier for the server
            command: Command to execute
            args: Command arguments
            env: Optional environment variables

        Yields:
            ClientSession: The connected session
        """
        await self.connect_server(server_name, command, args, env)
        try:
            yield self.sessions[server_name]
        finally:
            await self.disconnect_server(server_name)

    def __repr__(self) -> str:
        return (
            f"MCPServerManager(connected_servers={len(self._connected_servers)}, "
            f"servers={list(self._connected_servers)})"
        )
