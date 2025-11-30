"""
Workflow Structured Logging

JSON-based structured logging with tracing support for workflow execution.
"""

import logging
import json
import uuid
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from functools import wraps
from contextvars import ContextVar

# Context variables for tracing
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')
span_id_var: ContextVar[str] = ContextVar('span_id', default='')
workflow_id_var: ContextVar[str] = ContextVar('workflow_id', default='')
execution_id_var: ContextVar[str] = ContextVar('execution_id', default='')


class WorkflowLogFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id_var.get() or None,
            "span_id": span_id_var.get() or None,
            "workflow_id": workflow_id_var.get() or None,
            "execution_id": execution_id_var.get() or None,
        }
        
        # Add extra fields from record
        if hasattr(record, 'node_id'):
            log_data["node_id"] = record.node_id
        if hasattr(record, 'node_type'):
            log_data["node_type"] = record.node_type
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, 'status'):
            log_data["status"] = record.status
        if hasattr(record, 'error_code'):
            log_data["error_code"] = record.error_code
        if hasattr(record, 'extra_data'):
            log_data["data"] = record.extra_data
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        return json.dumps(log_data)


class WorkflowLogger:
    """Structured logger for workflow execution."""
    
    def __init__(self, name: str = "workflow"):
        self.logger = logging.getLogger(f"workflow.{name}")
        self._setup_handler()
    
    def _setup_handler(self):
        """Setup JSON handler if not already configured."""
        # Check if already has JSON handler
        for handler in self.logger.handlers:
            if isinstance(handler.formatter, WorkflowLogFormatter):
                return
        
        # Add JSON handler for structured logging
        handler = logging.StreamHandler()
        handler.setFormatter(WorkflowLogFormatter())
        self.logger.addHandler(handler)
    
    def _log(
        self,
        level: int,
        message: str,
        node_id: Optional[str] = None,
        node_type: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status: Optional[str] = None,
        error_code: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        """Internal log method with extra fields."""
        extra = {}
        if node_id:
            extra['node_id'] = node_id
        if node_type:
            extra['node_type'] = node_type
        if duration_ms is not None:
            extra['duration_ms'] = duration_ms
        if status:
            extra['status'] = status
        if error_code:
            extra['error_code'] = error_code
        if extra_data:
            extra['extra_data'] = extra_data
        
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    # Workflow-specific logging methods
    def workflow_start(
        self,
        workflow_id: str,
        execution_id: str,
        input_data: Optional[Dict] = None,
    ):
        """Log workflow execution start."""
        workflow_id_var.set(workflow_id)
        execution_id_var.set(execution_id)
        
        self.info(
            "Workflow execution started",
            status="started",
            extra_data={
                "input_keys": list(input_data.keys()) if input_data else [],
            }
        )
    
    def workflow_complete(
        self,
        duration_ms: float,
        status: str = "success",
        output_keys: Optional[list] = None,
    ):
        """Log workflow execution completion."""
        self.info(
            f"Workflow execution completed: {status}",
            duration_ms=duration_ms,
            status=status,
            extra_data={
                "output_keys": output_keys or [],
            }
        )
    
    def workflow_error(
        self,
        error: Exception,
        duration_ms: float,
        error_code: Optional[str] = None,
    ):
        """Log workflow execution error."""
        self.error(
            f"Workflow execution failed: {str(error)}",
            duration_ms=duration_ms,
            status="failed",
            error_code=error_code,
            exc_info=True,
        )
    
    def node_start(self, node_id: str, node_type: str):
        """Log node execution start."""
        span_id_var.set(f"node_{node_id[:8]}")
        self.info(
            f"Node execution started: {node_type}",
            node_id=node_id,
            node_type=node_type,
            status="running",
        )
    
    def node_complete(
        self,
        node_id: str,
        node_type: str,
        duration_ms: float,
        output_preview: Optional[str] = None,
    ):
        """Log node execution completion."""
        self.info(
            f"Node execution completed: {node_type}",
            node_id=node_id,
            node_type=node_type,
            duration_ms=duration_ms,
            status="success",
            extra_data={
                "output_preview": output_preview[:200] if output_preview else None,
            }
        )
    
    def node_error(
        self,
        node_id: str,
        node_type: str,
        error: Exception,
        duration_ms: float,
        error_code: Optional[str] = None,
    ):
        """Log node execution error."""
        self.error(
            f"Node execution failed: {node_type} - {str(error)}",
            node_id=node_id,
            node_type=node_type,
            duration_ms=duration_ms,
            status="failed",
            error_code=error_code,
        )
    
    def node_retry(
        self,
        node_id: str,
        node_type: str,
        attempt: int,
        max_retries: int,
        delay_seconds: float,
    ):
        """Log node retry attempt."""
        self.warning(
            f"Node retry scheduled: attempt {attempt}/{max_retries}",
            node_id=node_id,
            node_type=node_type,
            status="retrying",
            extra_data={
                "attempt": attempt,
                "max_retries": max_retries,
                "delay_seconds": delay_seconds,
            }
        )


def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    return uuid.uuid4().hex


def set_trace_context(
    trace_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
):
    """Set trace context for current execution."""
    if trace_id:
        trace_id_var.set(trace_id)
    if workflow_id:
        workflow_id_var.set(workflow_id)
    if execution_id:
        execution_id_var.set(execution_id)


def clear_trace_context():
    """Clear trace context after execution."""
    trace_id_var.set('')
    span_id_var.set('')
    workflow_id_var.set('')
    execution_id_var.set('')


def traced(name: Optional[str] = None):
    """
    Decorator for tracing function execution.
    
    Usage:
        @traced("my_operation")
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_name = name or func.__name__
            span_id = f"{operation_name}_{uuid.uuid4().hex[:8]}"
            span_id_var.set(span_id)
            
            logger = WorkflowLogger("trace")
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(
                    f"Operation completed: {operation_name}",
                    duration_ms=duration_ms,
                    status="success",
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {operation_name}",
                    duration_ms=duration_ms,
                    status="failed",
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation_name = name or func.__name__
            span_id = f"{operation_name}_{uuid.uuid4().hex[:8]}"
            span_id_var.set(span_id)
            
            logger = WorkflowLogger("trace")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(
                    f"Operation completed: {operation_name}",
                    duration_ms=duration_ms,
                    status="success",
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {operation_name}",
                    duration_ms=duration_ms,
                    status="failed",
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Global logger instance
workflow_logger = WorkflowLogger("executor")
