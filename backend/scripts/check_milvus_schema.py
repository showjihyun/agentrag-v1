"""
Script to check Milvus collection schemas and identify issues.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymilvus import connections, Collection, utility
from backend.config import settings
from backend.db.session import SessionLocal
from backend.db.models.agent_builder import Knowledgebase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_collection_schema(collection_name: str):
    """Check the schema of a collection."""
    try:
        if not utility.has_collection(collection_name, using="check"):
            logger.warning(f"Collection {collection_name} does not exist")
            return None
        
        collection = Collection(name=collection_name, using="check")
        schema = collection.schema
        
        print(f"\n{'='*60}")
        print(f"Collection: {collection_name}")
        print(f"{'='*60}")
        print(f"Description: {schema.description}")
        print(f"Number of entities: {collection.num_entities}")
        print(f"\nFields:")
        
        expected_fields = [
            "id", "document_id", "knowledgebase_id", "text", "embedding",
            "chunk_index", "document_name", "file_type", "upload_date",
            "author", "creation_date", "language", "keywords"
        ]
        
        actual_fields = [field.name for field in schema.fields]
        
        for field in schema.fields:
            status = "✓" if field.name in expected_fields else "?"
            print(f"  {status} {field.name:20s} - {field.dtype} {f'(primary)' if field.is_primary else ''}")
        
        # Check for missing fields
        missing_fields = set(expected_fields) - set(actual_fields)
        if missing_fields:
            print(f"\n⚠️  Missing fields: {', '.join(missing_fields)}")
            return False
        
        # Check for extra fields
        extra_fields = set(actual_fields) - set(expected_fields)
        if extra_fields:
            print(f"\nℹ️  Extra fields: {', '.join(extra_fields)}")
        
        print(f"\n✓ Schema is correct")
        return True
        
    except Exception as e:
        logger.error(f"Failed to check collection {collection_name}: {e}")
        return None


def check_all_collections():
    """Check all knowledgebase collections."""
    try:
        # Connect to Milvus
        connections.connect(
            alias="check",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        db = SessionLocal()
        try:
            # Get all knowledgebases
            knowledgebases = db.query(Knowledgebase).all()
            
            print(f"\n{'='*60}")
            print(f"Checking {len(knowledgebases)} knowledgebase collections")
            print(f"{'='*60}")
            
            results = {}
            for kb in knowledgebases:
                result = check_collection_schema(kb.milvus_collection_name)
                results[kb.name] = result
            
            # Summary
            print(f"\n{'='*60}")
            print("SUMMARY")
            print(f"{'='*60}")
            
            correct = sum(1 for v in results.values() if v is True)
            incorrect = sum(1 for v in results.values() if v is False)
            missing = sum(1 for v in results.values() if v is None)
            
            print(f"✓ Correct schema: {correct}")
            print(f"⚠️  Incorrect schema: {incorrect}")
            print(f"❌ Missing collections: {missing}")
            
            if incorrect > 0:
                print(f"\n⚠️  {incorrect} collection(s) need migration!")
                print("Run one of these scripts:")
                print("  - migrate_milvus_schema.py (preserves data)")
                print("  - recreate_milvus_collections.py (deletes data)")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to check collections: {e}", exc_info=True)
    finally:
        connections.disconnect(alias="check")


if __name__ == "__main__":
    check_all_collections()
