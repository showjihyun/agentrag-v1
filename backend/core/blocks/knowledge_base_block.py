"""
Knowledge Base Block for vector search in workflows.

Provides semantic search capabilities using the existing Milvus infrastructure.
"""

import logging
from typing import Dict, Any, Optional, List

from backend.core.blocks.base import BaseBlock, BlockExecutionError
from backend.core.blocks.registry import BlockRegistry
from backend.core.knowledge_base.search_service import get_search_service
from backend.core.knowledge_base.milvus_connector import get_milvus_connector

logger = logging.getLogger(__name__)


@BlockRegistry.register(
    block_type="knowledge_base",
    name="Knowledge Base",
    description="Search documents using vector similarity with metadata filtering",
    category="tools",
    sub_blocks=[
        {
            "id": "kb_config",
            "type": "knowledge-base",
            "title": "Knowledge Base Configuration",
            "description": "Configure knowledge base search with collection, query, and filters",
            "required": True,
            "placeholder": "Configure your knowledge base search",
        },
        {
            "id": "ranking_method",
            "type": "dropdown",
            "title": "Ranking Method",
            "description": "Method for ranking search results",
            "required": False,
            "defaultValue": "score",
            "options": [
                {"label": "Similarity Score", "value": "score"},
                {"label": "Recency", "value": "recency"},
                {"label": "Hybrid (Score + Recency)", "value": "hybrid"},
            ],
        },
        {
            "id": "include_metadata",
            "type": "dropdown",
            "title": "Include Metadata",
            "description": "Include full metadata in results",
            "required": False,
            "defaultValue": "true",
            "options": [
                {"label": "Yes", "value": "true"},
                {"label": "No", "value": "false"},
            ],
        },
    ],
    inputs={
        "query": {
            "type": "string",
            "description": "Search query text",
            "required": True,
        },
        "top_k": {
            "type": "number",
            "description": "Number of results to return",
            "required": False,
            "default": 5,
        },
        "filters": {
            "type": "object",
            "description": "Metadata filters",
            "required": False,
        },
        "ranking_method": {
            "type": "string",
            "description": "Ranking method (score, recency, hybrid)",
            "required": False,
            "default": "score",
        },
        "include_metadata": {
            "type": "boolean",
            "description": "Include metadata in results",
            "required": False,
            "default": True,
        },
    },
    outputs={
        "results": {
            "type": "array",
            "description": "List of search results with text and metadata",
        },
        "count": {
            "type": "number",
            "description": "Number of results returned",
        },
        "query": {
            "type": "string",
            "description": "Original search query",
        },
    },
    bg_color="#10B981",  # Green
    icon="🔍",
)
class KnowledgeBaseBlock(BaseBlock):
    """
    Block for searching documents using vector similarity.
    
    Integrates with existing Milvus infrastructure to provide semantic search
    capabilities in workflows.
    """

    def __init__(
        self,
        block_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        sub_blocks: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Knowledge Base block."""
        super().__init__(block_id, config, sub_blocks)
        
        # Get search service
        self.search_service = get_search_service()
        self.milvus_connector = get_milvus_connector()

    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute knowledge base search.
        
        Args:
            inputs: Input data containing:
                - query: Search query text
                - top_k: Number of results (optional)
                - filters: Metadata filters (optional)
                - ranking_method: Ranking method (optional)
                - include_metadata: Include metadata flag (optional)
            context: Execution context
            
        Returns:
            Dict containing:
                - results: List of search results
                - count: Number of results
                - query: Original query
                
        Raises:
            BlockExecutionError: If search fails
        """
        try:
            # Get KB configuration from SubBlocks or inputs
            kb_config = self.sub_blocks.get("kb_config", {})
            
            # Allow direct inputs to override kb_config
            query = inputs.get("query") or kb_config.get("query")
            
            if not query:
                raise BlockExecutionError(
                    "Search query is required",
                    block_type="knowledge_base",
                    block_id=self.block_id,
                )
            
            # Get top_k
            top_k_input = inputs.get("top_k") or kb_config.get("topK", 5)
            try:
                top_k = int(top_k_input)
            except (ValueError, TypeError):
                top_k = 5
            
            # Get filters
            filters = inputs.get("filters") or kb_config.get("filters")
            if filters and isinstance(filters, str):
                # Parse JSON string
                import json
                try:
                    filters = json.loads(filters)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON filters: {filters}")
                    filters = None
            
            # Get ranking method
            ranking_method = (
                inputs.get("ranking_method")
                or self.sub_blocks.get("ranking_method", "score")
            )
            
            # Get include_metadata
            include_metadata_str = (
                inputs.get("include_metadata")
                or self.sub_blocks.get("include_metadata", "true")
            )
            include_metadata = include_metadata_str in ["true", "True", True, "1", 1]
            
            logger.info(
                f"Knowledge Base search: query='{query[:50]}...', "
                f"top_k={top_k}, filters={bool(filters)}, "
                f"ranking={ranking_method}"
            )
            
            # Ensure Milvus is connected
            if not self.milvus_connector._connected:
                self.milvus_connector.connect()
            
            # Perform search based on ranking method
            if ranking_method in ["recency", "hybrid"]:
                results = await self.search_service.search_with_ranking(
                    query=query,
                    top_k=top_k,
                    filters=filters,
                    ranking_method=ranking_method,
                )
            else:
                results = await self.search_service.search(
                    query=query,
                    top_k=top_k,
                    filters=filters,
                    include_metadata=include_metadata,
                )
            
            logger.info(
                f"Knowledge Base search completed: {len(results)} results"
            )
            
            return {
                "results": results,
                "count": len(results),
                "query": query,
            }
            
        except BlockExecutionError:
            raise
        except Exception as e:
            error_msg = f"Knowledge Base search failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise BlockExecutionError(
                error_msg,
                block_type="knowledge_base",
                block_id=self.block_id,
                original_error=e,
            ) from e


