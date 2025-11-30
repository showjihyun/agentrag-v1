"""
Database Performance Utilities.

Provides tools for monitoring and optimizing database performance:
- Query execution timing
- Slow query detection
- Connection pool monitoring
- Query plan analysis
"""

import time
import logging
import functools
from typing import Any, Callable, Dict, List, Optional, TypeVar
from contextlib import contextmanager
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# Query Timing
# ============================================================================

@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query: str
    duration_ms: float
    timestamp: datetime
    rows_affected: int = 0
    is_slow: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:200] + "..." if len(self.query) > 200 else self.query,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "rows_affected": self.rows_affected,
            "is_slow": self.is_slow,
        }


class QueryProfiler:
    """
    Profiles database queries and tracks slow queries.
    
    Usage:
        profiler = QueryProfiler(slow_threshold_ms=100)
        profiler.attach(engine)
        
        # Later...
        slow_queries = profiler.get_slow_queries()
        stats = profiler.get_stats()
    """
    
    def __init__(
        self,
        slow_threshold_ms: float = 100.0,
        max_history: int = 1000,
        enabled: bool = True
    ):
        self.slow_threshold_ms = slow_threshold_ms
        self.max_history = max_history
        self.enabled = enabled
        
        self._queries: List[QueryMetrics] = []
        self._slow_queries: List[QueryMetrics] = []
        self._total_queries = 0
        self._total_duration_ms = 0.0
        self._start_times: Dict[int, float] = {}
    
    def attach(self, engine: Engine):
        """Attach profiler to SQLAlchemy engine."""
        event.listen(engine, "before_cursor_execute", self._before_execute)
        event.listen(engine, "after_cursor_execute", self._after_execute)
        logger.info("Query profiler attached to engine")
    
    def _before_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Record query start time."""
        if not self.enabled:
            return
        self._start_times[id(cursor)] = time.perf_counter()
    
    def _after_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Record query completion and metrics."""
        if not self.enabled:
            return
        
        cursor_id = id(cursor)
        start_time = self._start_times.pop(cursor_id, None)
        
        if start_time is None:
            return
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        is_slow = duration_ms > self.slow_threshold_ms
        
        metrics = QueryMetrics(
            query=statement,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            rows_affected=cursor.rowcount if cursor.rowcount >= 0 else 0,
            is_slow=is_slow,
        )
        
        # Update totals
        self._total_queries += 1
        self._total_duration_ms += duration_ms
        
        # Store in history
        self._queries.append(metrics)
        if len(self._queries) > self.max_history:
            self._queries.pop(0)
        
        # Track slow queries separately
        if is_slow:
            self._slow_queries.append(metrics)
            if len(self._slow_queries) > self.max_history:
                self._slow_queries.pop(0)
            
            logger.warning(
                f"Slow query detected: {duration_ms:.2f}ms",
                extra={
                    "query": statement[:100],
                    "duration_ms": duration_ms,
                }
            )
    
    def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent slow queries."""
        return [q.to_dict() for q in self._slow_queries[-limit:]]
    
    def get_recent_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent queries."""
        return [q.to_dict() for q in self._queries[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profiler statistics."""
        avg_duration = (
            self._total_duration_ms / self._total_queries
            if self._total_queries > 0 else 0
        )
        
        return {
            "total_queries": self._total_queries,
            "total_duration_ms": round(self._total_duration_ms, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "slow_query_count": len(self._slow_queries),
            "slow_threshold_ms": self.slow_threshold_ms,
            "enabled": self.enabled,
        }
    
    def reset(self):
        """Reset profiler statistics."""
        self._queries.clear()
        self._slow_queries.clear()
        self._total_queries = 0
        self._total_duration_ms = 0.0
        self._start_times.clear()


# Global profiler instance
_query_profiler: Optional[QueryProfiler] = None


def get_query_profiler() -> QueryProfiler:
    """Get global query profiler instance."""
    global _query_profiler
    if _query_profiler is None:
        _query_profiler = QueryProfiler()
    return _query_profiler


def setup_query_profiling(engine: Engine, slow_threshold_ms: float = 100.0):
    """Setup query profiling for an engine."""
    global _query_profiler
    _query_profiler = QueryProfiler(slow_threshold_ms=slow_threshold_ms)
    _query_profiler.attach(engine)
    return _query_profiler


# ============================================================================
# Query Timing Decorator
# ============================================================================

def timed_query(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to time database operations.
    
    Usage:
        @timed_query
        def get_user_by_id(db: Session, user_id: str):
            return db.query(User).filter(User.id == user_id).first()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.debug(
                f"Query {func.__name__} completed in {duration_ms:.2f}ms"
            )
            
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Query {func.__name__} failed after {duration_ms:.2f}ms: {e}"
            )
            raise
    
    return wrapper


@contextmanager
def query_timer(operation_name: str = "query"):
    """
    Context manager for timing database operations.
    
    Usage:
        with query_timer("fetch_users"):
            users = db.query(User).all()
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.debug(f"{operation_name} completed in {duration_ms:.2f}ms")


# ============================================================================
# Connection Pool Health
# ============================================================================

@dataclass
class PoolHealth:
    """Connection pool health status."""
    status: str  # healthy, degraded, unhealthy
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    utilization_percent: float
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "pool_size": self.pool_size,
            "checked_in": self.checked_in,
            "checked_out": self.checked_out,
            "overflow": self.overflow,
            "utilization_percent": round(self.utilization_percent, 2),
            "warnings": self.warnings,
        }


def check_pool_health(engine: Engine) -> PoolHealth:
    """
    Check connection pool health.
    
    Returns health status with warnings for potential issues.
    """
    pool = engine.pool
    
    pool_size = pool.size()
    checked_in = pool.checkedin()
    checked_out = pool.checkedout()
    overflow = pool.overflow()
    
    total_connections = pool_size + overflow
    utilization = (checked_out / total_connections * 100) if total_connections > 0 else 0
    
    warnings = []
    status = "healthy"
    
    # Check utilization
    if utilization > 90:
        status = "unhealthy"
        warnings.append(f"Pool utilization critical: {utilization:.1f}%")
    elif utilization > 75:
        status = "degraded"
        warnings.append(f"Pool utilization high: {utilization:.1f}%")
    
    # Check overflow
    if overflow > 0:
        warnings.append(f"Pool overflow active: {overflow} connections")
        if overflow > pool_size * 0.5:
            status = "degraded" if status == "healthy" else status
    
    # Check for potential leaks
    if checked_out > pool_size and checked_in == 0:
        warnings.append("Potential connection leak: all connections checked out")
        status = "unhealthy"
    
    return PoolHealth(
        status=status,
        pool_size=pool_size,
        checked_in=checked_in,
        checked_out=checked_out,
        overflow=overflow,
        utilization_percent=utilization,
        warnings=warnings,
    )


# ============================================================================
# Query Plan Analysis
# ============================================================================

def explain_query(db: Session, query_str: str) -> Dict[str, Any]:
    """
    Get query execution plan using EXPLAIN ANALYZE.
    
    Args:
        db: Database session
        query_str: SQL query to analyze
    
    Returns:
        Query plan analysis
    """
    try:
        result = db.execute(
            text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_str}")
        ).fetchone()
        
        if not result:
            return {"error": "No plan returned"}
        
        plan = result[0][0]
        
        # Extract key metrics
        execution_time = plan.get("Execution Time", 0)
        planning_time = plan.get("Planning Time", 0)
        plan_node = plan.get("Plan", {})
        
        # Analyze for issues
        issues = []
        
        plan_str = str(plan)
        if "Seq Scan" in plan_str:
            issues.append("Sequential scan detected - consider adding index")
        if "Sort" in plan_str and "Index" not in plan_str:
            issues.append("Sort without index - consider adding index for ORDER BY")
        if "Nested Loop" in plan_str:
            issues.append("Nested loop join - may be slow for large datasets")
        
        return {
            "execution_time_ms": execution_time,
            "planning_time_ms": planning_time,
            "total_time_ms": execution_time + planning_time,
            "actual_rows": plan_node.get("Actual Rows", 0),
            "plan_rows": plan_node.get("Plan Rows", 0),
            "node_type": plan_node.get("Node Type", "Unknown"),
            "issues": issues,
            "full_plan": plan,
        }
        
    except Exception as e:
        logger.error(f"Query plan analysis failed: {e}")
        return {"error": str(e)}


