"""
Debug script to check knowledgebase search issues
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db
from services.agent_builder.knowledgebase_service import KnowledgebaseService
from services.milvus import MilvusManager
from services.embedding import EmbeddingService

async def debug_kb_search():
    """Debug knowledgebase search"""
    
    kb_id = "8d7b765b-26a1-4068-8634-ac2645538bc4"
    query = "비래해충"
    
    print(f"\n=== Debugging KB Search ===")
    print(f"KB ID: {kb_id}")
    print(f"Query: {query}")
    
    # Get DB session
    db = next(get_db())
    
    try:
        # 1. Check KB exists and get details
        kb_service = KnowledgebaseService(db)
        kb = kb_service.get_knowledgebase(kb_id)
        
        if not kb:
            print(f"❌ Knowledgebase {kb_id} not found!")
            return
        
        print(f"\n✅ Knowledgebase found:")
        print(f"  - Name: {kb.name}")
        print(f"  - Collection: {kb.milvus_collection_name}")
        print(f"  - Embedding Model: {kb.embedding_model}")
        print(f"  - Embedding Dimension: {kb.embedding_dimension}")
        
        # 2. Check Milvus collection
        embedding_model = kb.embedding_model or "jhgan/ko-sroberta-multitask"
        embedding_dim = kb.embedding_dimension or 768
        
        print(f"\n=== Checking Milvus Collection ===")
        milvus_manager = MilvusManager(
            collection_name=kb.milvus_collection_name,
            embedding_dim=embedding_dim
        )
        
        milvus_manager.connect()
        collection = milvus_manager.get_collection()
        
        print(f"✅ Collection exists: {kb.milvus_collection_name}")
        
        # Load collection
        collection.load()
        num_entities = collection.num_entities
        print(f"  - Total entities: {num_entities}")
        
        if num_entities == 0:
            print(f"\n❌ Collection is EMPTY! No documents have been indexed.")
            print(f"   This is why search returns 0 results.")
            return
        
        # 3. Check a few sample entities
        print(f"\n=== Sample Entities ===")
        sample_results = collection.query(
            expr=f'knowledgebase_id == "{kb_id}"',
            output_fields=["id", "text", "document_id", "knowledgebase_id"],
            limit=3
        )
        
        if sample_results:
            for i, result in enumerate(sample_results, 1):
                text_preview = result.get("text", "")[:100]
                print(f"\n  Sample {i}:")
                print(f"    - ID: {result.get('id')}")
                print(f"    - Document ID: {result.get('document_id')}")
                print(f"    - Text: {text_preview}...")
        else:
            print(f"  ❌ No entities found with knowledgebase_id={kb_id}")
            print(f"     Checking without filter...")
            
            sample_results = collection.query(
                expr="",
                output_fields=["id", "text", "knowledgebase_id"],
                limit=3
            )
            
            if sample_results:
                print(f"  Found {len(sample_results)} entities in collection:")
                for result in sample_results:
                    print(f"    - KB ID: {result.get('knowledgebase_id')}")
            else:
                print(f"  ❌ Collection appears empty despite num_entities={num_entities}")
        
        # 4. Test embedding generation
        print(f"\n=== Testing Embedding Generation ===")
        embedding_service = EmbeddingService(model_name=embedding_model)
        print(f"  - Model: {embedding_service.model_name}")
        print(f"  - Dimension: {embedding_service.dimension}")
        
        query_embedding = await embedding_service.embed_text(query)
        print(f"  - Query embedding generated: {len(query_embedding)} dimensions")
        print(f"  - First 5 values: {query_embedding[:5]}")
        
        # 5. Test direct Milvus search
        print(f"\n=== Testing Direct Milvus Search ===")
        
        # Search with filter
        results_with_filter = await milvus_manager.search(
            query_embedding=query_embedding,
            top_k=5,
            filters=f'knowledgebase_id == "{kb_id}"'
        )
        
        print(f"  - Results with KB filter: {len(results_with_filter)}")
        for i, result in enumerate(results_with_filter, 1):
            print(f"    {i}. Score: {result.score:.4f}, Text: {result.text[:80]}...")
        
        # Search without filter
        results_no_filter = await milvus_manager.search(
            query_embedding=query_embedding,
            top_k=5,
            filters=None
        )
        
        print(f"\n  - Results without filter: {len(results_no_filter)}")
        for i, result in enumerate(results_no_filter, 1):
            print(f"    {i}. Score: {result.score:.4f}, Text: {result.text[:80]}...")
        
        # 6. Check documents in DB
        print(f"\n=== Checking Documents in Database ===")
        from db.models.agent_builder import KnowledgebaseDocument
        from db.models.document import Document
        
        kb_docs = db.query(KnowledgebaseDocument).filter(
            KnowledgebaseDocument.knowledgebase_id == kb_id
        ).all()
        
        print(f"  - Documents linked to KB: {len(kb_docs)}")
        
        for kb_doc in kb_docs:
            doc = db.query(Document).filter(Document.id == kb_doc.document_id).first()
            if doc:
                print(f"\n    Document: {doc.filename}")
                print(f"      - Status: {doc.status}")
                print(f"      - Chunks: {doc.chunk_count}")
                print(f"      - Size: {doc.file_size_bytes} bytes")
                if doc.error_message:
                    print(f"      - Error: {doc.error_message}")
        
        milvus_manager.disconnect()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_kb_search())
