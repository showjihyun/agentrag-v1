"""
Milvus administration endpoints for schema management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.agent_builder import Knowledgebase
from backend.services.milvus import MilvusManager
from pymilvus import connections, Collection, utility
from backend.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/collections/check")
async def check_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check all knowledgebase collections for schema issues.
    
    Returns:
        List of collections with their schema status
    """
    try:
        # Connect to Milvus
        connections.connect(
            alias="admin_check",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # Get all knowledgebases for current user
        knowledgebases = db.query(Knowledgebase).filter(
            Knowledgebase.user_id == current_user.id
        ).all()
        
        results = []
        expected_fields = [
            "id", "document_id", "knowledgebase_id", "text", "embedding",
            "chunk_index", "document_name", "file_type", "upload_date",
            "author", "creation_date", "language", "keywords"
        ]
        
        for kb in knowledgebases:
            try:
                if not utility.has_collection(kb.milvus_collection_name, using="admin_check"):
                    results.append({
                        "knowledgebase_id": kb.id,
                        "knowledgebase_name": kb.name,
                        "collection_name": kb.milvus_collection_name,
                        "status": "missing",
                        "message": "Collection does not exist",
                        "needs_migration": False
                    })
                    continue
                
                collection = Collection(name=kb.milvus_collection_name, using="admin_check")
                actual_fields = [field.name for field in collection.schema.fields]
                
                missing_fields = set(expected_fields) - set(actual_fields)
                has_knowledgebase_id = "knowledgebase_id" in actual_fields
                
                if missing_fields:
                    results.append({
                        "knowledgebase_id": kb.id,
                        "knowledgebase_name": kb.name,
                        "collection_name": kb.milvus_collection_name,
                        "status": "incorrect",
                        "message": f"Missing fields: {', '.join(missing_fields)}",
                        "needs_migration": True,
                        "num_entities": collection.num_entities
                    })
                else:
                    results.append({
                        "knowledgebase_id": kb.id,
                        "knowledgebase_name": kb.name,
                        "collection_name": kb.milvus_collection_name,
                        "status": "correct",
                        "message": "Schema is correct",
                        "needs_migration": False,
                        "num_entities": collection.num_entities
                    })
                    
            except Exception as e:
                logger.error(f"Error checking collection {kb.milvus_collection_name}: {e}")
                results.append({
                    "knowledgebase_id": kb.id,
                    "knowledgebase_name": kb.name,
                    "collection_name": kb.milvus_collection_name,
                    "status": "error",
                    "message": str(e),
                    "needs_migration": False
                })
        
        connections.disconnect(alias="admin_check")
        
        # Summary
        total = len(results)
        correct = sum(1 for r in results if r["status"] == "correct")
        incorrect = sum(1 for r in results if r["status"] == "incorrect")
        missing = sum(1 for r in results if r["status"] == "missing")
        
        return {
            "collections": results,
            "summary": {
                "total": total,
                "correct": correct,
                "incorrect": incorrect,
                "missing": missing,
                "needs_action": incorrect + missing
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to check collections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{kb_id}/recreate")
async def recreate_collection(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recreate a collection with the correct schema.
    
    WARNING: This will delete all data in the collection!
    
    Args:
        kb_id: Knowledgebase ID
        
    Returns:
        Success message
    """
    try:
        # Get knowledgebase
        kb = db.query(Knowledgebase).filter(
            Knowledgebase.id == kb_id,
            Knowledgebase.user_id == current_user.id
        ).first()
        
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledgebase not found")
        
        # Connect to Milvus
        connections.connect(
            alias="admin_recreate",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # Drop if exists
        if utility.has_collection(kb.milvus_collection_name, using="admin_recreate"):
            logger.info(f"Dropping collection: {kb.milvus_collection_name}")
            utility.drop_collection(kb.milvus_collection_name, using="admin_recreate")
        
        connections.disconnect(alias="admin_recreate")
        
        # Create new collection
        logger.info(f"Creating new collection: {kb.milvus_collection_name}")
        milvus_manager = MilvusManager(
            collection_name=kb.milvus_collection_name,
            embedding_dim=384
        )
        milvus_manager.connect()
        milvus_manager.create_collection()
        milvus_manager.disconnect()
        
        logger.info(f"Successfully recreated collection for knowledgebase {kb_id}")
        
        return {
            "success": True,
            "message": f"Collection recreated successfully. You can now upload documents to '{kb.name}'.",
            "knowledgebase_id": kb_id,
            "collection_name": kb.milvus_collection_name
        }
        
    except Exception as e:
        logger.error(f"Failed to recreate collection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/recreate-all")
async def recreate_all_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recreate all collections for the current user with the correct schema.
    
    WARNING: This will delete all data in all collections!
    
    Returns:
        Summary of recreated collections
    """
    try:
        # Get all knowledgebases for current user
        knowledgebases = db.query(Knowledgebase).filter(
            Knowledgebase.user_id == current_user.id
        ).all()
        
        if not knowledgebases:
            return {
                "success": True,
                "message": "No knowledgebases found",
                "recreated": 0,
                "failed": 0,
                "results": []
            }
        
        # Connect to Milvus
        connections.connect(
            alias="admin_recreate_all",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        results = []
        recreated_count = 0
        failed_count = 0
        
        for kb in knowledgebases:
            try:
                # Drop if exists
                if utility.has_collection(kb.milvus_collection_name, using="admin_recreate_all"):
                    utility.drop_collection(kb.milvus_collection_name, using="admin_recreate_all")
                
                # Create new collection
                milvus_manager = MilvusManager(
                    collection_name=kb.milvus_collection_name,
                    embedding_dim=384
                )
                milvus_manager.connect()
                milvus_manager.create_collection()
                milvus_manager.disconnect()
                
                results.append({
                    "knowledgebase_id": kb.id,
                    "knowledgebase_name": kb.name,
                    "collection_name": kb.milvus_collection_name,
                    "status": "success"
                })
                recreated_count += 1
                logger.info(f"Recreated collection for {kb.name}")
                
            except Exception as e:
                results.append({
                    "knowledgebase_id": kb.id,
                    "knowledgebase_name": kb.name,
                    "collection_name": kb.milvus_collection_name,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
                logger.error(f"Failed to recreate collection for {kb.name}: {e}")
        
        connections.disconnect(alias="admin_recreate_all")
        
        return {
            "success": True,
            "message": f"Recreated {recreated_count} collections, {failed_count} failed",
            "recreated": recreated_count,
            "failed": failed_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to recreate collections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
