"""
Performance and load testing for the RAG system.
Tests Requirements: 7.4
"""

import pytest
import asyncio
import time
from statistics import mean, median, stdev
from typing import List, Dict

from backend.services.document_processor import DocumentProcessor
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.memory.manager import MemoryManager


class PerformanceMetrics:
    """Helper class to track performance metrics."""

    def __init__(self):
        self.timings: List[float] = []
        self.errors: List[str] = []

    def add_timing(self, duration: float):
        """Add a timing measurement."""
        self.timings.append(duration)

    def add_error(self, error: str):
        """Add an error."""
        self.errors.append(error)

    def get_stats(self) -> Dict:
        """Get statistics."""
        if not self.timings:
            return {
                "count": 0,
                "errors": len(self.errors),
                "error_rate": 1.0 if self.errors else 0.0,
            }

        return {
            "count": len(self.timings),
            "mean": mean(self.timings),
            "median": median(self.timings),
            "min": min(self.timings),
            "max": max(self.timings),
            "stdev": stdev(self.timings) if len(self.timings) > 1 else 0,
            "errors": len(self.errors),
            "error_rate": len(self.errors) / (len(self.timings) + len(self.errors)),
        }

    def print_stats(self, operation: str):
        """Print statistics."""
        stats = self.get_stats()

        print(f"\n{operation} Performance:")
        print(f"  Operations: {stats['count']}")
        print(f"  Mean time: {stats.get('mean', 0)*1000:.2f}ms")
        print(f"  Median time: {stats.get('median', 0)*1000:.2f}ms")
        print(f"  Min time: {stats.get('min', 0)*1000:.2f}ms")
        print(f"  Max time: {stats.get('max', 0)*1000:.2f}ms")
        if stats.get("stdev"):
            print(f"  Std dev: {stats['stdev']*1000:.2f}ms")
        print(f"  Errors: {stats['errors']} ({stats['error_rate']*100:.1f}%)")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_embedding_generation_performance(embedding_service):
    """
    Test embedding generation performance.

    Requirements: 7.4
    """
    print("\n" + "=" * 60)
    print("EMBEDDING GENERATION PERFORMANCE TEST")
    print("=" * 60)

    metrics = PerformanceMetrics()

    # Test single embedding generation
    print("\n[TEST 1] Single Embedding Generation")
    test_texts = [
        "This is a short text.",
        "This is a medium length text with more words and content to process.",
        "This is a much longer text that contains significantly more content and information. "
        * 5,
    ]

    for text in test_texts:
        start = time.time()
        try:
            embedding = embedding_service.embed_text(text)
            duration = time.time() - start
            metrics.add_timing(duration)
            assert len(embedding) == 384, "Embedding should have correct dimension"
        except Exception as e:
            metrics.add_error(str(e))

    metrics.print_stats("Single Embedding")

    # Test batch embedding generation
    print("\n[TEST 2] Batch Embedding Generation")
    batch_metrics = PerformanceMetrics()

    batch_sizes = [10, 50, 100]
    for batch_size in batch_sizes:
        texts = [f"Test text number {i} with some content." for i in range(batch_size)]

        start = time.time()
        try:
            embeddings = embedding_service.embed_batch(texts)
            duration = time.time() - start
            batch_metrics.add_timing(duration)

            assert len(embeddings) == batch_size
            print(
                f"  Batch size {batch_size}: {duration*1000:.2f}ms ({duration*1000/batch_size:.2f}ms per item)"
            )
        except Exception as e:
            batch_metrics.add_error(str(e))

    batch_metrics.print_stats("Batch Embedding")

    print("\n" + "=" * 60)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_vector_search_performance(milvus_manager, embedding_service):
    """
    Test vector search performance with varying data sizes.

    Requirements: 7.4
    """
    print("\n" + "=" * 60)
    print("VECTOR SEARCH PERFORMANCE TEST")
    print("=" * 60)

    processor = DocumentProcessor()

    # Index varying amounts of data
    document_counts = [10, 50, 100]

    for doc_count in document_counts:
        print(f"\n[TEST] Indexing {doc_count} documents")

        # Generate test documents
        all_embeddings = []
        all_metadata = []

        for doc_id in range(doc_count):
            content = f"Document {doc_id}: " + " ".join(
                [
                    f"This is sentence {i} with content about topic {doc_id}."
                    for i in range(10)
                ]
            )

            chunks = processor.chunk_text(content)
            texts = [chunk["text"] for chunk in chunks]
            embeddings = embedding_service.embed_batch(texts)

            for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
                all_embeddings.append(embedding)
                all_metadata.append(
                    {
                        "document_id": f"perf_doc_{doc_id}",
                        "document_name": f"doc_{doc_id}.txt",
                        "chunk_id": i,
                        "text": chunk["text"],
                    }
                )

        # Index all at once
        index_start = time.time()
        ids = await milvus_manager.insert_embeddings(all_embeddings, all_metadata)
        index_duration = time.time() - index_start

        print(f"  Indexed {len(ids)} chunks in {index_duration:.2f}s")
        print(f"  Rate: {len(ids)/index_duration:.1f} chunks/sec")

        # Test search performance
        search_metrics = PerformanceMetrics()

        test_queries = [
            "What is this document about?",
            "Tell me about the topic",
            "Find information on the subject",
            "Explain the content",
            "What does this discuss?",
        ]

        for query in test_queries:
            query_embedding = embedding_service.embed_text(query)

            search_start = time.time()
            try:
                results = await milvus_manager.search(query_embedding, top_k=10)
                search_duration = time.time() - search_start
                search_metrics.add_timing(search_duration)
            except Exception as e:
                search_metrics.add_error(str(e))

        search_metrics.print_stats(f"Search ({doc_count} docs)")

        # Cleanup
        for doc_id in range(doc_count):
            await milvus_manager.delete_by_document_id(f"perf_doc_{doc_id}")

    print("\n" + "=" * 60)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_search_performance(milvus_manager, embedding_service):
    """
    Test performance under concurrent search load.

    Requirements: 7.4
    """
    print("\n" + "=" * 60)
    print("CONCURRENT SEARCH PERFORMANCE TEST")
    print("=" * 60)

    # Set up test data
    processor = DocumentProcessor()
    content = "Test content for concurrent search performance testing. " * 20

    chunks = processor.chunk_text(content)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    metadata_list = [
        {
            "document_id": "concurrent_perf_doc",
            "document_name": "concurrent_test.txt",
            "chunk_id": i,
            "text": chunk["text"],
        }
        for i, chunk in enumerate(chunks)
    ]

    await milvus_manager.insert_embeddings(embeddings, metadata_list)
    print("✓ Test data indexed")

    # Test with varying concurrency levels
    concurrency_levels = [1, 5, 10, 20]

    for concurrency in concurrency_levels:
        print(f"\n[TEST] Concurrency level: {concurrency}")

        async def search_task(task_id: int):
            query = f"Test query {task_id}"
            query_embedding = embedding_service.embed_text(query)

            start = time.time()
            results = await milvus_manager.search(query_embedding, top_k=5)
            duration = time.time() - start

            return duration, len(results)

        # Run concurrent searches
        overall_start = time.time()
        tasks = [search_task(i) for i in range(concurrency)]
        results = await asyncio.gather(*tasks)
        overall_duration = time.time() - overall_start

        # Calculate metrics
        durations = [r[0] for r in results]
        result_counts = [r[1] for r in results]

        print(f"  Total time: {overall_duration:.2f}s")
        print(f"  Throughput: {concurrency/overall_duration:.1f} queries/sec")
        print(f"  Mean query time: {mean(durations)*1000:.2f}ms")
        print(f"  Max query time: {max(durations)*1000:.2f}ms")
        print(f"  Results per query: {mean(result_counts):.1f}")

    # Cleanup
    await milvus_manager.delete_by_document_id("concurrent_perf_doc")

    print("\n" + "=" * 60)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_memory_operations_performance(memory_manager):
    """
    Test memory operations performance.

    Requirements: 7.4
    """
    print("\n" + "=" * 60)
    print("MEMORY OPERATIONS PERFORMANCE TEST")
    print("=" * 60)

    session_id = "perf_test_session"

    # Test STM write performance
    print("\n[TEST 1] STM Write Performance")
    write_metrics = PerformanceMetrics()

    message_counts = [10, 50, 100]
    for count in message_counts:
        start = time.time()

        for i in range(count):
            await memory_manager.stm.add_message(
                session_id=f"{session_id}_{count}",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i} with some content to store.",
            )

        duration = time.time() - start
        write_metrics.add_timing(duration)

        print(
            f"  {count} messages: {duration*1000:.2f}ms ({duration*1000/count:.2f}ms per message)"
        )

    # Test STM read performance
    print("\n[TEST 2] STM Read Performance")
    read_metrics = PerformanceMetrics()

    for count in message_counts:
        start = time.time()

        history = await memory_manager.stm.get_conversation_history(
            session_id=f"{session_id}_{count}", limit=count
        )

        duration = time.time() - start
        read_metrics.add_timing(duration)

        print(f"  Read {len(history)} messages: {duration*1000:.2f}ms")

    # Test context retrieval performance
    print("\n[TEST 3] Context Retrieval Performance")
    context_metrics = PerformanceMetrics()

    for _ in range(10):
        start = time.time()

        context = await memory_manager.get_context_for_query(
            session_id=f"{session_id}_100", query="Test query for context retrieval"
        )

        duration = time.time() - start
        context_metrics.add_timing(duration)

    context_metrics.print_stats("Context Retrieval")

    # Cleanup
    for count in message_counts:
        await memory_manager.stm.clear_session(f"{session_id}_{count}")

    print("\n" + "=" * 60)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_document_processing_performance(milvus_manager, embedding_service):
    """
    Test end-to-end document processing performance.

    Requirements: 7.4
    """
    print("\n" + "=" * 60)
    print("DOCUMENT PROCESSING PERFORMANCE TEST")
    print("=" * 60)

    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)

    # Test with varying document sizes
    document_sizes = [
        ("Small", 500),  # ~500 characters
        ("Medium", 5000),  # ~5000 characters
        ("Large", 50000),  # ~50000 characters
    ]

    for size_name, char_count in document_sizes:
        print(f"\n[TEST] {size_name} Document ({char_count} characters)")

        # Generate document
        content = "This is test content. " * (char_count // 20)

        # Measure chunking
        chunk_start = time.time()
        chunks = processor.chunk_text(content)
        chunk_duration = time.time() - chunk_start

        print(f"  Chunking: {chunk_duration*1000:.2f}ms ({len(chunks)} chunks)")

        # Measure embedding generation
        texts = [chunk["text"] for chunk in chunks]
        embed_start = time.time()
        embeddings = embedding_service.embed_batch(texts)
        embed_duration = time.time() - embed_start

        print(
            f"  Embedding: {embed_duration*1000:.2f}ms ({len(embeddings)} embeddings)"
        )

        # Measure indexing
        metadata_list = [
            {
                "document_id": f"perf_{size_name}",
                "document_name": f"{size_name}.txt",
                "chunk_id": i,
                "text": chunk["text"],
            }
            for i, chunk in enumerate(chunks)
        ]

        index_start = time.time()
        ids = await milvus_manager.insert_embeddings(embeddings, metadata_list)
        index_duration = time.time() - index_start

        print(f"  Indexing: {index_duration*1000:.2f}ms ({len(ids)} chunks)")

        # Total time
        total_duration = chunk_duration + embed_duration + index_duration
        print(f"  Total: {total_duration*1000:.2f}ms")
        print(f"  Rate: {char_count/total_duration:.0f} chars/sec")

        # Cleanup
        await milvus_manager.delete_by_document_id(f"perf_{size_name}")

    print("\n" + "=" * 60)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_system_under_load(milvus_manager, embedding_service, memory_manager):
    """
    Test overall system performance under sustained load.

    Requirements: 7.4
    """
    print("\n" + "=" * 60)
    print("SYSTEM LOAD TEST")
    print("=" * 60)

    # Set up test data
    processor = DocumentProcessor()

    print("\n[PHASE 1] Setting up test data...")
    for doc_id in range(20):
        content = f"Document {doc_id} content. " * 50
        chunks = processor.chunk_text(content)
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.embed_batch(texts)

        metadata_list = [
            {
                "document_id": f"load_doc_{doc_id}",
                "document_name": f"doc_{doc_id}.txt",
                "chunk_id": i,
                "text": chunk["text"],
            }
            for i, chunk in enumerate(chunks)
        ]

        await milvus_manager.insert_embeddings(embeddings, metadata_list)

    print("✓ Test data ready")

    # Simulate mixed workload
    print("\n[PHASE 2] Running mixed workload...")

    async def mixed_operation(op_id: int):
        """Simulate a mixed operation (search + memory)."""
        start = time.time()

        try:
            # Search operation
            query = f"Test query {op_id}"
            query_embedding = embedding_service.embed_text(query)
            results = await milvus_manager.search(query_embedding, top_k=5)

            # Memory operation
            session_id = f"load_session_{op_id % 10}"
            await memory_manager.stm.add_message(session_id, "user", query)
            await memory_manager.stm.add_message(
                session_id, "assistant", f"Response {op_id}"
            )

            duration = time.time() - start
            return True, duration, len(results)
        except Exception as e:
            duration = time.time() - start
            return False, duration, 0

    # Run sustained load
    num_operations = 100
    concurrency = 10

    all_results = []
    for batch in range(0, num_operations, concurrency):
        tasks = [
            mixed_operation(batch + i)
            for i in range(min(concurrency, num_operations - batch))
        ]
        batch_results = await asyncio.gather(*tasks)
        all_results.extend(batch_results)

    # Calculate metrics
    successes = [r for r in all_results if r[0]]
    failures = [r for r in all_results if not r[0]]
    durations = [r[1] for r in successes]

    print(f"\n✓ Completed {len(all_results)} operations")
    print(f"  Success rate: {len(successes)/len(all_results)*100:.1f}%")
    print(f"  Mean operation time: {mean(durations)*1000:.2f}ms")
    print(f"  Median operation time: {median(durations)*1000:.2f}ms")
    print(
        f"  95th percentile: {sorted(durations)[int(len(durations)*0.95)]*1000:.2f}ms"
    )
    print(f"  Max operation time: {max(durations)*1000:.2f}ms")

    # Cleanup
    print("\n[PHASE 3] Cleaning up...")
    for doc_id in range(20):
        await milvus_manager.delete_by_document_id(f"load_doc_{doc_id}")

    for session_id in range(10):
        await memory_manager.stm.clear_session(f"load_session_{session_id}")

    print("\n" + "=" * 60)
    print("✓ SYSTEM LOAD TEST COMPLETED")
    print("=" * 60)
