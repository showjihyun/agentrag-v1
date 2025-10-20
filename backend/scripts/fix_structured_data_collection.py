"""
Fix structured_data collection schema by recreating it with vector field
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pymilvus import connections, utility
from backend.config import settings

print("=" * 70)
print("Fix Structured Data Collection")
print("=" * 70)

# Connect to Milvus
print(f"\n1. Connecting to Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
connections.connect(
    alias="default",
    host=settings.MILVUS_HOST,
    port=str(settings.MILVUS_PORT)
)
print("   [OK] Connected")

# Check if collection exists
collection_name = "structured_tables"
print(f"\n2. Checking collection: {collection_name}")
if utility.has_collection(collection_name):
    print(f"   [FOUND] Collection exists")
    
    # Drop the collection
    print(f"   [ACTION] Dropping collection...")
    utility.drop_collection(collection_name)
    print(f"   [OK] Collection dropped")
else:
    print(f"   [INFO] Collection does not exist")

print(f"\n3. Collection will be recreated on next backend startup")
print(f"   The new schema will include a vector field for embeddings")

print("\n" + "=" * 70)
print("Done! Please restart the backend server.")
print("=" * 70)
