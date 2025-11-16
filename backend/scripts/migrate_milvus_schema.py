"""
Migration script to add knowledgebase_id field to existing Milvus collections.

This script handles the schema migration by:
1. Exporting existing data from old collection
2. Dropping the old collection
3. Creating new collection with updated schema
4. Re-inserting data with knowledgebase_id field
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymilvus import connections, Collection, utility
from backend.config import settings
from backend.services.milvus import MilvusManager
from backend.db.session import SessionLocal
from backend.db.models.agent_builder import Knowledgebase, KnowledgebaseDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_collection(
    collection_name: str,
    knowledgebase_id: str,
    embedding_dim: int = 384
):
    """
    Migrate a single collection to the new schema.
    
    Args:
        collection_name: Name of the Milvus collection
        knowledgebase_id: ID of the knowledgebase (for the new field)
        embedding_dim: Embedding dimension
    """
    try:
        # Connect to Milvus
        connections.connect(
            alias="migration",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # Check if collection exists
        if not utility.has_collection(collection_name, using="migration"):
            logger.warning(f"Collection {collection_name} does not exist, skipping")
            return
        
        # Load existing collection
        old_collection = Collection(name=collection_name, using="migration")
        old_collection.load()
        
        # Get all data from old collection
        logger.info(f"Exporting data from {collection_name}...")
        num_entities = old_collection.num_entities
        logger.info(f"Found {num_entities} entities")
        
        if num_entities == 0:
            logger.info("Collection is empty, just recreating schema")
            utility.drop_collection(collection_name, using="migration")
            
            # Create new collection with updated schema
            milvus_manager = MilvusManager(
                collection_name=collection_name,
                embedding_dim=embedding_dim
            )
            milvus_manager.connect()
            milvus_manager.create_collection()
            logger.info(f"Recreated empty collection {collection_name}")
            return
        
        # Query all data (in batches to avoid memory issues)
        batch_size = 1000
        all_data = []
        
        for offset in range(0, num_entities, batch_size):
            limit = min(batch_size, num_entities - offset)
            logger.info(f"Fetching batch {offset}-{offset+limit}...")
            
            results = old_collection.query(
                expr="",
                output_fields=[
                    "id", "document_id", "text", "embedding",
                    "chunk_index", "document_name", "file_type",
                    "upload_date", "author", "creation_date",
                    "language", "keywords"
                ],
                offset=offset,
                limit=limit
            )
            all_data.extend(results)
        
        logger.info(f"Exported {len(all_data)} entities")
        
        # Drop old collection
        logger.info(f"Dropping old collection {collection_name}...")
        utility.drop_collection(collection_name, using="migration")
        
        # Create new collection with updated schema
        logger.info(f"Creating new collection {collection_name} with updated schema...")
        milvus_manager = MilvusManager(
            collection_name=collection_name,
            embedding_dim=embedding_dim
        )
        milvus_manager.connect()
        milvus_manager.create_collection()
        
        # Re-insert data with knowledgebase_id field
        logger.info(f"Re-inserting {len(all_data)} entities with knowledgebase_id...")
        
        # Prepare data for insertion
        embeddings = []
        metadata_list = []
        
        for entity in all_data:
            embeddings.append(entity["embedding"])
            
            # Add knowledgebase_id to metadata
            metadata = {
                "id": entity["id"],
                "document_id": entity["document_id"],
                "knowledgebase_id": knowledgebase_id,  # NEW FIELD
                "text": entity["text"],
                "chunk_index": entity["chunk_index"],
                "document_name": entity["document_name"],
                "file_type": entity["file_type"],
                "upload_date": entity["upload_date"],
                "author": entity.get("author", ""),
                "creation_date": entity.get("creation_date", 0),
                "language": entity.get("language", ""),
                "keywords": entity.get("keywords", "")
            }
            metadata_list.append(metadata)
        
        # Insert in batches
        batch_size = 100
        for i in range(0, len(embeddings), batch_size):
            batch_embeddings = embeddings[i:i + batch_size]
            batch_metadata = metadata_list[i:i + batch_size]
            
            await milvus_manager.insert_embeddings(
                embeddings=batch_embeddings,
                metadata=batch_metadata
            )
            logger.info(f"Inserted batch {i//batch_size + 1}/{(len(embeddings) + batch_size - 1)//batch_size}")
        
        logger.info(f"✓ Successfully migrated collection {collection_name}")
        
    except Exception as e:
        logger.error(f"Failed to migrate collection {collection_name}: {e}", exc_info=True)
        raise
    finally:
        connections.disconnect(alias="migration")


async def migrate_all_knowledgebases():
    """Migrate all knowledgebase collections."""
    db = SessionLocal()
    try:
        # Get all knowledgebases
        knowledgebases = db.query(Knowledgebase).all()
        logger.info(f"Found {len(knowledgebases)} knowledgebases to migrate")
        
        for kb in knowledgebases:
            logger.info(f"\n{'='*60}")
            logger.info(f"Migrating knowledgebase: {kb.name} (ID: {kb.id})")
            logger.info(f"Collection: {kb.milvus_collection_name}")
            logger.info(f"{'='*60}")
            
            try:
                await migrate_collection(
                    collection_name=kb.milvus_collection_name,
                    knowledgebase_id=kb.id,
                    embedding_dim=384  # Default dimension
                )
            except Exception as e:
                logger.error(f"Failed to migrate {kb.name}: {e}")
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info("Migration completed!")
        logger.info(f"{'='*60}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Milvus Schema Migration Script                       ║
║                                                              ║
║  This script will migrate existing Milvus collections       ║
║  to add the 'knowledgebase_id' field.                       ║
║                                                              ║
║  WARNING: This will temporarily drop and recreate           ║
║           collections. Ensure you have backups!             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() != "yes":
        print("Migration cancelled.")
        sys.exit(0)
    
    asyncio.run(migrate_all_knowledgebases())
