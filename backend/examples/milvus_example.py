"""
Example usage of MilvusManager.

This script demonstrates the key features of MilvusManager:
- Connection management with retry logic
- Collection creation
- Batch embedding insertion
- Vector similarity search
- Document deletion
- Health checks

Note: Requires a running Milvus instance at localhost:19530
"""

import asyncio
import time
from typing import List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService


async def main():
    """Demonstrate MilvusManager functionality."""

    print("=" * 60)
    print("MilvusManager Example")
    print("=" * 60)

    # Initialize services
    print("\n1. Initializing services...")
    embedding_service = EmbeddingService()
    print(f"   Embedding dimension: {embedding_service.dimension}")

    milvus_manager = MilvusManager(
        host="localhost",
        port=19530,
        collection_name="example_documents",
        embedding_dim=embedding_service.dimension,
        max_retries=3,
    )
    print(f"   {milvus_manager}")

    # Connect to Milvus
    print("\n2. Connecting to Milvus...")
    try:
        milvus_manager.connect()
        print("   ✓ Connected successfully")
    except RuntimeError as e:
        print(f"   ✗ Connection failed: {e}")
        print("\n   Make sure Milvus is running:")
        print("   docker-compose up -d milvus")
        return

    # Health check
    print("\n3. Performing health check...")
    health = milvus_manager.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Connected: {health['connected']}")
    print(f"   Collection exists: {health.get('collection_exists', False)}")

    # Create collection
    print("\n4. Creating collection...")
    try:
        collection = milvus_manager.create_collection(drop_existing=True)
        print(f"   ✓ Collection created: {collection.name}")
    except Exception as e:
        print(f"   ✗ Failed to create collection: {e}")
        milvus_manager.disconnect()
        return

    # Prepare sample documents
    print("\n5. Preparing sample documents...")
    sample_texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Deep learning uses neural networks with multiple layers.",
        "Natural language processing helps computers understand human language.",
        "Computer vision enables machines to interpret visual information.",
        "Reinforcement learning trains agents through rewards and penalties.",
    ]

    print(f"   Sample documents: {len(sample_texts)}")

    # Generate embeddings
    print("\n6. Generating embeddings...")
    embeddings = embedding_service.embed_batch(sample_texts)
    print(f"   ✓ Generated {len(embeddings)} embeddings")

    # Prepare metadata
    print("\n7. Preparing metadata...")
    metadata = []
    document_id = "doc_example_001"
    upload_timestamp = int(time.time())

    for i, text in enumerate(sample_texts):
        metadata.append(
            {
                "id": f"chunk_{document_id}_{i}",
                "document_id": document_id,
                "text": text,
                "chunk_index": i,
                "document_name": "example_document.txt",
                "file_type": "txt",
                "upload_date": upload_timestamp,
            }
        )

    print(f"   ✓ Prepared metadata for {len(metadata)} chunks")

    # Insert embeddings
    print("\n8. Inserting embeddings into Milvus...")
    try:
        inserted_ids = await milvus_manager.insert_embeddings(embeddings, metadata)
        print(f"   ✓ Inserted {len(inserted_ids)} embeddings")
        print(f"   First 3 IDs: {inserted_ids[:3]}")
    except Exception as e:
        print(f"   ✗ Insertion failed: {e}")
        milvus_manager.disconnect()
        return

    # Get collection stats
    print("\n9. Collection statistics...")
    stats = milvus_manager.get_collection_stats()
    print(f"   Name: {stats['name']}")
    print(f"   Entities: {stats.get('num_entities', 'N/A')}")

    # Perform search
    print("\n10. Performing similarity search...")
    query_text = "How do neural networks learn?"
    print(f"    Query: '{query_text}'")

    query_embedding = embedding_service.embed_text(query_text)

    try:
        results = await milvus_manager.search(query_embedding=query_embedding, top_k=3)

        print(f"    ✓ Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n    Result {i}:")
            print(f"      Score: {result.score:.4f}")
            print(f"      Text: {result.text}")
            print(f"      Document: {result.document_name}")
            print(f"      Chunk: {result.chunk_index}")
    except Exception as e:
        print(f"    ✗ Search failed: {e}")

    # Search with filter
    print("\n11. Searching with filter...")
    try:
        filtered_results = await milvus_manager.search(
            query_embedding=query_embedding,
            top_k=5,
            filters=f'document_id == "{document_id}"',
        )
        print(f"    ✓ Found {len(filtered_results)} results with filter")
    except Exception as e:
        print(f"    ✗ Filtered search failed: {e}")

    # Delete document
    print("\n12. Deleting document...")
    try:
        deleted_count = await milvus_manager.delete_by_document_id(document_id)
        print(f"    ✓ Deleted {deleted_count} chunks")
    except Exception as e:
        print(f"    ✗ Deletion failed: {e}")

    # Verify deletion
    print("\n13. Verifying deletion...")
    stats_after = milvus_manager.get_collection_stats()
    print(f"    Entities after deletion: {stats_after.get('num_entities', 'N/A')}")

    # Disconnect
    print("\n14. Disconnecting...")
    milvus_manager.disconnect()
    print("    ✓ Disconnected")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
