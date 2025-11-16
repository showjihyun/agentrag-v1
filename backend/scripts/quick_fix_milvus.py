"""
Quick fix script to recreate a specific Milvus collection.
Run this from the backend directory with the virtual environment activated.
"""

import asyncio
from pymilvus import connections, utility
from backend.config import settings
from backend.services.milvus import MilvusManager


async def recreate_collection(collection_name: str):
    """Recreate a single collection with the new schema."""
    print(f"\n{'='*60}")
    print(f"Recreating collection: {collection_name}")
    print(f"{'='*60}")
    
    try:
        # Connect to Milvus
        connections.connect(
            alias="fix",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # Drop if exists
        if utility.has_collection(collection_name, using="fix"):
            print(f"Dropping existing collection...")
            utility.drop_collection(collection_name, using="fix")
            print(f"✓ Dropped")
        
        # Create new collection
        print(f"Creating new collection with updated schema...")
        milvus_manager = MilvusManager(
            collection_name=collection_name,
            embedding_dim=384
        )
        milvus_manager.connect()
        milvus_manager.create_collection()
        
        print(f"✓ Successfully recreated collection: {collection_name}")
        print(f"\nYou can now re-upload documents to this knowledgebase.")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        raise
    finally:
        connections.disconnect(alias="fix")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python quick_fix_milvus.py <collection_name>")
        print("\nExample: python quick_fix_milvus.py kb_abc123def456")
        sys.exit(1)
    
    collection_name = sys.argv[1]
    asyncio.run(recreate_collection(collection_name))
