"""Test search functionality"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.services.agent_builder.hybrid_search_service import HybridSearchService

async def test_search():
    """Test search with the uploaded document"""
    
    db = SessionLocal()
    
    try:
        # Initialize search service
        service = HybridSearchService(db)
        
        # Test query
        query = "비래해충"
        kb_id = "008dba88-5b3a-45f7-9b9e-b9af54bd7637"
        
        print(f"\n🔍 Testing search...")
        print(f"   Query: {query}")
        print(f"   KB ID: {kb_id}\n")
        
        # Perform search
        results = await service.search(
            knowledgebase_id=kb_id,
            query=query,
            limit=5,
            search_strategy="vector"
        )
        
        print(f"✅ Search completed!")
        print(f"   Total results: {results['metadata']['total_results']}")
        print(f"   Documents: {len(results['documents'])}")
        print(f"   Entities: {len(results['entities'])}")
        print(f"   Relationships: {len(results['relationships'])}\n")
        
        # Display results
        if results['documents']:
            print("📄 Document Results:")
            for i, doc in enumerate(results['documents'][:3], 1):
                print(f"\n   {i}. Score: {doc.get('score', 0):.4f}")
                print(f"      Document: {doc.get('document_name', 'Unknown')}")
                text = doc.get('text', doc.get('content', ''))
                print(f"      Text: {text[:200]}...")
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_search())
