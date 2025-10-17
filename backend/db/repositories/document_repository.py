"""Document repository for database operations."""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
import logging
from uuid import UUID

from backend.db.models.document import Document

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Database operations for documents."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_document(
        self,
        user_id: UUID,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
    ) -> Document:
        """
        Create a new document record.

        Args:
            user_id: User UUID
            filename: Name of the file
            file_path: Path where file is stored
            file_size: Size of file in bytes
            mime_type: MIME type of the file

        Returns:
            Created Document object

        Raises:
            IntegrityError: If database constraint is violated
        """
        try:
            document = Document(
                user_id=user_id,
                filename=filename,
                original_filename=filename,
                file_path=file_path,
                file_size_bytes=file_size,
                mime_type=mime_type,
                status="pending",
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            logger.info(
                f"Created document: {document.id} for user {user_id} "
                f"(filename={filename}, size={file_size})"
            )
            return document

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create document for user {user_id}: {e}")
            raise

    def get_user_documents(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Document]:
        """
        Get user's documents with optional status filter.

        Args:
            user_id: User UUID
            status: Optional status filter (pending, processing, completed, failed)
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of Document objects ordered by uploaded_at DESC
        """
        query = self.db.query(Document).filter(Document.user_id == user_id)

        # Apply status filter if provided
        if status:
            query = query.filter(Document.status == status)

        documents = (
            query.order_by(Document.uploaded_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        logger.debug(
            f"Retrieved {len(documents)} documents for user {user_id} "
            f"(status={status}, limit={limit}, offset={offset})"
        )

        return documents

    def get_document_by_id(
        self, document_id: UUID, user_id: UUID
    ) -> Optional[Document]:
        """
        Get document by ID with user ownership verification.

        Args:
            document_id: Document UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Document object if found and owned by user, None otherwise
        """
        document = (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )

        if document:
            logger.debug(f"Found document {document_id} for user {user_id}")
        else:
            logger.debug(
                f"Document {document_id} not found or not owned by user {user_id}"
            )

        return document

    def update_document_status(
        self, document_id: UUID, status: str, error_message: Optional[str] = None
    ) -> Optional[Document]:
        """
        Update document processing status.

        Args:
            document_id: Document UUID
            status: New status (pending, processing, completed, failed)
            error_message: Optional error message if status is 'failed'

        Returns:
            Updated Document object if found, None otherwise
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()

        if not document:
            logger.warning(
                f"Cannot update status for document {document_id}: not found"
            )
            return None

        # Update status
        document.status = status

        # Update error message if provided
        if error_message:
            document.error_message = error_message

        # Update timestamps based on status
        if status == "processing" and not document.processing_started_at:
            document.processing_started_at = datetime.utcnow()
        elif status in ("completed", "failed"):
            document.processing_completed_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(document)

            logger.info(
                f"Updated document {document_id} status to '{status}'"
                + (f" with error: {error_message}" if error_message else "")
            )

            return document
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document {document_id} status: {e}")
            raise

    def update_document_processing(
        self, document_id: UUID, chunk_count: int, collection: str
    ) -> Optional[Document]:
        """
        Update document processing information after vectorization.

        Args:
            document_id: Document UUID
            chunk_count: Number of chunks created
            collection: Milvus collection name

        Returns:
            Updated Document object if found, None otherwise
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()

        if not document:
            logger.warning(
                f"Cannot update processing info for document {document_id}: not found"
            )
            return None

        # Update processing information
        document.chunk_count = chunk_count
        document.milvus_collection = collection

        try:
            self.db.commit()
            self.db.refresh(document)

            logger.info(
                f"Updated document {document_id} processing info: "
                f"chunks={chunk_count}, collection={collection}"
            )

            return document
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to update document {document_id} processing info: {e}"
            )
            raise

    def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        """
        Delete a document record.

        Args:
            document_id: Document UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if document was deleted, False if not found or not owned by user
        """
        document = self.get_document_by_id(document_id, user_id)

        if not document:
            logger.warning(
                f"Cannot delete document {document_id}: not found or not owned by user {user_id}"
            )
            return False

        try:
            self.db.delete(document)
            self.db.commit()

            logger.info(f"Deleted document {document_id} for user {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    def get_document_count(self, user_id: UUID) -> int:
        """
        Get total number of documents for a user.

        Args:
            user_id: User UUID

        Returns:
            Total document count
        """
        count = (
            self.db.query(func.count(Document.id))
            .filter(Document.user_id == user_id)
            .scalar()
        )

        logger.debug(f"User {user_id} has {count} documents")

        return count or 0

    def get_total_storage_used(self, user_id: UUID) -> int:
        """
        Get total storage used by user's documents in bytes.

        Args:
            user_id: User UUID

        Returns:
            Total storage used in bytes
        """
        total = (
            self.db.query(func.sum(Document.file_size_bytes))
            .filter(Document.user_id == user_id)
            .scalar()
        )

        logger.debug(f"User {user_id} storage used: {total or 0} bytes")

        return total or 0

    def get_documents_by_filename(self, user_id: UUID, filename: str) -> List[Document]:
        """
        Get all versions of a document by filename.

        Args:
            user_id: User UUID
            filename: Document filename

        Returns:
            List of Document objects (all versions) ordered by version DESC
        """
        try:
            documents = (
                self.db.query(Document)
                .filter(Document.user_id == user_id, Document.filename == filename)
                .order_by(Document.version.desc())
                .all()
            )

            logger.debug(
                f"Found {len(documents)} versions of {filename} for user {user_id}"
            )
            return documents

        except Exception as e:
            logger.error(f"Failed to get documents by filename: {e}")
            raise

    def get_document_by_hash(self, user_id: UUID, file_hash: str) -> Optional[Document]:
        """
        Get document by file hash (for deduplication).

        Args:
            user_id: User UUID
            file_hash: SHA-256 hash of file content

        Returns:
            Document object if found, None otherwise
        """
        try:
            document = (
                self.db.query(Document)
                .filter(
                    Document.user_id == user_id,
                    Document.file_hash == file_hash,
                    Document.status != "archived",
                )
                .first()
            )

            if document:
                logger.debug(
                    f"Found document with hash {file_hash[:16]}... for user {user_id}"
                )

            return document

        except Exception as e:
            logger.error(f"Failed to get document by hash: {e}")
            raise

    def get_version_history(
        self, user_id: UUID, filename: str, include_archived: bool = True
    ) -> List[Document]:
        """
        Get complete version history for a document.

        Args:
            user_id: User UUID
            filename: Document filename
            include_archived: Whether to include archived versions

        Returns:
            List of Document objects ordered by version DESC
        """
        try:
            query = self.db.query(Document).filter(
                Document.user_id == user_id, Document.filename == filename
            )

            if not include_archived:
                query = query.filter(Document.status != "archived")

            documents = query.order_by(Document.version.desc()).all()

            logger.info(
                f"Retrieved {len(documents)} versions of {filename} for user {user_id}"
            )
            return documents

        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            raise

    def update_document(self, document: Document) -> Document:
        """
        Update document record.

        Args:
            document: Document object with updated fields

        Returns:
            Updated Document object
        """
        try:
            self.db.commit()
            self.db.refresh(document)

            logger.debug(f"Updated document: {document.id}")
            return document

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update document {document.id}: {e}")
            raise
