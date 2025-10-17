"""
Example usage of specialized agents with MCP servers.

This script demonstrates how to use VectorSearchAgent, LocalDataAgent,
and WebSearchAgent to perform various tasks.
"""

import asyncio
import logging
from backend.mcp.manager import MCPServerManager
from backend.agents import VectorSearchAgent, LocalDataAgent, WebSearchAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_vector_search():
    """Example: Using VectorSearchAgent for semantic search."""
    logger.info("=== Vector Search Example ===")

    # Initialize MCP manager
    mcp_manager = MCPServerManager()

    try:
        # Connect to vector server
        await mcp_manager.connect_server(
            server_name="vector_server",
            command="python",
            args=["mcp_servers/vector_server.py"],
        )

        # Create agent
        agent = VectorSearchAgent(mcp_manager, "vector_server")

        # Check health
        is_healthy = await agent.health_check()
        logger.info(f"Vector server health: {is_healthy}")

        if is_healthy:
            # Perform search
            results = await agent.search(query="machine learning algorithms", top_k=5)

            logger.info(f"Found {len(results)} results")
            for i, result in enumerate(results, 1):
                logger.info(
                    f"{i}. {result.document_name} (score: {result.score:.2f})\n"
                    f"   {result.text[:100]}..."
                )

    except Exception as e:
        logger.error(f"Vector search example failed: {e}")

    finally:
        await mcp_manager.disconnect_all()


async def example_local_data():
    """Example: Using LocalDataAgent for file and database access."""
    logger.info("=== Local Data Example ===")

    mcp_manager = MCPServerManager()

    try:
        # Connect to local data server
        await mcp_manager.connect_server(
            server_name="local_data_server",
            command="python",
            args=["mcp_servers/local_data_server.py"],
        )

        # Create agent
        agent = LocalDataAgent(mcp_manager, "local_data_server")

        # Check health
        is_healthy = await agent.health_check()
        logger.info(f"Local data server health: {is_healthy}")

        if is_healthy:
            # Read a file
            try:
                content = await agent.read_file("README.md")
                logger.info(f"File content (first 200 chars):\n{content[:200]}...")
            except Exception as e:
                logger.warning(f"Could not read file: {e}")

            # Query database (example - may not work without actual DB)
            try:
                rows = await agent.query_database(
                    "SELECT * FROM documents LIMIT 5", db_name="rag_db"
                )
                logger.info(f"Query returned {len(rows)} rows")
                for row in rows[:3]:
                    logger.info(f"  Row: {row}")
            except Exception as e:
                logger.warning(f"Could not query database: {e}")

    except Exception as e:
        logger.error(f"Local data example failed: {e}")

    finally:
        await mcp_manager.disconnect_all()


async def example_web_search():
    """Example: Using WebSearchAgent for web searches."""
    logger.info("=== Web Search Example ===")

    mcp_manager = MCPServerManager()

    try:
        # Connect to search server
        await mcp_manager.connect_server(
            server_name="search_server",
            command="python",
            args=["mcp_servers/search_server.py"],
        )

        # Create agent
        agent = WebSearchAgent(mcp_manager, "search_server")

        # Check health
        is_healthy = await agent.health_check()
        logger.info(f"Search server health: {is_healthy}")

        if is_healthy:
            # Perform web search
            results = await agent.search_web(
                query="latest developments in artificial intelligence", num_results=5
            )

            logger.info(f"Found {len(results)} web results")

            # Format and display results
            formatted = agent.format_results_as_text(results)
            logger.info(f"Search results:\n{formatted}")

            # Context-aware search
            results_with_context = await agent.search_with_context(
                query="transformer models",
                context="Looking for information about attention mechanisms in NLP",
                num_results=3,
            )

            logger.info(
                f"Context-aware search found {len(results_with_context)} results"
            )

    except Exception as e:
        logger.error(f"Web search example failed: {e}")

    finally:
        await mcp_manager.disconnect_all()


async def example_multi_agent():
    """Example: Using multiple agents together."""
    logger.info("=== Multi-Agent Example ===")

    mcp_manager = MCPServerManager()

    try:
        # Connect to all servers
        await mcp_manager.connect_server(
            "vector_server", "python", ["mcp_servers/vector_server.py"]
        )
        await mcp_manager.connect_server(
            "local_data_server", "python", ["mcp_servers/local_data_server.py"]
        )
        await mcp_manager.connect_server(
            "search_server", "python", ["mcp_servers/search_server.py"]
        )

        # Create all agents
        vector_agent = VectorSearchAgent(mcp_manager, "vector_server")
        local_agent = LocalDataAgent(mcp_manager, "local_data_server")
        web_agent = WebSearchAgent(mcp_manager, "search_server")

        # Check health of all agents
        vector_health = await vector_agent.health_check()
        local_health = await local_agent.health_check()
        web_health = await web_agent.health_check()

        logger.info(f"Agent health status:")
        logger.info(f"  Vector: {vector_health}")
        logger.info(f"  Local: {local_health}")
        logger.info(f"  Web: {web_health}")

        # Simulate a complex query that uses multiple agents
        query = "What are the latest trends in machine learning?"

        logger.info(f"\nProcessing query: '{query}'")

        # Step 1: Search local documents
        if vector_health:
            logger.info("Step 1: Searching local documents...")
            local_results = await vector_agent.search(query, top_k=3)
            logger.info(f"  Found {len(local_results)} local documents")

        # Step 2: Search the web for latest information
        if web_health:
            logger.info("Step 2: Searching the web...")
            web_results = await web_agent.search_web(query, num_results=3)
            logger.info(f"  Found {len(web_results)} web results")

        # Step 3: Read a specific file for context
        if local_health:
            logger.info("Step 3: Reading context file...")
            try:
                context = await local_agent.read_file("README.md")
                logger.info(f"  Read {len(context)} characters from context file")
            except Exception as e:
                logger.warning(f"  Could not read context: {e}")

        logger.info("\nMulti-agent query processing complete!")

    except Exception as e:
        logger.error(f"Multi-agent example failed: {e}")

    finally:
        await mcp_manager.disconnect_all()


async def main():
    """Run all examples."""
    logger.info("Starting agent usage examples...\n")

    # Run examples one by one
    await example_vector_search()
    print("\n" + "=" * 80 + "\n")

    await example_local_data()
    print("\n" + "=" * 80 + "\n")

    await example_web_search()
    print("\n" + "=" * 80 + "\n")

    await example_multi_agent()

    logger.info("\nAll examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
