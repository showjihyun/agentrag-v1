"""Agent Builder API endpoints for knowledgebase management.

한글/영어 이중 언어 지원:
- 한글 형태소 분석 기반 검색
- 하이브리드 검색 (Vector + BM25)
- 사용자별 개인화 설정
"""

import logging
from typing import List, Optional, Dict, Any

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
            kg_enabled=getattr(kb, 'kg_enabled', False),
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
        
        # Calculate document count and total size
        from backend.db.models.document import Document
        
        # kb.documents are KnowledgebaseDocument objects (association table)
        # We need to get the actual Document objects
        document_count = len(kb.documents) if kb.documents else 0
        
        # Get actual Document objects through the association
        total_size = 0
        if kb.documents:
            document_ids = [kb_doc.document_id for kb_doc in kb.documents]
            documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
            total_size = sum(doc.file_size_bytes for doc in documents if doc.file_size_bytes)
        
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
            kg_enabled=getattr(kb, 'kg_enabled', False),
            document_count=document_count,
            total_size=total_size,
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
        
        # Calculate document count and total size
        from backend.db.models.document import Document
        
        # updated_kb.documents are KnowledgebaseDocument objects (association table)
        document_count = len(updated_kb.documents) if updated_kb.documents else 0
        
        # Get actual Document objects through the association
        total_size = 0
        if updated_kb.documents:
            document_ids = [kb_doc.document_id for kb_doc in updated_kb.documents]
            documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
            total_size = sum(doc.file_size_bytes for doc in documents if doc.file_size_bytes)
        
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
            kg_enabled=getattr(updated_kb, 'kg_enabled', False),
            document_count=document_count,
            total_size=total_size,
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
                    kg_enabled=getattr(kb, 'kg_enabled', False),
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
    description="Search documents in a knowledgebase using hybrid search (Vector + BM25).",
)
async def search_knowledgebase(
    kb_id: str,
    query: str = Query(..., description="Search query (한글/영어 지원)"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    search_mode: str = Query(
        "hybrid",
        description="Search mode: 'vector' (semantic), 'keyword' (BM25), 'hybrid' (both)"
    ),
    expand_query: bool = Query(
        True,
        description="Expand query with synonyms (동의어 확장)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search knowledgebase with Korean/English bilingual support.
    
    한글/영어 이중 언어 검색 지원:
    - 한글 형태소 분석 기반 토큰화
    - 하이브리드 검색 (Vector + BM25)
    - 쿼리 확장 (동의어, 관련어)
    
    **Requirements:** 31.4
    
    **Path Parameters:**
    - kb_id: Knowledgebase UUID
    
    **Query Parameters:**
    - query: Search query (required, 한글/영어 지원)
    - top_k: Number of results (default: 10, max: 100)
    - search_mode: 'vector', 'keyword', or 'hybrid' (default: hybrid)
    - expand_query: Whether to expand query with synonyms (default: true)
    
    **Returns:**
    - Search results with relevance scores and source information
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access)
    - 404: Knowledgebase not found
    - 500: Internal server error
    """
    try:
        # Validate search_mode
        valid_modes = ["vector", "keyword", "hybrid"]
        if search_mode not in valid_modes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid search_mode. Must be one of: {valid_modes}"
            )
        
        logger.info(
            f"Searching knowledgebase {kb_id} with query: {query[:50]} "
            f"(mode={search_mode}, expand={expand_query})"
        )
        
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
        
        # Search knowledgebase with Korean/English support
        results = await kb_service.search_knowledgebase(
            kb_id=kb_id,
            query=query,
            top_k=top_k,
            search_mode=search_mode,
            expand_query=expand_query
        )
        
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


# ============================================================================
# User Settings Endpoints (사용자 개인화 설정)
# ============================================================================

@router.get(
    "/settings/user",
    summary="Get user knowledgebase settings",
    description="Get user's personalized knowledgebase settings (한글/영어 설정 포함).",
)
async def get_user_knowledgebase_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's knowledgebase settings.
    
    사용자별 개인화 설정:
    - 선호 언어 (한글/영어/자동)
    - 기본 검색 모드 (vector/keyword/hybrid)
    - 청킹 설정
    - 검색 가중치 설정
    
    **Returns:**
    - User settings object
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        from backend.services.agent_builder.knowledgebase_user_settings import (
            get_knowledgebase_user_settings_service
        )
        
        settings_service = get_knowledgebase_user_settings_service(db)
        settings = settings_service.get_user_settings(str(current_user.id))
        
        return settings.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to get user settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user settings"
        )


@router.put(
    "/settings/user",
    summary="Update user knowledgebase settings",
    description="Update user's personalized knowledgebase settings.",
)
async def update_user_knowledgebase_settings(
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user's knowledgebase settings.
    
    **Request Body:**
    - preferred_language: "ko", "en", or "auto"
    - default_search_mode: "vector", "keyword", or "hybrid"
    - default_top_k: 1-100
    - expand_query_by_default: boolean
    - min_score_threshold: 0.0-1.0
    - default_chunk_size: 100-2000
    - default_chunk_overlap: 0-500
    - vector_weight: 0.0-1.0
    - bm25_weight: 0.0-1.0
    - enable_reranking: boolean
    - embedding_model: string
    
    **Returns:**
    - Updated settings object
    
    **Errors:**
    - 400: Invalid settings
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        from backend.services.agent_builder.knowledgebase_user_settings import (
            get_knowledgebase_user_settings_service,
            KnowledgebaseUserSettings
        )
        
        settings_service = get_knowledgebase_user_settings_service(db)
        
        # Validate settings
        is_valid, error_msg = settings_service.validate_settings(settings)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Get current settings and merge
        current_settings = settings_service.get_user_settings(str(current_user.id))
        current_dict = current_settings.to_dict()
        current_dict.update(settings)
        
        # Create new settings object
        new_settings = KnowledgebaseUserSettings.from_dict(current_dict)
        
        # Update
        updated_settings = settings_service.update_user_settings(
            str(current_user.id),
            new_settings
        )
        
        logger.info(f"Updated knowledgebase settings for user {current_user.id}")
        
        return updated_settings.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings"
        )


@router.post(
    "/settings/user/reset",
    summary="Reset user knowledgebase settings",
    description="Reset user's knowledgebase settings to defaults.",
)
async def reset_user_knowledgebase_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reset user's knowledgebase settings to defaults.
    
    **Returns:**
    - Default settings object
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        from backend.services.agent_builder.knowledgebase_user_settings import (
            get_knowledgebase_user_settings_service
        )
        
        settings_service = get_knowledgebase_user_settings_service(db)
        default_settings = settings_service.reset_user_settings(str(current_user.id))
        
        logger.info(f"Reset knowledgebase settings for user {current_user.id}")
        
        return default_settings.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to reset user settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset user settings"
        )


# ============================================================================
# Language Detection & Analysis Endpoints
# ============================================================================

@router.post(
    "/analyze/text",
    summary="Analyze text for language and keywords",
    description="Analyze text to detect language and extract keywords (한글/영어 지원).",
)
async def analyze_text(
    text: str = Query(..., description="Text to analyze"),
    extract_keywords: bool = Query(True, description="Extract keywords"),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze text for language detection and keyword extraction.
    
    한글/영어 텍스트 분석:
    - 언어 감지
    - 키워드 추출
    - 토큰화
    
    **Query Parameters:**
    - text: Text to analyze
    - extract_keywords: Whether to extract keywords (default: true)
    
    **Returns:**
    - Analysis results including language, tokens, keywords
    
    **Errors:**
    - 400: Invalid text
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        if not text or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        from backend.services.agent_builder.knowledgebase_korean_processor import (
            get_knowledgebase_korean_processor
        )
        
        processor = get_knowledgebase_korean_processor()
        
        # Detect language
        language = processor.detect_language(text)
        
        # Tokenize
        tokens, _ = processor.tokenize(text, extract_nouns=True)
        
        # Extract keywords
        keywords = []
        if extract_keywords:
            keyword_scores = processor.extract_keywords(text, top_k=10)
            keywords = [{"keyword": kw, "score": score} for kw, score in keyword_scores]
        
        # Preprocess
        processed_text = processor.preprocess_text(text)
        
        return {
            "original_text": text,
            "processed_text": processed_text,
            "language": language.value,
            "tokens": tokens,
            "token_count": len(tokens),
            "keywords": keywords,
            "character_count": len(text),
            "word_count": len(text.split())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze text: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze text"
        )


@router.post(
    "/analyze/query",
    summary="Analyze and expand search query",
    description="Analyze search query and generate expanded queries (쿼리 확장).",
)
async def analyze_query(
    query: str = Query(..., description="Search query to analyze"),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze and expand search query.
    
    쿼리 분석 및 확장:
    - 언어 감지
    - 동의어 확장
    - 관련어 추가
    
    **Query Parameters:**
    - query: Search query to analyze
    
    **Returns:**
    - Original query, expanded queries, language info
    
    **Errors:**
    - 400: Invalid query
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        if not query or not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        from backend.services.agent_builder.knowledgebase_korean_processor import (
            get_knowledgebase_korean_processor
        )
        
        processor = get_knowledgebase_korean_processor()
        
        # Detect language
        language = processor.detect_language(query)
        
        # Preprocess
        processed_query = processor.preprocess_query(query)
        
        # Expand query
        expanded_queries = processor.expand_query(processed_query)
        
        # Tokenize
        tokens, _ = processor.tokenize(processed_query, extract_nouns=True)
        
        return {
            "original_query": query,
            "processed_query": processed_query,
            "language": language.value,
            "tokens": tokens,
            "expanded_queries": expanded_queries,
            "expansion_count": len(expanded_queries)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze query"
        )
