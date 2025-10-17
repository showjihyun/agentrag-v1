"""
End-to-end tests for query processing with agents.
Tests Requirements: 4.1, 7.2
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.aggregator import AggregatorAgent
from backend.services.llm_manager import LLMManager
from backend.memory.manager import MemoryManager
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.local_data import LocalDataAgent
from backend.agents.web_search import WebSearchAgent


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.requires_ollama
async def test_simple_query_workflow(
    memory_manager, llm_manager, milvus_manager, embedding_service
):
    """
    Test simple query processing workflow.

    Requirements: 4.1, 7.2
    """
    # Set up test data
    from services.document_processor import DocumentProcessor

    processor = DocumentProcessor()
    content = (
        "Python is a high-level programming language. "
        "It is known for its simplicity and readability. "
        "Python is widely used in data science and machine learning."
    )

    chunks = processor.chunk_text(content)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    metadata_list = [
        {
            "document_id": "python_doc",
            "document_name": "python_intro.txt",
            "chunk_id": i,
            "text": chunk["text"],
        }
        for i, chunk in enumerate(chunks)
    ]

    await milvus_manager.insert_embeddings(embeddings, metadata_list)
    print("✓ Test data indexed")

    # Create mock MCP manager and agents
    mock_mcp = MagicMock()

    # Mock vector search to return our test data
    async def mock_vector_search(*args, **kwargs):
        query_embedding = embedding_service.embed_text(kwargs.get("query", ""))
        results = await milvus_manager.search(query_embedding, top_k=3)
        return {"results": results}

    mock_mcp.call_tool = AsyncMock(side_effect=mock_vector_search)

    vector_agent = VectorSearchAgent(mock_mcp)
    local_agent = LocalDataAgent(mock_mcp)
    web_agent = WebSearchAgent(mock_mcp)

    # Create aggregator agent
    aggregator = AggregatorAgent(
        llm_manager=llm_manager,
        memory_manager=memory_manager,
        vector_agent=vector_agent,
        local_agent=local_agent,
        web_agent=web_agent,
    )

    # Process query
    query = "What is Python used for?"
    session_id = "test_session_001"

    print(f"\n✓ Processing query: '{query}'")

    steps = []
    async for step in aggregator.process_query(query, session_id):
        steps.append(step)
        print(f"  Step: {step.type} - {step.content[:100]}...")

    # Verify workflow
    assert len(steps) > 0, "Should produce reasoning steps"

    # Check for key step types
    step_types = [step.type for step in steps]
    assert "memory" in step_types, "Should load memory context"
    assert "response" in step_types, "Should produce final response"

    print(f"✓ Query processed with {len(steps)} steps")
    print(f"  Step types: {set(step_types)}")

    # Verify memory was saved
    history = await memory_manager.stm.get_conversation_history(session_id)
    assert len(history) > 0, "Should save conversation to memory"
    print(f"✓ Conversation saved to memory ({len(history)} messages)")

    # Clean up
    await milvus_manager.delete_by_document_id("python_doc")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_turn_conversation(
    memory_manager, milvus_manager, embedding_service
):
    """
    Test multi-turn conversation with memory persistence.

    Requirements: 5.1, 7.2
    """
    session_id = "test_session_002"

    # Set up test data
    from services.document_processor import DocumentProcessor

    processor = DocumentProcessor()
    content = (
        "Machine learning is a method of data analysis. "
        "It automates analytical model building. "
        "Supervised learning uses labeled data. "
        "Unsupervised learning finds hidden patterns."
    )

    chunks = processor.chunk_text(content)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    metadata_list = [
        {
            "document_id": "ml_doc",
            "document_name": "ml_basics.txt",
            "chunk_id": i,
            "text": chunk["text"],
        }
        for i, chunk in enumerate(chunks)
    ]

    await milvus_manager.insert_embeddings(embeddings, metadata_list)

    # Simulate multi-turn conversation
    turns = [
        {"role": "user", "content": "What is machine learning?"},
        {
            "role": "assistant",
            "content": "Machine learning is a method of data analysis that automates analytical model building.",
        },
        {"role": "user", "content": "What are the types?"},
        {
            "role": "assistant",
            "content": "There are supervised learning which uses labeled data, and unsupervised learning which finds hidden patterns.",
        },
    ]

    # Add messages to STM
    for turn in turns:
        await memory_manager.stm.add_message(
            session_id=session_id, role=turn["role"], content=turn["content"]
        )

    print(f"✓ Added {len(turns)} messages to conversation")

    # Retrieve conversation history
    history = await memory_manager.stm.get_conversation_history(session_id, limit=10)
    assert len(history) == len(turns), "Should retrieve all messages"
    print(f"✓ Retrieved {len(history)} messages from history")

    # Get context for new query
    context = await memory_manager.get_context_for_query(
        session_id=session_id, query="Tell me more about supervised learning"
    )

    assert "recent_history" in context, "Should include recent history"
    assert len(context["recent_history"]) > 0, "Should have conversation history"
    print(f"✓ Context includes {len(context['recent_history'])} recent messages")

    # Test memory consolidation
    await memory_manager.consolidate_memory(
        session_id=session_id,
        query="What is machine learning?",
        response="Machine learning is a method of data analysis.",
        success=True,
    )
    print("✓ Memory consolidated to LTM")

    # Clean up
    await memory_manager.stm.clear_session(session_id)
    await milvus_manager.delete_by_document_id("ml_doc")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_memory_persistence_across_sessions(memory_manager, embedding_service):
    """
    Test that LTM persists across different sessions.

    Requirements: 5.1
    """
    # Store interaction in LTM
    interaction_data = {
        "query": "What is deep learning?",
        "response": "Deep learning is a subset of machine learning using neural networks.",
        "success": True,
        "metadata": {"topic": "AI"},
    }

    await memory_manager.ltm.store_interaction(
        query=interaction_data["query"],
        response=interaction_data["response"],
        context={"documents": []},
        success=interaction_data["success"],
    )
    print("✓ Interaction stored in LTM")

    # Retrieve similar interactions from different session
    similar = await memory_manager.ltm.retrieve_similar_interactions(
        query="Tell me about neural networks", top_k=3
    )

    assert len(similar) > 0, "Should retrieve similar past interactions"
    print(f"✓ Retrieved {len(similar)} similar interactions from LTM")

    # Verify the interaction is relevant
    if similar:
        print(f"  Top match: {similar[0].get('query', '')[:50]}...")
        print(f"  Score: {similar[0].get('score', 0):.3f}")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.slow
async def test_complex_multi_step_query(
    memory_manager, milvus_manager, embedding_service
):
    """
    Test complex query requiring multiple reasoning steps.

    Requirements: 4.1
    """
    # Set up diverse test data
    from services.document_processor import DocumentProcessor

    processor = DocumentProcessor()

    documents = [
        {
            "id": "history_doc",
            "content": "The internet was invented in the 1960s. ARPANET was the first network. Tim Berners-Lee created the World Wide Web in 1989.",
        },
        {
            "id": "tech_doc",
            "content": "Modern web technologies include HTML, CSS, and JavaScript. React and Vue are popular frameworks. APIs enable communication between services.",
        },
    ]

    # Index documents
    for doc in documents:
        chunks = processor.chunk_text(doc["content"])
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.embed_batch(texts)

        metadata_list = [
            {
                "document_id": doc["id"],
                "document_name": f"{doc['id']}.txt",
                "chunk_id": i,
                "text": chunk["text"],
            }
            for i, chunk in enumerate(chunks)
        ]

        await milvus_manager.insert_embeddings(embeddings, metadata_list)

    print("✓ Multiple documents indexed")

    # Test retrieval from multiple documents
    queries = ["When was the internet invented?", "What are modern web technologies?"]

    for query in queries:
        query_embedding = embedding_service.embed_text(query)
        results = await milvus_manager.search(query_embedding, top_k=3)

        assert len(results) > 0, f"Should find results for: {query}"
        print(f"✓ Query: '{query}' - Found {len(results)} results")

    # Clean up
    for doc in documents:
        await milvus_manager.delete_by_document_id(doc["id"])


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_streaming_response(
    memory_manager, llm_manager, milvus_manager, embedding_service
):
    """
    Test streaming response generation.

    Requirements: 7.2
    """
    # Set up test data
    from services.document_processor import DocumentProcessor

    processor = DocumentProcessor()
    content = "Streaming allows real-time updates. It improves user experience. Data is sent incrementally."

    chunks = processor.chunk_text(content)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    metadata_list = [
        {
            "document_id": "stream_doc",
            "document_name": "streaming.txt",
            "chunk_id": i,
            "text": chunk["text"],
        }
        for i, chunk in enumerate(chunks)
    ]

    await milvus_manager.insert_embeddings(embeddings, metadata_list)

    # Create mock agents
    mock_mcp = MagicMock()

    async def mock_vector_search(*args, **kwargs):
        query_embedding = embedding_service.embed_text(kwargs.get("query", ""))
        results = await milvus_manager.search(query_embedding, top_k=3)
        return {"results": results}

    mock_mcp.call_tool = AsyncMock(side_effect=mock_vector_search)

    vector_agent = VectorSearchAgent(mock_mcp)
    local_agent = LocalDataAgent(mock_mcp)
    web_agent = WebSearchAgent(mock_mcp)

    aggregator = AggregatorAgent(
        llm_manager=llm_manager,
        memory_manager=memory_manager,
        vector_agent=vector_agent,
        local_agent=local_agent,
        web_agent=web_agent,
    )

    # Test streaming
    query = "What is streaming?"
    session_id = "test_stream_session"

    step_count = 0
    step_types = set()

    async for step in aggregator.process_query(query, session_id):
        step_count += 1
        step_types.add(step.type)
        # Verify each step has required fields
        assert hasattr(step, "type"), "Step should have type"
        assert hasattr(step, "content"), "Step should have content"
        assert hasattr(step, "metadata"), "Step should have metadata"

    assert step_count > 0, "Should stream multiple steps"
    print(f"✓ Streamed {step_count} steps")
    print(f"  Step types: {step_types}")

    # Clean up
    await milvus_manager.delete_by_document_id("stream_doc")
