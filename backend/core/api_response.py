"""
Standardized API Response Schema
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import time

T = TypeVar("T")


class ErrorCode(str, Enum):
    AUTH_INVALID_CREDENTIALS = "AUTH_1001"
    AUTH_TOKEN_EXPIRED = "AUTH_1002"
    AUTH_TOKEN_INVALID = "AUTH_1003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_1004"
    AUTH_ACCOUNT_INACTIVE = "AUTH_1005"
    AUTH_ACCOUNT_LOCKED = "AUTH_1006"
    VALIDATION_FAILED = "VAL_2001"
    VALIDATION_REQUIRED_FIELD = "VAL_2002"
    VALIDATION_INVALID_FORMAT = "VAL_2003"
    VALIDATION_OUT_OF_RANGE = "VAL_2004"
    VALIDATION_DUPLICATE_VALUE = "VAL_2005"
    VALIDATION_INVALID_TYPE = "VAL_2006"
    RESOURCE_NOT_FOUND = "RES_3001"
    RESOURCE_ALREADY_EXISTS = "RES_3002"
    RESOURCE_CONFLICT = "RES_3003"
    RESOURCE_LOCKED = "RES_3004"
    RESOURCE_DELETED = "RES_3005"
    BUSINESS_RULE_VIOLATION = "BIZ_4001"
    OPERATION_NOT_ALLOWED = "BIZ_4002"
    QUOTA_EXCEEDED = "BIZ_4003"
    RATE_LIMIT_EXCEEDED = "BIZ_4004"
    WORKFLOW_INVALID_STATE = "BIZ_4005"
    EXTERNAL_SERVICE_ERROR = "EXT_5001"
    EXTERNAL_SERVICE_TIMEOUT = "EXT_5002"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXT_5003"
    LLM_SERVICE_ERROR = "EXT_5004"
    DATABASE_ERROR = "EXT_5005"
    INTERNAL_ERROR = "INT_9001"
    CONFIGURATION_ERROR = "INT_9002"
    UNEXPECTED_ERROR = "INT_9999"


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class PaginationMeta(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    has_next: bool
    has_prev: bool


class ResponseMeta(BaseModel):
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    duration_ms: Optional[float] = None
    version: str = "1.0"
    pagination: Optional[PaginationMeta] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ListResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T] = Field(default_factory=list)
    error: Optional[ErrorDetail] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ResponseBuilder:
    @staticmethod
    def success(data: Any = None, request_id: Optional[str] = None, duration_ms: Optional[float] = None, pagination: Optional[PaginationMeta] = None) -> Dict[str, Any]:
        meta = ResponseMeta(request_id=request_id, duration_ms=duration_ms, pagination=pagination)
        return {"success": True, "data": data, "error": None, "meta": meta.model_dump()}

    @staticmethod
    def error(code: Union[ErrorCode, str], message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> Dict[str, Any]:
        error_code = code.value if isinstance(code, ErrorCode) else code
        error_detail = ErrorDetail(code=error_code, message=message, field=field, details=details)
        meta = ResponseMeta(request_id=request_id)
        return {"success": False, "data": None, "error": error_detail.model_dump(), "meta": meta.model_dump()}

    @staticmethod
    def paginated(items: List[Any], page: int, page_size: int, total_items: int, request_id: Optional[str] = None, duration_ms: Optional[float] = None) -> Dict[str, Any]:
        total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
        pagination = PaginationMeta(page=page, page_size=page_size, total_items=total_items, total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1)
        return ResponseBuilder.success(data=items, request_id=request_id, duration_ms=duration_ms, pagination=pagination)


class ResponseTimer:
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        return False

    @property
    def duration_ms(self) -> Optional[float]:
        if self.start_time is None or self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000


def api_response(data: Any = None, status_code: int = 200, request_id: Optional[str] = None, duration_ms: Optional[float] = None, pagination: Optional[PaginationMeta] = None) -> Dict[str, Any]:
    return ResponseBuilder.success(data=data, request_id=request_id, duration_ms=duration_ms, pagination=pagination)


def api_error(code: Union[ErrorCode, str], message: str, status_code: int = 400, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> Dict[str, Any]:
    return ResponseBuilder.error(code=code, message=message, field=field, details=details, request_id=request_id)


def paginated_response(items: List[Any], page: int, page_size: int, total_items: int, request_id: Optional[str] = None, duration_ms: Optional[float] = None) -> Dict[str, Any]:
    return ResponseBuilder.paginated(items=items, page=page, page_size=page_size, total_items=total_items, request_id=request_id, duration_ms=duration_ms)
