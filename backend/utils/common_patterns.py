"""
Common patterns and utilities to reduce code duplication.
"""
import logging
from typing import Any, Dict, Optional, Callable, TypeVar, List
from functools import wraps
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

T = TypeVar('T')


def log_execution(
    operation: str,
    level: str = "info",
    include_duration: bool = True
):
    """
    Decorator to log function execution.
    
    Args:
        operation: Operation name for logging
        level: Log level (info, debug, warning, error)
        include_duration: Include execution duration in log
        
    Usage:
        @log_execution("create_agent")
        async def create_agent(...):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow() if include_duration else None
            
            log_func = getattr(logger, level)
            log_func(
                f"Starting {operation}",
                extra={"operation": operation}
            )
            
            try:
                result = await func(*args, **kwargs)
                
                extra = {"operation": operation, "status": "success"}
                if include_duration and start_time:
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    extra["duration_ms"] = duration_ms
                
                log_func(f"Completed {operation}", extra=extra)
                
                return result
                
            except Exception as e:
                logger.error(
                    f"Failed {operation}",
                    extra={"operation": operation, "error": str(e)},
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow() if include_duration else None
            
            log_func = getattr(logger, level)
            log_func(
                f"Starting {operation}",
                extra={"operation": operation}
            )
            
            try:
                result = func(*args, **kwargs)
                
                extra = {"operation": operation, "status": "success"}
                if include_duration and start_time:
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    extra["duration_ms"] = duration_ms
                
                log_func(f"Completed {operation}", extra=extra)
                
                return result
                
            except Exception as e:
                logger.error(
                    f"Failed {operation}",
                    extra={"operation": operation, "error": str(e)},
                    exc_info=True
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def safe_get(
    data: Dict[str, Any],
    *keys: str,
    default: Any = None
) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to get value from
        *keys: Keys to traverse
        default: Default value if key not found
        
    Returns:
        Value or default
        
    Usage:
        value = safe_get(data, "user", "profile", "name", default="Unknown")
    """
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def batch_process(
    items: List[T],
    batch_size: int = 100
) -> List[List[T]]:
    """
    Split items into batches.
    
    Args:
        items: Items to batch
        batch_size: Size of each batch
        
    Returns:
        List of batches
        
    Usage:
        for batch in batch_process(items, batch_size=50):
            process_batch(batch)
    """
    return [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]


async def retry_on_failure(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry function on failure with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Exceptions to catch
        
    Returns:
        Function result
        
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
                
        except exceptions as e:
            last_exception = e
            
            if attempt < max_attempts - 1:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed, retrying in {current_delay}s",
                    extra={"error": str(e)}
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(
                    f"All {max_attempts} attempts failed",
                    extra={"error": str(e)}
                )
    
    raise last_exception


def format_error_response(
    error: Exception,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Format error as response dictionary.
    
    Args:
        error: Exception to format
        include_traceback: Include traceback in response
        
    Returns:
        Error response dictionary
    """
    response = {
        "success": False,
        "error": error.__class__.__name__,
        "message": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if include_traceback:
        import traceback
        response["traceback"] = traceback.format_exc()
    
    # Add custom error attributes
    if hasattr(error, 'to_dict'):
        response.update(error.to_dict())
    
    return response


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str],
    field_name: str = "data"
) -> None:
    """
    Validate required fields in dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        field_name: Name of the data for error message
        
    Raises:
        ValueError: If required fields are missing
    """
    missing_fields = [
        field for field in required_fields
        if field not in data or data[field] is None
    ]
    
    if missing_fields:
        raise ValueError(
            f"Missing required fields in {field_name}: {', '.join(missing_fields)}"
        )


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
        
    Usage:
        merged = merge_dicts(dict1, dict2, dict3)
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def extract_ids(items: List[Any], id_field: str = "id") -> List[Any]:
    """
    Extract IDs from list of objects.
    
    Args:
        items: List of objects
        id_field: Name of ID field
        
    Returns:
        List of IDs
        
    Usage:
        ids = extract_ids(agents, id_field="id")
    """
    return [
        getattr(item, id_field) if hasattr(item, id_field) else item.get(id_field)
        for item in items
        if hasattr(item, id_field) or (isinstance(item, dict) and id_field in item)
    ]


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter out None values from dictionary.
    
    Args:
        data: Dictionary to filter
        
    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in data.items() if v is not None}


def ensure_list(value: Any) -> List[Any]:
    """
    Ensure value is a list.
    
    Args:
        value: Value to convert
        
    Returns:
        List containing value(s)
        
    Usage:
        items = ensure_list(single_item_or_list)
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str = "operation", log_level: str = "info"):
        """
        Initialize timer.
        
        Args:
            name: Operation name
            log_level: Log level for result
        """
        self.name = name
        self.log_level = log_level
        self.start_time = None
        self.duration_ms = None
    
    def __enter__(self):
        """Start timer."""
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and log duration."""
        if self.start_time:
            self.duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
            
            log_func = getattr(logger, self.log_level)
            log_func(
                f"{self.name} completed",
                extra={"operation": self.name, "duration_ms": self.duration_ms}
            )
    
    async def __aenter__(self):
        """Start timer (async)."""
        self.start_time = datetime.utcnow()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and log duration (async)."""
        if self.start_time:
            self.duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
            
            log_func = getattr(logger, self.log_level)
            log_func(
                f"{self.name} completed",
                extra={"operation": self.name, "duration_ms": self.duration_ms}
            )
