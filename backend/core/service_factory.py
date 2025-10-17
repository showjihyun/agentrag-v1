"""
Service Factory for centralized service instance creation.

This module provides a factory pattern for creating service instances
with proper dependency injection, reducing code duplication across API endpoints.
"""

from typing import Optional
from sqlalchemy.orm import Session

from backend.services.document_service import DocumentService
from backend.services.conversation_service import ConversationService
from backend.services.batch_upload_service import BatchUploadService
from backend.services.document_processor import DocumentProcessor
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.services.file_storage_service import FileStorageService
from backend.db.repositories.document_repository import DocumentRepository
from backend.db.repositories.user_repository import UserRepository
from backend.db.repositories.batch_upload_repository import BatchUploadRepository


class ServiceFactory:
    """
    Factory for creating service instances with dependency injection.

    This centralizes service creation logic and reduces code duplication
    across API endpoints.
    """

    @staticmethod
    def create_document_service(
        db: Session,
        doc_processor: Optional[DocumentProcessor] = None,
        embedding_service: Optional[EmbeddingService] = None,
        milvus_manager: Optional[MilvusManager] = None,
        file_storage: Optional[FileStorageService] = None,
    ) -> DocumentService:
        """
        Create DocumentService instance with all dependencies.

        Args:
            db: Database session
            doc_processor: Optional document processor (will be created if None)
            embedding_service: Optional embedding service (will be created if None)
            milvus_manager: Optional Milvus manager (will be created if None)
            file_storage: Optional file storage service (will be created if None)

        Returns:
            Configured DocumentService instance
        """
        # Create repositories
        document_repo = DocumentRepository(db)
        user_repo = UserRepository(db)

        # Create or use provided services
        if file_storage is None:
            file_storage = FileStorageService()

        # Note: doc_processor, embedding_service, milvus_manager should be
        # provided via dependency injection from FastAPI Depends()

        return DocumentService(
            document_repository=document_repo,
            user_repository=user_repo,
            file_storage_service=file_storage,
            document_processor=doc_processor,
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
        )

    @staticmethod
    def create_conversation_service(db: Session) -> ConversationService:
        """
        Create ConversationService instance.

        Args:
            db: Database session

        Returns:
            Configured ConversationService instance
        """
        return ConversationService(db)

    @staticmethod
    def create_batch_upload_service(
        db: Session, document_service: Optional[DocumentService] = None
    ) -> BatchUploadService:
        """
        Create BatchUploadService instance.

        Args:
            db: Database session
            document_service: Optional document service (will be created if None)

        Returns:
            Configured BatchUploadService instance
        """
        batch_upload_repo = BatchUploadRepository(db)

        # Create document service if not provided
        if document_service is None:
            document_service = ServiceFactory.create_document_service(db)

        return BatchUploadService(
            batch_upload_repository=batch_upload_repo, document_service=document_service
        )
