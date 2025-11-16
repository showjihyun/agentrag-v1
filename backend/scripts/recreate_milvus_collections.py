"""
Script to drop and recreate Milvus collections with updated schema.

WARNING: This will DELETE ALL DATA in the collections!
Use this only if you don't need to preserve existing data.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymilvus import connections, utility
from backend.config import settings
from backend.services.milvus import MilvusManager
from backend.db.session import SessionLocal
from backend.db.models.agent_builder import Knowledgebase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def recreate_collection(collection_name: str, embedding_dim: int = 384):
    """
    Drop and recreate a collection with the new schema.
    
    Args:
        collection_name: Name of the collection
        embedding_dim: Embedding dimension
    """
    try:
        # Connect to Milvus
        connections.connect(
            alias="recreate",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # Drop if exists
        if utility.has_collection(collection_name, using="recreate"):
            logger.info(f"Dropping collection: {collection_name}")
            utility.drop_collection(collection_name, using="recreate")
        
        # Create new collection
        logger.info(f"Creating collection: {collection_name}")
        milvus_manager = MilvusManager(
            collection_name=collection_name,
            embedding_dim=embedding_dim
        )
        milvus_manager.connect()
        milvus_manager.create_collection()
        
        logger.info(f"✓ Successfully recreated collection: {collection_name}")
        
    except Exception as e:
        logger.error(f"Failed to recreate collection {collection_name}: {e}")
        raise
    finally:
        connections.disconnect(alias="recreate")


def recreate_all_collections():
    """Recreate all knowledgebase collections."""
    db = SessionLocal()
    try:
        # Get all knowledgebases
        knowledgebases = db.query(Knowledgebase).all()
        logger.info(f"Found {len(knowledgebases)} knowledgebase collections")
        
        for kb in knowledgebases:
            logger.info(f"\nRecreating collection for: {kb.name}")
            logger.info(f"  Collection: {kb.milvus_collection_name}")
            
            try:
                recreate_collection(
                    collection_name=kb.milvus_collection_name,
                    embedding_dim=384
                )
            except Exception as e:
                logger.error(f"Failed to recreate {kb.name}: {e}")
                continue
        
        logger.info("\n" + "="*60)
        logger.info("All collections recreated successfully!")
        logger.info("="*60)
        
    finally:
        db.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Milvus Collection Recreate Script                   ║
║                                                              ║
║  ⚠️  WARNING: THIS WILL DELETE ALL DATA! ⚠️                  ║
║                                                              ║
║  This script will drop and recreate all Milvus collections  ║
║  with the updated schema that includes 'knowledgebase_id'.  ║
║                                                              ║
║  All existing embeddings and documents will be LOST!        ║
║  You will need to re-upload your documents.                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    response = input("Are you SURE you want to delete all data? (type 'DELETE' to confirm): ")
    if response != "DELETE":
        print("Operation cancelled.")
        sys.exit(0)
    
    recreate_all_collections()
