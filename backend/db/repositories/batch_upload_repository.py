"""Batch upload repository for database operations."""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime
import logging
from uuid import UUID

from backend.db.models.document import BatchUpload

logger = logging.getLogger(__name__)


class BatchUploadRepository:
    """Database operations for batch uploads."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_batch(
        self, user_id: UUID, total_files: int, metadata: Optional[dict] = None
    ) -> BatchUpload:
        """
        Create a new batch upload record.

        Args:
            user_id: User UUID
            total_files: Total number of files in the batch
            metadata: Optional metadata dictionary

        Returns:
            Created BatchUpload object

        Raises:
            IntegrityError: If database constraint is violated
        """
        try:
            batch = BatchUpload(
                user_id=user_id,
                total_files=total_files,
                completed_files=0,
                failed_files=0,
                status="pending",
                extra_metadata=metadata or {},
            )

            self.db.add(batch)
            self.db.commit()
            self.db.refresh(batch)

            logger.info(
                f"Created batch upload: {batch.id} for user {user_id} "
                f"(total_files={total_files})"
            )
            return batch

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create batch upload for user {user_id}: {e}")
            raise

    def update_batch_progress(
        self, batch_id: UUID, completed: int, failed: int
    ) -> Optional[BatchUpload]:
        """
        Update batch upload progress.

        Args:
            batch_id: Batch upload UUID
            completed: Number of completed files
            failed: Number of failed files

        Returns:
            Updated BatchUpload object if found, None otherwise
        """
        batch = self.db.query(BatchUpload).filter(BatchUpload.id == batch_id).first()

        if not batch:
            logger.warning(f"Cannot update progress for batch {batch_id}: not found")
            return None

        # Update progress
        batch.completed_files = completed
        batch.failed_files = failed

        # Update status based on progress
        if completed + failed >= batch.total_files:
            # All files processed
            if failed == 0:
                batch.status = "completed"
            elif completed == 0:
                batch.status = "failed"
            else:
                batch.status = "completed"  # Partial success still counts as completed

            batch.completed_at = datetime.utcnow()
        elif batch.status == "pending":
            # First file processed, mark as processing
            batch.status = "processing"
            if not batch.started_at:
                batch.started_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(batch)

            logger.info(
                f"Updated batch {batch_id} progress: "
                f"completed={completed}, failed={failed}, status={batch.status}"
            )

            return batch
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update batch {batch_id} progress: {e}")
            raise

    def update_batch_status(self, batch_id: UUID, status: str) -> Optional[BatchUpload]:
        """
        Update batch upload status.

        Args:
            batch_id: Batch upload UUID
            status: New status (pending, processing, completed, failed)

        Returns:
            Updated BatchUpload object if found, None otherwise
        """
        batch = self.db.query(BatchUpload).filter(BatchUpload.id == batch_id).first()

        if not batch:
            logger.warning(f"Cannot update status for batch {batch_id}: not found")
            return None

        # Update status
        old_status = batch.status
        batch.status = status

        # Update timestamps based on status
        if status == "processing" and not batch.started_at:
            batch.started_at = datetime.utcnow()
        elif status in ("completed", "failed") and not batch.completed_at:
            batch.completed_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(batch)

            logger.info(f"Updated batch {batch_id} status: {old_status} -> {status}")

            return batch
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update batch {batch_id} status: {e}")
            raise

    def get_batch_by_id(self, batch_id: UUID, user_id: UUID) -> Optional[BatchUpload]:
        """
        Get batch upload by ID with user ownership verification.

        Args:
            batch_id: Batch upload UUID
            user_id: User UUID (for ownership verification)

        Returns:
            BatchUpload object if found and owned by user, None otherwise
        """
        batch = (
            self.db.query(BatchUpload)
            .filter(BatchUpload.id == batch_id, BatchUpload.user_id == user_id)
            .first()
        )

        if batch:
            logger.debug(f"Found batch {batch_id} for user {user_id}")
        else:
            logger.debug(f"Batch {batch_id} not found or not owned by user {user_id}")

        return batch

    def update_batch_metadata(
        self, batch_id: UUID, metadata: dict
    ) -> Optional[BatchUpload]:
        """
        Update batch upload metadata.

        Args:
            batch_id: Batch upload UUID
            metadata: Metadata dictionary to update

        Returns:
            Updated BatchUpload object if found, None otherwise
        """
        batch = self.db.query(BatchUpload).filter(BatchUpload.id == batch_id).first()

        if not batch:
            logger.warning(f"Cannot update metadata for batch {batch_id}: not found")
            return None

        # Update metadata
        batch.extra_metadata = metadata

        try:
            self.db.commit()
            self.db.refresh(batch)

            logger.info(f"Updated batch {batch_id} metadata")

            return batch
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update batch {batch_id} metadata: {e}")
            raise

    def get_user_batches(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[BatchUpload]:
        """
        Get user's batch uploads.

        Args:
            user_id: User UUID
            limit: Maximum number of batches to return
            offset: Number of batches to skip

        Returns:
            List of BatchUpload objects ordered by created_at DESC
        """
        batches = (
            self.db.query(BatchUpload)
            .filter(BatchUpload.user_id == user_id)
            .order_by(BatchUpload.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        logger.debug(
            f"Retrieved {len(batches)} batch uploads for user {user_id} "
            f"(limit={limit}, offset={offset})"
        )

        return batches
