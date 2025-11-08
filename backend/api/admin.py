"""
Admin API

Provides administrative endpoints for system management.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import logging

from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType
from backend.config import settings
from backend.core.milvus_pool import get_milvus_pool
from backend.services.system_config_service import SystemConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset-milvus")
async def reset_milvus():
    """
    Reset Milvus database by dropping and recreating the collection.
    
    WARNING: This will delete all vector data!
    
    Returns:
        Success message
    """
    try:
        # Get Milvus pool with settings
        pool = get_milvus_pool(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            pool_size=10
        )
        
        # Initialize pool if needed
        await pool.initialize()
        
        # Get collection name from settings
        collection_name = settings.MILVUS_COLLECTION_NAME
        
        # Use connection from pool
        async with pool.acquire() as alias:
            # Drop collection if exists
            if utility.has_collection(collection_name, using=alias):
                utility.drop_collection(collection_name, using=alias)
                logger.info(f"Dropped collection: {collection_name}")
            
            # Get embedding dimension from system config
            embedding_info = await SystemConfigService.get_embedding_info()
            embedding_dim = embedding_info['dimension']
            model_name = embedding_info['model_name']
            
            logger.info(f"Creating collection with model: {model_name}, dimension: {embedding_dim}")
            
            # Create schema matching the existing collection structure (12 fields)
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
            collection = Collection(name=collection_name, schema=schema, using=alias)
            logger.info(f"Created new collection: {collection_name}")
            
            # Create index
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            logger.info(f"Created index for collection: {collection_name}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Milvus database has been reset successfully",
            "collection_name": collection_name,
        })
        
    except Exception as e:
        logger.error(f"Error resetting Milvus: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset Milvus: {str(e)}"
        )


@router.post("/delete-all-files")
async def delete_all_files():
    """
    Delete all uploaded files from local storage.
    
    WARNING: This will delete all uploaded documents!
    
    Returns:
        Success message with count of deleted files
    """
    try:
        upload_dir = Path(settings.LOCAL_STORAGE_PATH)
        
        if not upload_dir.exists():
            return JSONResponse(content={
                "success": True,
                "message": "No files to delete",
                "deleted_count": 0,
            })
        
        # Count files before deletion
        deleted_count = 0
        deleted_dirs = []
        
        for item in upload_dir.iterdir():
            if item.is_dir():
                # Count files in directory
                file_count = len(list(item.glob("*")))
                deleted_count += file_count
                deleted_dirs.append(item.name)
                
                # Delete directory and all contents
                shutil.rmtree(item)
                logger.info(f"Deleted directory: {item.name} ({file_count} files)")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Deleted {deleted_count} files from {len(deleted_dirs)} directories",
            "deleted_count": deleted_count,
            "deleted_directories": deleted_dirs,
        })
        
    except Exception as e:
        logger.error(f"Error deleting files: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete files: {str(e)}"
        )


@router.post("/reset-all")
async def reset_all():
    """
    Reset both Milvus database and delete all uploaded files.
    
    WARNING: This will delete ALL data!
    
    Returns:
        Combined success message
    """
    try:
        # Reset Milvus
        milvus_result = await reset_milvus()
        milvus_data = milvus_result.body.decode('utf-8')
        
        # Delete files
        files_result = await delete_all_files()
        files_data = files_result.body.decode('utf-8')
        
        import json
        milvus_info = json.loads(milvus_data)
        files_info = json.loads(files_data)
        
        return JSONResponse(content={
            "success": True,
            "message": "System has been completely reset",
            "milvus": milvus_info,
            "files": files_info,
        })
        
    except Exception as e:
        logger.error(f"Error resetting system: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset system: {str(e)}"
        )


@router.get("/stats")
async def get_system_stats():
    """
    Get system statistics.
    
    Returns:
        System statistics including file count and Milvus entity count
    """
    try:
        # Count uploaded files
        upload_dir = Path(settings.LOCAL_STORAGE_PATH)
        file_count = 0
        dir_count = 0
        
        if upload_dir.exists():
            for item in upload_dir.iterdir():
                if item.is_dir():
                    dir_count += 1
                    file_count += len(list(item.glob("*")))
        
        # Get Milvus stats
        pool = get_milvus_pool(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            pool_size=10
        )
        await pool.initialize()
        
        collection_name = settings.MILVUS_COLLECTION_NAME
        entity_count = 0
        
        async with pool.acquire() as alias:
            if utility.has_collection(collection_name, using=alias):
                collection = Collection(collection_name, using=alias)
                entity_count = collection.num_entities
        
        return JSONResponse(content={
            "success": True,
            "files": {
                "total_files": file_count,
                "total_directories": dir_count,
            },
            "milvus": {
                "collection_name": collection_name,
                "entity_count": entity_count,
            },
        })
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system stats: {str(e)}"
        )
