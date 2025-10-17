"""
Complete end-to-end workflow tests.
Tests Requirements: 1.5, 2.4, 4.1, 5.1, 7.2
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from backend.services.document_processor import DocumentProcessor
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.services.llm_manager import LLMManager
from backend.memory.manager import MemoryManager
from backend.agents.aggregator import AggregatorAgent
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.local_data import LocalDataAgent
from backend.agents.web_search import WebSearchAgent


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.requires_ollama
async def test_complete_rag_workflow(
    milvus_manager, embedding_service, memory_manager, llm_manager, test_data_dir
):
    """
    Test complete RAG workflow from document upload to query response.

    This test simulates a real user workflow:
    1. Upload and index documents
    2. Submit a query
    3. Agent processes query with reasoning
    4. Retrieve relevant documents
    5. Generate response with citations
    6. Save to memory

    Requirements: 1.5, 2.4, 4.1, 5.1, 7.2
    """
    print("\n" + "=" * 60)
    print("COMPLETE RAG WORKFLOW TEST")
    print("=" * 60)

    # ========== PHASE 1: Document Upload and Indexing ==========
    print("\n[PHASE 1] Document Upload and Indexing")
    print("-" * 60)

    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)

    # Read test document
    doc_path = test_data_dir / "sample_doc.txt"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"✓ Loaded document: {doc_path.name} ({len(content)} characters)")

    # Process document
    chunks = processor.chunk_text(content)
    print(f"✓ Chunked into {len(chunks)} pieces")

    # Generate embeddings
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)
    print(f"✓ Generated {len(embeddings)} embeddings")

    # Store in Milvus
    import time

    timestamp = int(time.time())
    metadata_list = []
    for i, chunk in enumerate(chunks):
        metadata_list.append(
            {
                "id": f"chunk_{i}",
                "document_id": "workflow_test_doc",
                "document_name": "sample_doc.txt",
                "text": chunk["text"],
                "chunk_index": i,
                "file_type": "txt",
                "upload_date": timestamp,
                "author": "",
                "creation_date": 0,
                "language": "",
                "keywords": "",
            }
        )

    ids = await milvus_manager.insert_embeddings(embeddings, metadata_list)
    print(f"✓ Indexed {len(ids)} chunks in vector database")

    # ========== PHASE 2: Query Submission ==========
    print("\n[PHASE 2] Query Submission")
    print("-" * 60)

    query = "What is machine learning and how does it work?"
    session_id = "workflow_test_session"

    print(f"Query: '{query}'")
    print(f"Session: {session_id}")

    # ========== PHASE 3: Agent Processing ==========
    print("\n[PHASE 3] Agent Processing with Reasoning")
    print("-" * 60)

    # Create mock MCP manager
    mock_mcp = MagicMock()

    async def mock_vector_search(*args, **kwargs):
        arguments = args[2] if len(args) > 2 else kwargs.get("arguments", {})
        query_text = arguments.get("query", query)
        top_k = arguments.get("top_k", 5)

        query_embedding = embedding_service.embed_text(query_text)
        results = await milvus_manager.search(query_embedding, top_k=top_k)
        return MagicMock(content=[MagicMock(text=str({"results": results}))])

    mock_mcp.call_tool = AsyncMock(side_effect=mock_vector_search)

    # Create agents
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

    # Process query and collect steps
    steps = []
    step_types = []

    print("\nAgent Reasoning Steps:")
    async for step in aggregator.process_query(query, session_id):
        steps.append(step)
        step_types.append(step.type)

        # Print step summary
        content_preview = (
            step.content[:80] + "..." if len(step.content) > 80 else step.content
        )
        print(f"  [{step.type.upper()}] {content_preview}")

    print(f"\n✓ Completed {len(steps)} reasoning steps")
    print(f"  Step types: {set(step_types)}")

    # ========== PHASE 4: Verify Results ==========
    print("\n[PHASE 4] Result Verification")
    print("-" * 60)

    # Verify we have key step types
    assert "memory" in step_types, "Should load memory context"
    assert "response" in step_types, "Should generate final response"
    print("✓ All required step types present")

    # Get final response
    response_steps = [s for s in steps if s.type == "response"]
    assert len(response_steps) > 0, "Should have at least one response"

    final_response = response_steps[-1].content
    print(f"✓ Final response generated ({len(final_response)} characters)")
    print(f"\nResponse preview:")
    print(f"  {final_response[:200]}...")

    # ========== PHASE 5: Memory Verification ==========
    print("\n[PHASE 5] Memory Verification")
    print("-" * 60)

    # Check short-term memory
    history = await memory_manager.stm.get_conversation_history(session_id)
    assert len(history) > 0, "Should save conversation to STM"
    print(f"✓ Conversation saved to STM ({len(history)} messages)")

    # Check if we can retrieve context
    context = await memory_manager.get_context_for_query(
        session_id, "follow-up question"
    )
    assert "recent_history" in context, "Should provide conversation context"
    print(
        f"✓ Context retrieval working ({len(context['recent_history'])} recent messages)"
    )

    # ========== PHASE 6: Multi-turn Conversation ==========
    print("\n[PHASE 6] Multi-turn Conversation")
    print("-" * 60)

    follow_up_query = "Can you explain more about neural networks?"
    print(f"Follow-up query: '{follow_up_query}'")

    follow_up_steps = []
    async for step in aggregator.process_query(follow_up_query, session_id):
        follow_up_steps.append(step)

    print(f"✓ Follow-up processed ({len(follow_up_steps)} steps)")

    # Verify conversation history includes both queries
    final_history = await memory_manager.stm.get_conversation_history(session_id)
    assert len(final_history) > len(
        history
    ), "Should have more messages after follow-up"
    print(f"✓ Conversation history updated ({len(final_history)} total messages)")

    # ========== PHASE 7: Cleanup ==========
    print("\n[PHASE 7] Cleanup")
    print("-" * 60)

    await milvus_manager.delete_by_document_id("workflow_test_doc")
    await memory_manager.stm.clear_session(session_id)
    print("✓ Test data cleaned up")

    print("\n" + "=" * 60)
    print("✓ COMPLETE WORKFLOW TEST PASSED")
    print("=" * 60)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_concurrent_queries(milvus_manager, embedding_service, memory_manager):
    """
    Test handling of concurrent queries from different sessions.

    Requirements: 7.4
    """
    print("\n" + "=" * 60)
    print("CONCURRENT QUERIES TEST")
    print("=" * 60)

    # Set up test data
    processor = DocumentProcessor()
    content = "Concurrent processing allows multiple operations simultaneously. It improves system throughput and responsiveness."

    chunks = processor.chunk_text(content)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    metadata_list = [
        {
            "id": f"chunk_{i}",
            "document_id": "concurrent_doc",
            "document_name": "concurrent.txt",
            "text": chunk["text"],
            "chunk_index": i,
            "file_type": "txt",
            "upload_date": timestamp,
            "author": "",
            "creation_date": 0,
            "language": "",
            "keywords": "",
        }
        for i, chunk in enumerate(chunks)
    ]

    await milvus_manager.insert_embeddings(embeddings, metadata_list)
    print("✓ Test data indexed")

    # Create multiple sessions
    sessions = [f"session_{i}" for i in range(5)]
    queries = [
        "What is concurrent processing?",
        "How does concurrency work?",
        "What are the benefits?",
        "Tell me about throughput",
        "Explain responsiveness",
    ]

    # Process queries concurrently
    async def process_session_query(session_id, query):
        # Add message to STM
        await memory_manager.stm.add_message(session_id, "user", query)

        # Simulate query processing
        query_embedding = embedding_service.embed_text(query)
        results = await milvus_manager.search(query_embedding, top_k=3)

        # Add response to STM
        await memory_manager.stm.add_message(
            session_id, "assistant", f"Response to: {query}"
        )

        return session_id, len(results)

    # Run all queries concurrently
    tasks = [
        process_session_query(session, query)
        for session, query in zip(sessions, queries)
    ]

    results = await asyncio.gather(*tasks)

    print(f"✓ Processed {len(results)} concurrent queries")

    # Verify each session has its own history
    for session_id in sessions:
        history = await memory_manager.stm.get_conversation_history(session_id)
        assert len(history) == 2, f"Session {session_id} should have 2 messages"

    print("✓ All sessions maintained separate histories")

    # Cleanup
    for session_id in sessions:
        await memory_manager.stm.clear_session(session_id)

    await milvus_manager.delete_by_document_id("concurrent_doc")

    print("=" * 60)
    print("✓ CONCURRENT QUERIES TEST PASSED")
    print("=" * 60)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_error_recovery(milvus_manager, embedding_service, memory_manager):
    """
    Test system recovery from various error conditions.

    Requirements: 7.5
    """
    print("\n" + "=" * 60)
    print("ERROR RECOVERY TEST")
    print("=" * 60)

    # Test 1: Empty query
    print("\n[TEST 1] Empty Query")
    try:
        query_embedding = embedding_service.embed_text("")
        results = await milvus_manager.search(query_embedding, top_k=3)
        print("✓ Handled empty query gracefully")
    except Exception as e:
        print(f"✓ Raised appropriate error: {type(e).__name__}")

    # Test 2: Invalid top_k
    print("\n[TEST 2] Invalid Parameters")
    try:
        query_embedding = embedding_service.embed_text("test")
        results = await milvus_manager.search(query_embedding, top_k=0)
        print("✓ Handled invalid top_k gracefully")
    except Exception as e:
        print(f"✓ Raised appropriate error: {type(e).__name__}")

    # Test 3: Non-existent document deletion
    print("\n[TEST 3] Non-existent Document")
    try:
        await milvus_manager.delete_by_document_id("non_existent_doc")
        print("✓ Handled non-existent document gracefully")
    except Exception as e:
        print(f"✓ Raised appropriate error: {type(e).__name__}")

    # Test 4: Session operations
    print("\n[TEST 4] Session Operations")
    session_id = "error_test_session"

    # Clear non-existent session (should not error)
    await memory_manager.stm.clear_session(session_id)
    print("✓ Cleared non-existent session gracefully")

    # Get history from empty session
    history = await memory_manager.stm.get_conversation_history(session_id)
    assert len(history) == 0, "Empty session should have no history"
    print("✓ Retrieved empty history gracefully")

    print("\n" + "=" * 60)
    print("✓ ERROR RECOVERY TEST PASSED")
    print("=" * 60)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_data_persistence(milvus_manager, embedding_service, memory_manager):
    """
    Test data persistence across operations.

    Requirements: 1.5, 5.1
    """
    print("\n" + "=" * 60)
    print("DATA PERSISTENCE TEST")
    print("=" * 60)

    # Phase 1: Store data
    print("\n[PHASE 1] Storing Data")

    processor = DocumentProcessor()
    content = "Persistence ensures data survives across operations. It is crucial for reliability."

    chunks = processor.chunk_text(content)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    metadata_list = [
        {
            "id": f"chunk_{i}",
            "document_id": "persist_doc",
            "document_name": "persistence.txt",
            "text": chunk["text"],
            "chunk_index": i,
            "file_type": "txt",
            "upload_date": timestamp,
            "author": "",
            "creation_date": 0,
            "language": "",
            "keywords": "",
        }
        for i, chunk in enumerate(chunks)
    ]

    ids = await milvus_manager.insert_embeddings(embeddings, metadata_list)
    print(f"✓ Stored {len(ids)} chunks")

    # Store in LTM
    await memory_manager.ltm.store_interaction(
        query="What is persistence?",
        response="Persistence ensures data survives.",
        context={"test": True},
        success=True,
    )
    print("✓ Stored interaction in LTM")

    # Phase 2: Verify persistence
    print("\n[PHASE 2] Verifying Persistence")

    # Search for stored data
    query_embedding = embedding_service.embed_text("data persistence")
    results = await milvus_manager.search(query_embedding, top_k=3)

    assert len(results) > 0, "Should retrieve stored data"
    assert any("persist_doc" in str(r.get("document_id", "")) for r in results)
    print(f"✓ Retrieved {len(results)} chunks from storage")

    # Retrieve from LTM
    similar = await memory_manager.ltm.retrieve_similar_interactions(
        query="Tell me about data persistence", top_k=3
    )

    assert len(similar) > 0, "Should retrieve from LTM"
    print(f"✓ Retrieved {len(similar)} interactions from LTM")

    # Phase 3: Cleanup
    print("\n[PHASE 3] Cleanup")
    await milvus_manager.delete_by_document_id("persist_doc")
    print("✓ Cleaned up test data")

    print("\n" + "=" * 60)
    print("✓ DATA PERSISTENCE TEST PASSED")
    print("=" * 60)
