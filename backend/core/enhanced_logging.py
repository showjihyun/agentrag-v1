"""
Enhanced Structured Logging

Provides structured logging with context, correlation IDs,
and automatic field extraction for better observability.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import traceback

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        trace_id = trace_id_var.get()
        if trace_id:
            log_data["trace_id"] = trace_id
        
        # Add location info
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        return json.dumps(log_data, default=str)


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds context to all log messages"""
    
    def process(self, msg, kwargs):
        """Add context to log message"""
        
        # Get extra fields
        extra = kwargs.get("extra", {})
        
        # Add context variables
        request_id = request_id_var.get()
        if request_id:
            extra["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            extra["user_id"] = user_id
        
        trace_id = trace_id_var.get()
        if trace_id:
            extra["trace_id"] = trace_id
        
        kwargs["extra"] = {"extra_fields": extra}
        
        return msg, kwargs


def setup_enhanced_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True
):
    """
    Setup enhanced structured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_format: Whether to use JSON format
    """
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    logging.info("Enhanced logging configured", extra={
        "log_level": log_level,
        "json_format": json_format,
        "log_file": log_file
    })


def get_logger(name: str) -> ContextLogger:
    """
    Get context-aware logger.
    
    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", extra={"user_id": 123})
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, {})


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None
):
    """Set request context for logging"""
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if trace_id:
        trace_id_var.set(trace_id)


def clear_request_context():
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)
    trace_id_var.set(None)


def log_execution_time(func_name: str, duration_ms: float, **kwargs):
    """Log function execution time"""
    logger = get_logger("performance")
    logger.info(
        f"Function executed: {func_name}",
        extra={
            "function": func_name,
            "duration_ms": duration_ms,
            **kwargs
        }
    )


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    logger_name: str = "error"
):
    """Log error with context"""
    logger = get_logger(logger_name)
    
    extra = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if context:
        extra.update(context)
    
    logger.error(
        f"Error occurred: {error}",
        exc_info=True,
        extra=extra
    )
