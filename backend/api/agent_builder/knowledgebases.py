"""Agent Builder API endpoints for knowledgebase management."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
from backend.models.agent_builder import (
    KnowledgebaseCreate,
    KnowledgebaseUpdate,
    KnowledgebaseResponse,
    KnowledgebaseListResponse,
    KnowledgebaseDocumentResponse,
    KnowledgebaseSearchRequest,
    KnowledgebaseSearchResponse,
    KnowledgebaseVersionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/knowledgebases",
    tags=["agent-builder-knowledgebases"],
)


@router.post(
    "",
    response_model=KnowledgebaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledgebase",
    description="Create a new knowledgebase with Milvus collection.",
)
async def create_knowledgebase(
    kb_data: KnowledgebaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new knowledgebase.
    
    **Requirements:** 31.1
    
    **Request Body:**
    - name: Knowledgebase name (required)
    - description: Knowledgebase description
    - embedding_model: Embedding model to use
    - chunk_size: Chunk size for document processing
    - chunk_overlap: Chunk overlap size
    
    **Returns:**
    - Knowledgebase object with ID and Milvus collection name
    
    **Errors:**
    - 400: Invalid request data
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Creating knowledgebase for user {current_user.id}: {kb_data.name}")
        
        kb_service = KnowledgebaseService(db)
        kb = kb_service.create_knowledgebase(
            user_id=str(current_user.id),
            kb_data=kb_data
        )
        
        logger.info(f"Knowledgebase created successfully: {kb.id}")
        
        # Convert UUID fields to strings for response
        # Use getattr with defaults for optional fields
        return KnowledgebaseResponse(
            id=str(kb.id),
            user_id=str(kb.user_id),
            name=kb.name,
            description=kb.description,
            milvus_collection_name=kb.milvus_collection_name,
            embedding_model=kb.embedding_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            document_count=getattr(kb, 'document_count', 0),
            total_size=getattr(kb, 'total_size', 0),
            created_at=kb.created_at,
            updated_at=kb.updated_at
        )
        
    except ValueError as e:
        logger.warning(f"Invalid knowledgebase data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create knowledgebase: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create knowledgebase"
        )


@router.get(
    "/{kb_id}",
    response_model=KnowledgebaseResponse,
    summary="Get knowledgebase by ID",
    description="Retrieve a specific knowledgebase by ID.",
)
async def get_knowledgebase(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get knowledgebase by ID.
    
    **Requirements:** 31.1
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    
    **Returns:**
    - Knowledgebase object with full details
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access)
    - 404: Knowledgebase not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Fetching knowledgebase {kb_id} for user {current_user.id}")
        
        kb_service = KnowledgebaseService(db)
        kb = kb_service.get_knowledgebase(kb_id)
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledgebase {kb_id} not found"
            )
        
        # Check permissions (owner only for now)
        if str(kb.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this knowledgebase"
            )
        
        # Convert UUID fields to strings for response
        return KnowledgebaseResponse(
            id=str(kb.id),
            user_id=str(kb.user_id),
            name=kb.name,
            description=kb.description,
            milvus_collection_name=kb.milvus_collection_name,
            embedding_model=kb.embedding_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            document_count=kb.document_count,
            total_size=kb.total_size,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get knowledgebase: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledgebase"
        )


@router.put(
    "/{kb_id}",
    response_model=KnowledgebaseResponse,
    summary="Update knowledgebase",
    description="Update an existing knowledgebase. Requires ownership.",
)
async def update_knowledgebase(
    kb_id: str,
    kb_data: KnowledgebaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update knowledgebase.
    
    **Requirements:** 31.1
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    
    **Request Body:**
    - Fields to update (all optional)
    
    **Returns:**
    - Updated knowledgebase object
    
    **Errors:**
    - 400: Invalid request data
    - 401: Unauthorized
    - 403: Forbidden (not owner)
    - 404: Knowledgebase not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Updating knowledgebase {kb_id} for user {current_user.id}")
        
        kb_service = KnowledgebaseService(db)
        
        # Check ownership
        existing_kb = kb_service.get_knowledgebase(kb_id)
        if not existing_kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledgebase {kb_id} not found"
            )
        
        # Compare as strings to handle both UUID and string types
        if str(existing_kb.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this knowledgebase"
            )
        
        # Update knowledgebase
        updated_kb = kb_service.update_knowledgebase(kb_id, kb_data)
        
        logger.info(f"Knowledgebase updated successfully: {kb_id}")
        
        # Convert UUID fields to strings for response
        return KnowledgebaseResponse(
            id=str(updated_kb.id),
            user_id=str(updated_kb.user_id),
            name=updated_kb.name,
            description=updated_kb.description,
            milvus_collection_name=updated_kb.milvus_collection_name,
            embedding_model=updated_kb.embedding_model,
            chunk_size=updated_kb.chunk_size,
            chunk_overlap=updated_kb.chunk_overlap,
            document_count=updated_kb.document_count,
            total_size=updated_kb.total_size,
            created_at=updated_kb.created_at,
            updated_at=updated_kb.updated_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid knowledgebase data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update knowledgebase: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update knowledgebase"
        )


@router.delete(
    "/{kb_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete knowledgebase",
    description="Delete a knowledgebase and its Milvus collection. Requires ownership.",
)
async def delete_knowledgebase(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete knowledgebase.
    
    **Requirements:** 31.1
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    
    **Returns:**
    - 204 No Content on success
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (not owner)
    - 404: Knowledgebase not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Deleting knowledgebase {kb_id} for user {current_user.id}")
        
        kb_service = KnowledgebaseService(db)
        
        # Check ownership
        existing_kb = kb_service.get_knowledgebase(kb_id)
        if not existing_kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledgebase {kb_id} not found"
            )
        
        # Compare as strings to handle both UUID and string types
        kb_user_id = str(existing_kb.user_id) if existing_kb.user_id else None
        current_user_id = str(current_user.id)
        
        if kb_user_id != current_user_id:
            logger.warning(
                f"Permission denied: KB user_id={kb_user_id}, "
                f"current_user_id={current_user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this knowledgebase"
            )
        
        # Delete knowledgebase
        kb_service.delete_knowledgebase(kb_id)
        
        logger.info(f"Knowledgebase deleted successfully: {kb_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete knowledgebase: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete knowledgebase"
        )


@router.get(
    "",
    response_model=KnowledgebaseListResponse,
    summary="List knowledgebases",
    description="List user's knowledgebases with pagination.",
)
async def list_knowledgebases(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List user's knowledgebases.
    
    **Requirements:** 31.1
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 50, max: 100)
    - search: Search in name and description
    
    **Returns:**
    - List of knowledgebases with pagination metadata
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Listing knowledgebases for user {current_user.id}")
        
        kb_service = KnowledgebaseService(db)
        
        # Build filters
        filters = {"user_id": str(current_user.id)}
        if search:
            filters["search"] = search
        
        # Get knowledgebases
        kbs, total = kb_service.list_knowledgebases(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        # Convert UUID fields to strings for each knowledgebase
        from backend.db.models.document import Document
        
        kb_responses = []
        for kb in kbs:
            # Calculate document count and total size
            # kb.documents are KnowledgebaseDocument objects (association table)
            # We need to get the actual Document objects
            document_count = len(kb.documents) if kb.documents else 0
            
            # Get actual Document objects through the association
            total_size = 0
            if kb.documents:
                document_ids = [kb_doc.document_id for kb_doc in kb.documents]
                documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
                total_size = sum(doc.file_size_bytes for doc in documents if doc.file_size_bytes)
            
            kb_responses.append(
                KnowledgebaseResponse(
                    id=str(kb.id),
                    user_id=str(kb.user_id),
                    name=kb.name,
                    description=kb.description,
                    milvus_collection_name=kb.milvus_collection_name,
                    embedding_model=kb.embedding_model,
                    chunk_size=kb.chunk_size,
                    chunk_overlap=kb.chunk_overlap,
                    document_count=document_count,
                    total_size=total_size,
                    created_at=kb.created_at,
                    updated_at=kb.updated_at
                )
            )
        
        return KnowledgebaseListResponse(
            knowledgebases=kb_responses,
            total=total,
            offset=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list knowledgebases: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list knowledgebases"
        )


@router.post(
    "/{kb_id}/documents",
    response_model=List[KnowledgebaseDocumentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload documents to knowledgebase",
    description="Upload and process documents for a knowledgebase.",
)
async def upload_documents(
    kb_id: str,
    files: List[UploadFile] = File(..., description="Documents to upload"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload documents to knowledgebase.
    
    **Requirements:** 31.2
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    
    **Request:**
    - files: List of document files to upload
    
    **Returns:**
    - List of uploaded document objects
    
    **Errors:**
    - 400: Invalid files or processing error
    - 401: Unauthorized
    - 403: Forbidden (not owner)
    - 404: Knowledgebase not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Uploading {len(files)} documents to knowledgebase {kb_id}")
        
        kb_service = KnowledgebaseService(db)
        
        # Check ownership
        kb = kb_service.get_knowledgebase(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledgebase {kb_id} not found"
            )
        
        if str(kb.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to upload to this knowledgebase"
            )
        
        # Upload documents
        documents = await kb_service.add_documents(kb_id, files)
        
        # Convert to response models
        response_documents = []
        for doc in documents:
            response_documents.append(
                KnowledgebaseDocumentResponse(
                    id=str(doc.id),
                    knowledgebase_id=kb_id,  # Use the kb_id from path parameter
                    filename=doc.filename,
                    file_size=doc.file_size_bytes,  # Document model uses file_size_bytes
                    chunk_count=doc.chunk_count,
                    created_at=doc.uploaded_at  # Document model uses uploaded_at
                )
            )
        
        logger.info(f"Uploaded {len(documents)} documents to knowledgebase {kb_id}")
        return response_documents
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to upload documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload documents"
        )


@router.get(
    "/{kb_id}/search",
    response_model=KnowledgebaseSearchResponse,
    summary="Search knowledgebase",
    description="Search documents in a knowledgebase using hybrid search.",
)
async def search_knowledgebase(
    kb_id: str,
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search knowledgebase.
    
    **Requirements:** 31.4
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    
    **Query Parameters:**
    - query: Search query (required)
    - top_k: Number of results (default: 10, max: 100)
    
    **Returns:**
    - Search results with relevance scores
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access)
    - 404: Knowledgebase not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Searching knowledgebase {kb_id} with query: {query[:50]}")
        
        kb_service = KnowledgebaseService(db)
        
        # Check if knowledgebase exists and user has access
        kb = kb_service.get_knowledgebase(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledgebase {kb_id} not found"
            )
        
        # Check permissions (owner only for now)
        if str(kb.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to search this knowledgebase"
            )
        
        # Search knowledgebase
        results = await kb_service.search_knowledgebase(kb_id, query, top_k)
        
        logger.info(f"Found {len(results)} results in knowledgebase {kb_id}")
        return KnowledgebaseSearchResponse(
            query=query,
            results=results,
            total=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search knowledgebase: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search knowledgebase"
        )


@router.get(
    "/{kb_id}/versions",
    response_model=List[KnowledgebaseVersionResponse],
    summary="Get knowledgebase versions",
    description="Retrieve version history for a knowledgebase.",
)
async def get_knowledgebase_versions(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get knowledgebase version history.
    
    **Requirements:** 35.1, 35.3
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    
    **Returns:**
    - List of knowledgebase versions
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access)
    - 404: Knowledgebase not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Fetching versions for knowledgebase {kb_id}")
        
        kb_service = KnowledgebaseService(db)
        
        # Check if knowledgebase exists and user has access
        kb = kb_service.get_knowledgebase(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledgebase {kb_id} not found"
            )
        
        # Check permissions (owner only for now)
        if str(kb.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this knowledgebase"
            )
        
        # Get versions
        versions = kb_service.get_versions(kb_id)
        
        return versions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get knowledgebase versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledgebase versions"
        )


@router.post(
    "/{kb_id}/rollback",
    response_model=KnowledgebaseResponse,
    summary="Rollback knowledgebase to version",
    description="Rollback knowledgebase to a previous version.",
)
async def rollback_knowledgebase(
    kb_id: str,
    version_id: str = Query(..., description="Version ID to rollback to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Rollback knowledgebase to version.
    
    **Requirements:** 35.4
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    
    **Query Parameters:**
    - version_id: Version UUID to rollback to
    
    **Returns:**
    - Updated knowledgebase object
    
    **Errors:**
    - 400: Invalid version
    - 401: Unauthorized
    - 403: Forbidden (not owner)
    - 404: Knowledgebase or version not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Rolling back knowledgebase {kb_id} to version {version_id}")
        
        kb_service = KnowledgebaseService(db)
        
        # Check ownership
        kb = kb_service.get_knowledgebase(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledgebase {kb_id} not found"
            )
        
        if str(kb.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to rollback this knowledgebase"
            )
        
        # Rollback
        updated_kb = kb_service.rollback_version(kb_id, version_id)
        
        logger.info(f"Knowledgebase rolled back successfully: {kb_id}")
        return updated_kb
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid rollback request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to rollback knowledgebase: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rollback knowledgebase"
        )


@router.get(
    "/{kb_id}/documents/{document_id}/status",
    summary="Get document processing status",
    description="Check the processing status of an uploaded document.",
)
async def get_document_status(
    kb_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get document processing status.
    
    Returns the current processing status of a document including:
    - status: pending, processing, completed, failed
    - progress: 0-100
    - error: error message if failed
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    - document_id: Document UUID
    
    **Returns:**
    - Document status information
    
    **Errors:**
    - 404: Document or knowledgebase not found
    - 403: No permission
    """
    try:
        # Validate document_id format
        if not document_id or document_id == 'undefined':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID"
            )
        
        kb_service = KnowledgebaseService(db)
        
        # Check ownership
        kb = kb_service.get_knowledgebase(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledgebase {kb_id} not found"
            )
        
        if str(kb.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this knowledgebase"
            )
        
        # Get document status
        status_info = kb_service.get_document_status(kb_id, document_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document status"
        )
