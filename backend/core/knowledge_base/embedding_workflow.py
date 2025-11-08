"""
Embedding Generation Workflow for Knowledge Base Integration.

Reuses existing embedding service and provides workflow-compatible
interface for generating embeddings and storing in Milvus.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from backend.services.embedding import EmbeddingService
from backend.models.document import Document, TextChunk
from backend.core.knowledge_base.milvus_connector import get_milvus_connector

logger = logging.getLogger(__name__)


class EmbeddingWorkflow:
    """
    Workflow-compatible embedding generation service.
    
    Reuses existing EmbeddingService and provides simplified interface
    for workflow blocks to generate and store embeddings.
    """

    def __init__(self):
        """Initialize embedding workflow."""
        # Reuse existing embedding service
        self.embedding_service = EmbeddingService()
        
        # Get Milvus connector
        self.milvus_connector = get_milvus_connector()
        
        logger.info(
            f"EmbeddingWorkflow initialized with model: "
            f"{self.embedding_service.model_name} "
            f"(dimension: {self.embedding_service.dimension})"
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            RuntimeError: If embedding generation fails
        """
        try:
            embedding = await self.embedding_service.embed_text(text)
            
            logger.debug(
                f"Generated embedding: text_length={len(text)}, "
                f"dimension={len(embedding)}"
            )
            
            return embedding
            
        except Exception as e:
            error_msg = f"Failed to generate embedding: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts
            batch_size: Optional batch size (auto-calculated if None)
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If batch embedding generation fails
        """
        try:
            embeddings = await self.embedding_service.embed_batch(
                texts=texts,
                batch_size=batch_size,
            )
            
            logger.info(
                f"Generated {len(embeddings)} embeddings in batch "
                f"(dimension={len(embeddings[0])})"
            )
            
            return embeddings
            
        except Exception as e:
            error_msg = f"Failed to generate batch embeddings: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def embed_document(self, document: Document) -> Document:
        """
        Generate embeddings for all chunks in a document.
        
        Args:
            document: Document with text chunks
            
        Returns:
            Document with embeddings added to chunks
            
        Raises:
            RuntimeError: If embedding generation fails
        """
        try:
            if not document.chunks:
                raise ValueError("Document has no chunks to embed")
            
            # Extract texts from chunks
            texts = [chunk.text for chunk in document.chunks]
            
            # Generate embeddings in batch
            embeddings = await self.generate_batch_embeddings(texts)
            
            # Add embeddings to chunks
            for chunk, embedding in zip(document.chunks, embeddings):
                chunk.embedding = embedding
            
            logger.info(
                f"Embedded document: {document.name} -> {len(embeddings)} chunks"
            )
            
            return document
            
        except Exception as e:
            error_msg = f"Failed to embed document '{document.name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def store_document_in_milvus(
        self,
        document: Document,
    ) -> Dict[str, Any]:
        """
        Store document chunks with embeddings in Milvus.
        
        Args:
            document: Document with embedded chunks
            
        Returns:
            dict: Storage result with inserted IDs
            
        Raises:
            RuntimeError: If storage fails
        """
        try:
            # Ensure Milvus is connected
            if not self.milvus_connector._connected:
                self.milvus_connector.connect()
            
            collection = self.milvus_connector.get_collection()
            
            # Prepare data for insertion
            data = []
            
            for chunk in document.chunks:
                if not chunk.embedding:
                    raise ValueError(
                        f"Chunk {chunk.id} has no embedding. "
                        f"Call embed_document() first."
                    )
                
                # Build entity
                entity = {
                    "id": chunk.id,
                    "document_id": document.id,
                    "text": chunk.text,
                    "embedding": chunk.embedding,
                    "chunk_index": chunk.chunk_index,
                    "document_name": document.name,
                    "file_type": document.file_type,
                    "upload_date": int(document.upload_date.timestamp()),
                    "author": document.metadata.get("author", ""),
                    "creation_date": document.metadata.get(
                        "creation_date", int(datetime.now().timestamp())
                    ),
                    "language": document.metadata.get("language", "en"),
                    "keywords": document.metadata.get("keywords", ""),
                }
                
                data.append(entity)
            
            # Insert into Milvus
            insert_result = collection.insert(data)
            
            # Flush to ensure data is persisted
            collection.flush()
            
            logger.info(
                f"Stored document in Milvus: {document.name} -> "
                f"{len(data)} chunks inserted"
            )
            
            return {
                "document_id": document.id,
                "document_name": document.name,
                "chunks_inserted": len(data),
                "insert_ids": insert_result.primary_keys,
            }
            
        except Exception as e:
            error_msg = f"Failed to store document in Milvus: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def process_and_store_document(
        self,
        document: Document,
    ) -> Dict[str, Any]:
        """
        Complete workflow: embed document and store in Milvus.
        
        Args:
            document: Document with text chunks (no embeddings yet)
            
        Returns:
            dict: Processing result
            
        Raises:
            RuntimeError: If processing fails
        """
        try:
            # Generate embeddings
            document = await self.embed_document(document)
            
            # Store in Milvus
            result = await self.store_document_in_milvus(document)
            
            logger.info(
                f"Document processing complete: {document.name} -> "
                f"{result['chunks_inserted']} chunks stored"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to process and store document: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def update_embeddings(
        self,
        document_id: str,
        chunks: List[TextChunk],
    ) -> Dict[str, Any]:
        """
        Update embeddings for specific chunks.
        
        Args:
            document_id: Document ID
            chunks: Chunks to update
            
        Returns:
            dict: Update result
            
        Raises:
            RuntimeError: If update fails
        """
        try:
            # Generate embeddings for chunks
            texts = [chunk.text for chunk in chunks]
            embeddings = await self.generate_batch_embeddings(texts)
            
            # Update chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            
            # Delete old chunks from Milvus
            if not self.milvus_connector._connected:
                self.milvus_connector.connect()
            
            collection = self.milvus_connector.get_collection()
            
            chunk_ids = [chunk.id for chunk in chunks]
            expr = f"id in {chunk_ids}"
            collection.delete(expr)
            
            # Insert updated chunks
            data = []
            for chunk in chunks:
                entity = {
                    "id": chunk.id,
                    "document_id": document_id,
                    "text": chunk.text,
                    "embedding": chunk.embedding,
                    "chunk_index": chunk.chunk_index,
                    # Add other required fields...
                }
                data.append(entity)
            
            insert_result = collection.insert(data)
            collection.flush()
            
            logger.info(
                f"Updated embeddings: {len(chunks)} chunks for document {document_id}"
            )
            
            return {
                "document_id": document_id,
                "chunks_updated": len(chunks),
                "insert_ids": insert_result.primary_keys,
            }
            
        except Exception as e:
            error_msg = f"Failed to update embeddings: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def get_embedding_info(self) -> Dict[str, Any]:
        """
        Get embedding model information.
        
        Returns:
            dict: Model information
        """
        return self.embedding_service.get_model_info()


# Global workflow instance
_workflow: Optional[EmbeddingWorkflow] = None


def get_embedding_workflow() -> EmbeddingWorkflow:
    """
    Get or create global embedding workflow instance.
    
    Returns:
        EmbeddingWorkflow: Global workflow instance
    """
    global _workflow
    
    if _workflow is None:
        _workflow = EmbeddingWorkflow()
    
    return _workflow
