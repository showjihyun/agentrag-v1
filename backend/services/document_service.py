"""
Document Service for managing document uploads and processing.

Integrates FileStorageService, DocumentProcessor, DocumentRepository,
UserRepository, and MilvusManager to provide end-to-end document management
with user isolation, storage tracking, and error handling.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import UploadFile

from backend.db.repositories.document_repository import DocumentRepository
from backend.db.repositories.user_repository import UserRepository
from backend.services.file_storage_service import FileStorageService, FileStorageError
from backend.services.document_processor import (
    DocumentProcessor,
    DocumentProcessingError,
)
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.db.models.document import Document

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    """Custom exception for document service errors."""

    pass


class DocumentService:
    """
    Service for managing document uploads and processing.

    Features:
    - User-isolated document management
    - File validation and storage
    - Document processing and vectorization
    - Storage quota tracking
    - Comprehensive error handling with rollback
    - Milvus integration with user_id metadata
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        user_repository: UserRepository,
        file_storage_service: FileStorageService,
        document_processor: DocumentProcessor,
        embedding_service: EmbeddingService,
        milvus_manager: MilvusManager,
    ):
        """
        Initialize DocumentService.

        Args:
            document_repository: Repository for document database operations
            user_repository: Repository for user database operations
            file_storage_service: Service for file storage operations
            document_processor: Service for document processing
            embedding_service: Service for generating embeddings
            milvus_manager: Manager for Milvus vector database
        """
        self.document_repo = document_repository
        self.user_repo = user_repository
        self.file_storage = file_storage_service
        self.doc_processor = document_processor
        self.embedding_service = embedding_service
        self.milvus_manager = milvus_manager

        logger.info("DocumentService initialized")

    async def upload_document(self, user_id: UUID, file: UploadFile) -> Document:
        """
        Upload and process a document for a user.

        This method performs the following steps:
        1. Validate file type and size
        2. Save file to user's storage directory
        3. Create document record in database (status='pending')
        4. Process document (extract text, chunk)
        5. Generate embeddings
        6. Store vectors in Milvus with user_id in metadata
        7. Update document status to 'completed' and chunk_count
        8. Update user storage quota
        9. Rollback on any failure (delete file, delete document record)

        Args:
            user_id: User's unique identifier
            file: Uploaded file object

        Returns:
            Document: Created document record

        Raises:
            DocumentServiceError: If upload or processing fails
            ValueError: If validation fails
        """
        file_path = None
        document_id = None
        file_size = 0
        vectors_inserted = False

        try:
            logger.info(f"Starting document upload for user {user_id}: {file.filename}")

            # Step 1: Validate file type
            if not self.file_storage.validate_file_type(file.filename):
                allowed = ", ".join(self.file_storage.ALLOWED_EXTENSIONS.keys())
                raise ValueError(f"File type not allowed. Supported types: {allowed}")

            # Check if HWP/HWPX and log recommendation
            file_ext = (
                file.filename.lower().split(".")[-1] if "." in file.filename else ""
            )
            if file_ext in ["hwp", "hwpx"]:
                logger.info(
                    f"HWP/HWPX file detected: {file.filename}. "
                    "Note: For better text and table extraction accuracy, "
                    "consider converting to PDF format before uploading."
                )

            # Step 2: Save file to storage
            try:
                file_path, file_size = await self.file_storage.save_file(file, user_id)
                logger.info(f"File saved to: {file_path} ({file_size} bytes)")
            except (FileStorageError, ValueError) as e:
                logger.error(
                    f"File storage failed for user {user_id}, file {file.filename}: {e}"
                )
                raise DocumentServiceError(f"Failed to save file: {e}")

            # Step 3: Validate file size
            from backend.config import settings
            max_size = settings.MAX_FILE_SIZE  # Load from config (.env)
            if not self.file_storage.validate_file_size(file_size, max_size):
                raise ValueError(
                    f"File size {file_size / 1024 / 1024:.2f}MB exceeds "
                    f"maximum {max_size / 1024 / 1024:.2f}MB"
                )

            # Step 4: Create document record in database (status='pending')
            try:
                # Get MIME type from file extension
                ext = (
                    file.filename.lower().split(".")[-1] if "." in file.filename else ""
                )
                mime_type = self.file_storage.ALLOWED_EXTENSIONS.get(
                    f".{ext}", "application/octet-stream"
                )

                document = self.document_repo.create_document(
                    user_id=user_id,
                    filename=file.filename,
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type,
                )
                document_id = document.id

                logger.info(
                    f"Document record created: {document_id} for user {user_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to create document record for user {user_id}, "
                    f"file {file.filename}: {e}",
                    exc_info=True,
                )
                raise DocumentServiceError(f"Failed to create document record: {e}")

            # Step 5: Update status to 'processing'
            try:
                self.document_repo.update_document_status(document_id, "processing")
            except Exception as e:
                logger.error(f"Failed to update document status to processing: {e}")
                raise DocumentServiceError(f"Failed to update document status: {e}")

            # Step 6: Process document (hybrid: Native + ColPali)
            try:
                # Detect file type
                file_type = self.doc_processor.detect_file_type(file.filename)
                
                # Use hybrid processor for intelligent processing
                from backend.services.hybrid_document_processor import get_hybrid_document_processor
                from backend.config import settings
                
                hybrid_processor = get_hybrid_document_processor(
                    enable_colpali=settings.ENABLE_HYBRID_PROCESSING and settings.ENABLE_COLPALI,
                    colpali_threshold=settings.HYBRID_COLPALI_THRESHOLD,
                    process_images_always=settings.HYBRID_PROCESS_IMAGES_ALWAYS
                )
                
                # Hybrid processing
                result = await hybrid_processor.process_document(
                    file_path=file_path,
                    file_type=file_type,
                    document_id=str(document_id),
                    metadata={
                        'user_id': str(user_id),
                        'filename': file.filename,
                        'original_filename': file.filename
                    }
                )
                
                # Get processed data
                text = result['native_text']
                chunks = result['native_chunks']
                
                logger.info(
                    f"Hybrid processing completed for {document_id}: "
                    f"method={result['processing_method']}, "
                    f"text_ratio={result['text_ratio']:.2f}, "
                    f"is_scanned={result['is_scanned']}, "
                    f"colpali_processed={result['colpali_processed']}, "
                    f"chunks={len(chunks)}"
                )

            except (DocumentProcessingError, ValueError) as e:
                # Update document status to 'failed'
                try:
                    self.document_repo.update_document_status(
                        document_id, "failed", error_message=str(e)
                    )
                except Exception as status_error:
                    logger.error(
                        f"Failed to update document status to failed: {status_error}"
                    )

                logger.error(
                    f"Document processing failed for document {document_id}: {e}",
                    exc_info=True,
                )
                raise DocumentServiceError(f"Failed to process document: {e}")

            # Step 7: Generate embeddings
            try:
                chunk_texts = [chunk.text for chunk in chunks]
                embeddings = await self.embedding_service.embed_batch(chunk_texts)
                logger.info(
                    f"Generated {len(embeddings)} embeddings for document {document_id}"
                )
            except Exception as e:
                # Update document status to 'failed'
                try:
                    self.document_repo.update_document_status(
                        document_id,
                        "failed",
                        error_message=f"Embedding generation failed: {e}",
                    )
                except Exception as status_error:
                    logger.error(
                        f"Failed to update document status to failed: {status_error}"
                    )

                logger.error(
                    f"Embedding generation failed for document {document_id}: {e}",
                    exc_info=True,
                )
                raise DocumentServiceError(f"Failed to generate embeddings: {e}")

            # Step 8: Store vectors in Milvus with user_id in metadata
            try:
                # Prepare metadata for Milvus
                metadata_list = []
                upload_timestamp = int(datetime.utcnow().timestamp())

                for i, chunk in enumerate(chunks):
                    metadata = {
                        "id": chunk.chunk_id,
                        "document_id": str(document_id),
                        "text": chunk.text,
                        "chunk_index": chunk.chunk_index,
                        "document_name": file.filename,
                        "file_type": file_type,
                        "upload_date": upload_timestamp,
                        # Optional metadata fields (will be populated from document metadata if available)
                        "author": "",
                        "creation_date": 0,
                        "language": "",
                        "keywords": "",
                    }
                    metadata_list.append(metadata)

                # Insert into Milvus
                inserted_ids = await self.milvus_manager.insert_embeddings(
                    embeddings=embeddings, metadata=metadata_list
                )
                vectors_inserted = True
                logger.info(
                    f"Inserted {len(inserted_ids)} vectors into Milvus "
                    f"for document {document_id}"
                )

            except Exception as e:
                # Update document status to 'failed'
                try:
                    self.document_repo.update_document_status(
                        document_id,
                        "failed",
                        error_message=f"Vector storage failed: {e}",
                    )
                except Exception as status_error:
                    logger.error(
                        f"Failed to update document status to failed: {status_error}"
                    )

                logger.error(
                    f"Vector storage failed for document {document_id}: {e}",
                    exc_info=True,
                )
                raise DocumentServiceError(f"Failed to store vectors: {e}")

            # Step 9: Index in BM25 for keyword search
            try:
                from backend.services.bm25_indexer import get_bm25_indexer

                bm25_indexer = get_bm25_indexer()

                # Prepare chunks for BM25 indexing
                bm25_chunks = [
                    {"id": chunk.chunk_id, "text": chunk.text} for chunk in chunks
                ]

                indexed_count = await bm25_indexer.index_chunks(bm25_chunks)
                logger.info(
                    f"Indexed {indexed_count} chunks in BM25 for document {document_id}"
                )

            except Exception as e:
                # BM25 indexing failure shouldn't block document upload
                logger.warning(f"BM25 indexing failed for document {document_id}: {e}")

            # Step 10: Update document status to 'completed' and chunk_count
            try:
                self.document_repo.update_document_status(document_id, "completed")
                self.document_repo.update_document_processing(
                    document_id,
                    chunk_count=len(chunks),
                    collection=self.milvus_manager.collection_name,
                )
                logger.info(f"Document processing completed: {document_id}")
            except Exception as e:
                logger.error(
                    f"Failed to update document status to completed for {document_id}: {e}",
                    exc_info=True,
                )
                # Don't raise here, document is already processed

            # Step 10: Update user storage quota
            try:
                self.user_repo.update_storage_used(user_id, file_size)
                logger.info(
                    f"Updated storage quota for user {user_id}: +{file_size} bytes"
                )
            except Exception as e:
                logger.error(
                    f"Failed to update user storage quota for user {user_id}: {e}",
                    exc_info=True,
                )
                # Don't raise here, document is already processed

            # Refresh document to get latest state
            document = self.document_repo.get_document_by_id(document_id, user_id)

            logger.info(
                f"Document upload completed successfully: {document_id} "
                f"({len(chunks)} chunks, {file_size} bytes)"
            )

            return document

        except (DocumentServiceError, ValueError) as e:
            # Known exceptions - perform cleanup and re-raise
            logger.error(
                f"Document upload failed for user {user_id}, file {file.filename}: {e}"
            )
            self._cleanup_failed_upload(
                file_path=file_path,
                document_id=document_id,
                user_id=user_id,
                vectors_inserted=vectors_inserted,
            )
            raise

        except Exception as e:
            # Unexpected error - perform cleanup and wrap in DocumentServiceError
            logger.error(
                f"Unexpected error during document upload for user {user_id}, "
                f"file {file.filename}: {e}",
                exc_info=True,
            )
            self._cleanup_failed_upload(
                file_path=file_path,
                document_id=document_id,
                user_id=user_id,
                vectors_inserted=vectors_inserted,
            )
            raise DocumentServiceError(f"Unexpected error during upload: {e}")

    def _cleanup_failed_upload(
        self,
        file_path: Optional[str],
        document_id: Optional[UUID],
        user_id: UUID,
        vectors_inserted: bool = False,
    ) -> None:
        """
        Clean up resources after a failed upload.

        This method ensures that partial uploads don't leave orphaned data:
        - Deletes vectors from Milvus if they were inserted
        - Deletes file from storage if it was saved
        - Deletes document record from database if it was created

        Args:
            file_path: Path to the uploaded file (if saved)
            document_id: ID of the document record (if created)
            user_id: User's unique identifier
            vectors_inserted: Whether vectors were inserted into Milvus
        """
        logger.info(
            f"Starting cleanup for failed upload: "
            f"file_path={file_path}, document_id={document_id}, "
            f"vectors_inserted={vectors_inserted}"
        )

        # Step 1: Delete vectors from Milvus if they were inserted
        if vectors_inserted and document_id:
            try:
                deleted_count = self.milvus_manager.delete_by_document_id(
                    str(document_id)
                )
                logger.info(
                    f"Cleanup: Deleted {deleted_count} vectors from Milvus "
                    f"for document {document_id}"
                )
            except Exception as e:
                logger.error(
                    f"Cleanup: Failed to delete vectors from Milvus "
                    f"for document {document_id}: {e}",
                    exc_info=True,
                )

        # Step 2: Delete file from storage if it was saved
        if file_path:
            try:
                self.file_storage.delete_file(file_path)
                logger.info(f"Cleanup: Deleted file: {file_path}")
            except Exception as e:
                logger.error(
                    f"Cleanup: Failed to delete file {file_path}: {e}", exc_info=True
                )

        # Step 3: Delete document record from database if it was created
        if document_id:
            try:
                self.document_repo.delete_document(document_id, user_id)
                logger.info(f"Cleanup: Deleted document record: {document_id}")
            except Exception as e:
                logger.error(
                    f"Cleanup: Failed to delete document record {document_id}: {e}",
                    exc_info=True,
                )

        logger.info("Cleanup completed")

    async def get_user_documents(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Document]:
        """
        Get user's documents with optional status filter.

        Args:
            user_id: User's unique identifier
            status: Optional status filter (pending, processing, completed, failed)
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List[Document]: List of documents ordered by uploaded_at DESC

        Raises:
            DocumentServiceError: If retrieval fails
        """
        try:
            logger.info(
                f"Getting documents for user {user_id} "
                f"(status={status}, limit={limit}, offset={offset})"
            )

            documents = self.document_repo.get_user_documents(
                user_id=user_id, status=status, limit=limit, offset=offset
            )

            logger.info(f"Retrieved {len(documents)} documents for user {user_id}")

            return documents

        except Exception as e:
            logger.error(f"Failed to get user documents: {e}")
            raise DocumentServiceError(f"Failed to get user documents: {e}")

    async def get_document(
        self, document_id: UUID, user_id: UUID
    ) -> Optional[Document]:
        """
        Get a specific document with ownership verification.

        Args:
            document_id: Document's unique identifier
            user_id: User's unique identifier (for ownership verification)

        Returns:
            Optional[Document]: Document if found and owned by user, None otherwise

        Raises:
            DocumentServiceError: If retrieval fails
        """
        try:
            logger.info(f"Getting document {document_id} for user {user_id}")

            document = self.document_repo.get_document_by_id(document_id, user_id)

            if document:
                logger.info(f"Found document {document_id}")
            else:
                logger.info(
                    f"Document {document_id} not found or not owned by user {user_id}"
                )

            return document

        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise DocumentServiceError(f"Failed to get document: {e}")

    async def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        """
        Delete a document and all associated data.

        This method performs the following steps:
        1. Verify document ownership
        2. Delete vectors from Milvus (filter by document_id and user_id)
        3. Delete file from storage
        4. Delete document record from database
        5. Update user storage quota (decrement)

        Args:
            document_id: Document's unique identifier
            user_id: User's unique identifier (for ownership verification)

        Returns:
            bool: True if document was deleted successfully

        Raises:
            DocumentServiceError: If deletion fails
            ValueError: If document not found or not owned by user
        """
        document = None
        file_path = None
        file_size = 0
        milvus_deleted = False
        file_deleted = False

        try:
            logger.info(f"Deleting document {document_id} for user {user_id}")

            # Step 1: Get document and verify ownership
            try:
                document = self.document_repo.get_document_by_id(document_id, user_id)
            except Exception as e:
                logger.error(
                    f"Failed to retrieve document {document_id} for user {user_id}: {e}",
                    exc_info=True,
                )
                raise DocumentServiceError(f"Failed to retrieve document: {e}")

            if not document:
                raise ValueError(
                    f"Document {document_id} not found or not owned by user {user_id}"
                )

            file_path = document.file_path
            file_size = document.file_size_bytes

            logger.info(
                f"Document found: {document_id}, file_path={file_path}, "
                f"file_size={file_size} bytes"
            )

            # Step 2: Delete from Milvus
            try:
                deleted_count = await self.milvus_manager.delete_by_document_id(
                    str(document_id)
                )
                milvus_deleted = True
                logger.info(
                    f"Deleted {deleted_count} vectors from Milvus "
                    f"for document {document_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to delete vectors from Milvus for document {document_id}: {e}",
                    exc_info=True,
                )
                # Continue with deletion even if Milvus deletion fails
                # This prevents orphaned database records

            # Step 3: Delete file from storage
            try:
                if file_path:
                    self.file_storage.delete_file(file_path)
                    file_deleted = True
                    logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {e}", exc_info=True)
                # Continue with deletion even if file deletion fails
                # This prevents orphaned database records

            # Step 4: Delete document record
            try:
                self.document_repo.delete_document(document_id, user_id)
                logger.info(f"Deleted document record: {document_id}")
            except Exception as e:
                logger.error(
                    f"Failed to delete document record {document_id}: {e}",
                    exc_info=True,
                )
                raise DocumentServiceError(f"Failed to delete document record: {e}")

            # Step 5: Update user storage quota (decrement)
            try:
                self.user_repo.update_storage_used(user_id, -file_size)
                logger.info(
                    f"Updated storage quota for user {user_id}: -{file_size} bytes"
                )
            except Exception as e:
                logger.error(
                    f"Failed to update user storage quota for user {user_id}: {e}",
                    exc_info=True,
                )
                # Don't raise here, document is already deleted
                # Storage quota can be recalculated if needed

            logger.info(
                f"Document {document_id} deleted successfully "
                f"(milvus_deleted={milvus_deleted}, file_deleted={file_deleted})"
            )

            return True

        except ValueError as e:
            # Re-raise validation errors with context
            logger.error(f"Validation error during document deletion: {e}")
            raise

        except DocumentServiceError as e:
            # Re-raise service errors with context
            logger.error(f"Service error during document deletion: {e}")
            raise

        except Exception as e:
            # Unexpected error
            logger.error(
                f"Unexpected error during document deletion for document {document_id}, "
                f"user {user_id}: {e}",
                exc_info=True,
            )
            raise DocumentServiceError(f"Failed to delete document: {e}")

    def get_document_count(self, user_id: UUID) -> int:
        """
        Get total number of documents for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            int: Total document count

        Raises:
            DocumentServiceError: If retrieval fails
        """
        try:
            count = self.document_repo.get_document_count(user_id)
            logger.debug(f"User {user_id} has {count} documents")
            return count
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            raise DocumentServiceError(f"Failed to get document count: {e}")

    def get_total_storage_used(self, user_id: UUID) -> int:
        """
        Get total storage used by user's documents in bytes.

        Args:
            user_id: User's unique identifier

        Returns:
            int: Total storage used in bytes

        Raises:
            DocumentServiceError: If retrieval fails
        """
        try:
            total = self.document_repo.get_total_storage_used(user_id)
            logger.debug(
                f"User {user_id} storage: {total} bytes "
                f"({total / 1024 / 1024:.2f} MB)"
            )
            return total
        except Exception as e:
            logger.error(f"Failed to get total storage: {e}")
            raise DocumentServiceError(f"Failed to get total storage: {e}")