@BlockRegistry.register(
    block_type="knowledge_base_upload",
    name="Upload to Knowledge Base",
    description="Upload and process documents to the knowledge base",
    category="tools",
    sub_blocks=[
        {
            "id": "file_path",
            "type": "short-input",
            "title": "File Path",
            "description": "Path to the file to upload",
            "required": True,
            "placeholder": "/path/to/document.pdf",
        },
        {
            "id": "author",
            "type": "short-input",
            "title": "Author",
            "description": "Document author",
            "required": False,
            "placeholder": "John Doe",
        },
        {
            "id": "keywords",
            "type": "short-input",
            "title": "Keywords",
            "description": "Comma-separated keywords",
            "required": False,
            "placeholder": "machine learning, AI, neural networks",
        },
        {
            "id": "language",
            "type": "dropdown",
            "title": "Language",
            "description": "Document language",
            "required": False,
            "defaultValue": "en",
            "options": [
                {"label": "English", "value": "en"},
                {"label": "Korean", "value": "ko"},
                {"label": "Japanese", "value": "ja"},
                {"label": "Chinese", "value": "zh"},
                {"label": "Spanish", "value": "es"},
                {"label": "French", "value": "fr"},
                {"label": "German", "value": "de"},
            ],
        },
    ],
    inputs={
        "file_path": {
            "type": "string",
            "description": "Path to file",
            "required": True,
        },
        "file_content": {
            "type": "bytes",
            "description": "File content (alternative to file_path)",
            "required": False,
        },
        "filename": {
            "type": "string",
            "description": "Filename (required if using file_content)",
            "required": False,
        },
        "metadata": {
            "type": "object",
            "description": "Document metadata",
            "required": False,
        },
    },
    outputs={
        "document_id": {
            "type": "string",
            "description": "Uploaded document ID",
        },
        "chunks_count": {
            "type": "number",
            "description": "Number of chunks created",
        },
        "success": {
            "type": "boolean",
            "description": "Upload success status",
        },
    },
    bg_color="#3B82F6",  # Blue
    icon="📤",
)
class KnowledgeBaseUploadBlock(BaseBlock):
    """
    Block for uploading documents to the knowledge base.
    
    Processes documents and stores them in Milvus for semantic search.
    """

    def __init__(
        self,
        block_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        sub_blocks: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Knowledge Base Upload block."""
        super().__init__(block_id, config, sub_blocks)
        
        # Import workflows
        from backend.core.knowledge_base.document_workflow import get_document_workflow
        from backend.core.knowledge_base.embedding_workflow import get_embedding_workflow
        
        self.document_workflow = get_document_workflow()
        self.embedding_workflow = get_embedding_workflow()

    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute document upload to knowledge base.
        
        Args:
            inputs: Input data containing file information and metadata
            context: Execution context
            
        Returns:
            Dict containing upload result
            
        Raises:
            BlockExecutionError: If upload fails
        """
        try:
            # Get file content
            file_content = inputs.get("file_content")
            file_path = inputs.get("file_path") or self.sub_blocks.get("file_path")
            filename = inputs.get("filename")
            
            if not file_content and not file_path:
                raise BlockExecutionError(
                    "Either file_content or file_path is required",
                    block_type="knowledge_base_upload",
                    block_id=self.block_id,
                )
            
            # Read file if path provided
            if file_path and not file_content:
                import os
                if not os.path.exists(file_path):
                    raise BlockExecutionError(
                        f"File not found: {file_path}",
                        block_type="knowledge_base_upload",
                        block_id=self.block_id,
                    )
                
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                filename = filename or os.path.basename(file_path)
            
            if not filename:
                raise BlockExecutionError(
                    "Filename is required",
                    block_type="knowledge_base_upload",
                    block_id=self.block_id,
                )
            
            # Build metadata
            metadata = inputs.get("metadata", {})
            metadata.update({
                "author": self.sub_blocks.get("author", ""),
                "keywords": self.sub_blocks.get("keywords", ""),
                "language": self.sub_blocks.get("language", "en"),
            })
            
            logger.info(f"Uploading document: {filename}")
            
            # Process document
            document = await self.document_workflow.process_document(
                file_content=file_content,
                filename=filename,
                metadata=metadata,
            )
            
            # Generate embeddings and store
            result = await self.embedding_workflow.process_and_store_document(
                document=document
            )
            
            logger.info(
                f"Document uploaded successfully: {filename} -> "
                f"{result['chunks_inserted']} chunks"
            )
            
            return {
                "document_id": result["document_id"],
                "chunks_count": result["chunks_inserted"],
                "success": True,
            }
            
        except BlockExecutionError:
            raise
        except Exception as e:
            error_msg = f"Document upload failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise BlockExecutionError(
                error_msg,
                block_type="knowledge_base_upload",
                block_id=self.block_id,
                original_error=e,
            ) from e
