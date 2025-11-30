"""
Common Utilities Module

Provides shared utility functions used across the backend.
Centralizes common patterns to reduce code duplication.
"""

import re
import uuid
import hashlib
from typing import Any, Dict, List, Optional, TypeVar, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# UUID Utilities
# =============================================================================

def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def parse_uuid(value: str) -> Optional[uuid.UUID]:
    """Parse a string to UUID, returning None if invalid."""
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        return None


# =============================================================================
# String Utilities
# =============================================================================

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to max_length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_string(text: str, allow_unicode: bool = True) -> str:
    """Sanitize a string by removing potentially dangerous characters."""
    if allow_unicode:
        # Remove control characters but keep unicode
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    else:
        # ASCII only
        return re.sub(r'[^\x20-\x7e]', '', text)


def generate_slug(text: str, max_length: int = 50) -> str:
    """Generate a URL-safe slug from text."""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:max_length].strip('-')


# =============================================================================
# Hash Utilities
# =============================================================================

def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """Generate a hash of the given data."""
    hasher = hashlib.new(algorithm)
    hasher.update(data.encode('utf-8'))
    return hasher.hexdigest()


def generate_short_hash(data: str, length: int = 8) -> str:
    """Generate a short hash for cache keys or identifiers."""
    return generate_hash(data)[:length]


# =============================================================================
# Date/Time Utilities
# =============================================================================

def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


def utc_now_iso() -> str:
    """Get current UTC datetime as ISO string."""
    return datetime.utcnow().isoformat() + "Z"


def parse_iso_datetime(value: str) -> Optional[datetime]:
    """Parse an ISO datetime string."""
    try:
        # Handle 'Z' suffix
        if value.endswith('Z'):
            value = value[:-1] + '+00:00'
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# =============================================================================
# Dictionary Utilities
# =============================================================================

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_get(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary."""
    result = d
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
        if result is None:
            return default
    return result


# =============================================================================
# List Utilities
# =============================================================================

def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deduplicate(lst: List[T], key: Optional[Callable[[T], Any]] = None) -> List[T]:
    """Remove duplicates from a list while preserving order."""
    seen = set()
    result = []
    for item in lst:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


# =============================================================================
# Retry Decorator
# =============================================================================

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying a function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}"
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


# =============================================================================
# Async Retry Decorator
# =============================================================================

def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Async version of retry decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Async retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator
