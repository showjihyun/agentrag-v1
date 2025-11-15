"""Document models."""

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    DateTime,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


class Document(Base):
    """Uploaded document model."""

    __tablename__ = "documents"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))

    # Processing Status
    status = Column(
        String(50), default="pending", index=True
    )  # pending, processing, completed, failed
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    error_message = Column(Text)

    # Vector DB Information
    milvus_collection = Column(String(255))
    chunk_count = Column(Integer, default=0)

    # Timestamp
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Version Management
    version = Column(Integer, default=1)
    previous_version_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True
    )
    file_hash = Column(String(64))  # SHA-256 hash for deduplication
    archived_at = Column(DateTime, nullable=True)

    # Rich Metadata (extracted from document)
    document_title = Column(String(500), nullable=True)
    document_author = Column(String(200), nullable=True, index=True)
    document_subject = Column(String(500), nullable=True)
    document_keywords = Column(Text, nullable=True)  # Comma-separated keywords
    document_language = Column(String(10), nullable=True, index=True)  # ISO 639-1 code
    document_creation_date = Column(DateTime, nullable=True, index=True)
    document_modification_date = Column(DateTime, nullable=True)

    # Metadata
    extra_metadata = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="documents")
    previous_version = relationship(
        "Document", remote_side=[id], foreign_keys=[previous_version_id]
    )

    # Composite Indexes and Constraints
    __table_args__ = (
        Index("ix_documents_user_status", "user_id", "status"),
        Index("ix_documents_user_uploaded", "user_id", "uploaded_at"),
        Index("ix_documents_user_filename", "user_id", "filename"),
        Index("ix_documents_file_hash", "file_hash"),
        CheckConstraint("file_size_bytes > 0", name="check_file_size_positive"),
        CheckConstraint("chunk_count >= 0", name="check_chunk_count_positive"),
        CheckConstraint("version > 0", name="check_version_positive"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'archived')",
            name="check_status_valid",
        ),
    )

    def __repr__(self):
        return (
            f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
        )


class BatchUpload(Base):
    """Batch upload job model."""

    __tablename__ = "batch_uploads"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Batch Information
    total_files = Column(Integer, nullable=False)
    completed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)

    # Status
    status = Column(
        String(50), default="pending", index=True
    )  # pending, processing, completed, failed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Metadata
    extra_metadata = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="batch_uploads")

    # Database Constraints
    __table_args__ = (
        CheckConstraint("total_files > 0", name="check_total_files_positive"),
        CheckConstraint("completed_files >= 0", name="check_completed_files_positive"),
        CheckConstraint("failed_files >= 0", name="check_failed_files_positive"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="check_batch_status_valid",
        ),
    )

    def __repr__(self):
        return f"<BatchUpload(id={self.id}, total_files={self.total_files}, status={self.status})>"
