import sys
sys.path.insert(0, 'C:/WorkSpace/agenticRag')

from pymilvus import connections, utility, Collection
from backend.services.milvus import MilvusManager
from backend.db.database import SessionLocal
from backend.db.models.agent_builder import Knowledgebase

print("="*70)
print("Fixing Milvus Collections")
print("="*70)

# Connect
connections.connect(alias="fix", host="localhost", port=19530)
print("✓ Connected to Milvus")

# Get knowledgebases
db = SessionLocal()
kbs = db.query(Knowledgebase).all()
print(f"✓ Found {len(kbs)} knowledgebases\n")

# Fix each
for i, kb in enumerate(kbs, 1):
    print(f"[{i}/{len(kbs)}] {kb.name}")
    print(f"  Collection: {kb.milvus_collection_name}")
    
    # Drop
    if utility.has_collection(kb.milvus_collection_name, using="fix"):
        utility.drop_collection(kb.milvus_collection_name, using="fix")
        print(f"  ✓ Dropped")
    
    # Create
    mgr = MilvusManager(collection_name=kb.milvus_collection_name, embedding_dim=384)
    mgr.connect()
    mgr.create_collection()
    mgr.disconnect()
    print(f"  ✓ Created with knowledgebase_id field\n")

connections.disconnect(alias="fix")
db.close()

print("="*70)
print("✓ ALL DONE!")
print("="*70)
print("\nNext: Restart backend & re-upload documents")
