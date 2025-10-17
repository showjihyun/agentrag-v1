"""Document management API endpoints."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
)
from sqlalchemy.orm import Session

from backend.services.document_processor import DocumentProcessor
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.services.document_service import DocumentService, DocumentServiceError
from backend.services.batch_upload_service import (
    BatchUploadService,
    BatchUploadServiceError,
)
from backend.models.document import (
    DocumentResponse,
    DocumentListResponse,
    BatchUploadResponse,
    BatchProgressResponse,
)
from backend.db.database import get_db
from backend.db.repositories.document_repository import DocumentRepository
from backend.db.repositories.user_repository import UserRepository
from backend.db.repositories.batch_upload_repository import BatchUploadRepository
from backend.db.models.user import User
from backend.core.auth_dependencies import get_current_user, get_optional_user
from backend.core.dependencies import (
    get_document_processor,
    get_embedding_service,
    get_milvus_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


# Storage quota limits (from config)
from backend.config import settings

MAX_STORAGE_BYTES = 1 * 1024 * 1024 * 1024  # 1GB default
MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # From .env
MAX_BATCH_SIZE_BYTES = settings.MAX_BATCH_SIZE_MB * 1024 * 1024  # From .env


# Dependency to get DocumentService
async def get_document_service_dep(
    db: Session = Depends(get_db),
    doc_processor: DocumentProcessor = Depends(get_document_processor),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    milvus_manager: MilvusManager = Depends(get_milvus_manager),
) -> DocumentService:
    """Create DocumentService instance with all dependencies."""
    document_repo = DocumentRepository(db)
    user_repo = UserRepository(db)
    from backend.services.file_storage_service import FileStorageService

    file_storage = FileStorageService()

    return DocumentService(
        document_repository=document_repo,
        user_repository=user_repo,
        file_storage_service=file_storage,
        document_processor=doc_processor,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )


# Dependency to get BatchUploadService
async def get_batch_upload_service_dep(
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service_dep),
) -> BatchUploadService:
    """Create BatchUploadService instance with all dependencies."""
    batch_upload_repo = BatchUploadRepository(db)

    return BatchUploadService(
        batch_upload_repository=batch_upload_repo, document_service=document_service
    )


@router.post(
    "/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    replace_existing: bool = True,
    current_user: Optional[User] = Depends(get_optional_user),
    document_service: DocumentService = Depends(get_document_service_dep),
    db: Session = Depends(get_db),
):
    """
    Upload and process a single document with version management (optional authentication).

    Supported formats: PDF, TXT, DOCX, HWP, HWPX
    Maximum file size: 10MB

    Version Management:
    - If file with same name exists and content is identical ??skip (return existing)
    - If file with same name exists and content is different ??create new version
    - If replace_existing=True ??archive old version and replace vectors
    - If replace_existing=False ??keep both versions

    The document will be:
    1. Validated for file type and size
    2. Checked for duplicates (by filename and hash)
    3. Checked against user's storage quota
    4. Saved to user's storage directory
    5. Processed and chunked
    6. Embedded using the configured model
    7. Stored in the vector database with user_id metadata
    8. User storage quota updated

    Args:
        file: Document file to upload
        replace_existing: If True, replace old version; if False, keep both
        current_user: Authenticated user (from JWT token)
        document_service: Document service instance
        db: Database session

    Returns:
        DocumentResponse: Created or existing document with metadata

    Raises:
        400: Invalid file type or size
        413: Storage quota exceeded
        422: Processing failed
        500: Internal server error
    """
    try:
        # Handle guest user (development mode)
        if not current_user:
            logger.warning(
                "Guest upload: creating temporary guest user (development mode only!)"
            )
            # Create a temporary guest user for development
            from backend.db.repositories.user_repository import UserRepository

            user_repo = UserRepository(db)

            # Try to get or create a guest user
            guest_user = user_repo.get_user_by_email("guest@localhost")
            if not guest_user:
                from backend.db.models.user import User
                import uuid

                guest_user = User(
                    id=uuid.uuid4(),
                    email="guest@localhost",
                    username="guest",
                    password_hash="",  # No password for guest
                    role="user",
                )
                db.add(guest_user)
                db.commit()
                db.refresh(guest_user)
            current_user = guest_user

        logger.info(
            f"Received upload request from user {current_user.id} ({current_user.email}): "
            f"{file.filename}"
        )

        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required"
            )

        # Read file to get size
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer

        # Validate file size
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size {file_size / 1024 / 1024:.2f}MB exceeds maximum {MAX_FILE_SIZE_BYTES / 1024 / 1024:.2f}MB",
            )

        # Check user storage quota
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(current_user.id)
        if user:
            current_storage = user.storage_used_bytes or 0
            if current_storage + file_size > MAX_STORAGE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Storage quota exceeded. Current: {current_storage / 1024 / 1024:.2f}MB, "
                    f"File: {file_size / 1024 / 1024:.2f}MB, "
                    f"Limit: {MAX_STORAGE_BYTES / 1024 / 1024:.2f}MB",
                )

        # Upload document with version management
        from backend.services.document_version_service import DocumentVersionService
        from backend.services.milvus import MilvusManager
        from backend.core.dependencies import get_milvus_manager

        # Get dependencies
        milvus_manager = await get_milvus_manager()
        version_service = DocumentVersionService(
            document_repository=DocumentRepository(db),
            user_repository=user_repo,
            document_service=document_service,
            milvus_manager=milvus_manager,
        )

        # Upload with versioning
        try:
            document = await version_service.upload_with_versioning(
                user_id=current_user.id, file=file, replace_existing=replace_existing
            )
        except ValueError as e:
            # Validation errors (file type, etc.)
            logger.warning(f"File validation failed: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except DocumentServiceError as e:
            # Service errors (processing, storage, etc.)
            logger.error(f"Document service error: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )

        logger.info(
            f"Document uploaded successfully: {document.id} "
            f"({document.chunk_count} chunks)"
        )

        # Return response using DocumentResponse model
        return DocumentResponse.from_db_model(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status_filter: Optional[str] = None,
    author_filter: Optional[str] = None,
    language_filter: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_optional_user),
    document_service: DocumentService = Depends(get_document_service_dep),
    db: Session = Depends(get_db),
):
    """
    List user's documents with optional filters (requires authentication).

    Supports filtering by:
    - Status (pending, processing, completed, failed)
    - Author
    - Language (ISO 639-1 code, e.g., 'en', 'ko')
    - Date range (creation date)

    Args:
        status_filter: Optional status filter
        author_filter: Optional author name filter (partial match)
        language_filter: Optional language code filter (exact match)
        from_date: Optional start date (ISO format: YYYY-MM-DD)
        to_date: Optional end date (ISO format: YYYY-MM-DD)
        limit: Maximum number of documents to return (default: 20)
        offset: Number of documents to skip for pagination (default: 0)
        current_user: Authenticated user (from JWT token)
        document_service: Document service instance

    Returns:
        DocumentListResponse: Paginated list of user's documents

    Raises:
        400: Invalid filter parameters
        401: Not authenticated
        500: Internal server error
    """
    try:
        user_id_str = current_user.id if current_user else "guest"
        logger.info(
            f"Listing documents for user {user_id_str} "
            f"(status={status_filter}, author={author_filter}, "
            f"language={language_filter}, from={from_date}, to={to_date}, "
            f"limit={limit}, offset={offset})"
        )

        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if author_filter:
            filters["author"] = author_filter
        if language_filter:
            filters["language"] = language_filter
        if from_date:
            try:
                filters["from_date"] = datetime.fromisoformat(from_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid from_date format. Use YYYY-MM-DD",
                )
        if to_date:
            try:
                filters["to_date"] = datetime.fromisoformat(to_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid to_date format. Use YYYY-MM-DD",
                )

        # Get user's documents with filters
        from backend.db.repositories.document_repository import DocumentRepository
        from backend.db.models.document import Document

        doc_repo = DocumentRepository(db)

        # Build query
        # If user is authenticated, show only their documents
        # If guest (development mode), show all documents
        if current_user:
            query = db.query(Document).filter(Document.user_id == current_user.id)
        else:
            # Guest access (development mode) - show all documents
            logger.warning(
                "?�️  Guest access: showing all documents (development mode only!)"
            )
            query = db.query(Document)

        # Apply filters
        if filters.get("status"):
            query = query.filter(Document.status == filters["status"])
        if filters.get("author"):
            query = query.filter(
                Document.document_author.ilike(f"%{filters['author']}%")
            )
        if filters.get("language"):
            query = query.filter(Document.document_language == filters["language"])
        if filters.get("from_date"):
            query = query.filter(
                Document.document_creation_date >= filters["from_date"]
            )
        if filters.get("to_date"):
            query = query.filter(Document.document_creation_date <= filters["to_date"])

        # Get total count
        total = query.count()

        # Apply pagination and get results
        documents = (
            query.order_by(Document.uploaded_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        logger.info(
            f"Found {len(documents)} documents for user {user_id_str} "
            f"(total: {total} with filters)"
        )

        # Convert to response models
        document_responses = [DocumentResponse.from_db_model(doc) for doc in documents]

        return DocumentListResponse(
            documents=document_responses, total=total, limit=limit, offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_details(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service_dep),
):
    """
    Get details for a specific document (requires authentication).

    Verifies that the document belongs to the authenticated user.

    Args:
        document_id: Document UUID
        current_user: Authenticated user (from JWT token)
        document_service: Document service instance

    Returns:
        DocumentResponse: Document details

    Raises:
        401: Not authenticated
        403: Document not owned by user
        404: Document not found
        500: Internal server error
    """
    try:
        logger.info(
            f"Getting details for document {document_id}, user {current_user.id}"
        )

        # Get document with ownership verification
        document = await document_service.get_document(
            document_id=document_id, user_id=current_user.id
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found or access denied",
            )

        logger.info(f"Retrieved document {document_id}")

        return DocumentResponse.from_db_model(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document details: {str(e)}",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    document_service: DocumentService = Depends(get_document_service_dep),
):
    """
    Delete a document and all associated data (optional authentication).

    Verifies that the document belongs to the authenticated user.
    Deletes:
    - Vectors from Milvus
    - File from storage
    - Document record from database
    - Updates user storage quota

    Args:
        document_id: Document UUID
        current_user: Authenticated user (from JWT token)
        document_service: Document service instance

    Returns:
        204 No Content on success

    Raises:
        401: Not authenticated
        403: Document not owned by user
        404: Document not found
        500: Internal server error
    """
    try:
        # Handle guest user (development mode)
        if not current_user:
            logger.warning(
                "?�️  Guest delete: using guest user (development mode only!)"
            )
            from backend.db.repositories.user_repository import UserRepository
            from backend.db.database import get_db

            # Get guest user
            db = next(get_db())
            user_repo = UserRepository(db)
            guest_user = user_repo.get_user_by_email("guest@localhost")
            if guest_user:
                current_user = guest_user
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

        logger.info(f"Deleting document {document_id} for user {current_user.id}")

        # Delete document with ownership verification
        try:
            await document_service.delete_document(
                document_id=document_id, user_id=current_user.id
            )
        except ValueError as e:
            # Document not found or not owned by user
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except DocumentServiceError as e:
            # Service error
            logger.error(f"Document service error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

        logger.info(f"Document {document_id} deleted successfully")

        # Return 204 No Content (no response body)
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@router.post(
    "/batch", response_model=BatchUploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(
        ..., description="Multiple document files to upload"
    ),
    current_user: User = Depends(get_current_user),
    batch_upload_service: BatchUploadService = Depends(get_batch_upload_service_dep),
    db: Session = Depends(get_db),
):
    """
    Upload multiple documents in a batch (requires authentication).

    Supports up to 100 files with a total size of 100MB.
    Processing happens in the background, and progress can be tracked via the batch ID.

    Args:
        background_tasks: FastAPI BackgroundTasks for async processing
        files: List of document files to upload
        current_user: Authenticated user (from JWT token)
        batch_upload_service: Batch upload service instance
        db: Database session

    Returns:
        BatchUploadResponse: Batch ID and status for tracking progress

    Raises:
        400: Invalid request (no files, too many files, total size too large)
        413: Storage quota exceeded
        422: Processing failed
        500: Internal server error
    """
    try:
        logger.info(
            f"Received batch upload request from user {current_user.id} ({current_user.email}): "
            f"{len(files)} files"
        )

        # Validate files list
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided for batch upload",
            )

        # Calculate total size for quota check
        total_size = 0
        for file in files:
            content = await file.read()
            total_size += len(content)
            await file.seek(0)  # Reset file pointer

        # Check user storage quota
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(current_user.id)
        if user:
            current_storage = user.storage_used_bytes or 0
            if current_storage + total_size > MAX_STORAGE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Storage quota exceeded. Current: {current_storage / 1024 / 1024:.2f}MB, "
                    f"Batch: {total_size / 1024 / 1024:.2f}MB, "
                    f"Limit: {MAX_STORAGE_BYTES / 1024 / 1024:.2f}MB",
                )

        # Create batch record with validation
        try:
            batch = await batch_upload_service.create_batch(
                user_id=current_user.id, files=files
            )
        except ValueError as e:
            # Validation errors (file count, size, etc.)
            logger.warning(f"Batch validation failed: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except BatchUploadServiceError as e:
            # Service errors
            logger.error(f"Batch upload service error: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )

        # Schedule background processing using FastAPI BackgroundTasks
        background_tasks.add_task(
            batch_upload_service.process_batch_background,
            batch.id,
            current_user.id,
            files,
        )

        logger.info(
            f"Batch upload created and scheduled for background processing: {batch.id} "
            f"({len(files)} files)"
        )

        # Return response immediately using BatchUploadResponse model
        return BatchUploadResponse.model_validate(batch)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch upload: {str(e)}",
        )


@router.get("/batch/{batch_id}", response_model=BatchProgressResponse)
async def get_batch_status(
    batch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    batch_upload_service: BatchUploadService = Depends(get_batch_upload_service_dep),
):
    """
    Get the status of a batch upload (requires authentication).

    Verifies that the batch belongs to the authenticated user.
    Returns current progress including completed and failed file counts.

    Args:
        batch_id: Batch upload UUID
        current_user: Authenticated user (from JWT token)
        batch_upload_service: Batch upload service instance

    Returns:
        BatchProgressResponse: Batch progress information

    Raises:
        401: Not authenticated
        403: Batch not owned by user
        404: Batch not found
        500: Internal server error
    """
    try:
        logger.info(f"Getting batch status for {batch_id}, user {current_user.id}")

        # Get batch status with ownership verification
        try:
            batch = await batch_upload_service.get_batch_status(
                batch_id=batch_id, user_id=current_user.id
            )
        except BatchUploadServiceError as e:
            logger.error(f"Failed to get batch status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {batch_id} not found or access denied",
            )

        # Get failed file names from metadata
        failed_file_names = []
        if batch.extra_metadata and "failed_files" in batch.extra_metadata:
            failed_file_names = [
                f["filename"] for f in batch.extra_metadata["failed_files"]
            ]

        # Return response using BatchProgressResponse model
        return BatchProgressResponse(
            batch_id=batch.id,
            total_files=batch.total_files,
            completed_files=batch.completed_files,
            failed_files=batch.failed_files,
            status=batch.status,
            failed_file_names=failed_file_names,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch status: {str(e)}",
        )


@router.get("/batch/{batch_id}/progress")
async def stream_batch_progress(
    batch_id: uuid.UUID,
    token: Optional[str] = None,
    batch_upload_service: BatchUploadService = Depends(get_batch_upload_service_dep),
    db: Session = Depends(get_db),
):
    """
    Stream real-time batch upload progress via Server-Sent Events (SSE).

    Verifies that the batch belongs to the authenticated user.
    This endpoint keeps the connection open and sends progress updates
    as the batch is being processed in the background.

    **Authentication**:
    Since EventSource doesn't support custom headers, authentication is done via
    query parameter. The token is validated and the user is extracted.

    Args:
        batch_id: Batch upload UUID
        token: JWT access token (query parameter)
        batch_upload_service: Batch upload service instance
        db: Database session

    Returns:
        StreamingResponse: SSE stream with progress updates

    Raises:
        401: Not authenticated or invalid token
        403: Batch not owned by user
        404: Batch not found
        500: Internal server error
    """
    from fastapi.responses import StreamingResponse
    import json
    from backend.services.auth_service import AuthService
    from db.repositories.user_repository import UserRepository

    # Validate token and get user
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
        )

    # Decode token
    payload = AuthService.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    # Get user ID from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in token"
        )

    # Verify user exists and is active
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    async def event_generator():
        """Generate SSE events for batch progress."""
        try:
            logger.info(f"Starting SSE stream for batch {batch_id}, user {user.id}")

            # Stream progress updates
            try:
                async for progress in batch_upload_service.stream_batch_progress(
                    batch_id=batch_id, user_id=user.id
                ):
                    # Format as SSE event
                    # Convert UUID to string for JSON serialization
                    if "batch_id" in progress and isinstance(
                        progress["batch_id"], uuid.UUID
                    ):
                        progress["batch_id"] = str(progress["batch_id"])

                    data = json.dumps(progress)
                    yield f"data: {data}\n\n"

            except BatchUploadServiceError as e:
                logger.error(f"Batch upload service error: {e}")
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"

        except Exception as e:
            logger.error(f"Error streaming batch progress: {e}", exc_info=True)
            error_data = json.dumps({"error": f"Failed to stream progress: {str(e)}"})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/versions/{filename:path}", response_model=List[DocumentResponse])
async def get_document_versions(
    filename: str,
    include_archived: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get version history for a document (requires authentication).

    Returns all versions of a document with the specified filename,
    ordered by version number (newest first).

    Args:
        filename: Document filename
        include_archived: Whether to include archived versions
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        List[DocumentResponse]: List of document versions

    Raises:
        401: Not authenticated
        404: No versions found
        500: Internal server error
    """
    try:
        logger.info(f"Getting version history for {filename}, user {current_user.id}")

        # Get version history
        doc_repo = DocumentRepository(db)
        versions = doc_repo.get_version_history(
            user_id=current_user.id,
            filename=filename,
            include_archived=include_archived,
        )

        if not versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No versions found for {filename}",
            )

        logger.info(f"Found {len(versions)} versions for {filename}")

        # Convert to response models
        return [DocumentResponse.from_db_model(v) for v in versions]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version history: {str(e)}",
        )


