"""
Query Optimization Utilities

Provides tools for optimizing database queries:
- N+1 query detection and prevention
- Eager loading helpers
- Query result caching
- Batch loading utilities
"""

import logging
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BatchLoader(Generic[T]):
    """
    DataLoader-style batch loader to prevent N+1 queries.

    Usage:
        loader = BatchLoader(load_users_by_ids)
        user1 = await loader.load(1)
        user2 = await loader.load(2)
        # Both loaded in single batch query
    """

    def __init__(
        self,
        batch_load_fn: Callable[[List[Any]], List[T]],
        max_batch_size: int = 100,
        cache: bool = True,
    ):
        """
        Initialize batch loader.

        Args:
            batch_load_fn: Function that loads items by list of keys
            max_batch_size: Maximum batch size
            cache: Enable caching of loaded items
        """
        self.batch_load_fn = batch_load_fn
        self.max_batch_size = max_batch_size
        self.cache_enabled = cache

        self._queue: List[tuple] = []
        self._cache: Dict[Any, T] = {}
        self._batch_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def load(self, key: Any) -> Optional[T]:
        """Load single item by key."""
        # Check cache first
        if self.cache_enabled and key in self._cache:
            return self._cache[key]

        # Add to queue
        future = asyncio.Future()
        async with self._lock:
            self._queue.append((key, future))

            # Schedule batch if not already scheduled
            if self._batch_task is None or self._batch_task.done():
                self._batch_task = asyncio.create_task(self._process_batch())

        return await future

    async def load_many(self, keys: List[Any]) -> List[Optional[T]]:
        """Load multiple items by keys."""
        tasks = [self.load(key) for key in keys]
        return await asyncio.gather(*tasks)

    async def _process_batch(self) -> None:
        """Process queued items in batch."""
        # Small delay to collect more items
        await asyncio.sleep(0.001)

        async with self._lock:
            if not self._queue:
                return

            # Get batch
            batch = self._queue[: self.max_batch_size]
            self._queue = self._queue[self.max_batch_size :]

            keys = [item[0] for item in batch]
            futures = [item[1] for item in batch]

        try:
            # Load items
            if asyncio.iscoroutinefunction(self.batch_load_fn):
                results = await self.batch_load_fn(keys)
            else:
                results = self.batch_load_fn(keys)

            # Create key -> result mapping
            result_map = {item.id: item for item in results if hasattr(item, "id")}

            # Update cache
            if self.cache_enabled:
                self._cache.update(result_map)

            # Resolve futures
            for key, future in zip(keys, futures):
                if not future.done():
                    future.set_result(result_map.get(key))

        except Exception as e:
            logger.error(f"Batch load error: {e}")
            # Reject all futures
            for _, future in batch:
                if not future.done():
                    future.set_exception(e)

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()


class QueryOptimizer:
    """
    Query optimization utilities.
    """

    @staticmethod
    def with_eager_loading(query, *relationships):
        """
        Add eager loading to query.

        Usage:
            query = select(User)
            query = QueryOptimizer.with_eager_loading(
                query,
                User.posts,
                User.profile
            )
        """
        for relationship in relationships:
            query = query.options(joinedload(relationship))
        return query

    @staticmethod
    def with_selectin_loading(query, *relationships):
        """
        Add selectin loading to query (better for collections).

        Usage:
            query = select(User)
            query = QueryOptimizer.with_selectin_loading(
                query,
                User.posts
            )
        """
        for relationship in relationships:
            query = query.options(selectinload(relationship))
        return query

    @staticmethod
    def paginate(query, page: int = 1, per_page: int = 20):
        """
        Add pagination to query.

        Args:
            query: SQLAlchemy query
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Modified query with limit and offset
        """
        offset = (page - 1) * per_page
        return query.limit(per_page).offset(offset)

    @staticmethod
    def count_query(session: Session, query) -> int:
        """
        Get count for query efficiently.

        Args:
            session: Database session
            query: SQLAlchemy query

        Returns:
            Total count
        """
        from sqlalchemy import func, select as sql_select

        # Get the query's column clause
        count_query = sql_select(func.count()).select_from(query.subquery())
        result = session.execute(count_query)
        return result.scalar()


def cache_query_result(
    cache_manager,
    namespace: str = "query",
    ttl: int = 300,
    key_fn: Optional[Callable] = None,
):
    """
    Decorator to cache query results.

    Usage:
        @cache_query_result(cache_manager, namespace="users", ttl=600)
        async def get_user_by_id(user_id: int):
            # Query database
            return user
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_fn:
                cache_key = key_fn(*args, **kwargs)
            else:
                # Default: use function name and arguments
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            result = await cache_manager.get(cache_key, namespace)
            if result is not None:
                logger.debug(f"Query cache hit: {cache_key}")
                return result

            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Cache result
            await cache_manager.set(cache_key, result, namespace, ttl)

            return result

        return wrapper

    return decorator


class QueryPerformanceMonitor:
    """
    Monitor query performance and detect slow queries.
    """

    def __init__(self, slow_query_threshold: float = 1.0):
        """
        Initialize monitor.

        Args:
            slow_query_threshold: Threshold in seconds for slow query warning
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def record_query(
        self, query_name: str, duration: float, result_count: Optional[int] = None
    ) -> None:
        """Record query execution."""
        async with self._lock:
            if query_name not in self.query_stats:
                self.query_stats[query_name] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "min_duration": float("inf"),
                    "max_duration": 0.0,
                    "slow_count": 0,
                }

            stats = self.query_stats[query_name]
            stats["count"] += 1
            stats["total_duration"] += duration
            stats["min_duration"] = min(stats["min_duration"], duration)
            stats["max_duration"] = max(stats["max_duration"], duration)

            if duration > self.slow_query_threshold:
                stats["slow_count"] += 1
                logger.warning(
                    f"Slow query detected: {query_name} took {duration:.3f}s "
                    f"(threshold: {self.slow_query_threshold}s)"
                )

    async def get_stats(self) -> Dict[str, Any]:
        """Get query statistics."""
        async with self._lock:
            stats = {}
            for query_name, data in self.query_stats.items():
                avg_duration = data["total_duration"] / data["count"]
                stats[query_name] = {
                    "count": data["count"],
                    "avg_duration": f"{avg_duration:.3f}s",
                    "min_duration": f"{data['min_duration']:.3f}s",
                    "max_duration": f"{data['max_duration']:.3f}s",
                    "slow_count": data["slow_count"],
                }
            return stats

    async def reset_stats(self) -> None:
        """Reset all statistics."""
        async with self._lock:
            self.query_stats.clear()


# Global query performance monitor
_query_monitor: Optional[QueryPerformanceMonitor] = None


def get_query_monitor() -> QueryPerformanceMonitor:
    """Get or create global query monitor."""
    global _query_monitor

    if _query_monitor is None:
        _query_monitor = QueryPerformanceMonitor()

    return _query_monitor


def monitor_query(query_name: str):
    """
    Decorator to monitor query performance.

    Usage:
        @monitor_query("get_user_by_id")
        async def get_user_by_id(user_id: int):
            # Query database
            return user
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                duration = time.time() - start_time

                # Record query
                monitor = get_query_monitor()
                result_count = len(result) if isinstance(result, list) else None
                await monitor.record_query(query_name, duration, result_count)

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Query {query_name} failed after {duration:.3f}s: {e}")
                raise

        return wrapper

    return decorator
