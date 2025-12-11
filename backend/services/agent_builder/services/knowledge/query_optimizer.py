"""
Database Query Optimization for Agent Builder.

Provides query optimization utilities and best practices for efficient database access.
"""

import logging
from typing import List, Optional, Any
from sqlalchemy import Index
from sqlalchemy.orm import Session, joinedload, selectinload, subqueryload
from sqlalchemy.sql import text

from backend.db.models.agent_builder import (
    Agent,
    AgentExecution,
    Block,
    Workflow,
    Knowledgebase,
    Variable
)

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Provides optimized database queries for Agent Builder.
    
    Features:
    - Eager loading strategies
    - Query result caching
    - Index recommendations
    - Query performance monitoring
    """
    
    def __init__(self, db: Session):
        """
        Initialize query optimizer.
        
        Args:
            db: Database session
        """
        self.db = db
        logger.info("QueryOptimizer initialized")
    
    # ========================================================================
    # Optimized Agent Queries
    # ========================================================================
    
    def get_agent_with_relations(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent with all related data in a single query.
        
        Uses eager loading to avoid N+1 queries.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent with relations or None
        """
        return (
            self.db.query(Agent)
            .options(
                joinedload(Agent.tools),
                joinedload(Agent.knowledgebases),
                selectinload(Agent.versions)
            )
            .filter(Agent.id == agent_id)
            .first()
        )
    
    def list_agents_optimized(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Agent]:
        """
        List agents with optimized query.
        
        Args:
            user_id: User ID
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of agents
        """
        return (
            self.db.query(Agent)
            .filter(
                Agent.user_id == user_id,
                Agent.deleted_at.is_(None)
            )
            .order_by(Agent.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    # ========================================================================
    # Optimized Execution Queries
    # ========================================================================
    
    def get_execution_with_details(
        self,
        execution_id: str
    ) -> Optional[AgentExecution]:
        """
        Get execution with all related data.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            AgentExecution with relations or None
        """
        return (
            self.db.query(AgentExecution)
            .options(
                joinedload(AgentExecution.agent),
                selectinload(AgentExecution.steps),
                joinedload(AgentExecution.metrics)
            )
            .filter(AgentExecution.id == execution_id)
            .first()
        )
    
    def list_executions_optimized(
        self,
        user_id: str,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AgentExecution]:
        """
        List executions with optimized query.
        
        Args:
            user_id: User ID
            agent_id: Optional agent ID filter
            status: Optional status filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of executions
        """
        query = self.db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id
        )
        
        if agent_id:
            query = query.filter(AgentExecution.agent_id == agent_id)
        
        if status:
            query = query.filter(AgentExecution.status == status)
        
        return (
            query
            .order_by(AgentExecution.started_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    # ========================================================================
    # Bulk Operations
    # ========================================================================
    
    def bulk_update_execution_status(
        self,
        execution_ids: List[str],
        status: str
    ):
        """
        Bulk update execution status.
        
        More efficient than updating one by one.
        
        Args:
            execution_ids: List of execution IDs
            status: New status
        """
        self.db.query(AgentExecution).filter(
            AgentExecution.id.in_(execution_ids)
        ).update(
            {"status": status},
            synchronize_session=False
        )
        self.db.commit()
    
    # ========================================================================
    # Aggregation Queries
    # ========================================================================
    
    def get_execution_stats(
        self,
        user_id: str,
        agent_id: Optional[str] = None
    ) -> dict:
        """
        Get execution statistics with a single query.
        
        Args:
            user_id: User ID
            agent_id: Optional agent ID filter
            
        Returns:
            Dictionary with statistics
        """
        query = """
        SELECT
            COUNT(*) as total_executions,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
            AVG(duration_ms) as avg_duration_ms,
            MAX(duration_ms) as max_duration_ms,
            MIN(duration_ms) as min_duration_ms
        FROM agent_executions
        WHERE user_id = :user_id
        """
        
        params = {"user_id": user_id}
        
        if agent_id:
            query += " AND agent_id = :agent_id"
            params["agent_id"] = agent_id
        
        result = self.db.execute(text(query), params).fetchone()
        
        return {
            "total_executions": result[0] or 0,
            "completed": result[1] or 0,
            "failed": result[2] or 0,
            "running": result[3] or 0,
            "avg_duration_ms": float(result[4]) if result[4] else 0.0,
            "max_duration_ms": result[5] or 0,
            "min_duration_ms": result[6] or 0,
            "success_rate": (result[1] / result[0] * 100) if result[0] else 0.0
        }
    
    # ========================================================================
    # Index Recommendations
    # ========================================================================
    
    @staticmethod
    def get_recommended_indexes() -> List[str]:
        """
        Get list of recommended indexes for Agent Builder tables.
        
        Returns:
            List of index creation SQL statements
        """
        return [
            # Agent indexes
            "CREATE INDEX IF NOT EXISTS idx_agents_user_type ON agents(user_id, agent_type);",
            "CREATE INDEX IF NOT EXISTS idx_agents_user_created ON agents(user_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_agents_public ON agents(is_public) WHERE is_public = true;",
            "CREATE INDEX IF NOT EXISTS idx_agents_deleted ON agents(deleted_at) WHERE deleted_at IS NULL;",
            
            # Execution indexes
            "CREATE INDEX IF NOT EXISTS idx_executions_user_status ON agent_executions(user_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_executions_agent_started ON agent_executions(agent_id, started_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_executions_user_started ON agent_executions(user_id, started_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_executions_status ON agent_executions(status) WHERE status = 'running';",
            
            # Block indexes
            "CREATE INDEX IF NOT EXISTS idx_blocks_user_type ON blocks(user_id, block_type);",
            "CREATE INDEX IF NOT EXISTS idx_blocks_public ON blocks(is_public) WHERE is_public = true;",
            
            # Workflow indexes
            "CREATE INDEX IF NOT EXISTS idx_workflows_user ON workflows(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_workflows_public ON workflows(is_public) WHERE is_public = true;",
            
            # Variable indexes
            "CREATE INDEX IF NOT EXISTS idx_variables_scope ON variables(scope, scope_id, name);",
            "CREATE INDEX IF NOT EXISTS idx_variables_deleted ON variables(deleted_at) WHERE deleted_at IS NULL;",
            
            # Knowledgebase indexes
            "CREATE INDEX IF NOT EXISTS idx_knowledgebases_user ON knowledgebases(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_kb_documents_kb ON knowledgebase_documents(knowledgebase_id);",
        ]
    
    def apply_recommended_indexes(self):
        """Apply all recommended indexes."""
        indexes = self.get_recommended_indexes()
        
        for index_sql in indexes:
            try:
                self.db.execute(text(index_sql))
                logger.info(f"Applied index: {index_sql[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to apply index: {e}")
        
        self.db.commit()
        logger.info("Applied all recommended indexes")
    
    # ========================================================================
    # Query Performance Monitoring
    # ========================================================================
    
    def analyze_slow_queries(self, threshold_ms: int = 1000) -> List[dict]:
        """
        Analyze slow queries from PostgreSQL logs.
        
        Args:
            threshold_ms: Threshold in milliseconds
            
        Returns:
            List of slow query information
        """
        query = """
        SELECT
            query,
            calls,
            total_time,
            mean_time,
            max_time
        FROM pg_stat_statements
        WHERE mean_time > :threshold
        ORDER BY mean_time DESC
        LIMIT 20;
        """
        
        try:
            result = self.db.execute(
                text(query),
                {"threshold": threshold_ms}
            ).fetchall()
            
            return [
                {
                    "query": row[0],
                    "calls": row[1],
                    "total_time_ms": row[2],
                    "mean_time_ms": row[3],
                    "max_time_ms": row[4]
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to analyze slow queries: {e}")
            return []


# Query optimization best practices documentation
QUERY_OPTIMIZATION_BEST_PRACTICES = """
# Database Query Optimization Best Practices

## 1. Use Eager Loading
- Use `joinedload()` for one-to-one and many-to-one relationships
- Use `selectinload()` for one-to-many and many-to-many relationships
- Avoid N+1 query problems

## 2. Add Proper Indexes
- Index foreign keys
- Index columns used in WHERE clauses
- Index columns used in ORDER BY
- Use composite indexes for multi-column queries
- Use partial indexes for filtered queries

## 3. Limit Result Sets
- Always use LIMIT for list queries
- Implement pagination
- Use cursor-based pagination for large datasets

## 4. Use Bulk Operations
- Use bulk_insert_mappings() for multiple inserts
- Use bulk_update_mappings() for multiple updates
- Use IN clauses instead of multiple OR conditions

## 5. Optimize Aggregations
- Use database aggregation functions (COUNT, SUM, AVG)
- Avoid loading all records for counting
- Use subqueries for complex aggregations

## 6. Connection Pooling
- Configure appropriate pool_size
- Set max_overflow for burst traffic
- Use pool_pre_ping to handle stale connections
- Set pool_recycle to refresh connections

## 7. Query Caching
- Cache frequently accessed data in Redis
- Use appropriate TTL values
- Invalidate cache on updates
- Consider query result caching

## 8. Monitor Performance
- Enable query logging in development
- Use pg_stat_statements for production
- Monitor slow query logs
- Track connection pool metrics

## 9. Avoid Common Pitfalls
- Don't use SELECT * (specify columns)
- Don't load relationships unnecessarily
- Don't perform calculations in Python (use SQL)
- Don't forget to close sessions
- Don't use synchronous queries in async code

## 10. Database-Specific Optimizations
- Use EXPLAIN ANALYZE to understand query plans
- Create appropriate indexes based on query patterns
- Use materialized views for complex aggregations
- Consider table partitioning for large tables
"""
