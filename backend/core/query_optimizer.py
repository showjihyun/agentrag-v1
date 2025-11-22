"""
Database query optimization utilities.
"""
from typing import List, Optional, Any, Type
from sqlalchemy.orm import Session, Query, joinedload, selectinload, subqueryload
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Utilities for optimizing database queries."""
    
    @staticmethod
    def apply_eager_loading(
        query: Query,
        model: Type,
        relationships: List[str],
        strategy: str = "joined"
    ) -> Query:
        """
        Apply eager loading to query to prevent N+1 problems.
        
        Args:
            query: SQLAlchemy query
            model: Model class
            relationships: List of relationship names to load
            strategy: Loading strategy (joined, select, subquery)
            
        Returns:
            Optimized query
        """
        load_strategy = {
            "joined": joinedload,
            "select": selectinload,
            "subquery": subqueryload,
        }.get(strategy, joinedload)
        
        for rel in relationships:
            try:
                query = query.options(load_strategy(getattr(model, rel)))
            except AttributeError:
                logger.warning(f"Relationship '{rel}' not found on {model.__name__}")
        
        return query
    
    @staticmethod
    def paginate_query(
        query: Query,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ) -> tuple[List[Any], int]:
        """
        Paginate query results efficiently.
        
        Args:
            query: SQLAlchemy query
            page: Page number (1-indexed)
            page_size: Items per page
            max_page_size: Maximum allowed page size
            
        Returns:
            Tuple of (items, total_count)
        """
        # Validate and limit page size
        page_size = min(page_size, max_page_size)
        page = max(1, page)
        
        # Get total count efficiently
        total_count = query.count()
        
        # Get paginated items
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total_count
    
    @staticmethod
    def optimize_count_query(query: Query) -> int:
        """
        Optimize count query by using COUNT(*) instead of loading objects.
        
        Args:
            query: SQLAlchemy query
            
        Returns:
            Count result
        """
        # Use func.count() for better performance
        count_query = query.statement.with_only_columns([func.count()]).order_by(None)
        return query.session.execute(count_query).scalar()
    
    @staticmethod
    def batch_load_by_ids(
        session: Session,
        model: Type,
        ids: List[Any],
        batch_size: int = 100
    ) -> List[Any]:
        """
        Load objects by IDs in batches to avoid large IN clauses.
        
        Args:
            session: Database session
            model: Model class
            ids: List of IDs to load
            batch_size: Batch size
            
        Returns:
            List of loaded objects
        """
        results = []
        
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_results = session.query(model).filter(
                model.id.in_(batch_ids)
            ).all()
            results.extend(batch_results)
        
        return results
    
    @staticmethod
    def add_time_range_filter(
        query: Query,
        time_column,
        hours: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Query:
        """
        Add time range filter to query efficiently.
        
        Args:
            query: SQLAlchemy query
            time_column: Column to filter on
            hours: Number of hours to look back
            start_time: Start time (alternative to hours)
            end_time: End time
            
        Returns:
            Filtered query
        """
        if hours is not None:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(time_column >= cutoff_time)
        
        if start_time is not None:
            query = query.filter(time_column >= start_time)
        
        if end_time is not None:
            query = query.filter(time_column <= end_time)
        
        return query
    
    @staticmethod
    def optimize_exists_check(
        session: Session,
        model: Type,
        filters: dict
    ) -> bool:
        """
        Efficiently check if record exists without loading it.
        
        Args:
            session: Database session
            model: Model class
            filters: Filter conditions
            
        Returns:
            True if exists, False otherwise
        """
        query = session.query(model.id)
        
        for key, value in filters.items():
            query = query.filter(getattr(model, key) == value)
        
        return session.query(query.exists()).scalar()
    
    @staticmethod
    def bulk_update_optimized(
        session: Session,
        model: Type,
        updates: List[dict],
        id_field: str = "id"
    ) -> int:
        """
        Perform bulk update efficiently.
        
        Args:
            session: Database session
            model: Model class
            updates: List of dicts with id and fields to update
            id_field: Name of ID field
            
        Returns:
            Number of updated records
        """
        if not updates:
            return 0
        
        # Use bulk_update_mappings for better performance
        session.bulk_update_mappings(model, updates)
        session.commit()
        
        return len(updates)
    
    @staticmethod
    def get_aggregated_stats(
        session: Session,
        model: Type,
        group_by_column,
        aggregate_column,
        aggregate_func: str = "count",
        filters: Optional[dict] = None
    ) -> List[tuple]:
        """
        Get aggregated statistics efficiently.
        
        Args:
            session: Database session
            model: Model class
            group_by_column: Column to group by
            aggregate_column: Column to aggregate
            aggregate_func: Aggregation function (count, sum, avg, max, min)
            filters: Optional filter conditions
            
        Returns:
            List of (group_value, aggregate_value) tuples
        """
        # Map function name to SQLAlchemy func
        func_map = {
            "count": func.count,
            "sum": func.sum,
            "avg": func.avg,
            "max": func.max,
            "min": func.min,
        }
        
        agg_func = func_map.get(aggregate_func, func.count)
        
        query = session.query(
            group_by_column,
            agg_func(aggregate_column).label('aggregate_value')
        ).group_by(group_by_column)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                query = query.filter(getattr(model, key) == value)
        
        return query.all()


class QueryProfiler:
    """Profile and analyze query performance."""
    
    def __init__(self):
        self.query_times = []
    
    def profile_query(self, query_name: str):
        """
        Decorator to profile query execution time.
        
        Usage:
            @profiler.profile_query("get_agents")
            async def get_agents():
                ...
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = datetime.utcnow()
                
                try:
                    result = await func(*args, **kwargs)
                    
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    self.query_times.append({
                        "query_name": query_name,
                        "duration_ms": duration_ms,
                        "timestamp": start_time,
                        "success": True
                    })
                    
                    if duration_ms > 1000:  # Log slow queries
                        logger.warning(
                            f"Slow query detected: {query_name} took {duration_ms:.2f}ms"
                        )
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    self.query_times.append({
                        "query_name": query_name,
                        "duration_ms": duration_ms,
                        "timestamp": start_time,
                        "success": False,
                        "error": str(e)
                    })
                    
                    raise
            
            return wrapper
        return decorator
    
    def get_stats(self) -> dict:
        """Get profiling statistics."""
        if not self.query_times:
            return {}
        
        total_queries = len(self.query_times)
        successful_queries = sum(1 for q in self.query_times if q.get("success", True))
        
        durations = [q["duration_ms"] for q in self.query_times]
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": total_queries - successful_queries,
            "avg_duration_ms": sum(durations) / len(durations),
            "max_duration_ms": max(durations),
            "min_duration_ms": min(durations),
            "slow_queries": [
                q for q in self.query_times 
                if q["duration_ms"] > 1000
            ]
        }
    
    def reset(self):
        """Reset profiling data."""
        self.query_times = []


# Global profiler instance
query_profiler = QueryProfiler()