# Singleton instance
_document_service: Optional[DocumentService] = None


def get_document_service(
    document_repository: DocumentRepository,
    user_repository: UserRepository,
    file_storage_service: FileStorageService,
    document_processor: DocumentProcessor,
    embedding_service: EmbeddingService,
    milvus_manager: MilvusManager,
) -> DocumentService:
    """
    Get or create DocumentService singleton instance.

    Args:
        document_repository: Repository for document database operations
        user_repository: Repository for user database operations
        file_storage_service: Service for file storage operations
        document_processor: Service for document processing
        embedding_service: Service for generating embeddings
        milvus_manager: Manager for Milvus vector database

    Returns:
        DocumentService: Singleton instance
    """
    global _document_service

    if _document_service is None:
        _document_service = DocumentService(
            document_repository=document_repository,
            user_repository=user_repository,
            file_storage_service=file_storage_service,
            document_processor=document_processor,
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
        )

    return _document_service

    def _store_document_metadata(
        self, document: Document, metadata: Dict[str, Any]
    ) -> None:
        """
        Store extracted metadata in document record.

        Args:
            document: Document database record
            metadata: Extracted metadata dictionary
        """
        try:
            # Store rich metadata in dedicated fields
            document.document_title = (
                metadata.get("title", "")[:500] if metadata.get("title") else None
            )
            document.document_author = (
                metadata.get("author", "")[:200] if metadata.get("author") else None
            )
            document.document_subject = (
                metadata.get("subject", "")[:500] if metadata.get("subject") else None
            )

            # Store keywords (convert list to comma-separated string if needed)
            keywords = metadata.get("keywords", "")
            if isinstance(keywords, list):
                keywords = ", ".join(keywords)
            document.document_keywords = keywords if keywords else None

            # Store language
            document.document_language = (
                metadata.get("language", "")[:10] if metadata.get("language") else None
            )

            # Store dates
            creation_date_str = metadata.get("creation_date")
            if creation_date_str:
                try:
                    if isinstance(creation_date_str, str):
                        document.document_creation_date = datetime.fromisoformat(
                            creation_date_str.replace("Z", "+00:00")
                        )
                    elif isinstance(creation_date_str, datetime):
                        document.document_creation_date = creation_date_str
                except Exception as e:
                    logger.debug(f"Failed to parse creation date: {e}")

            modification_date_str = metadata.get("modification_date")
            if modification_date_str:
                try:
                    if isinstance(modification_date_str, str):
                        document.document_modification_date = datetime.fromisoformat(
                            modification_date_str.replace("Z", "+00:00")
                        )
                    elif isinstance(modification_date_str, datetime):
                        document.document_modification_date = modification_date_str
                except Exception as e:
                    logger.debug(f"Failed to parse modification date: {e}")

            # Store full metadata in JSON field
            document.extra_metadata = metadata

            logger.debug(
                f"Stored metadata for document {document.id}: "
                f"title={document.document_title}, author={document.document_author}, "
                f"language={document.document_language}"
            )

        except Exception as e:
            logger.error(f"Failed to store document metadata: {e}")
            # Don't fail the upload, just log the error
