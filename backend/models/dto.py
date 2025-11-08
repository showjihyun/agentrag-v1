"""Data Transfer Objects (DTOs) using dataclasses for type safety."""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from backend.models.enums import BookmarkType, NotificationType, ShareRole, TimeRange


# ============================================================================
# Bookmark DTOs
# ============================================================================

@dataclass
class BookmarkCreateDTO:
    """Data for creating a bookmark."""
    user_id: UUID
    type: BookmarkType
    item_id: str
    title: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not self.title or len(self.title) > 500:
            raise ValueError("Title must be between 1 and 500 characters")
        if self.description and len(self.description) > 2000:
            raise ValueError("Description must be less than 2000 characters")
        if len(self.tags) > 10:
            raise ValueError("Maximum 10 tags allowed")


@dataclass
class BookmarkFilterDTO:
    """Filter criteria for bookmarks."""
    user_id: UUID
    type: Optional[BookmarkType] = None
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0
    
    def __post_init__(self):
        """Validate filter parameters."""
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")


@dataclass
class BookmarkUpdateDTO:
    """Data for updating a bookmark."""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None


# ============================================================================
# Notification DTOs
# ============================================================================

@dataclass
class NotificationCreateDTO:
    """Data for creating a notification."""
    user_id: UUID
    type: NotificationType
    title: str
    message: str
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate notification data."""
        if not self.title or len(self.title) > 200:
            raise ValueError("Title must be between 1 and 200 characters")
        if not self.message:
            raise ValueError("Message is required")


@dataclass
class NotificationFilterDTO:
    """Filter criteria for notifications."""
    user_id: UUID
    unread_only: bool = False
    limit: int = 50
    offset: int = 0
    
    def __post_init__(self):
        """Validate filter parameters."""
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")


# ============================================================================
# Usage DTOs
# ============================================================================

@dataclass
class UsageDataPoint:
    """Single usage data point."""
    date: str
    queries: int
    tokens: int
    cost: float


@dataclass
class UsageSummary:
    """Usage summary statistics."""
    total_queries: int
    total_documents: int
    total_tokens: int
    estimated_cost: float
    avg_queries_per_day: float
    peak_usage_day: str
    current_month_cost: float = 0.0
    projected_month_cost: float = 0.0


@dataclass
class UsageStats:
    """Complete usage statistics."""
    usage: List[UsageDataPoint]
    summary: UsageSummary


@dataclass
class UsageFilterDTO:
    """Filter criteria for usage statistics."""
    user_id: Optional[UUID] = None
    time_range: TimeRange = TimeRange.WEEK
    limit: int = 30
    
    def __post_init__(self):
        """Validate filter parameters."""
        if self.limit < 1 or self.limit > 365:
            raise ValueError("Limit must be between 1 and 365")


# ============================================================================
# Share DTOs
# ============================================================================

@dataclass
class ShareCreateDTO:
    """Data for creating a share."""
    conversation_id: UUID
    owner_id: UUID
    target_user_id: UUID
    role: ShareRole = ShareRole.VIEWER


@dataclass
class ShareUpdateDTO:
    """Data for updating a share."""
    role: ShareRole


@dataclass
class PublicLinkDTO:
    """Public link information."""
    is_public: bool
    public_url: Optional[str] = None
    public_token: Optional[str] = None


# ============================================================================
# Dashboard DTOs
# ============================================================================

@dataclass
class WidgetConfig:
    """Widget configuration."""
    value: Optional[int] = None
    trend: Optional[str] = None
    chart_type: Optional[str] = None
    queries: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class WidgetPosition:
    """Widget position on dashboard."""
    x: int
    y: int


@dataclass
class DashboardWidget:
    """Dashboard widget."""
    id: str
    type: str  # stat, chart, list, table
    title: str
    size: str  # small, medium, large
    position: WidgetPosition
    config: WidgetConfig


@dataclass
class DashboardLayout:
    """Dashboard layout."""
    widgets: List[DashboardWidget]
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# Response DTOs
# ============================================================================

@dataclass
class PaginatedResponse:
    """Generic paginated response."""
    items: List[any]
    total: int
    limit: int
    offset: int
    has_more: bool


@dataclass
class SuccessResponse:
    """Generic success response."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[dict] = None


@dataclass
class ErrorResponse:
    """Generic error response."""
    success: bool = False
    error: str = ""
    error_type: str = ""
    details: Optional[dict] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
