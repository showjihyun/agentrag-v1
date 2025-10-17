"""
Demo script showing memory integration between speculative and agentic paths.

This script demonstrates:
1. Speculative path loading conversation context from STM
2. Speculative path saving results to STM with path markers
3. Agentic path incorporating speculative findings
4. Memory consolidation with contributing paths marked
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.speculative_processor import SpeculativeProcessor
from backend.agents.aggregator import AggregatorAgent
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.services.llm_manager import LLMManager
from backend.memory.stm import ShortTermMemory
from backend.memory.ltm import LongTermMemory
from backend.memory.manager import MemoryManager
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.local_data import LocalDataAgent
from backend.agents.web_search import WebSearchAgent
from config import settings
import redis.asyncio as redis


async def main():
    """Run memory integration demo."""

    print("=" * 70)
    print("MEMORY INTEGRATION DEMO")
    print("=" * 70)
    print()

    # Initialize components
    print("1. Initializing components...")

    # Redis client for caching
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )

    # STM
    stm = ShortTermMemory(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        ttl=settings.STM_TTL,
    )

    # LTM
    ltm = LongTermMemory(
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
        collection_name=settings.MILVUS_LTM_COLLECTION,
    )

    # Memory Manager
    memory_manager = MemoryManager(stm=stm, ltm=ltm)

    # Embedding Service
    embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)

    # Milvus Manager
    milvus_manager = MilvusManager(
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
        collection_name=settings.MILVUS_COLLECTION,
    )

    # LLM Manager
    llm_manager = LLMManager()

    # Speculative Processor
    speculative_processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
        stm=stm,  # STM integration
    )

    # Agents for AggregatorAgent
    vector_agent = VectorSearchAgent(
        milvus_manager=milvus_manager, embedding_service=embedding_service
    )

    local_agent = LocalDataAgent()
    search_agent = WebSearchAgent()

    # Aggregator Agent
    aggregator_agent = AggregatorAgent(
        llm_manager=llm_manager,
        memory_manager=memory_manager,
        vector_agent=vector_agent,
        local_agent=local_agent,
        search_agent=search_agent,
    )

    print("✓ Components initialized")
    print()

    # Demo session
    session_id = "demo_session_001"

    # Step 1: First query with speculative path
    print("2. Processing first query with speculative path...")
    print(f"   Session ID: {session_id}")
    print(f"   Query: 'What is machine learning?'")
    print()

    query1 = "What is machine learning?"

    try:
        spec_response1 = await speculative_processor.process(
            query=query1, session_id=session_id, top_k=5
        )

        print(f"   ✓ Speculative response generated")
        print(f"     - Confidence: {spec_response1.confidence_score:.3f}")
        print(f"     - Processing time: {spec_response1.processing_time:.3f}s")
        print(f"     - Sources: {len(spec_response1.sources)}")
        print(f"     - Response: {spec_response1.response[:100]}...")
        print()

        # Check STM
        history = stm.get_conversation_history(session_id, limit=10)
        print(f"   ✓ Saved to STM: {len(history)} messages")

        # Check for path markers
        spec_messages = [
            msg
            for msg in history
            if msg.get("metadata", {}).get("path") == "speculative"
        ]
        print(f"     - Messages with 'speculative' path marker: {len(spec_messages)}")
        print()

    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()

    # Step 2: Follow-up query (should load context)
    print("3. Processing follow-up query with context...")
    print(f"   Query: 'How does it differ from traditional programming?'")
    print()

    query2 = "How does it differ from traditional programming?"

    try:
        spec_response2 = await speculative_processor.process(
            query=query2, session_id=session_id, top_k=5
        )

        print(f"   ✓ Speculative response generated (with context)")
        print(f"     - Confidence: {spec_response2.confidence_score:.3f}")
        print(f"     - Response: {spec_response2.response[:100]}...")
        print()

        # Check STM again
        history = stm.get_conversation_history(session_id, limit=10)
        print(f"   ✓ STM now has: {len(history)} messages")
        print()

    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()

    # Step 3: Process with agentic path incorporating speculative results
    print("4. Processing with agentic path (incorporating speculative results)...")
    print(f"   Query: 'Explain neural networks in detail'")
    print()

    query3 = "Explain neural networks in detail"

    try:
        # First get speculative results
        spec_response3 = await speculative_processor.process(
            query=query3, session_id=session_id, top_k=5
        )

        print(f"   ✓ Speculative results obtained")
        print(f"     - Confidence: {spec_response3.confidence_score:.3f}")
        print()

        # Convert to dict for agentic path
        speculative_results = {
            "response": spec_response3.response,
            "confidence_score": spec_response3.confidence_score,
            "sources": [
                {
                    "chunk_id": s.chunk_id,
                    "document_id": s.document_id,
                    "document_name": s.document_name,
                    "text": s.text,
                    "score": s.score,
                    "metadata": s.metadata,
                }
                for s in spec_response3.sources
            ],
        }

        # Process with agentic path
        print("   Processing with agentic path...")
        steps = []
        async for step in aggregator_agent.process_query(
            query=query3,
            session_id=session_id,
            top_k=10,
            speculative_results=speculative_results,
        ):
            steps.append(step)

            # Print key steps
            if step.type in ["thought", "memory", "response"]:
                print(f"     [{step.type.upper()}] {step.content[:80]}...")

        print()
        print(f"   ✓ Agentic processing complete: {len(steps)} steps")

        # Check final response metadata
        response_steps = [s for s in steps if s.type == "response"]
        if response_steps:
            final_step = response_steps[-1]
            has_speculative = final_step.metadata.get("has_speculative", False)
            print(f"     - Incorporated speculative results: {has_speculative}")

        # Check memory save
        memory_steps = [s for s in steps if s.type == "memory" and "Saved" in s.content]
        if memory_steps:
            memory_step = memory_steps[-1]
            contributing_paths = memory_step.metadata.get("contributing_paths", [])
            print(f"     - Contributing paths: {contributing_paths}")

        print()

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback

        traceback.print_exc()
        print()

    # Step 4: Check final memory state
    print("5. Checking final memory state...")

    try:
        # Get session info
        session_info = stm.get_session_info(session_id)
        print(f"   ✓ Session info:")
        print(f"     - Message count: {session_info.get('message_count', 0)}")
        print(
            f"     - Working memory keys: {len(session_info.get('working_memory_keys', []))}"
        )

        # Get conversation history
        history = stm.get_conversation_history(session_id, limit=20)
        print(f"   ✓ Conversation history: {len(history)} messages")

        # Count by path
        speculative_count = sum(
            1 for msg in history if msg.get("metadata", {}).get("path") == "speculative"
        )
        agentic_count = sum(
            1 for msg in history if msg.get("metadata", {}).get("path") == "agentic"
        )

        print(f"     - Speculative path messages: {speculative_count}")
        print(f"     - Agentic path messages: {agentic_count}")
        print()

    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()

    # Cleanup
    print("6. Cleaning up...")
    try:
        stm.clear_session(session_id)
        await redis_client.close()
        print("   ✓ Cleanup complete")
    except Exception as e:
        print(f"   ✗ Cleanup error: {e}")

    print()
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print("- Speculative path loads conversation context from STM")
    print("- Speculative results saved to STM with path markers")
    print("- Agentic path incorporates speculative findings")
    print("- Memory consolidation tracks contributing paths")
    print()


if __name__ == "__main__":
    asyncio.run(main())
