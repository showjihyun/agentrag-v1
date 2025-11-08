"""
Quick script to reset Milvus collection with correct schema.

This will drop the existing collection and recreate it with the proper 12-field schema.
"""

import asyncio
from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType
from backend.config import settings
from backend.services.system_config_service import SystemConfigService

async def reset_milvus():
    """Reset Milvus collection with correct schema."""
    try:
        # Connect to Milvus
        print(f"Connecting to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}...")
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        collection_name = settings.MILVUS_COLLECTION_NAME
        
        # Drop existing collection
        if utility.has_collection(collection_name):
            print(f"Dropping existing collection: {collection_name}")
            utility.drop_collection(collection_name)
        
        # Get embedding dimension from system config
        embedding_info = await SystemConfigService.get_embedding_info()
        embedding_dim = embedding_info['dimension']
        model_name = embedding_info['model_name']
        
        print(f"Creating collection with model: {model_name}, dimension: {embedding_dim}")
        
        # Create schema with 12 fields (matching insert_embeddings)
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=255),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="document_name", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="file_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="upload_date", dtype=DataType.INT64),
            FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="creation_date", dtype=DataType.INT64),
            FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="keywords", dtype=DataType.VARCHAR, max_length=1000),
        ]
        schema = CollectionSchema(fields=fields, description="Document embeddings with metadata")
        
        # Create collection
        collection = Collection(name=collection_name, schema=schema)
        print(f"✓ Created collection: {collection_name}")
        
        # Create index
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 200}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        print(f"✓ Created index with COSINE metric")
        
        print("\n✓ Milvus collection reset successfully!")
        print(f"  Collection: {collection_name}")
        print(f"  Fields: 12 (id, document_id, text, embedding, chunk_index, document_name,")
        print(f"              file_type, upload_date, author, creation_date, language, keywords)")
        print(f"  Embedding dimension: {embedding_dim}")
        
        # Disconnect
        connections.disconnect("default")
        
    except Exception as e:
        print(f"\n✗ Error resetting Milvus: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reset_milvus())
