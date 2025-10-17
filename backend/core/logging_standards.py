"""
Standardized logging utilities for consistent logging across the application.

This module provides helper functions for structured logging with consistent
format and appropriate log levels.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Standard log levels with usage guidelines."""

    DEBUG = "DEBUG"  # Detailed information for debugging
    INFO = "INFO"  # Important business events
    WARNING = "WARNING"  # Potential issues that need monitoring
    ERROR = "ERROR"  # Errors that need immediate attention


class StandardLogger:
    """
    Standardized logger with consistent formatting and log levels.

    Usage Guidelines:
    - ERROR: System errors requiring immediate action
    - WARNING: Potential problems requiring monitoring
    - INFO: Important business events (login, upload, query)
    - DEBUG: Detailed information for development/debugging
    """

    @staticmethod
    def log_api_request(
        logger: logging.Logger,
        method: str,
        path: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ):
        """
        Log API request with standard format.

        Args:
            logger: Logger instance
            method: HTTP method (GET, POST, etc.)
            path: Request path
            user_id: Optional user ID
            request_id: Optional request ID
            duration_ms: Optional request duration in milliseconds
        """
        extra_data = {
            "event_type": "api_request",
            "method": method,
            "path": path,
            "timestamp": datetime.now().isoformat(),
        }

        if user_id:
            extra_data["user_id"] = user_id
        if request_id:
            extra_data["request_id"] = request_id
        if duration_ms is not None:
            extra_data["duration_ms"] = duration_ms

        message = f"{method} {path}"
        if duration_ms is not None:
            message += f" - {duration_ms:.2f}ms"

        logger.info(message, extra=extra_data)

    @staticmethod
    def log_business_event(
        logger: logging.Logger,
        event_name: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ):
        """
        Log business event (document upload, query execution, etc.).

        Args:
            logger: Logger instance
            event_name: Name of the business event
            user_id: User ID
            details: Optional event details
            success: Whether the event was successful
        """
        extra_data = {
            "event_type": "business_event",
            "event_name": event_name,
            "user_id": user_id,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }

        if details:
            extra_data["details"] = details

        status = "succeeded" if success else "failed"
        message = f"Business Event: {event_name} {status}"

        if success:
            logger.info(message, extra=extra_data)
        else:
            logger.warning(message, extra=extra_data)

    @staticmethod
    def log_error(
        logger: logging.Logger,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ):
        """
        Log error with context information.

        Args:
            logger: Logger instance
            error: Exception that occurred
            context: Optional context information
            user_id: Optional user ID
        """
        extra_data = {
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
        }

        if context:
            extra_data["context"] = context
        if user_id:
            extra_data["user_id"] = user_id

        logger.error(
            f"Error: {type(error).__name__} - {str(error)}",
            extra=extra_data,
            exc_info=True,
        )

    @staticmethod
    def log_performance_metric(
        logger: logging.Logger,
        operation: str,
        duration_ms: float,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log performance metric.

        Args:
            logger: Logger instance
            operation: Operation name
            duration_ms: Duration in milliseconds
            details: Optional additional details
        """
        extra_data = {
            "event_type": "performance",
            "operation": operation,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        }

        if details:
            extra_data["details"] = details

        # Log as DEBUG for normal operations, WARNING if slow
        message = f"Performance: {operation} - {duration_ms:.2f}ms"

        if duration_ms > 5000:  # > 5 seconds
            logger.warning(f"SLOW: {message}", extra=extra_data)
        elif duration_ms > 1000:  # > 1 second
            logger.info(message, extra=extra_data)
        else:
            logger.debug(message, extra=extra_data)

    @staticmethod
    def log_security_event(
        logger: logging.Logger,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
    ):
        """
        Log security-related event.

        Args:
            logger: Logger instance
            event_type: Type of security event
            user_id: Optional user ID
            ip_address: Optional IP address
            details: Optional event details
            severity: Severity level (INFO, WARNING, ERROR)
        """
        extra_data = {
            "event_type": "security",
            "security_event": event_type,
            "timestamp": datetime.now().isoformat(),
        }

        if user_id:
            extra_data["user_id"] = user_id
        if ip_address:
            extra_data["ip_address"] = ip_address
        if details:
            extra_data["details"] = details

        message = f"Security Event: {event_type}"

        if severity == "ERROR":
            logger.error(message, extra=extra_data)
        elif severity == "WARNING":
            logger.warning(message, extra=extra_data)
        else:
            logger.info(message, extra=extra_data)

    @staticmethod
    def log_cache_event(
        logger: logging.Logger,
        operation: str,
        cache_key: str,
        hit: bool,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log cache operation.

        Args:
            logger: Logger instance
            operation: Cache operation (get, set, delete)
            cache_key: Cache key
            hit: Whether it was a cache hit
            details: Optional additional details
        """
        extra_data = {
            "event_type": "cache",
            "operation": operation,
            "cache_key": cache_key,
            "hit": hit,
            "timestamp": datetime.now().isoformat(),
        }

        if details:
            extra_data["details"] = details

        status = "HIT" if hit else "MISS"
        logger.debug(f"Cache {operation}: {cache_key} - {status}", extra=extra_data)
