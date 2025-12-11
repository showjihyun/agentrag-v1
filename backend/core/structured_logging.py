"""
Structured Logging with Contextvars

Provides JSON-formatted logs with automatic context propagation.
"""

import logging
import sys
from typing import Any, Dict, Optional
from contextvars import ContextVar
from datetime import datetime

import structlog
from structlog.types import EventDict, Processor

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')
workflow_id_var: ContextVar[str] = ContextVar('workflow_id', default='')
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

# Global logger
_logger: Optional[structlog.BoundLogger] = None


def add_context_processor(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add context variables to log events"""
    
    # Add request context
    if request_id := request_id_var.get():
        event_dict['request_id'] = request_id
    
    if user_id := user_id_var.get():
        event_dict['user_id'] = user_id
    
    if workflow_id := workflow_id_var.get():
        event_dict['workflow_id'] = workflow_id
    
    if trace_id := trace_id_var.get():
        event_dict['trace_id'] = trace_id
    
    return event_dict


def add_timestamp_processor(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add ISO timestamp to log events"""
    event_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    return event_dict


def add_severity_processor(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add severity level for cloud logging compatibility"""
    level = event_dict.get('level', '').upper()
    
    # Map to Google Cloud Logging severity levels
    severity_map = {
        'DEBUG': 'DEBUG',
        'INFO': 'INFO',
        'WARNING': 'WARNING',
        'ERROR': 'ERROR',
        'CRITICAL': 'CRITICAL'
    }
    
    event_dict['severity'] = severity_map.get(level, 'INFO')
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    enable_colors: bool = False
) -> structlog.BoundLogger:
    """
    Setup structured logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Output logs in JSON format
        enable_colors: Enable colored output (for development)
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Build processor chain
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_context_processor,
        add_timestamp_processor,
        structlog.stdlib.add_log_level,
        add_severity_processor,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add appropriate renderer
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        if enable_colors:
            processors.append(structlog.dev.ConsoleRenderer(colors=True))
        else:
            processors.append(structlog.dev.ConsoleRenderer(colors=False))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    _logger = structlog.get_logger()
    
    _logger.info(
        "structured_logging_initialized",
        log_level=log_level,
        json_logs=json_logs
    )
    
    return _logger


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Bound logger with context
    """
    global _logger
    
    if _logger is None:
        _logger = setup_logging()
    
    if name:
        return _logger.bind(logger_name=name)
    
    return _logger


class LogContext:
    """Context manager for adding temporary log context"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.tokens = {}
    
    def __enter__(self):
        # Set context variables
        if 'request_id' in self.context:
            self.tokens['request_id'] = request_id_var.set(self.context['request_id'])
        if 'user_id' in self.context:
            self.tokens['user_id'] = user_id_var.set(str(self.context['user_id']))
        if 'workflow_id' in self.context:
            self.tokens['workflow_id'] = workflow_id_var.set(str(self.context['workflow_id']))
        if 'trace_id' in self.context:
            self.tokens['trace_id'] = trace_id_var.set(self.context['trace_id'])
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset context variables
        for var_name, token in self.tokens.items():
            if var_name == 'request_id':
                request_id_var.reset(token)
            elif var_name == 'user_id':
                user_id_var.reset(token)
            elif var_name == 'workflow_id':
                workflow_id_var.reset(token)
            elif var_name == 'trace_id':
                trace_id_var.reset(token)
        
        return False


# Convenience functions for common logging patterns

def log_workflow_execution(
    logger: structlog.BoundLogger,
    workflow_id: int,
    status: str,
    duration_ms: Optional[float] = None,
    **kwargs
):
    """Log workflow execution event"""
    log_data = {
        "event": "workflow_execution",
        "workflow_id": workflow_id,
        "status": status,
        **kwargs
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    if status == "completed":
        logger.info("workflow_execution_completed", **log_data)
    elif status == "failed":
        logger.error("workflow_execution_failed", **log_data)
    else:
        logger.info("workflow_execution_status", **log_data)


def log_api_request(
    logger: structlog.BoundLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **kwargs
):
    """Log API request"""
    log_data = {
        "event": "api_request",
        "http_method": method,
        "http_path": path,
        "http_status": status_code,
        "duration_ms": duration_ms,
        **kwargs
    }
    
    if status_code >= 500:
        logger.error("api_request_error", **log_data)
    elif status_code >= 400:
        logger.warning("api_request_client_error", **log_data)
    else:
        logger.info("api_request_success", **log_data)


def log_database_query(
    logger: structlog.BoundLogger,
    query_type: str,
    table: str,
    duration_ms: float,
    rows_affected: Optional[int] = None,
    **kwargs
):
    """Log database query"""
    log_data = {
        "event": "database_query",
        "query_type": query_type,
        "table": table,
        "duration_ms": duration_ms,
        **kwargs
    }
    
    if rows_affected is not None:
        log_data["rows_affected"] = rows_affected
    
    if duration_ms > 1000:  # Slow query threshold
        logger.warning("slow_database_query", **log_data)
    else:
        logger.debug("database_query", **log_data)


def log_cache_operation(
    logger: structlog.BoundLogger,
    operation: str,
    key: str,
    hit: bool,
    duration_ms: Optional[float] = None,
    **kwargs
):
    """Log cache operation"""
    log_data = {
        "event": "cache_operation",
        "operation": operation,
        "key": key,
        "hit": hit,
        **kwargs
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    logger.debug("cache_operation", **log_data)


def log_llm_call(
    logger: structlog.BoundLogger,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: float,
    cost: Optional[float] = None,
    **kwargs
):
    """Log LLM API call"""
    log_data = {
        "event": "llm_call",
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "duration_ms": duration_ms,
        **kwargs
    }
    
    if cost is not None:
        log_data["cost_usd"] = cost
    
    logger.info("llm_call", **log_data)


def log_error(
    logger: structlog.BoundLogger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """Log error with context"""
    log_data = {
        "event": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
        **kwargs
    }
    
    if context:
        log_data["context"] = context
    
    logger.error("error_occurred", **log_data, exc_info=True)


def log_security_event(
    logger: structlog.BoundLogger,
    event_type: str,
    severity: str,
    details: Dict[str, Any],
    **kwargs
):
    """Log security event"""
    log_data = {
        "event": "security_event",
        "event_type": event_type,
        "severity": severity,
        "details": details,
        **kwargs
    }
    
    if severity in ["high", "critical"]:
        logger.error("security_event", **log_data)
    else:
        logger.warning("security_event", **log_data)


def log_performance_metric(
    logger: structlog.BoundLogger,
    metric_name: str,
    value: float,
    unit: str,
    **kwargs
):
    """Log performance metric"""
    log_data = {
        "event": "performance_metric",
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        **kwargs
    }
    
    logger.info("performance_metric", **log_data)


# Middleware for FastAPI

class StructuredLoggingMiddleware:
    """Middleware to add structured logging to FastAPI"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())
        
        # Set context
        request_id_var.set(request_id)
        
        # Log request start
        self.logger.info(
            "request_started",
            method=scope["method"],
            path=scope["path"],
            request_id=request_id
        )
        
        # Process request
        import time
        start_time = time.time()
        
        try:
            await self.app(scope, receive, send)
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request completion
            self.logger.info(
                "request_completed",
                method=scope["method"],
                path=scope["path"],
                duration_ms=duration_ms,
                request_id=request_id
            )