@router.get("/compare/{document_id_1}/{document_id_2}")
async def compare_document_versions(
    document_id_1: uuid.UUID,
    document_id_2: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compare two document versions (requires authentication).

    Returns comparison information including:
    - Basic metadata for both versions
    - Content differences (hash comparison)
    - Size and chunk count differences

    Args:
        document_id_1: First document UUID
        document_id_2: Second document UUID
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        Dict: Comparison information

    Raises:
        401: Not authenticated
        403: Documents not owned by user
        404: One or both documents not found
        500: Internal server error
    """
    try:
        logger.info(
            f"Comparing documents {document_id_1} and {document_id_2}, "
            f"user {current_user.id}"
        )

        # Get version service
        from backend.services.document_version_service import DocumentVersionService
        from backend.services.milvus import MilvusManager
        from backend.core.dependencies import (
            get_milvus_manager,
            get_document_service_dep,
        )

        doc_repo = DocumentRepository(db)
        user_repo = UserRepository(db)
        milvus_manager = await get_milvus_manager()
        document_service = await get_document_service_dep(db)

        version_service = DocumentVersionService(
            document_repository=doc_repo,
            user_repository=user_repo,
            document_service=document_service,
            milvus_manager=milvus_manager,
        )

        # Get comparison
        comparison = version_service.get_version_comparison(
            document_id_1=document_id_1,
            document_id_2=document_id_2,
            user_id=current_user.id,
        )

        logger.info("Version comparison completed")

        return comparison

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare versions: {str(e)}",
        )



@router.post(
    "/upload-audio",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file to upload (wav, mp3, flac, etc.)"),
    chunk_duration: float = 30.0,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service_dep),
) -> DocumentResponse:
    """
    오디오 파일 업로드 및 인덱싱
    
    Features:
    - WavRAG 스타일 직접 오디오 임베딩
    - 자동 청킹 (긴 오디오)
    - 음성 정보 보존
    - 텍스트 변환 (선택)
    
    Args:
        file: 오디오 파일 (wav, mp3, flac, m4a, ogg)
        chunk_duration: 청킹 길이 (초, 0이면 청킹 안함)
    
    Returns:
        DocumentResponse with audio metadata
    """
    try:
        # 파일 형식 검증
        allowed_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.opus'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio format: {file_ext}. "
                       f"Allowed: {', '.join(allowed_extensions)}"
            )
        
        # 파일 크기 검증
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large: {file_size / 1024 / 1024:.2f}MB. "
                       f"Max: {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f}MB"
            )
        
        # 임시 파일 저장
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # 멀티모달 서비스로 처리
            from backend.services.multimodal_document_service import get_multimodal_document_service
            multimodal_service = get_multimodal_document_service()
            
            document_id = str(uuid.uuid4())
            
            result = await multimodal_service.process_audio_document(
                audio_path=tmp_path,
                document_id=document_id,
                metadata={
                    'filename': file.filename,
                    'file_size': file_size,
                    'user_id': str(current_user.id),
                    'upload_time': datetime.utcnow().isoformat()
                },
                chunk_duration=chunk_duration
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Audio processing failed: {result.get('error', 'Unknown error')}"
                )
            
            # 응답 생성
            response = DocumentResponse(
                id=uuid.UUID(document_id),
                filename=file.filename,
                file_size=file_size,
                status="completed",
                user_id=current_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={
                    'type': 'audio',
                    'duration': result['duration'],
                    'transcription': result.get('transcription', ''),
                    'num_chunks': result['num_chunks'],
                    'audio_ids': result['audio_ids'],
                    'method': result['method']
                }
            )
            
            logger.info(
                f"✅ Audio uploaded: {file.filename} "
                f"({result['duration']:.2f}s, {result['num_chunks']} chunks)"
            )
            
            return response
            
        finally:
            # 임시 파일 삭제
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio upload failed: {str(e)}"
        )


@router.post("/upload-image", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload (jpg, png, etc.)"),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service_dep),
) -> DocumentResponse:
    """
    이미지 파일 업로드 및 인덱싱 (ColPali)
    
    Features:
    - ColPali 비전 임베딩
    - 텍스트, 표, 차트 인식
    - 고성능 검색
    
    Args:
        file: 이미지 파일 (jpg, png, pdf 페이지)
    
    Returns:
        DocumentResponse with image metadata
    """
    try:
        # 파일 형식 검증
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image format: {file_ext}. "
                       f"Allowed: {', '.join(allowed_extensions)}"
            )
        
        # 파일 크기 검증
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large: {file_size / 1024 / 1024:.2f}MB"
            )
        
        # 임시 파일 저장
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # 멀티모달 서비스로 처리
            from backend.services.multimodal_document_service import get_multimodal_document_service
            multimodal_service = get_multimodal_document_service()
            
            document_id = str(uuid.uuid4())
            
            result = await multimodal_service.process_image_document(
                image_path=tmp_path,
                document_id=document_id,
                metadata={
                    'filename': file.filename,
                    'file_size': file_size,
                    'user_id': str(current_user.id),
                    'upload_time': datetime.utcnow().isoformat()
                }
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Image processing failed: {result.get('error', 'Unknown error')}"
                )
            
            # 응답 생성
            response = DocumentResponse(
                id=uuid.UUID(document_id),
                filename=file.filename,
                file_size=file_size,
                status="completed",
                user_id=current_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={
                    'type': 'image',
                    'num_patches': result['num_patches'],
                    'image_id': result['image_id'],
                    'method': result['method']
                }
            )
            
            logger.info(f"✅ Image uploaded: {file.filename} ({result['num_patches']} patches)")
            
            return response
            
        finally:
            # 임시 파일 삭제
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )



@router.post("/search/multimodal")
async def search_multimodal(
    query: str = "",
    query_image: Optional[UploadFile] = File(None),
    query_audio: Optional[UploadFile] = File(None),
    top_k: int = 5,
    search_images: bool = True,
    search_text: bool = True,
    search_audio: bool = True,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    content_types: Optional[str] = None,
    speaker: Optional[str] = None,
    author: Optional[str] = None,
    language: Optional[str] = None,
    min_score: Optional[float] = None,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    멀티모달 검색 (Phase 3-4 개선)
    
    Features:
    - 텍스트 쿼리
    - 이미지 쿼리 (파일 업로드)
    - 오디오 쿼리 (파일 업로드)
    - 크로스 모달 검색
    - 메타데이터 필터링 (Phase 3)
    - 멀티모달 리랭킹 (Phase 3)
    - 통합 결과 반환
    
    Args:
        query: 텍스트 쿼리 (선택)
        query_image: 이미지 쿼리 파일 (선택)
        query_audio: 오디오 쿼리 파일 (선택)
        top_k: 반환할 결과 수
        search_images: 이미지 검색 활성화
        search_text: 텍스트 검색 활성화
        search_audio: 오디오 검색 활성화
        date_range_start: 시작 날짜 (YYYY-MM-DD)
        date_range_end: 종료 날짜 (YYYY-MM-DD)
        content_types: 콘텐츠 타입 (JSON 배열 문자열)
        speaker: 화자 이름
        author: 작성자 이름
        language: 언어 코드
        min_score: 최소 점수
    
    Returns:
        검색 결과
    """
    try:
        # 멀티모달 서비스
        from backend.services.multimodal_document_service import get_multimodal_document_service
        multimodal_service = get_multimodal_document_service()
        
        # 메타데이터 필터 서비스 (Phase 3)
        from backend.services.metadata_filter import get_metadata_filter
        metadata_filter = get_metadata_filter()
        
        # 필터 파싱
        import json
        parsed_content_types = None
        if content_types:
            try:
                parsed_content_types = json.loads(content_types)
            except:
                parsed_content_types = [content_types]
        
        # 필터 유효성 검증
        date_range = None
        if date_range_start or date_range_end:
            date_range = (date_range_start or '', date_range_end or '')
        
        is_valid, error_msg = metadata_filter.validate_filters(
            date_range=date_range,
            content_types=parsed_content_types
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filters: {error_msg}"
            )
        
        # 임시 파일 경로
        query_image_path = None
        query_audio_path = None
        
        try:
            # 이미지 쿼리 처리
            if query_image:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(query_image.filename).suffix) as tmp:
                    content = await query_image.read()
                    tmp.write(content)
                    query_image_path = tmp.name
            
            # 오디오 쿼리 처리
            if query_audio:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(query_audio.filename).suffix) as tmp:
                    content = await query_audio.read()
                    tmp.write(content)
                    query_audio_path = tmp.name
            
            # 멀티모달 검색 (리랭킹 자동 적용)
            results = await multimodal_service.search_multimodal(
                query=query,
                top_k=top_k,
                search_images=search_images,
                search_text=search_text,
                search_audio=search_audio,
                query_image_path=query_image_path,
                query_audio_path=query_audio_path
            )
            
            # 메타데이터 필터 적용 (Phase 3)
            if results.get('combined'):
                filters_dict = {}
                if speaker:
                    filters_dict['speaker'] = speaker
                if author:
                    filters_dict['author'] = author
                if language:
                    filters_dict['language'] = language
                
                results['combined'] = metadata_filter.apply_filters_to_results(
                    results=results['combined'],
                    filters=filters_dict if filters_dict else None,
                    min_score=min_score,
                    max_results=top_k
                )
            
            logger.info(
                f"Multimodal search (Phase 3-4): query={query}, "
                f"image={query_image is not None}, "
                f"audio={query_audio is not None}, "
                f"filters={bool(speaker or author or language)}, "
                f"results={len(results.get('combined', []))}"
            )
            
            return results
            
        finally:
            # 임시 파일 정리
            import os
            if query_image_path and os.path.exists(query_image_path):
                os.unlink(query_image_path)
            if query_audio_path and os.path.exists(query_audio_path):
                os.unlink(query_audio_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multimodal search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multimodal search failed: {str(e)}"
        )
