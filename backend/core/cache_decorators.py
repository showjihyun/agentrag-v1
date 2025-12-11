"""
Cache decorators for API endpoints and service methods.

Provides easy-to-use decorators for caching function results.
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional, Union
from datetime import timedelta

logger = logging.getLogger(__name__)


def generate_cache_key(
    prefix: str,
    func_name: str,
    args: tuple,
    kwargs: dict,
    key_params: Optional[list[str]] = None,
) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        prefix: Cache key prefix
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments
        key_params: Specific kwargs to include in key (None = all)
    
    Returns:
        Cache key string
    """
    # Build key data
    key_data = {"func": func_name}
    
    # Add positional args (skip self/cls)
    if args:
        key_data["args"] = [str(a) for a in args if not hasattr(a, "__dict__")]
    
    # Add keyword args
    if key_params:
        key_data["kwargs"] = {k: v for k, v in kwargs.items() if k in key_params}
    else:
        # Exclude non-serializable objects
        key_data["kwargs"] = {
            k: v for k, v in kwargs.items() 
            if isinstance(v, (str, int, float, bool, list, dict, type(None)))
        }
    
    # Generate hash
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    return f"{prefix}:{func_name}:{key_hash}"


def cached(
    ttl: Union[int, timedelta] = 300,
    namespace: str = "api",
    key_params: Optional[list[str]] = None,
    use_l1: bool = True,
    use_l2: bool = True,
):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds or timedelta
        namespace: Cache namespace
        key_params: Specific kwargs to include in cache key
        use_l1: Use L1 (memory) cache
        use_l2: Use L2 (Redis) cache
    
    Usage:
        @cached(ttl=300, namespace="documents")
        async def get_document(document_id: str):
            ...
    """
    if isinstance(ttl, timedelta):
        ttl = int(ttl.total_seconds())
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager from dependencies
            from backend.core.dependencies import get_cache_manager_instance
            
            cache_manager = get_cache_manager_instance()
            if not cache_manager:
                # No cache available, execute function directly
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = generate_cache_key(
                prefix=namespace,
                func_name=func.__name__,
                args=args,
                kwargs=kwargs,
                key_params=key_params,
            )
            
            # Try to get from cache
            try:
                cached_value = await cache_manager.get(
                    key=cache_key,
                    namespace=namespace,
                    use_l1=use_l1,
                    use_l2=use_l2,
                )
                
                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value
            except Exception as e:
                logger.warning(f"Cache get error: {e}")
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            try:
                await cache_manager.set(
                    key=cache_key,
                    value=result,
                    namespace=namespace,
                    ttl=ttl,
                    use_l1=use_l1,
                    use_l2=use_l2,
                )
                logger.debug(f"Cache set: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set error: {e}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(
    namespace: str,
    key_pattern: Optional[str] = None,
):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        namespace: Cache namespace to invalidate
        key_pattern: Optional key pattern to match
    
    Usage:
        @invalidate_cache(namespace="documents")
        async def update_document(document_id: str, data: dict):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function first
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            from backend.core.dependencies import get_cache_manager_instance
            
            cache_manager = get_cache_manager_instance()
            if cache_manager:
                try:
                    await cache_manager.clear_namespace(namespace)
                    logger.debug(f"Cache invalidated: {namespace}")
                except Exception as e:
                    logger.warning(f"Cache invalidation error: {e}")
            
            return result
        
        return wrapper
    return decorator


class CacheConfig:
    """Cache configuration presets."""
    
    # Short-lived cache (30 seconds) - for frequently changing data
    SHORT = {"ttl": 30, "use_l1": True, "use_l2": False}
    
    # Medium cache (5 minutes) - default for most API responses
    MEDIUM = {"ttl": 300, "use_l1": True, "use_l2": True}
    
    # Long cache (30 minutes) - for rarely changing data
    LONG = {"ttl": 1800, "use_l1": True, "use_l2": True}
    
    # Static cache (1 hour) - for static/configuration data
    STATIC = {"ttl": 3600, "use_l1": True, "use_l2": True}
    
    # Query cache (10 minutes) - for search/query results
    QUERY = {"ttl": 600, "use_l1": True, "use_l2": True}
    
    # User-specific cache (5 minutes)
    USER = {"ttl": 300, "use_l1": True, "use_l2": True}


# Convenience decorators with preset configurations
def cached_short(namespace: str = "api", key_params: Optional[list[str]] = None):
    """Cache for 30 seconds (L1 only)."""
    return cached(namespace=namespace, key_params=key_params, **CacheConfig.SHORT)


def cached_medium(namespace: str = "api", key_params: Optional[list[str]] = None):
    """Cache for 5 minutes (L1 + L2)."""
    return cached(namespace=namespace, key_params=key_params, **CacheConfig.MEDIUM)


def cached_long(namespace: str = "api", key_params: Optional[list[str]] = None):
    """Cache for 30 minutes (L1 + L2)."""
    return cached(namespace=namespace, key_params=key_params, **CacheConfig.LONG)


def cached_static(namespace: str = "api", key_params: Optional[list[str]] = None):
    """Cache for 1 hour (L1 + L2)."""
    return cached(namespace=namespace, key_params=key_params, **CacheConfig.STATIC)


def cached_query(namespace: str = "query", key_params: Optional[list[str]] = None):
    """Cache query results for 10 minutes."""
    return cached(namespace=namespace, key_params=key_params, **CacheConfig.QUERY)
