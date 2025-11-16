"""Fix ALL Milvus collections - including documents collection"""
import sys
sys.path.insert(0, 'C:/WorkSpace/agenticRag')

from pymilvus import connections, utility
from backend.services.milvus import MilvusManager

print("="*70)
print("Fixing ALL Milvus Collections")
print("="*70)

# Connect to Milvus
connections.connect(alias="fix", host="localhost", port=19530)
print("✓ Connected to Milvus\n")

# Collections to fix (those that need knowledgebase_id field)
collections_to_fix = [
    'documents',  # Main documents collection
]

# Add all kb_* collections
all_collections = utility.list_collections(using="fix")
kb_collections = [c for c in all_collections if c.startswith('kb_')]
collections_to_fix.extend(kb_collections)

print(f"Collections to fix: {len(collections_to_fix)}")
for col in collections_to_fix:
    print(f"  - {col}")
print()

# Fix each collection
for i, col_name in enumerate(collections_to_fix, 1):
    print(f"[{i}/{len(collections_to_fix)}] {col_name}")
    
    try:
        # Check if exists
        if not utility.has_collection(col_name, using="fix"):
            print(f"  - Collection doesn't exist, creating new...")
        else:
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
        import traceback
        traceback.print_exc()

connections.disconnect(alias="fix")

print("="*70)
print("✓ ALL COLLECTIONS FIXED!")
print("="*70)
print("\nIMPORTANT:")
print("1. Restart backend server NOW")
print("2. Re-upload ALL documents")
print("3. Test search functionality")
print("\nAll data has been deleted. You must re-upload documents.")
