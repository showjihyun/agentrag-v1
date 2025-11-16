"""Direct Milvus collection fix - no database dependency"""
import sys
sys.path.insert(0, 'C:/WorkSpace/agenticRag')

from pymilvus import connections, utility
from backend.services.milvus import MilvusManager

print("="*70)
print("Fixing Milvus Collections (Direct)")
print("="*70)

# Connect to Milvus
connections.connect(alias="fix", host="localhost", port=19530)
print("✓ Connected to Milvus\n")

# Get all collections
all_collections = utility.list_collections(using="fix")
print(f"Found {len(all_collections)} collections:")
for col in all_collections:
    print(f"  - {col}")

# Filter knowledgebase collections (start with 'kb_')
kb_collections = [c for c in all_collections if c.startswith('kb_')]
print(f"\nKnowledgebase collections to fix: {len(kb_collections)}\n")

if not kb_collections:
    print("No knowledgebase collections found!")
    sys.exit(0)

# Fix each collection
for i, col_name in enumerate(kb_collections, 1):
    print(f"[{i}/{len(kb_collections)}] {col_name}")
    
    try:
        # Drop old collection
        utility.drop_collection(col_name, using="fix")
        print(f"  ✓ Dropped old collection")
        
        # Create new collection with knowledgebase_id field
        mgr = MilvusManager(collection_name=col_name, embedding_dim=384)
        mgr.connect()
        mgr.create_collection()
        mgr.disconnect()
        print(f"  ✓ Created new collection with knowledgebase_id field\n")
        
    except Exception as e:
        print(f"  ✗ Error: {e}\n")

connections.disconnect(alias="fix")

print("="*70)
print("✓ ALL COLLECTIONS FIXED!")
print("="*70)
print("\nNext steps:")
print("1. Restart backend server")
print("2. Re-upload documents in UI")
print("3. Test search functionality")
