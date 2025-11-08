"""Common enums for type safety across the application."""

from enum import Enum


class BookmarkType(str, Enum):
    """Bookmark types."""
    CONVERSATION = "conversation"
    DOCUMENT = "document"


class NotificationType(str, Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class ShareRole(str, Enum):
    """Share roles for conversation sharing."""
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class TimeRange(str, Enum):
    """Time range options for statistics."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class QueryMode(str, Enum):
    """Query processing modes."""
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"


class PermissionType(str, Enum):
    """Permission types for document access."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


# ============================================================================
# Phase 1 추가 Enum들
# ============================================================================

class FileType(str, Enum):
    """File types for document processing."""
    HWP = "hwp"
    HWPX = "hwpx"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    PPTX = "pptx"
    XLSX = "xlsx"
    CSV = "csv"
    JSON = "json"
    MD = "md"


class ConfigType(str, Enum):
    """Configuration value types."""
    INTEGER = "integer"
    FLOAT = "float"
    JSON = "json"
    STRING = "string"
    BOOLEAN = "boolean"


class UploadStatus(str, Enum):
    """File upload status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchType(str, Enum):
    """Search types for hybrid search."""
    VECTOR_ONLY = "vector_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"


class QueryType(str, Enum):
    """Query types for decomposition."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"
    AGGREGATION = "aggregation"
    MULTI_HOP = "multi_hop"


class QueryComplexity(str, Enum):
    """Query complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModalityType(str, Enum):
    """Modality types for multimodal processing."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class RerankerMethod(str, Enum):
    """Reranker methods."""
    CLIP = "clip"
    COLPALI = "colpali"
