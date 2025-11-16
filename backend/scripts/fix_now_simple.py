"""간단한 컬렉션 수정 스크립트"""
import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

try:
    from pymilvus import connections, utility
    from backend.config import settings
    from backend.services.milvus import MilvusManager
    from backend.db.session import SessionLocal
    from backend.db.models.agent_builder import Knowledgebase
    
    print("="*70)
    print("Milvus Collection Fix Script")
    print("="*70)
    
    # Connect to Milvus
    connections.connect(
        alias="fix",
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT
    )
    print(f"✓ Connected to Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    
    # Get all knowledgebases
    db = SessionLocal()
    knowledgebases = db.query(Knowledgebase).all()
    print(f"✓ Found {len(knowledgebases)} knowledgebases")
    
    # Fix each collection
    for i, kb in enumerate(knowledgebases, 1):
        print(f"\n[{i}/{len(knowledgebases)}] {kb.name}")
        print(f"  Collection: {kb.milvus_collection_name}")
        
        # Drop old collection
        if utility.has_collection(kb.milvus_collection_name, using="fix"):
            utility.drop_collection(kb.milvus_collection_name, using="fix")
            print(f"  ✓ Dropped old collection")
        
        # Create new collection
        milvus_manager = MilvusManager(
            collection_name=kb.milvus_collection_name,
            embedding_dim=384
        )
        milvus_manager.connect()
        milvus_manager.create_collection()
        milvus_manager.disconnect()
        print(f"  ✓ Created new collection with knowledgebase_id field")
    
    connections.disconnect(alias="fix")
    db.close()
    
    print("\n" + "="*70)
    print("✓ ALL COLLECTIONS FIXED!")
    print("="*70)
    print("\nNext steps:")
    print("1. Restart backend server")
    print("2. Re-upload documents in UI")
    print("3. Test search functionality")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
