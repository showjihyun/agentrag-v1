"""Error response models."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path where error occurred")
    request_id: Optional[str] = Field(
        None, description="Request identifier for tracking"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional error metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Document not found",
                "error_type": "NotFoundError",
                "detail": "The requested document with ID 'doc123' does not exist",
                "status_code": 404,
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/api/documents/doc123",
                "request_id": "req_abc123",
                "metadata": {},
            }
        }
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""

    error: str = Field(default="Validation error", description="Error message")
    error_type: str = Field(default="ValidationError", description="Type of error")
    status_code: int = Field(default=422, description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp")
    validation_errors: list[Dict[str, Any]] = Field(
        ..., description="List of validation errors"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Validation error",
                "error_type": "ValidationError",
                "status_code": 422,
                "timestamp": "2024-01-01T12:00:00Z",
                "validation_errors": [
                    {
                        "field": "query",
                        "message": "Query cannot be empty",
                        "type": "value_error",
                    }
                ],
            }
        }
    )
