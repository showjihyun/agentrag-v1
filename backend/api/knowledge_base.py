"""
Knowledge Base API endpoints.

Provides REST API for knowledge base operations including search,
document management, and collection information.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field

from backend.core.knowledge_base import (
    get_search_service,
    get_milvus_connector,
    get_document_workflow,
    get_embedding_workflow,
)
from backend.core.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge-base"])


# Request/Response Models
class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., description="Search query text")
    top_k: int = Field(5, ge=1, le=100, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    ranking_method: str = Field("score", description="Ranking method")
    include_metadata: bool = Field(True, description="Include metadata in results")


class SearchResponse(BaseModel):
    """Search response model."""

    results: List[Dict[str, Any]]
    count: int
    query: str


class CollectionInfo(BaseModel):
    """Collection information model."""

    name: str
    num_entities: int
    loaded: bool


class CollectionsResponse(BaseModel):
    """Collections response model."""

    collections: List[CollectionInfo]


class DocumentInfo(BaseModel):
    """Document information model."""

    document_id: str
    document_name: str
    file_type: str
    chunk_count: int
    author: Optional[str] = None
    language: Optional[str] = None
    upload_date: Optional[int] = None


class DocumentsResponse(BaseModel):
    """Documents response model."""

    documents: List[DocumentInfo]
    total: int


class UploadResponse(BaseModel):
    """Upload response model."""

    document_id: str
    document_name: str
    chunks_inserted: int
    success: bool


# Endpoints
@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(
    request: SearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Search knowledge base using semantic similarity.

    Args:
        request: Search request with query and filters
        current_user: Current authenticated user

    Returns:
        Search results with metadata
    """
    try:
        search_service = get_search_service()

        # Perform search
        if request.ranking_method in ["recency", "hybrid"]:
            results = await search_service.search_with_ranking(
                query=request.query,
                top_k=request.top_k,
                filters=request.filters,
                ranking_method=request.ranking_method,
            )
        else:
            results = await search_service.search(
                query=request.query,
                top_k=request.top_k,
                filters=request.filters,
                include_metadata=request.include_metadata,
            )

        return SearchResponse(
            results=results,
            count=len(results),
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/collections", response_model=CollectionsResponse)
async def get_collections(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get available Milvus collections.

    Args:
        current_user: Current authenticated user

    Returns:
        List of available collections
    """
    try:
        milvus_connector = get_milvus_connector()

        # Ensure connected
        if not milvus_connector._connected:
            milvus_connector.connect()

        # Get collection stats
        stats = milvus_connector.get_collection_stats()

        # Return as list (currently only one collection)
        collections = [
            CollectionInfo(
                name=stats["collection_name"],
                num_entities=stats.get("num_entities", 0),
                loaded=stats.get("loaded", False),
            )
        ]

        return CollectionsResponse(collections=collections)

    except Exception as e:
        logger.error(f"Failed to get collections: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get collections: {str(e)}"
        )


@router.get("/documents", response_model=DocumentsResponse)
async def get_documents(
    limit: int = 100,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get list of documents in knowledge base.

    Args:
        limit: Maximum number of documents to return
        offset: Offset for pagination
        current_user: Current authenticated user

    Returns:
        List of documents with metadata
    """
    try:
        milvus_connector = get_milvus_connector()

        # Ensure connected
        if not milvus_connector._connected:
            milvus_connector.connect()

        collection = milvus_connector.get_collection()

        # Query for unique documents
        # Note: This is a simplified implementation
        # In production, you might want to maintain a separate documents table
        results = collection.query(
            expr="",  # Get all
            output_fields=[
                "document_id",
                "document_name",
                "file_type",
                "author",
                "language",
                "upload_date",
            ],
            limit=limit,
            offset=offset,
        )

        # Group by document_id to get unique documents
        documents_dict: Dict[str, DocumentInfo] = {}

        for result in results:
            doc_id = result.get("document_id")
            if doc_id and doc_id not in documents_dict:
                documents_dict[doc_id] = DocumentInfo(
                    document_id=doc_id,
                    document_name=result.get("document_name", "Unknown"),
                    file_type=result.get("file_type", "unknown"),
                    chunk_count=0,  # Will be counted below
                    author=result.get("author"),
                    language=result.get("language"),
                    upload_date=result.get("upload_date"),
                )

        # Count chunks for each document
        for doc_id in documents_dict:
            chunk_results = collection.query(
                expr=f'document_id == "{doc_id}"',
                output_fields=["id"],
                limit=10000,
            )
            documents_dict[doc_id].chunk_count = len(chunk_results)

        documents = list(documents_dict.values())

        return DocumentsResponse(
            documents=documents,
            total=len(documents),
        )

    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get documents: {str(e)}"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    author: Optional[str] = None,
    keywords: Optional[str] = None,
    language: str = "en",
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Upload a document to the knowledge base.

    Args:
        file: File to upload
        author: Document author
        keywords: Comma-separated keywords
        language: Document language
        current_user: Current authenticated user

    Returns:
        Upload result with document ID and chunk count
    """
    try:
        # Read file content
        file_content = await file.read()

        # Build metadata
        metadata = {
            "author": author or "",
            "keywords": keywords or "",
            "language": language,
        }

        # Process document
        document_workflow = get_document_workflow()
        document = await document_workflow.process_document(
            file_content=file_content,
            filename=file.filename or "unknown",
            metadata=metadata,
        )

        # Generate embeddings and store
        embedding_workflow = get_embedding_workflow()
        result = await embedding_workflow.process_and_store_document(document)

        return UploadResponse(
            document_id=result["document_id"],
            document_name=result["document_name"],
            chunks_inserted=result["chunks_inserted"],
            success=True,
        )

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete a document from the knowledge base.

    Args:
        document_id: Document ID to delete
        current_user: Current authenticated user

    Returns:
        Deletion result
    """
    try:
        milvus_connector = get_milvus_connector()

        # Ensure connected
        if not milvus_connector._connected:
            milvus_connector.connect()

        collection = milvus_connector.get_collection()

        # Delete all chunks for this document
        expr = f'document_id == "{document_id}"'
        collection.delete(expr)

        logger.info(f"Deleted document: {document_id}")

        return {"success": True, "document_id": document_id}

    except Exception as e:
        logger.error(f"Delete failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/stats")
async def get_knowledge_base_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get knowledge base statistics.

    Args:
        current_user: Current authenticated user

    Returns:
        Knowledge base statistics
    """
    try:
        milvus_connector = get_milvus_connector()

        # Ensure connected
        if not milvus_connector._connected:
            milvus_connector.connect()

        stats = milvus_connector.get_collection_stats()

        # Get embedding info
        embedding_workflow = get_embedding_workflow()
        embedding_info = embedding_workflow.get_embedding_info()

        return {
            "collection": stats,
            "embedding_model": embedding_info,
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
