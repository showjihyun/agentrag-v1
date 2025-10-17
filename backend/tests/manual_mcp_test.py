"""
Manual test script for MCP server infrastructure.

This script demonstrates how to use the MCPServerManager and MCP servers.
Run this after installing the MCP SDK to verify the implementation.

Usage:
    python backend/tests/manual_mcp_test.py
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

try:
    from backend.mcp.manager import MCPServerManager, MCP_AVAILABLE
except ImportError as e:
    print(f"Error importing MCPServerManager: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


async def test_mcp_manager():
    """Test MCPServerManager basic functionality."""
    print("=" * 60)
    print("Testing MCP Server Infrastructure")
    print("=" * 60)

    if not MCP_AVAILABLE:
        print("\n❌ MCP SDK is not installed!")
        print("Install with: pip install mcp")
        return False

    print("\n✅ MCP SDK is available")

    # Create manager
    print("\n1. Creating MCPServerManager...")
    manager = MCPServerManager()
    print(f"   Manager created: {manager}")

    # Test connection to local data server
    print("\n2. Testing Local Data Server connection...")
    try:
        await manager.connect_server(
            server_name="local_data_test",
            command="python",
            args=["-m", "mcp_servers.local_data_server"],
            env={"ALLOWED_PATHS": os.getcwd()},
        )
        print("   ✅ Connected to local data server")

        # List tools
        print("\n3. Listing available tools...")
        tools = await manager.list_tools("local_data_test")
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")

        # Test read_file tool
        print("\n4. Testing read_file tool...")
        test_file = "README.md"
        if os.path.exists(test_file):
            result = await manager.call_tool(
                "local_data_test", "read_file", {"path": test_file}
            )
            print(f"   ✅ Successfully read {test_file}")
            print(f"   Result type: {type(result)}")
        else:
            print(f"   ⚠️  Test file {test_file} not found, skipping")

        # Disconnect
        print("\n5. Disconnecting from server...")
        await manager.disconnect_server("local_data_test")
        print("   ✅ Disconnected")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        print(f"   This is expected if MCP servers aren't fully set up yet")
        return False

    print("\n" + "=" * 60)
    print("✅ MCP Infrastructure Test Complete!")
    print("=" * 60)
    return True


async def test_vector_server():
    """Test Vector Search Server (requires Milvus)."""
    print("\n" + "=" * 60)
    print("Testing Vector Search Server")
    print("=" * 60)

    if not MCP_AVAILABLE:
        print("   ⚠️  Skipped: MCP SDK not installed")
        return False

    manager = MCPServerManager()

    try:
        print("\n1. Connecting to vector search server...")
        await manager.connect_server(
            server_name="vector_test",
            command="python",
            args=["-m", "mcp_servers.vector_server"],
        )
        print("   ✅ Connected")

        print("\n2. Listing tools...")
        tools = await manager.list_tools("vector_test")
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}")

        print("\n3. Testing vector_search tool...")
        result = await manager.call_tool(
            "vector_test", "vector_search", {"query": "test query", "top_k": 3}
        )
        print("   ✅ Vector search executed")

        await manager.disconnect_server("vector_test")
        print("\n✅ Vector server test complete")
        return True

    except Exception as e:
        print(f"   ⚠️  Vector server test skipped: {str(e)}")
        print("   (This is expected if Milvus is not running)")
        return False


async def test_search_server():
    """Test Web Search Server."""
    print("\n" + "=" * 60)
    print("Testing Web Search Server")
    print("=" * 60)

    if not MCP_AVAILABLE:
        print("   ⚠️  Skipped: MCP SDK not installed")
        return False

    manager = MCPServerManager()

    try:
        print("\n1. Connecting to search server...")
        await manager.connect_server(
            server_name="search_test",
            command="python",
            args=["-m", "mcp_servers.search_server"],
        )
        print("   ✅ Connected")

        print("\n2. Listing tools...")
        tools = await manager.list_tools("search_test")
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}")

        print("\n3. Testing web_search tool...")
        result = await manager.call_tool(
            "search_test",
            "web_search",
            {"query": "Python programming", "num_results": 3},
        )
        print("   ✅ Web search executed")

        await manager.disconnect_server("search_test")
        print("\n✅ Search server test complete")
        return True

    except Exception as e:
        print(f"   ⚠️  Search server test skipped: {str(e)}")
        print("   (This is expected if duckduckgo-search is not installed)")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MCP Server Infrastructure Manual Test")
    print("=" * 60)
    print("\nThis script tests the MCP server implementation.")
    print("Some tests may be skipped if dependencies aren't installed.\n")

    results = []

    # Test basic manager
    results.append(("MCPServerManager", await test_mcp_manager()))

    # Test vector server (may fail if Milvus not running)
    results.append(("Vector Server", await test_vector_server()))

    # Test search server (may fail if duckduckgo-search not installed)
    results.append(("Search Server", await test_search_server()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASSED" if passed else "⚠️  SKIPPED/FAILED"
        print(f"{name}: {status}")

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Install MCP SDK: pip install mcp")
    print("2. Install search: pip install duckduckgo-search")
    print("3. Start Milvus: docker-compose up -d milvus")
    print("4. Run pytest tests: pytest backend/tests/unit/test_mcp_manager.py -v")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
