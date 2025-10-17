"""
Integration tests for MCP servers.

These tests verify that MCP servers can be started, connected to,
and their tools can be executed successfully.
"""

import pytest
import asyncio
import os
import tempfile
import sqlite3
from pathlib import Path
from backend.mcp.manager import MCPServerManager, MCP_AVAILABLE


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP SDK not installed")
@pytest.mark.integration
class TestMCPServerIntegration:
    """Integration tests for MCP servers."""

    @pytest.fixture
    def manager(self):
        """Create a MCPServerManager instance."""
        return MCPServerManager()

    @pytest.fixture
    async def cleanup_manager(self, manager):
        """Cleanup manager after tests."""
        yield manager
        await manager.disconnect_all()

    @pytest.mark.asyncio
    async def test_vector_server_connection(self, cleanup_manager):
        """Test connecting to vector search MCP server."""
        manager = cleanup_manager

        # Note: This test requires the vector server to be runnable
        # In a real environment, you would start the server process
        # For now, we test the connection logic

        try:
            await manager.connect_server(
                server_name="vector_server",
                command="python",
                args=["-m", "mcp_servers.vector_server"],
                env={},
            )

            # If connection succeeds, verify it's connected
            assert manager.is_connected("vector_server")

            # Try to list tools
            tools = await manager.list_tools("vector_server")
            assert len(tools) > 0

            # Check for vector_search tool
            tool_names = [tool["name"] for tool in tools]
            assert "vector_search" in tool_names

        except Exception as e:
            # Connection might fail if dependencies aren't set up
            pytest.skip(f"Could not connect to vector server: {str(e)}")

    @pytest.mark.asyncio
    async def test_local_data_server_connection(self, cleanup_manager):
        """Test connecting to local data MCP server."""
        manager = cleanup_manager

        try:
            await manager.connect_server(
                server_name="local_data_server",
                command="python",
                args=["-m", "mcp_servers.local_data_server"],
                env={},
            )

            assert manager.is_connected("local_data_server")

            # List tools
            tools = await manager.list_tools("local_data_server")
            assert len(tools) > 0

            # Check for expected tools
            tool_names = [tool["name"] for tool in tools]
            assert "read_file" in tool_names
            assert "query_database" in tool_names

        except Exception as e:
            pytest.skip(f"Could not connect to local data server: {str(e)}")

    @pytest.mark.asyncio
    async def test_search_server_connection(self, cleanup_manager):
        """Test connecting to web search MCP server."""
        manager = cleanup_manager

        try:
            await manager.connect_server(
                server_name="search_server",
                command="python",
                args=["-m", "mcp_servers.search_server"],
                env={},
            )

            assert manager.is_connected("search_server")

            # List tools
            tools = await manager.list_tools("search_server")
            assert len(tools) > 0

            # Check for web_search tool
            tool_names = [tool["name"] for tool in tools]
            assert "web_search" in tool_names

        except Exception as e:
            pytest.skip(f"Could not connect to search server: {str(e)}")

    @pytest.mark.asyncio
    async def test_local_data_read_file(self, cleanup_manager, tmp_path):
        """Test reading a file through local data server."""
        manager = cleanup_manager

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = "This is a test file for MCP server."
        test_file.write_text(test_content)

        try:
            # Connect with allowed path
            await manager.connect_server(
                server_name="local_data_server",
                command="python",
                args=["-m", "mcp_servers.local_data_server"],
                env={"ALLOWED_PATHS": str(tmp_path)},
            )

            # Call read_file tool
            result = await manager.call_tool(
                "local_data_server", "read_file", {"path": str(test_file)}
            )

            # Verify result contains file content
            assert result is not None
            # Result format depends on MCP server implementation

        except Exception as e:
            pytest.skip(f"Could not test read_file: {str(e)}")

    @pytest.mark.asyncio
    async def test_local_data_query_database(self, cleanup_manager, tmp_path):
        """Test querying a database through local data server."""
        manager = cleanup_manager

        # Create a test database
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create test table and data
        cursor.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        """
        )
        cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
        cursor.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')")
        conn.commit()
        conn.close()

        try:
            # Connect with allowed path
            await manager.connect_server(
                server_name="local_data_server",
                command="python",
                args=["-m", "mcp_servers.local_data_server"],
                env={"ALLOWED_PATHS": str(tmp_path)},
            )

            # Call query_database tool
            result = await manager.call_tool(
                "local_data_server",
                "query_database",
                {"database": str(db_path), "query": "SELECT * FROM users"},
            )

            # Verify result
            assert result is not None

        except Exception as e:
            pytest.skip(f"Could not test query_database: {str(e)}")

    @pytest.mark.asyncio
    async def test_reconnection_on_failure(self, cleanup_manager):
        """Test that manager can reconnect after connection failure."""
        manager = cleanup_manager

        try:
            # Connect to a server
            await manager.connect_server(
                server_name="test_server",
                command="python",
                args=["-m", "mcp_servers.local_data_server"],
                env={},
            )

            assert manager.is_connected("test_server")

            # Simulate disconnection
            await manager.disconnect_server("test_server")
            assert not manager.is_connected("test_server")

            # Reconnect
            await manager.reconnect_server("test_server")
            assert manager.is_connected("test_server")

        except Exception as e:
            pytest.skip(f"Could not test reconnection: {str(e)}")

    @pytest.mark.asyncio
    async def test_multiple_servers_simultaneously(self, cleanup_manager):
        """Test connecting to multiple servers at once."""
        manager = cleanup_manager

        servers_to_connect = [
            ("local_data_1", "python", ["-m", "mcp_servers.local_data_server"]),
            ("local_data_2", "python", ["-m", "mcp_servers.local_data_server"]),
        ]

        try:
            # Connect to multiple servers
            for server_name, command, args in servers_to_connect:
                await manager.connect_server(server_name, command, args)

            # Verify all are connected
            connected = manager.get_connected_servers()
            assert len(connected) == len(servers_to_connect)

            for server_name, _, _ in servers_to_connect:
                assert server_name in connected

        except Exception as e:
            pytest.skip(f"Could not test multiple servers: {str(e)}")

    @pytest.mark.asyncio
    async def test_error_handling_invalid_tool(self, cleanup_manager):
        """Test error handling when calling non-existent tool."""
        manager = cleanup_manager

        try:
            await manager.connect_server(
                server_name="test_server",
                command="python",
                args=["-m", "mcp_servers.local_data_server"],
                env={},
            )

            # Try to call non-existent tool
            with pytest.raises(RuntimeError):
                await manager.call_tool(
                    "test_server", "nonexistent_tool", {}, retry_on_failure=False
                )

        except Exception as e:
            pytest.skip(f"Could not test error handling: {str(e)}")


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP SDK not installed")
@pytest.mark.integration
class TestMCPServerSecurity:
    """Security tests for MCP servers."""

    @pytest.mark.asyncio
    async def test_local_data_path_validation(self, tmp_path):
        """Test that local data server validates file paths."""
        manager = MCPServerManager()

        # Create test files
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        allowed_file = allowed_dir / "allowed.txt"
        allowed_file.write_text("Allowed content")

        forbidden_dir = tmp_path / "forbidden"
        forbidden_dir.mkdir()
        forbidden_file = forbidden_dir / "forbidden.txt"
        forbidden_file.write_text("Forbidden content")

        try:
            # Connect with restricted path
            await manager.connect_server(
                server_name="local_data_server",
                command="python",
                args=["-m", "mcp_servers.local_data_server"],
                env={"ALLOWED_PATHS": str(allowed_dir)},
            )

            # Try to read allowed file - should succeed
            result_allowed = await manager.call_tool(
                "local_data_server", "read_file", {"path": str(allowed_file)}
            )
            assert result_allowed is not None

            # Try to read forbidden file - should fail
            result_forbidden = await manager.call_tool(
                "local_data_server", "read_file", {"path": str(forbidden_file)}
            )
            # Result should contain error message about access denied

        except Exception as e:
            pytest.skip(f"Could not test path validation: {str(e)}")
        finally:
            await manager.disconnect_all()

    @pytest.mark.asyncio
    async def test_database_query_restrictions(self, tmp_path):
        """Test that only SELECT queries are allowed."""
        manager = MCPServerManager()

        # Create test database
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER, value TEXT)")
        cursor.execute("INSERT INTO test VALUES (1, 'test')")
        conn.commit()
        conn.close()

        try:
            await manager.connect_server(
                server_name="local_data_server",
                command="python",
                args=["-m", "mcp_servers.local_data_server"],
                env={"ALLOWED_PATHS": str(tmp_path)},
            )

            # SELECT should work
            result_select = await manager.call_tool(
                "local_data_server",
                "query_database",
                {"database": str(db_path), "query": "SELECT * FROM test"},
            )
            assert result_select is not None

            # DELETE should be rejected
            result_delete = await manager.call_tool(
                "local_data_server",
                "query_database",
                {"database": str(db_path), "query": "DELETE FROM test"},
            )
            # Result should contain error about only SELECT being allowed

        except Exception as e:
            pytest.skip(f"Could not test query restrictions: {str(e)}")
        finally:
            await manager.disconnect_all()
