"""
Unit tests for MCPServerManager.

Tests the MCP server manager's connection management, tool discovery,
and tool execution capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backend.mcp.manager import MCPServerManager, MCP_AVAILABLE


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP SDK not installed")
class TestMCPServerManager:
    """Test suite for MCPServerManager."""

    @pytest.fixture
    def manager(self):
        """Create a MCPServerManager instance."""
        return MCPServerManager()

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager is not None
        assert isinstance(manager.servers, dict)
        assert isinstance(manager.sessions, dict)
        assert len(manager.get_connected_servers()) == 0

    @pytest.mark.asyncio
    async def test_connect_server_validation(self, manager):
        """Test server connection parameter validation."""
        # Test empty server name
        with pytest.raises(ValueError, match="server_name cannot be empty"):
            await manager.connect_server("", "python", ["-m", "test"])

        # Test empty command
        with pytest.raises(ValueError, match="command cannot be empty"):
            await manager.connect_server("test_server", "", [])

    @pytest.mark.asyncio
    @patch("backend.mcp.manager.stdio_client")
    @patch("backend.mcp.manager.ClientSession")
    async def test_connect_server_success(
        self, mock_session_class, mock_stdio_client, manager
    ):
        """Test successful server connection."""
        # Mock stdio_client to return read/write streams
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_stdio_client.return_value = (mock_read, mock_write)

        # Mock ClientSession
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session_class.return_value = mock_session

        # Connect to server
        await manager.connect_server(
            server_name="test_server",
            command="python",
            args=["-m", "test_module"],
            env={"TEST_VAR": "value"},
        )

        # Verify connection
        assert manager.is_connected("test_server")
        assert "test_server" in manager.get_connected_servers()
        assert mock_session.initialize.called

    @pytest.mark.asyncio
    async def test_disconnect_server(self, manager):
        """Test server disconnection."""
        # Manually add a mock server
        manager._connected_servers.add("test_server")
        manager.sessions["test_server"] = Mock()
        manager.servers["test_server"] = Mock()

        # Disconnect
        await manager.disconnect_server("test_server")

        # Verify disconnection
        assert not manager.is_connected("test_server")
        assert "test_server" not in manager.get_connected_servers()

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_server(self, manager):
        """Test disconnecting from a server that isn't connected."""
        # Should not raise an error
        await manager.disconnect_server("nonexistent_server")

    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self, manager):
        """Test calling a tool on a disconnected server."""
        with pytest.raises(ValueError, match="not connected"):
            await manager.call_tool("nonexistent_server", "test_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_empty_name(self, manager):
        """Test calling a tool with empty name."""
        # Add a mock connected server
        manager._connected_servers.add("test_server")
        manager.sessions["test_server"] = AsyncMock()

        with pytest.raises(ValueError, match="tool_name cannot be empty"):
            await manager.call_tool("test_server", "", {})

    @pytest.mark.asyncio
    @patch("backend.mcp.manager.stdio_client")
    @patch("backend.mcp.manager.ClientSession")
    async def test_call_tool_success(
        self, mock_session_class, mock_stdio_client, manager
    ):
        """Test successful tool call."""
        # Setup mocks
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_stdio_client.return_value = (mock_read, mock_write)

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value={"result": "success"})
        mock_session_class.return_value = mock_session

        # Connect server
        await manager.connect_server("test_server", "python", ["-m", "test"])

        # Call tool
        result = await manager.call_tool(
            "test_server", "test_tool", {"arg1": "value1"}, retry_on_failure=False
        )

        # Verify
        assert result == {"result": "success"}
        mock_session.call_tool.assert_called_once_with("test_tool", {"arg1": "value1"})

    @pytest.mark.asyncio
    @patch("backend.mcp.manager.stdio_client")
    @patch("backend.mcp.manager.ClientSession")
    async def test_list_tools(self, mock_session_class, mock_stdio_client, manager):
        """Test listing tools from a server."""
        # Setup mocks
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_stdio_client.return_value = (mock_read, mock_write)

        # Mock tool response
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool.inputSchema = {"type": "object"}

        mock_tools_response = Mock()
        mock_tools_response.tools = [mock_tool]

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_tools_response)
        mock_session_class.return_value = mock_session

        # Connect server
        await manager.connect_server("test_server", "python", ["-m", "test"])

        # List tools
        tools = await manager.list_tools("test_server")

        # Verify
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert tools[0]["description"] == "A test tool"
        assert tools[0]["input_schema"] == {"type": "object"}

    @pytest.mark.asyncio
    async def test_list_tools_not_connected(self, manager):
        """Test listing tools from a disconnected server."""
        with pytest.raises(ValueError, match="not connected"):
            await manager.list_tools("nonexistent_server")

    def test_get_connected_servers(self, manager):
        """Test getting list of connected servers."""
        # Add mock servers
        manager._connected_servers.add("server1")
        manager._connected_servers.add("server2")

        servers = manager.get_connected_servers()

        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers

    def test_get_server_info(self, manager):
        """Test getting server information."""
        # Add mock server
        mock_params = Mock()
        mock_params.command = "python"
        mock_params.args = ["-m", "test"]
        mock_params.env = {"VAR": "value"}

        manager.servers["test_server"] = mock_params
        manager._connected_servers.add("test_server")

        info = manager.get_server_info("test_server")

        assert info is not None
        assert info["name"] == "test_server"
        assert info["command"] == "python"
        assert info["args"] == ["-m", "test"]
        assert info["connected"] is True
        assert "VAR" in info["env_vars"]

    def test_get_server_info_nonexistent(self, manager):
        """Test getting info for nonexistent server."""
        info = manager.get_server_info("nonexistent")
        assert info is None

    @pytest.mark.asyncio
    async def test_disconnect_all(self, manager):
        """Test disconnecting all servers."""
        # Add mock servers
        manager._connected_servers.add("server1")
        manager._connected_servers.add("server2")
        manager.sessions["server1"] = Mock()
        manager.sessions["server2"] = Mock()
        manager.servers["server1"] = Mock()
        manager.servers["server2"] = Mock()

        # Disconnect all
        await manager.disconnect_all()

        # Verify
        assert len(manager.get_connected_servers()) == 0

    @pytest.mark.asyncio
    @patch("backend.mcp.manager.stdio_client")
    @patch("backend.mcp.manager.ClientSession")
    async def test_server_connection_context_manager(
        self, mock_session_class, mock_stdio_client, manager
    ):
        """Test server connection context manager."""
        # Setup mocks
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_stdio_client.return_value = (mock_read, mock_write)

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session_class.return_value = mock_session

        # Use context manager
        async with manager.server_connection("temp_server", "python", ["-m", "test"]):
            assert manager.is_connected("temp_server")

        # Verify disconnection after context
        assert not manager.is_connected("temp_server")

    def test_repr(self, manager):
        """Test string representation."""
        manager._connected_servers.add("server1")
        repr_str = repr(manager)

        assert "MCPServerManager" in repr_str
        assert "connected_servers=1" in repr_str
        assert "server1" in repr_str


@pytest.mark.skipif(MCP_AVAILABLE, reason="Testing behavior when MCP is not available")
def test_mcp_not_available():
    """Test that appropriate error is raised when MCP is not available."""
    with pytest.raises(RuntimeError, match="MCP SDK is not installed"):
        MCPServerManager()
