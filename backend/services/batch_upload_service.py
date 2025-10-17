"""
Batch Upload Service for managing batch document uploads.

Provides batch upload functionality with background processing,
progress tracking, and real-time status updates via SSE.
"""

import logging
import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import UploadFile

from backend.db.repositories.batch_upload_repository import BatchUploadRepository
from backend.services.document_service import DocumentService, DocumentServiceError
from backend.db.models.document import BatchUpload

logger = logging.getLogger(__name__)


class BatchUploadServiceError(Exception):
    """Custom exception for batch upload service errors."""

    pass


class BatchUploadService:
    """
    Service for managing batch document uploads.

    Features:
    - Batch validation (file count and total size)
    - Background processing with progress tracking
    - Real-time progress updates via SSE
    - Individual file error handling
    - Failed file tracking in metadata
    """

    # Maximum limits for batch uploads
    MAX_BATCH_FILES = 100
    MAX_BATCH_SIZE_BYTES = 100 * 1024 * 1024  # 100MB

    def __init__(
        self,
        batch_upload_repository: BatchUploadRepository,
        document_service: DocumentService,
    ):
        """
        Initialize BatchUploadService.

        Args:
            batch_upload_repository: Repository for batch upload database operations
            document_service: Service for individual document uploads
        """
        self.batch_repo = batch_upload_repository
        self.document_service = document_service

        logger.info("BatchUploadService initialized")

    async def create_batch(self, user_id: UUID, files: List[UploadFile]) -> BatchUpload:
        """
        Create a new batch upload job with validation.

        Validates:
        - File count ≤ 100
        - Total size ≤ 100MB

        Args:
            user_id: User's unique identifier
            files: List of uploaded files

        Returns:
            BatchUpload: Created batch upload record

        Raises:
            ValueError: If validation fails
            BatchUploadServiceError: If batch creation fails
        """
        try:
            logger.info(
                f"Creating batch upload for user {user_id} with {len(files)} files"
            )

            # Validate file count
            if len(files) == 0:
                raise ValueError("No files provided for batch upload")

            if len(files) > self.MAX_BATCH_FILES:
                raise ValueError(
                    f"Too many files: {len(files)}. "
                    f"Maximum allowed: {self.MAX_BATCH_FILES}"
                )

            # Calculate total size and validate
            total_size = 0
            file_info = []

            for file in files:
                # Read file to get size (we need to do this anyway for upload)
                # Store content temporarily to avoid re-reading
                content = await file.read()
                file_size = len(content)
                total_size += file_size

                # Reset file pointer for later processing
                await file.seek(0)

                file_info.append(
                    {
                        "filename": file.filename,
                        "size": file_size,
                        "content_type": file.content_type,
                    }
                )

                logger.debug(
                    f"File: {file.filename}, size: {file_size} bytes "
                    f"({file_size / 1024 / 1024:.2f} MB)"
                )

            # Validate total size
            if total_size > self.MAX_BATCH_SIZE_BYTES:
                raise ValueError(
                    f"Total batch size {total_size / 1024 / 1024:.2f}MB exceeds "
                    f"maximum {self.MAX_BATCH_SIZE_BYTES / 1024 / 1024:.2f}MB"
                )

            logger.info(
                f"Batch validation passed: {len(files)} files, "
                f"total size: {total_size / 1024 / 1024:.2f}MB"
            )

            # Create batch record with metadata
            metadata = {
                "total_size_bytes": total_size,
                "files": file_info,
                "failed_files": [],  # Will be populated during processing
            }

            batch = self.batch_repo.create_batch(
                user_id=user_id, total_files=len(files), metadata=metadata
            )

            logger.info(
                f"Batch upload created: {batch.id} for user {user_id} "
                f"({len(files)} files, {total_size / 1024 / 1024:.2f}MB)"
            )

            return batch

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(
                f"Failed to create batch upload for user {user_id}: {e}", exc_info=True
            )
            raise BatchUploadServiceError(f"Failed to create batch upload: {e}")

    async def process_batch_background(
        self, batch_id: UUID, user_id: UUID, files: List[UploadFile]
    ) -> None:
        """
        Process batch upload in background with concurrent processing.

        Processes files concurrently (up to 5 at a time) for better performance.
        Individual file failures don't stop the batch processing.
        Failed file names are recorded in batch metadata.

        Args:
            batch_id: Batch upload UUID
            user_id: User's unique identifier
            files: List of uploaded files to process
        """
        completed = 0
        failed = 0
        failed_files = []

        # Concurrency limit to avoid overwhelming the system
        MAX_CONCURRENT = 5

        try:
            logger.info(
                f"Starting background processing for batch {batch_id} "
                f"({len(files)} files, max {MAX_CONCURRENT} concurrent)"
            )

            # Update status to processing
            self.batch_repo.update_batch_status(batch_id, "processing")

            # Process files in chunks for concurrent processing
            async def process_single_file(
                file: UploadFile, file_num: int
            ) -> tuple[bool, Optional[dict]]:
                """Process a single file and return (success, error_info)."""
                try:
                    logger.info(
                        f"Processing file {file_num}/{len(files)} "
                        f"in batch {batch_id}: {file.filename}"
                    )

                    # Upload document using DocumentService
                    document = await self.document_service.upload_document(
                        user_id=user_id, file=file
                    )

                    logger.info(
                        f"File {file_num}/{len(files)} completed: {file.filename} "
                        f"(document_id: {document.id})"
                    )

                    return (True, None)

                except (DocumentServiceError, ValueError) as e:
                    # Individual file failure
                    error_info = {
                        "filename": file.filename,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    logger.warning(
                        f"File {file_num}/{len(files)} failed: {file.filename} - {e}"
                    )

                    return (False, error_info)

                except Exception as e:
                    # Unexpected error
                    error_info = {
                        "filename": file.filename,
                        "error": f"Unexpected error: {e}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    logger.error(
                        f"Unexpected error processing file {file_num}/{len(files)} "
                        f"({file.filename}) in batch {batch_id}: {e}",
                        exc_info=True,
                    )

                    return (False, error_info)

            # Process files in batches with concurrency limit
            for i in range(0, len(files), MAX_CONCURRENT):
                chunk = files[i : i + MAX_CONCURRENT]
                chunk_start = i + 1

                # Process chunk concurrently
                tasks = [
                    process_single_file(file, chunk_start + idx)
                    for idx, file in enumerate(chunk)
                ]

                results = await asyncio.gather(*tasks, return_exceptions=False)

                # Update counters
                for success, error_info in results:
                    if success:
                        completed += 1
                    else:
                        failed += 1
                        if error_info:
                            failed_files.append(error_info)

                # Update progress after each chunk
                try:
                    batch = self.batch_repo.update_batch_progress(
                        batch_id=batch_id, completed=completed, failed=failed
                    )

                    if batch:
                        logger.debug(
                            f"Batch {batch_id} progress updated: "
                            f"{completed} completed, {failed} failed"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to update batch progress for {batch_id}: {e}",
                        exc_info=True,
                    )
                    # Continue processing even if progress update fails

            # Update batch metadata with failed files
            try:
                batch = self.batch_repo.get_batch_by_id(batch_id, user_id)
                if batch:
                    metadata = batch.extra_metadata or {}
                    metadata["failed_files"] = failed_files

                    # Update metadata in database
                    self.batch_repo.update_batch_metadata(batch_id, metadata)

                    if failed_files:
                        logger.info(
                            f"Batch {batch_id} completed with {failed} failures. "
                            f"Failed files: {[f['filename'] for f in failed_files]}"
                        )
                    else:
                        logger.info(
                            f"Batch {batch_id} completed successfully with no failures"
                        )
            except Exception as e:
                logger.error(
                    f"Failed to update batch metadata for {batch_id}: {e}",
                    exc_info=True,
                )

            # Final status update
            final_status = "completed" if failed < len(files) else "failed"
            self.batch_repo.update_batch_status(batch_id, final_status)

            logger.info(
                f"Batch {batch_id} processing completed: "
                f"{completed} succeeded, {failed} failed, status: {final_status}"
            )

        except Exception as e:
            # Critical error during batch processing
            logger.error(
                f"Critical error during batch {batch_id} processing: {e}", exc_info=True
            )

            # Update batch status to failed
            try:
                self.batch_repo.update_batch_status(batch_id, "failed")
            except Exception as status_error:
                logger.error(f"Failed to update batch status to failed: {status_error}")

    async def get_batch_status(
        self, batch_id: UUID, user_id: UUID
    ) -> Optional[BatchUpload]:
        """
        Get batch upload status with ownership verification.

        Args:
            batch_id: Batch upload UUID
            user_id: User's unique identifier (for ownership verification)

        Returns:
            Optional[BatchUpload]: Batch upload record if found and owned by user

        Raises:
            BatchUploadServiceError: If retrieval fails
        """
        try:
            logger.debug(f"Getting batch status for {batch_id}, user {user_id}")

            batch = self.batch_repo.get_batch_by_id(batch_id, user_id)

            if batch:
                logger.debug(
                    f"Batch {batch_id} status: {batch.status}, "
                    f"progress: {batch.completed_files + batch.failed_files}/"
                    f"{batch.total_files}"
                )
            else:
                logger.debug(
                    f"Batch {batch_id} not found or not owned by user {user_id}"
                )

            return batch

        except Exception as e:
            logger.error(f"Failed to get batch status: {e}", exc_info=True)
            raise BatchUploadServiceError(f"Failed to get batch status: {e}")

    async def stream_batch_progress(
        self, batch_id: UUID, user_id: UUID
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream real-time batch progress updates via SSE.

        Polls the database for progress updates and yields them as
        Server-Sent Events (SSE) formatted dictionaries.

        Args:
            batch_id: Batch upload UUID
            user_id: User's unique identifier (for ownership verification)

        Yields:
            Dict[str, Any]: Progress update with batch status

        Raises:
            BatchUploadServiceError: If batch not found or access denied
        """
        try:
            logger.info(
                f"Starting progress stream for batch {batch_id}, user {user_id}"
            )

            # Verify batch exists and user owns it
            batch = await self.get_batch_status(batch_id, user_id)
            if not batch:
                raise BatchUploadServiceError(
                    f"Batch {batch_id} not found or access denied"
                )

            # Track last known state to detect changes
            last_completed = -1
            last_failed = -1
            last_status = None

            # Stream updates until batch is complete
            while True:
                # Get current batch status
                batch = await self.get_batch_status(batch_id, user_id)

                if not batch:
                    logger.warning(f"Batch {batch_id} disappeared during streaming")
                    break

                # Check if there's an update
                if (
                    batch.completed_files != last_completed
                    or batch.failed_files != last_failed
                    or batch.status != last_status
                ):
                    # Calculate progress percentage
                    total_processed = batch.completed_files + batch.failed_files
                    progress_percent = (
                        (total_processed / batch.total_files * 100)
                        if batch.total_files > 0
                        else 0
                    )

                    # Get failed file names from metadata
                    failed_file_names = []
                    if batch.extra_metadata and "failed_files" in batch.extra_metadata:
                        failed_file_names = [
                            f["filename"] for f in batch.extra_metadata["failed_files"]
                        ]

                    # Yield progress update
                    update = {
                        "batch_id": str(batch.id),
                        "status": batch.status,
                        "total_files": batch.total_files,
                        "completed_files": batch.completed_files,
                        "failed_files": batch.failed_files,
                        "progress_percent": round(progress_percent, 2),
                        "failed_file_names": failed_file_names,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    logger.debug(
                        f"Batch {batch_id} progress: {total_processed}/"
                        f"{batch.total_files} ({progress_percent:.1f}%), "
                        f"status: {batch.status}"
                    )

                    yield update

                    # Update last known state
                    last_completed = batch.completed_files
                    last_failed = batch.failed_files
                    last_status = batch.status

                # Check if batch is complete
                if batch.status in ("completed", "failed"):
                    logger.info(f"Batch {batch_id} processing finished: {batch.status}")
                    break

                # Wait before next poll (1 second)
                await asyncio.sleep(1)

            logger.info(f"Progress stream ended for batch {batch_id}")

        except BatchUploadServiceError:
            # Re-raise service errors
            raise
        except Exception as e:
            logger.error(
                f"Error streaming batch progress for {batch_id}: {e}", exc_info=True
            )
            raise BatchUploadServiceError(f"Failed to stream batch progress: {e}")


# Singleton instance
_batch_upload_service: Optional[BatchUploadService] = None


def get_batch_upload_service(
    batch_upload_repository: BatchUploadRepository, document_service: DocumentService
) -> BatchUploadService:
    """
    Get or create BatchUploadService singleton instance.

    Args:
        batch_upload_repository: Repository for batch upload database operations
        document_service: Service for individual document uploads

    Returns:
        BatchUploadService: Singleton instance
    """
    global _batch_upload_service

    if _batch_upload_service is None:
        _batch_upload_service = BatchUploadService(
            batch_upload_repository=batch_upload_repository,
            document_service=document_service,
        )

    return _batch_upload_service
