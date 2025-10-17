"""
Structured Logging System

Provides JSON-formatted logging with context enrichment,
correlation IDs, and structured data for better log analysis.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import traceback

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format with consistent structure:
    {
        "timestamp": "2025-10-07T10:30:45.123Z",
        "level": "INFO",
        "logger": "backend.api.query",
        "message": "Query processed successfully",
        "request_id": "abc-123",
        "user_id": "user_456",
        "duration_ms": 234.5,
        "extra": {...}
    }
    """

    def __init__(self, include_traceback: bool = True, include_context: bool = True):
        """
        Initialize structured formatter.

        Args:
            include_traceback: Include traceback for errors
            include_context: Include request context (request_id, user_id, etc.)
        """
        super().__init__()
        self.include_traceback = include_traceback
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context if enabled
        if self.include_context:
            request_id = request_id_var.get()
            user_id = user_id_var.get()
            session_id = session_id_var.get()

            if request_id:
                log_data["request_id"] = request_id
            if user_id:
                log_data["user_id"] = user_id
            if session_id:
                log_data["session_id"] = session_id

        # Add exception info if present
        if record.exc_info and self.include_traceback:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "taskName",
            ]:
                # Only include JSON-serializable values
                try:
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    extra_fields[key] = str(value)

        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """
    Wrapper for structured logging with convenience methods.
    """

    def __init__(self, name: str):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually __name__)
        """
        self.logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **kwargs) -> None:
        """Internal log method with extra fields."""
        # Extract exc_info if present (it's a reserved logging parameter)
        exc_info = kwargs.pop("exc_info", None)

        # Build extra dict from remaining kwargs
        extra = {k: v for k, v in kwargs.items() if v is not None}

        # Log with exc_info as a separate parameter if provided
        if exc_info is not None:
            self.logger.log(level, message, exc_info=exc_info, extra=extra)
        else:
            self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)

    # Convenience methods for common scenarios

    def log_request(
        self, method: str, path: str, status_code: int, duration_ms: float, **kwargs
    ) -> None:
        """Log HTTP request."""
        self.info(
            f"{method} {path} - {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_query(
        self,
        query_name: str,
        duration_ms: float,
        result_count: Optional[int] = None,
        **kwargs,
    ) -> None:
        """Log database query."""
        self.info(
            f"Query: {query_name}",
            query_name=query_name,
            duration_ms=duration_ms,
            result_count=result_count,
            **kwargs,
        )

    def log_cache_hit(self, cache_key: str, cache_level: str = "L1", **kwargs) -> None:
        """Log cache hit."""
        self.debug(
            f"Cache hit: {cache_key}",
            cache_key=cache_key,
            cache_level=cache_level,
            cache_hit=True,
            **kwargs,
        )

    def log_cache_miss(self, cache_key: str, **kwargs) -> None:
        """Log cache miss."""
        self.debug(
            f"Cache miss: {cache_key}", cache_key=cache_key, cache_hit=False, **kwargs
        )

    def log_performance(
        self, operation: str, duration_ms: float, threshold_ms: float = 1000, **kwargs
    ) -> None:
        """Log performance metric."""
        if duration_ms > threshold_ms:
            self.warning(
                f"Slow operation: {operation}",
                operation=operation,
                duration_ms=duration_ms,
                threshold_ms=threshold_ms,
                slow_operation=True,
                **kwargs,
            )
        else:
            self.debug(
                f"Operation: {operation}",
                operation=operation,
                duration_ms=duration_ms,
                **kwargs,
            )


def setup_structured_logging(
    log_level: str = "INFO", log_file: Optional[str] = None, json_format: bool = True
) -> None:
    """
    Setup structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_format: Use JSON format (True) or plain text (False)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.error(f"Failed to setup file logging: {e}")

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("pymilvus").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root_logger.info(
        "Structured logging initialized",
        extra={
            "log_level": log_level,
            "json_format": json_format,
            "log_file": log_file,
        },
    )


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """
    Set request context for logging.

    Args:
        request_id: Request ID
        user_id: User ID
        session_id: Session ID
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if session_id:
        session_id_var.set(session_id)


def clear_request_context() -> None:
    """Clear request context."""
    request_id_var.set(None)
    user_id_var.set(None)
    session_id_var.set(None)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Performance logging decorator
def log_performance(operation_name: Optional[str] = None):
    """
    Decorator to log function performance.

    Usage:
        @log_performance("process_document")
        async def process_document(doc_id: str):
            # Function code
            pass
    """

    def decorator(func):
        import asyncio
        import time
        from functools import wraps

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation_name or func.__name__

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger.log_performance(
                    operation=op_name, duration_ms=duration_ms, success=True
                )

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {op_name}",
                    operation=op_name,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation_name or func.__name__

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger.log_performance(
                    operation=op_name, duration_ms=duration_ms, success=True
                )

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {op_name}",
                    operation=op_name,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
