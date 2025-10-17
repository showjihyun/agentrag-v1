"""
Simple diagnostic script to find why "빅밸류의 주소는?" returns "No response generated"
"""

import sys
import os

# Suppress config summary
os.environ['SUPPRESS_CONFIG_SUMMARY'] = '1'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService

async def main():
    print("=" * 60)
    print("Diagnosing: No response generated issue")
    print("=" * 60)
    
    # Initialize services
    print("\n1. Initializing services...")
    try:
        # Use model from config (EMBEDDING_MODEL env var)
        embedding_service = EmbeddingService()
        print(f"   [OK] Embedding service initialized: {embedding_service.model_name}")
    except Exception as e:
        print(f"   [FAIL] Embedding service: {e}")
        return
    
    try:
        from backend.config import settings
        milvus_manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION_NAME
        )
        print(f"   [OK] Milvus manager initialized (port: {settings.MILVUS_PORT})")
    except Exception as e:
        print(f"   [FAIL] Milvus manager: {e}")
        return
    
    # Connect to Milvus
    print("\n2. Connecting to Milvus...")
    try:
        milvus_manager.connect()
        print("   [OK] Connected to Milvus")
    except Exception as e:
        print(f"   [FAIL] Cannot connect to Milvus: {e}")
        print("\n   Possible reasons:")
        print("   - Milvus is not running")
        print("   - Wrong host/port (check .env file)")
        print("   - Firewall blocking connection")
        return
    
    # Check collection
    print("\n3. Checking collection...")
    try:
        collection_stats = milvus_manager.get_collection_stats()
        if collection_stats:
            num_entities = collection_stats.get('row_count', 0)
            print(f"   [OK] Collection exists with {num_entities} documents")
            
            if num_entities == 0:
                print("\n   [PROBLEM FOUND] No documents in Milvus!")
                print("   This is why you get 'No response generated'")
                print("\n   Solution:")
                print("   1. Upload documents through the API")
                print("   2. Use: POST /api/documents/upload")
                return
        else:
            print("   [FAIL] Collection does not exist")
            print("\n   [PROBLEM FOUND] Collection not created!")
            print("   This is why you get 'No response generated'")
            return
    except Exception as e:
        print(f"   [FAIL] Error checking collection: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test search
    print("\n4. Testing search with '빅밸류의 주소는?'...")
    try:
        query_embedding = await embedding_service.embed_query("빅밸류의 주소는?")
        print(f"   [OK] Generated embedding (dim: {len(query_embedding)})")
        
        results = milvus_manager.search(
            query_embedding=query_embedding,
            top_k=5
        )
        
        if results:
            print(f"   [OK] Found {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"\n   Result {i}:")
                print(f"   - Document: {result.document_name}")
                print(f"   - Score: {result.score:.4f}")
                print(f"   - Text: {result.text[:100]}...")
        else:
            print("   [PROBLEM FOUND] No search results!")
            print("   This is why you get 'No response generated'")
            print("\n   Possible reasons:")
            print("   1. No documents contain '빅밸류' information")
            print("   2. Documents are not in Korean")
            print("   3. Embedding model mismatch")
            print("\n   Solution:")
            print("   1. Upload documents with '빅밸류' information")
            print("   2. Verify documents are in Korean")
    except Exception as e:
        print(f"   [FAIL] Search error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Close connection
    milvus_manager.close()
    
    print("\n" + "=" * 60)
    print("Diagnosis complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
