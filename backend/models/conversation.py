"""Conversation request and response models."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SessionCreate(BaseModel):
    """Request model for creating a new session."""

    title: Optional[str] = Field(
        None,
        description="Session title (auto-generated if not provided)",
        max_length=255,
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"title": "Discussion about machine learning"}}
    )


class SessionResponse(BaseModel):
    """Response model for session information."""

    id: UUID = Field(..., description="Session unique identifier")
    user_id: UUID = Field(..., description="User who owns this session")
    title: Optional[str] = Field(None, description="Session title")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(default=0, description="Number of messages in session")
    total_tokens: int = Field(default=0, description="Total tokens used in session")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440000",
                "title": "Machine Learning Discussion",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:30:00Z",
                "message_count": 10,
                "total_tokens": 5000,
            }
        },
    )


class SessionUpdate(BaseModel):
    """Request model for updating a session."""

    title: str = Field(
        ..., description="New session title", min_length=1, max_length=255
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"title": "Updated Discussion Title"}}
    )


class MessageSourceResponse(BaseModel):
    """Response model for message source references."""

    id: UUID = Field(..., description="Source unique identifier")
    document_id: str = Field(..., description="ID of the source document")
    document_name: str = Field(..., description="Name of the source document")
    chunk_id: Optional[str] = Field(None, description="ID of the specific chunk")
    score: Optional[float] = Field(None, description="Relevance score (0-1)")
    text: Optional[str] = Field(None, description="Excerpt from the source")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "document_id": "doc123",
                "document_name": "research_paper.pdf",
                "chunk_id": "doc123_chunk_5",
                "score": 0.92,
                "text": "Machine learning models require large datasets...",
            }
        },
    )


class MessageResponse(BaseModel):
    """Response model for message information."""

    id: UUID = Field(..., description="Message unique identifier")
    session_id: UUID = Field(..., description="Session this message belongs to")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    query_mode: Optional[str] = Field(
        None, description="Query mode used (fast, balanced, deep)"
    )
    confidence_score: Optional[float] = Field(
        None, description="Confidence score of the response"
    )
    cache_hit: bool = Field(
        default=False, description="Whether response was from cache"
    )
    created_at: datetime = Field(..., description="Message creation timestamp")
    sources: List[MessageSourceResponse] = Field(
        default_factory=list, description="Source references"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "assistant",
                "content": "Machine learning is a subset of artificial intelligence...",
                "query_mode": "balanced",
                "confidence_score": 0.95,
                "cache_hit": False,
                "created_at": "2024-01-01T12:00:00Z",
                "sources": [],
            }
        },
    )


class MessageListResponse(BaseModel):
    """Response model for paginated message list."""

    messages: List[MessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages", ge=0)
    limit: int = Field(..., description="Number of messages per page", ge=1)
    offset: int = Field(..., description="Offset for pagination", ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"messages": [], "total": 100, "limit": 50, "offset": 0}
        }
    )


class SearchRequest(BaseModel):
    """Request model for searching messages."""

    query: str = Field(..., description="Search query text", min_length=1)
    session_id: Optional[UUID] = Field(None, description="Filter by specific session")
    start_date: Optional[datetime] = Field(
        None, description="Filter messages after this date"
    )
    end_date: Optional[datetime] = Field(
        None, description="Filter messages before this date"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "machine learning",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z",
            }
        }
    )


class SearchResponse(BaseModel):
    """Response model for message search results."""

    messages: List[MessageResponse] = Field(
        ..., description="List of matching messages"
    )
    total: int = Field(..., description="Total number of matching messages", ge=0)

    model_config = ConfigDict(
        json_schema_extra={"example": {"messages": [], "total": 25}}
    )
