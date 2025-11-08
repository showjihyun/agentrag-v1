"""
Vector Search Service for Knowledge Base Integration.

Provides workflow-compatible search interface with metadata filtering,
result ranking, and formatting.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.core.knowledge_base.milvus_connector import get_milvus_connector
from backend.core.knowledge_base.embedding_workflow import get_embedding_workflow

logger = logging.getLogger(__name__)


class SearchService:
    """
    Vector search service for Knowledge Base workflows.
    
    Provides semantic search with metadata filtering and result formatting.
    """

    def __init__(self):
        """Initialize search service."""
        self.milvus_connector = get_milvus_connector()
        self.embedding_workflow = get_embedding_workflow()
        
        logger.info("SearchService initialized")

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using semantic similarity.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"author": "John Doe", "language": "en"})
            include_metadata: Whether to include full metadata in results
            
        Returns:
            List of search results with text, metadata, and scores
            
        Raises:
            RuntimeError: If search fails
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_workflow.generate_embedding(query)
            
            # Ensure Milvus is connected
            if not self.milvus_connector._connected:
                self.milvus_connector.connect()
            
            # Define output fields
            output_fields = [
                "text",
                "document_name",
                "document_id",
                "chunk_index",
                "file_type",
            ]
            
            if include_metadata:
                output_fields.extend([
                    "author",
                    "keywords",
                    "language",
                    "creation_date",
                    "upload_date",
                ])
            
            # Perform search
            results = self.milvus_connector.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters,
                output_fields=output_fields,
            )
            
            # Format results
            formatted_results = self._format_search_results(results, include_metadata)
            
            logger.info(
                f"Search completed: query='{query[:50]}...', "
                f"results={len(formatted_results)}, filters={bool(filters)}"
            )
            
            return formatted_results
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def search_by_metadata(
        self,
        filters: Dict[str, Any],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search documents by metadata only (no semantic search).
        
        Args:
            filters: Metadata filters
            top_k: Maximum number of results
            
        Returns:
            List of matching documents
            
        Raises:
            RuntimeError: If search fails
        """
        try:
            # Ensure Milvus is connected
            if not self.milvus_connector._connected:
                self.milvus_connector.connect()
            
            collection = self.milvus_connector.get_collection()
            
            # Build filter expression
            filter_expr = self.milvus_connector._build_filter_expression(filters)
            
            if not filter_expr:
                raise ValueError("No filters provided for metadata search")
            
            # Query by expression
            results = collection.query(
                expr=filter_expr,
                output_fields=[
                    "text",
                    "document_name",
                    "document_id",
                    "chunk_index",
                    "author",
                    "keywords",
                    "language",
                    "file_type",
                    "creation_date",
                    "upload_date",
                ],
                limit=top_k,
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.get("id"),
                    "text": result.get("text"),
                    "document_name": result.get("document_name"),
                    "document_id": result.get("document_id"),
                    "chunk_index": result.get("chunk_index"),
                    "metadata": {
                        "author": result.get("author"),
                        "keywords": result.get("keywords"),
                        "language": result.get("language"),
                        "file_type": result.get("file_type"),
                        "creation_date": result.get("creation_date"),
                        "upload_date": result.get("upload_date"),
                    },
                })
            
            logger.info(
                f"Metadata search completed: {len(formatted_results)} results, "
                f"filters={filters}"
            )
            
            return formatted_results
            
        except Exception as e:
            error_msg = f"Metadata search failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def search_with_ranking(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        ranking_method: str = "score",
    ) -> List[Dict[str, Any]]:
        """
        Search with custom ranking method.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Metadata filters
            ranking_method: Ranking method ("score", "recency", "hybrid")
            
        Returns:
            List of ranked search results
            
        Raises:
            RuntimeError: If search fails
        """
        try:
            # Perform base search
            results = await self.search(
                query=query,
                top_k=top_k * 2,  # Get more results for reranking
                filters=filters,
                include_metadata=True,
            )
            
            # Apply ranking
            if ranking_method == "score":
                # Already sorted by score
                ranked_results = results
            elif ranking_method == "recency":
                # Sort by upload date (most recent first)
                ranked_results = sorted(
                    results,
                    key=lambda x: x["metadata"].get("upload_date", 0),
                    reverse=True,
                )
            elif ranking_method == "hybrid":
                # Combine score and recency
                ranked_results = self._hybrid_ranking(results)
            else:
                raise ValueError(f"Unknown ranking method: {ranking_method}")
            
            # Return top_k results
            final_results = ranked_results[:top_k]
            
            logger.info(
                f"Ranked search completed: {len(final_results)} results, "
                f"method={ranking_method}"
            )
            
            return final_results
            
        except Exception as e:
            error_msg = f"Ranked search failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _format_search_results(
        self,
        results: List[Dict[str, Any]],
        include_metadata: bool,
    ) -> List[Dict[str, Any]]:
        """
        Format search results for workflow consumption.
        
        Args:
            results: Raw search results from Milvus
            include_metadata: Whether to include metadata
            
        Returns:
            List of formatted results
        """
        formatted = []
        
        for result in results:
            formatted_result = {
                "id": result.get("id"),
                "text": result.get("text"),
                "score": result.get("score"),
                "document_name": result.get("document_name"),
                "document_id": result.get("document_id"),
                "chunk_index": result.get("chunk_index"),
                "file_type": result.get("file_type"),
            }
            
            if include_metadata:
                formatted_result["metadata"] = {
                    "author": result.get("author"),
                    "keywords": result.get("keywords"),
                    "language": result.get("language"),
                    "creation_date": result.get("creation_date"),
                    "upload_date": result.get("upload_date"),
                }
            
            formatted.append(formatted_result)
        
        return formatted

    def _hybrid_ranking(
        self,
        results: List[Dict[str, Any]],
        score_weight: float = 0.7,
        recency_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Apply hybrid ranking combining score and recency.
        
        Args:
            results: Search results
            score_weight: Weight for similarity score
            recency_weight: Weight for recency
            
        Returns:
            Reranked results
        """
        if not results:
            return results
        
        # Normalize scores
        max_score = max(r["score"] for r in results)
        min_score = min(r["score"] for r in results)
        score_range = max_score - min_score if max_score != min_score else 1.0
        
        # Normalize recency (upload_date)
        now = int(datetime.now().timestamp())
        max_age = 365 * 24 * 3600  # 1 year in seconds
        
        # Calculate hybrid scores
        for result in results:
            # Normalize similarity score (0-1)
            norm_score = (result["score"] - min_score) / score_range
            
            # Normalize recency (0-1, newer is better)
            upload_date = result["metadata"].get("upload_date", 0)
            age = now - upload_date
            norm_recency = max(0, 1 - (age / max_age))
            
            # Combine scores
            hybrid_score = (
                score_weight * norm_score + recency_weight * norm_recency
            )
            
            result["hybrid_score"] = hybrid_score
        
        # Sort by hybrid score
        ranked = sorted(results, key=lambda x: x["hybrid_score"], reverse=True)
        
        return ranked

    async def get_document_chunks(
        self,
        document_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of chunks
            
        Raises:
            RuntimeError: If retrieval fails
        """
        try:
            # Search by document_id
            results = await self.search_by_metadata(
                filters={"document_id": document_id},
                top_k=1000,  # Get all chunks
            )
            
            # Sort by chunk_index
            sorted_results = sorted(results, key=lambda x: x["chunk_index"])
            
            logger.info(
                f"Retrieved {len(sorted_results)} chunks for document {document_id}"
            )
            
            return sorted_results
            
        except Exception as e:
            error_msg = f"Failed to get document chunks: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def get_available_filters(self) -> Dict[str, List[str]]:
        """
        Get available metadata filter fields and their types.
        
        Returns:
            dict: Available filter fields
        """
        return {
            "string_fields": ["author", "language", "file_type", "keywords"],
            "numeric_fields": ["creation_date", "upload_date", "chunk_index"],
            "operators": {
                "string": ["==", "in"],
                "numeric": ["==", ">", "<", ">=", "<=", "in"],
            },
        }


# Global service instance
_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """
    Get or create global search service instance.
    
    Returns:
        SearchService: Global service instance
    """
    global _service
    
    if _service is None:
        _service = SearchService()
    
    return _service
