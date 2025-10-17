"""
Document Ingestion Service for end-to-end document processing pipeline.

Integrates DocumentProcessor, EmbeddingService, and MilvusManager to provide
a complete document upload and indexing workflow.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.services.document_processor import (
    DocumentProcessor,
    DocumentProcessingError,
)
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.models.document import Document, TextChunk

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """
    Service for complete document ingestion pipeline.

    Workflow:
    1. Process document (extract and chunk text)
    2. Generate embeddings for chunks
    3. Store chunks with embeddings in Milvus
    4. Return processing status
    """

    def __init__(
        self,
        document_processor: DocumentProcessor,
        embedding_service: EmbeddingService,
        milvus_manager: MilvusManager,
        hybrid_search_manager=None,
    ):
        """
        Initialize DocumentIngestionService.

        Args:
            document_processor: Service for document processing
            embedding_service: Service for generating embeddings
            milvus_manager: Manager for Milvus operations
            hybrid_search_manager: Optional HybridSearchManager for BM25 indexing
        """
        self.document_processor = document_processor
        self.embedding_service = embedding_service
        self.milvus_manager = milvus_manager
        self.hybrid_search = hybrid_search_manager

        logger.info(
            f"DocumentIngestionService initialized "
            f"(hybrid_search={'enabled' if hybrid_search_manager else 'disabled'})"
        )

    async def ingest_document(
        self, file_content: bytes, filename: str, file_size: int
    ) -> Dict[str, Any]:
        """
        Ingest a document through the complete pipeline.

        Args:
            file_content: File content as bytes
            filename: Original filename
            file_size: File size in bytes

        Returns:
            Dict with processing status and metadata:
            {
                "document_id": str,
                "filename": str,
                "status": str,
                "chunk_count": int,
                "processing_time_ms": float,
                "error": Optional[str]
            }

        Raises:
            ValueError: If inputs are invalid
            DocumentProcessingError: If processing fails
            RuntimeError: If embedding or storage fails
        """
        start_time = datetime.now()

        try:
            logger.info(f"Starting document ingestion: {filename}")

            # Step 1: Process document (extract and chunk)
            document, chunks = await self.document_processor.process_document(
                file_content=file_content, filename=filename, file_size=file_size
            )

            logger.info(
                f"Document processed: {document.document_id}, "
                f"{len(chunks)} chunks created"
            )

            # Step 2: Generate embeddings for all chunks with dynamic batch sizing
            chunk_texts = [chunk.text for chunk in chunks]

            # Dynamic batch size based on number of chunks
            num_chunks = len(chunk_texts)
            if num_chunks < 10:
                batch_size = num_chunks  # Small documents - process all at once
            elif num_chunks < 100:
                batch_size = 32  # Medium documents
            else:
                batch_size = 64  # Large documents - larger batches for efficiency

            logger.info(
                f"Generating embeddings for {num_chunks} chunks (batch_size={batch_size})"
            )
            embeddings = await self.embedding_service.embed_batch(
                texts=chunk_texts, batch_size=batch_size
            )

            logger.info(f"Generated {len(embeddings)} embeddings")

            # Step 3: Prepare metadata for Milvus
            metadata_list = []
            upload_timestamp = int(document.upload_timestamp.timestamp())

            for i, chunk in enumerate(chunks):
                metadata = {
                    "id": chunk.chunk_id,
                    "document_id": document.document_id,
                    "text": chunk.text,
                    "chunk_index": chunk.chunk_index,
                    "document_name": document.filename,
                    "file_type": document.file_type,
                    "upload_date": upload_timestamp,
                    # Optional metadata fields
                    "author": "",
                    "creation_date": 0,
                    "language": "",
                    "keywords": "",
                }
                metadata_list.append(metadata)

            # Step 4: Store in Milvus
            logger.info(f"Storing {len(embeddings)} embeddings in Milvus")
            inserted_ids = await self.milvus_manager.insert_embeddings(
                embeddings=embeddings, metadata=metadata_list
            )

            logger.info(f"Successfully stored {len(inserted_ids)} chunks in Milvus")

            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            # Return success response
            result = {
                "document_id": document.document_id,
                "filename": document.filename,
                "status": "completed",
                "chunk_count": len(chunks),
                "processing_time_ms": round(processing_time_ms, 2),
                "metadata": document.metadata,
                "error": None,
            }

            logger.info(
                f"Document ingestion completed: {document.document_id} "
                f"in {processing_time_ms:.2f}ms"
            )

            # Update BM25 index if hybrid search is enabled
            if self.hybrid_search:
                try:
                    await self._update_bm25_index()
                    logger.info("BM25 index updated successfully")
                except Exception as e:
                    logger.warning(f"Failed to update BM25 index: {e}")
                    # Don't fail the ingestion if BM25 update fails

            return result

        except DocumentProcessingError as e:
            # Document processing failed
            error_msg = f"Document processing failed: {str(e)}"
            logger.error(error_msg)

            end_time = datetime.now()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            return {
                "document_id": None,
                "filename": filename,
                "status": "failed",
                "chunk_count": 0,
                "processing_time_ms": round(processing_time_ms, 2),
                "metadata": {},
                "error": error_msg,
            }

        except RuntimeError as e:
            # Embedding or Milvus storage failed
            error_msg = f"Storage failed: {str(e)}"
            logger.error(error_msg)

            end_time = datetime.now()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            # If we have a document ID, try to clean up
            if "document" in locals() and document:
                try:
                    await self.milvus_manager.delete_by_document_id(
                        document.document_id
                    )
                    logger.info(f"Cleaned up partial data for {document.document_id}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up: {str(cleanup_error)}")

            return {
                "document_id": document.document_id if "document" in locals() else None,
                "filename": filename,
                "status": "failed",
                "chunk_count": len(chunks) if "chunks" in locals() else 0,
                "processing_time_ms": round(processing_time_ms, 2),
                "metadata": {},
                "error": error_msg,
            }

        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during ingestion: {str(e)}"
            logger.error(error_msg, exc_info=True)

            end_time = datetime.now()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            return {
                "document_id": None,
                "filename": filename,
                "status": "failed",
                "chunk_count": 0,
                "processing_time_ms": round(processing_time_ms, 2),
                "metadata": {},
                "error": error_msg,
            }

    async def get_document_chunks(
        self, document_id: str, top_k: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a specific document.

        Args:
            document_id: ID of the document
            top_k: Maximum number of chunks to retrieve

        Returns:
            List of chunk dictionaries

        Raises:
            ValueError: If document_id is invalid
            RuntimeError: If retrieval fails
        """
        if not document_id:
            raise ValueError("document_id cannot be empty")

        try:
            logger.info(f"Retrieving chunks for document: {document_id}")

            # Create a dummy embedding for search (we'll filter by document_id)
            # This is a workaround since Milvus requires a vector for search
            dummy_embedding = [0.0] * self.embedding_service.dimension

            # Search with document_id filter
            results = await self.milvus_manager.search(
                query_embedding=dummy_embedding,
                top_k=top_k,
                filters=f'document_id == "{document_id}"',
            )

            # Convert to dictionaries
            chunks = [result.to_dict() for result in results]

            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")

            return chunks

        except Exception as e:
            error_msg = (
                f"Failed to retrieve chunks for document {document_id}: {str(e)}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document and all its chunks from Milvus.

        Args:
            document_id: ID of the document to delete

        Returns:
            Dict with deletion status:
            {
                "document_id": str,
                "status": str,
                "chunks_deleted": int,
                "error": Optional[str]
            }

        Raises:
            ValueError: If document_id is invalid
        """
        if not document_id:
            raise ValueError("document_id cannot be empty")

        try:
            logger.info(f"Deleting document: {document_id}")

            # Delete all chunks for the document
            chunks_deleted = await self.milvus_manager.delete_by_document_id(
                document_id
            )

            logger.info(f"Deleted {chunks_deleted} chunks for document {document_id}")

            return {
                "document_id": document_id,
                "status": "deleted",
                "chunks_deleted": chunks_deleted,
                "error": None,
            }

        except Exception as e:
            error_msg = f"Failed to delete document {document_id}: {str(e)}"
            logger.error(error_msg)

            return {
                "document_id": document_id,
                "status": "failed",
                "chunks_deleted": 0,
                "error": error_msg,
            }

    async def _update_bm25_index(self):
        """
        Update BM25 index with all documents from Milvus.

        This is called after each document ingestion to keep the
        BM25 index synchronized with the vector database.
        """
        try:
            logger.info("Updating BM25 index...")

            # Get all documents from Milvus
            # Use a dummy embedding to retrieve all documents
            dummy_embedding = [0.0] * self.embedding_service.dimension

            # Retrieve a large number of documents
            all_results = await self.milvus_manager.search(
                query_embedding=dummy_embedding,
                top_k=10000,  # Adjust based on your collection size
            )

            # Prepare documents for BM25 indexing
            documents = []
            for result in all_results:
                doc = {
                    "id": result.id,
                    "document_id": result.document_id,
                    "text": result.text,
                    "document_name": result.document_name,
                    "chunk_index": result.chunk_index,
                }
                documents.append(doc)

            # Build BM25 index
            if documents:
                self.hybrid_search.build_bm25_index(documents)
                logger.info(f"BM25 index built with {len(documents)} documents")
            else:
                logger.warning("No documents found for BM25 indexing")

        except Exception as e:
            logger.error(f"Failed to update BM25 index: {e}")
            raise

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the ingestion service configuration.

        Returns:
            Dict with service configuration
        """
        return {
            "chunk_size": self.document_processor.chunk_size,
            "chunk_overlap": self.document_processor.chunk_overlap,
            "max_file_size": self.document_processor.max_file_size,
            "embedding_model": self.embedding_service.model_name,
            "embedding_dimension": self.embedding_service.dimension,
            "milvus_collection": self.milvus_manager.collection_name,
            "supported_file_types": list(
                self.document_processor.SUPPORTED_TYPES.keys()
            ),
            "hybrid_search_enabled": self.hybrid_search is not None,
        }