# ============================================================================
# Batch Operation Utilities
# ============================================================================

def batch_insert(
    db: Session,
    model,
    records: List[Dict[str, Any]],
    batch_size: int = 1000
) -> int:
    """
    Efficiently insert records in batches.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        records: List of record dictionaries
        batch_size: Records per batch
    
    Returns:
        Total records inserted
    """
    from sqlalchemy.dialects.postgresql import insert
    
    total_inserted = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        stmt = insert(model.__table__).values(batch)
        db.execute(stmt)
        total_inserted += len(batch)
        
        # Commit each batch to avoid memory issues
        db.commit()
    
    logger.info(f"Batch inserted {total_inserted} records into {model.__tablename__}")
    return total_inserted


def batch_update(
    db: Session,
    model,
    updates: List[Dict[str, Any]],
    id_field: str = "id",
    batch_size: int = 1000
) -> int:
    """
    Efficiently update records in batches.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        updates: List of update dictionaries (must include id_field)
        id_field: Name of the ID field
        batch_size: Records per batch
    
    Returns:
        Total records updated
    """
    total_updated = 0
    
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]
        
        for record in batch:
            record_id = record.pop(id_field)
            db.query(model).filter(
                getattr(model, id_field) == record_id
            ).update(record, synchronize_session=False)
            total_updated += 1
        
        db.commit()
    
    logger.info(f"Batch updated {total_updated} records in {model.__tablename__}")
    return total_updated
