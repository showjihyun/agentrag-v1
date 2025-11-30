"""
Database Query Optimizers

Advanced query optimization utilities for workflow system.
Includes batch operations, cursor pagination, and query analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, TypeVar, Generic
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session, Query
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CursorPage(Generic[T]):
    """Cursor-based pagination result."""
    items: List[T]
    next_cursor: Optional[str]
    has_more: bool
    total_estimate: Optional[int] = None


@dataclass
class QueryStats:
    """Query execution statistics."""
    query: str
    execution_time_ms: float
    rows_returned: int
    rows_examined: int
    index_used: Optional[str]
    suggestions: List[str]


class WorkflowQueryOptimizer:
    """
    Query optimizer for workflow-related queries.
    
    Features:
    - Cursor-based pagination (better than OFFSET for large datasets)
    - Batch insert/update operations
    - Query analysis and suggestions
    - Materialized view management
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # =========================================================================
    # CURSOR-BASED PAGINATION
    # =========================================================================
    
    def get_executions_cursor(
        self,
        workflow_id: str,
        cursor: Optional[str] = None,
        limit: int = 50,
        status_filter: Optional[str] = None,
    ) -> CursorPage:
        """
        Get workflow executions with cursor-based pagination.
        
        More efficient than OFFSET for large datasets.
        
        Args:
            workflow_id: Workflow ID
            cursor: Cursor from previous page (started_at timestamp)
            limit: Page size
            status_filter: Optional status filter
            
        Returns:
            CursorPage with executions
        """
        from backend.db.models.agent_builder import WorkflowExecution
        
        query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        )
        
        if status_filter:
            query = query.filter(WorkflowExecution.status == status_filter)
        
        if cursor:
            # Decode cursor (ISO timestamp)
            cursor_time = datetime.fromisoformat(cursor)
            query = query.filter(WorkflowExecution.started_at < cursor_time)
        
        # Get one extra to check if there are more
        items = query.order_by(
            WorkflowExecution.started_at.desc()
        ).limit(limit + 1).all()
        
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        
        next_cursor = None
        if items and has_more:
            next_cursor = items[-1].started_at.isoformat()
        
        return CursorPage(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )
    
    def get_workflows_cursor(
        self,
        user_id: str,
        cursor: Optional[str] = None,
        limit: int = 20,
        include_public: bool = True,
    ) -> CursorPage:
        """
        Get workflows with cursor-based pagination.
        
        Args:
            user_id: User ID
            cursor: Cursor (updated_at timestamp)
            limit: Page size
            include_public: Include public workflows
            
        Returns:
            CursorPage with workflows
        """
        from backend.db.models.agent_builder import Workflow
        
        if include_public:
            query = self.db.query(Workflow).filter(
                or_(Workflow.user_id == user_id, Workflow.is_public == True)
            )
        else:
            query = self.db.query(Workflow).filter(Workflow.user_id == user_id)
        
        if cursor:
            cursor_time = datetime.fromisoformat(cursor)
            query = query.filter(Workflow.updated_at < cursor_time)
        
        items = query.order_by(
            Workflow.updated_at.desc()
        ).limit(limit + 1).all()
        
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        
        next_cursor = None
        if items and has_more:
            next_cursor = items[-1].updated_at.isoformat()
        
        return CursorPage(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )
    
    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================
    
    def batch_insert_executions(
        self,
        executions: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """
        Batch insert workflow executions.
        
        Args:
            executions: List of execution dicts
            batch_size: Batch size for inserts
            
        Returns:
            Number of inserted rows
        """
        from backend.db.models.agent_builder import WorkflowExecution
        
        total_inserted = 0
        
        for i in range(0, len(executions), batch_size):
            batch = executions[i:i + batch_size]
            
            stmt = insert(WorkflowExecution.__table__).values(batch)
            self.db.execute(stmt)
            total_inserted += len(batch)
        
        self.db.commit()
        logger.info(f"Batch inserted {total_inserted} executions")
        
        return total_inserted
    
    def batch_update_status(
        self,
        execution_ids: List[str],
        new_status: str,
        error_message: Optional[str] = None,
    ) -> int:
        """
        Batch update execution status.
        
        Args:
            execution_ids: List of execution IDs
            new_status: New status
            error_message: Optional error message
            
        Returns:
            Number of updated rows
        """
        from backend.db.models.agent_builder import WorkflowExecution
        
        update_values = {
            "status": new_status,
            "completed_at": datetime.utcnow() if new_status in ["completed", "failed"] else None,
        }
        
        if error_message:
            update_values["error_message"] = error_message
        
        result = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id.in_(execution_ids)
        ).update(update_values, synchronize_session=False)
        
        self.db.commit()
        logger.info(f"Batch updated {result} executions to status '{new_status}'")
        
        return result
    
    def bulk_delete_old_executions(
        self,
        workflow_id: str,
        older_than_days: int = 90,
        keep_failed: bool = True,
    ) -> int:
        """
        Bulk delete old executions.
        
        Args:
            workflow_id: Workflow ID
            older_than_days: Delete executions older than this
            keep_failed: Keep failed executions for debugging
            
        Returns:
            Number of deleted rows
        """
        from backend.db.models.agent_builder import WorkflowExecution
        
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        
        query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id,
            WorkflowExecution.started_at < cutoff,
        )
        
        if keep_failed:
            query = query.filter(WorkflowExecution.status != "failed")
        
        result = query.delete(synchronize_session=False)
        self.db.commit()
        
        logger.info(f"Deleted {result} old executions for workflow {workflow_id}")
        
        return result
    
    # =========================================================================
    # STATISTICS QUERIES (Using DB Functions)
    # =========================================================================
    
    def get_execution_stats(
        self,
        workflow_id: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get execution statistics using optimized DB function.
        
        Args:
            workflow_id: Workflow ID
            days: Number of days to analyze
            
        Returns:
            Statistics dict
        """
        try:
            result = self.db.execute(
                text("SELECT * FROM get_workflow_execution_stats(:workflow_id, :days)"),
                {"workflow_id": workflow_id, "days": days}
            ).fetchone()
            
            if result:
                return {
                    "total_executions": result[0] or 0,
                    "successful_executions": result[1] or 0,
                    "failed_executions": result[2] or 0,
                    "avg_duration_ms": float(result[3]) if result[3] else 0,
                    "p50_duration_ms": float(result[4]) if result[4] else 0,
                    "p95_duration_ms": float(result[5]) if result[5] else 0,
                    "p99_duration_ms": float(result[6]) if result[6] else 0,
                }
        except Exception as e:
            logger.warning(f"DB function not available, using fallback: {e}")
        
        # Fallback to regular query
        return self._get_execution_stats_fallback(workflow_id, days)
    
    def _get_execution_stats_fallback(
        self,
        workflow_id: str,
        days: int,
    ) -> Dict[str, Any]:
        """Fallback statistics query."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        executions = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id,
            WorkflowExecution.started_at >= cutoff,
        ).all()
        
        if not executions:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "avg_duration_ms": 0,
                "p50_duration_ms": 0,
                "p95_duration_ms": 0,
                "p99_duration_ms": 0,
            }
        
        durations = [e.duration_ms for e in executions if e.duration_ms]
        durations.sort()
        
        def percentile(data, p):
            if not data:
                return 0
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]
        
        return {
            "total_executions": len(executions),
            "successful_executions": sum(1 for e in executions if e.status == "completed"),
            "failed_executions": sum(1 for e in executions if e.status == "failed"),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "p50_duration_ms": percentile(durations, 50),
            "p95_duration_ms": percentile(durations, 95),
            "p99_duration_ms": percentile(durations, 99),
        }
    
    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get user workflow summary using optimized DB function.
        
        Args:
            user_id: User ID
            
        Returns:
            Summary dict
        """
        try:
            result = self.db.execute(
                text("SELECT * FROM get_user_workflow_summary(:user_id)"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return {
                    "total_workflows": result[0] or 0,
                    "total_executions": result[1] or 0,
                    "executions_today": result[2] or 0,
                    "executions_this_week": result[3] or 0,
                    "success_rate": float(result[4]) if result[4] else 100.0,
                }
        except Exception as e:
            logger.warning(f"DB function not available: {e}")
        
        return {
            "total_workflows": 0,
            "total_executions": 0,
            "executions_today": 0,
            "executions_this_week": 0,
            "success_rate": 100.0,
        }
    
    # =========================================================================
    # QUERY ANALYSIS
    # =========================================================================
    
    def analyze_query(self, query_str: str) -> QueryStats:
        """
        Analyze a query and provide optimization suggestions.
        
        Args:
            query_str: SQL query string
            
        Returns:
            QueryStats with analysis
        """
        suggestions = []
        
        # Get EXPLAIN ANALYZE
        try:
            result = self.db.execute(
                text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_str}")
            ).fetchone()
            
            plan = result[0][0] if result else {}
            
            execution_time = plan.get("Execution Time", 0)
            planning_time = plan.get("Planning Time", 0)
            
            # Analyze plan
            plan_node = plan.get("Plan", {})
            rows_returned = plan_node.get("Actual Rows", 0)
            rows_examined = plan_node.get("Plan Rows", 0)
            
            # Check for sequential scans
            if "Seq Scan" in str(plan):
                suggestions.append("Consider adding an index to avoid sequential scan")
            
            # Check for high row estimates
            if rows_examined > 10000:
                suggestions.append("Query examines many rows - consider adding filters or indexes")
            
            # Check for sort operations
            if "Sort" in str(plan):
                suggestions.append("Query includes sorting - ensure index supports ORDER BY")
            
            return QueryStats(
                query=query_str[:200],
                execution_time_ms=execution_time,
                rows_returned=rows_returned,
                rows_examined=rows_examined,
                index_used=plan_node.get("Index Name"),
                suggestions=suggestions,
            )
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return QueryStats(
                query=query_str[:200],
                execution_time_ms=0,
                rows_returned=0,
                rows_examined=0,
                index_used=None,
                suggestions=[f"Analysis failed: {str(e)}"],
            )
    
    def get_slow_queries(self, min_duration_ms: float = 100) -> List[Dict[str, Any]]:
        """
        Get slow queries from pg_stat_statements.
        
        Args:
            min_duration_ms: Minimum duration threshold
            
        Returns:
            List of slow query info
        """
        try:
            result = self.db.execute(text("""
                SELECT 
                    query,
                    calls,
                    mean_exec_time as avg_time_ms,
                    max_exec_time as max_time_ms,
                    rows
                FROM pg_stat_statements
                WHERE mean_exec_time > :min_duration
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """), {"min_duration": min_duration_ms}).fetchall()
            
            return [
                {
                    "query": row[0][:200],
                    "calls": row[1],
                    "avg_time_ms": row[2],
                    "max_time_ms": row[3],
                    "rows": row[4],
                }
                for row in result
            ]
        except Exception as e:
            logger.warning(f"pg_stat_statements not available: {e}")
            return []
    
    # =========================================================================
    # INDEX RECOMMENDATIONS
    # =========================================================================
    
    def get_missing_indexes(self) -> List[Dict[str, Any]]:
        """
        Get missing index recommendations.
        
        Returns:
            List of index recommendations
        """
        try:
            result = self.db.execute(text("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch
                FROM pg_stat_user_tables
                WHERE seq_scan > idx_scan
                  AND seq_tup_read > 10000
                ORDER BY seq_tup_read DESC
                LIMIT 10
            """)).fetchall()
            
            recommendations = []
            for row in result:
                recommendations.append({
                    "table": row[1],
                    "seq_scans": row[2],
                    "seq_rows_read": row[3],
                    "index_scans": row[4],
                    "suggestion": f"Table '{row[1]}' has high sequential scan ratio. Consider adding indexes.",
                })
            
            return recommendations
        except Exception as e:
            logger.warning(f"Index analysis failed: {e}")
            return []
