"""Document and TextChunk models."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TextChunk(BaseModel):
    """Represents a chunk of text from a document."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    document_id: str = Field(..., description="ID of the parent document")
    text: str = Field(..., description="The actual text content")
    chunk_index: int = Field(..., description="Position of chunk in document")
    start_char: int = Field(
        ..., description="Starting character position in original document"
    )
    end_char: int = Field(
        ..., description="Ending character position in original document"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    embedding: Optional[list[float]] = Field(
        None, description="Vector embedding of the chunk"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": "doc123_chunk_0",
                "document_id": "doc123",
                "text": "This is a sample text chunk from the document.",
                "chunk_index": 0,
                "start_char": 0,
                "end_char": 46,
                "metadata": {"page": 1, "section": "Introduction"},
                "embedding": None,
            }
        }
    )


class Document(BaseModel):
    """Represents a document in the system."""

    document_id: str = Field(..., description="Unique identifier for the document")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (pdf, txt, docx, hwp, hwpx)")
    file_size: int = Field(..., description="File size in bytes")
    upload_timestamp: datetime = Field(
        default_factory=datetime.now, description="When document was uploaded"
    )
    processing_status: str = Field(
        default="pending", description="Status: pending, processing, completed, failed"
    )
    chunk_count: Optional[int] = Field(None, description="Number of chunks created")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if processing failed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "doc123",
                "filename": "research_paper.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "upload_timestamp": "2024-01-01T12:00:00",
                "processing_status": "completed",
                "chunk_count": 25,
                "metadata": {"author": "John Doe", "pages": 10},
                "error_message": None,
            }
        }
    )


# ============================================================================
# API Response Models
# ============================================================================


class DocumentResponse(BaseModel):
    """Response model for document information with frontend-compatible field names."""

    document_id: str = Field(..., description="Document ID")
    user_id: str = Field(..., description="Owner user ID")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="MIME type of the file")
    status: str = Field(
        ..., description="Processing status: pending, processing, completed, failed"
    )
    chunk_count: int = Field(default=0, description="Number of chunks created")
    created_at: datetime = Field(..., description="Upload timestamp")
    processing_completed_at: Optional[datetime] = Field(
        None, description="Processing completion timestamp"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if processing failed"
    )

    @classmethod
    def from_db_model(cls, db_document):
        """Create from database model"""
        return cls(
            document_id=str(db_document.id),
            user_id=str(db_document.user_id),
            filename=db_document.filename,
            file_size=db_document.file_size_bytes,
            file_type=db_document.mime_type or "application/octet-stream",
            status=db_document.status,
            chunk_count=db_document.chunk_count,
            created_at=db_document.uploaded_at,
            processing_completed_at=db_document.processing_completed_at,
            error_message=db_document.error_message,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "filename": "research_paper.pdf",
                "file_size": 1024000,
                "file_type": "application/pdf",
                "status": "completed",
                "chunk_count": 25,
                "created_at": "2024-01-01T12:00:00",
                "processing_completed_at": "2024-01-01T12:01:30",
                "error_message": None,
            }
        }
    )


class DocumentListResponse(BaseModel):
    """Response model for paginated document list."""

    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents matching the query")
    limit: int = Field(..., description="Number of documents per page")
    offset: int = Field(..., description="Offset for pagination")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "filename": "research_paper.pdf",
                        "file_size_bytes": 1024000,
                        "mime_type": "application/pdf",
                        "status": "completed",
                        "chunk_count": 25,
                        "uploaded_at": "2024-01-01T12:00:00",
                        "processing_completed_at": "2024-01-01T12:01:30",
                        "error_message": None,
                    }
                ],
                "total": 42,
                "limit": 20,
                "offset": 0,
            }
        }
    )


class BatchUploadResponse(BaseModel):
    """Response model for batch upload creation."""

    batch_id: UUID = Field(..., description="Batch upload job ID")
    total_files: int = Field(..., description="Total number of files in the batch")
    status: str = Field(
        ..., description="Batch status: pending, processing, completed, failed"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "batch_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_files": 10,
                "status": "pending",
            }
        },
    )


class BatchProgressResponse(BaseModel):
    """Response model for batch upload progress."""

    batch_id: UUID = Field(..., description="Batch upload job ID")
    total_files: int = Field(..., description="Total number of files in the batch")
    completed_files: int = Field(
        ..., description="Number of files successfully processed"
    )
    failed_files: int = Field(..., description="Number of files that failed processing")
    status: str = Field(
        ..., description="Batch status: pending, processing, completed, failed"
    )
    failed_file_names: List[str] = Field(
        default_factory=list, description="List of filenames that failed"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "batch_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_files": 10,
                "completed_files": 8,
                "failed_files": 2,
                "status": "processing",
                "failed_file_names": ["corrupted_file.pdf", "invalid_format.txt"],
            }
        },
    )
