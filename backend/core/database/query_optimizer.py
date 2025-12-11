"""
Slow Query Detection and Optimization

Automatically detects slow queries and provides optimization recommendations.
"""

from sqlalchemy import event
from sqlalchemy.engine import Engine
from typing import Optional, List, Dict
import time
import re

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

# Slow query threshold (seconds)
SLOW_QUERY_THRESHOLD = 1.0

# Query patterns that might need optimization
OPTIMIZATION_PATTERNS = {
    'missing_where': r'SELECT.*FROM.*(?!WHERE)',
    'select_star': r'SELECT\s+\*\s+FROM',
    'no_limit': r'SELECT.*FROM.*(?!LIMIT)',
    'multiple_joins': r'JOIN.*JOIN.*JOIN',
    'subquery_in_select': r'SELECT.*\(SELECT',
}


class QueryOptimizer:
    """Analyze and optimize slow queries"""
    
    def __init__(self):
        self.slow_queries: List[Dict] = []
        self.logger = get_logger(__name__)
    
    def analyze_query(self, statement: str, duration: float) -> Optional[Dict]:
        """
        Analyze query and provide recommendations
        
        Args:
            statement: SQL statement
            duration: Execution time in seconds
            
        Returns:
            Analysis result with recommendations
        """
        if duration < SLOW_QUERY_THRESHOLD:
            return None
        
        recommendations = []
        
        # Check for common issues
        statement_upper = statement.upper()
        
        # 1. SELECT * usage
        if re.search(OPTIMIZATION_PATTERNS['select_star'], statement_upper):
            recommendations.append({
                'issue': 'SELECT * usage',
                'severity': 'medium',
                'recommendation': 'Specify only needed columns instead of SELECT *',
                'example': 'SELECT id, name, email FROM users'
            })
        
        # 2. Missing WHERE clause
        if 'SELECT' in statement_upper and 'WHERE' not in statement_upper:
            recommendations.append({
                'issue': 'Missing WHERE clause',
                'severity': 'high',
                'recommendation': 'Add WHERE clause to filter results',
                'example': 'SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY'
            })
        
        # 3. Missing LIMIT
        if 'SELECT' in statement_upper and 'LIMIT' not in statement_upper:
            recommendations.append({
                'issue': 'Missing LIMIT clause',
                'severity': 'medium',
                'recommendation': 'Add LIMIT to prevent large result sets',
                'example': 'SELECT * FROM users LIMIT 100'
            })
        
        # 4. Multiple JOINs
        join_count = statement_upper.count('JOIN')
        if join_count >= 3:
            recommendations.append({
                'issue': f'Multiple JOINs ({join_count})',
                'severity': 'high',
                'recommendation': 'Consider denormalization or caching for complex joins',
                'example': 'Use materialized views or cache results'
            })
        
        # 5. Subquery in SELECT
        if re.search(OPTIMIZATION_PATTERNS['subquery_in_select'], statement_upper):
            recommendations.append({
                'issue': 'Subquery in SELECT clause',
                'severity': 'high',
                'recommendation': 'Move subquery to JOIN or use window functions',
                'example': 'Use LEFT JOIN instead of correlated subquery'
            })
        
        # Suggest indexes
        index_suggestions = self._suggest_indexes(statement)
        
        result = {
            'statement': statement[:500],  # Truncate long queries
            'duration': duration,
            'recommendations': recommendations,
            'index_suggestions': index_suggestions,
            'severity': self._calculate_severity(duration, recommendations)
        }
        
        return result
    
    def _suggest_indexes(self, statement: str) -> List[str]:
        """Suggest indexes based on query pattern"""
        suggestions = []
        statement_upper = statement.upper()
        
        # Extract table and column names from WHERE clause
        where_match = re.search(r'WHERE\s+(\w+)\.(\w+)', statement_upper)
        if where_match:
            table = where_match.group(1)
            column = where_match.group(2)
            suggestions.append(f"CREATE INDEX idx_{table}_{column} ON {table}({column})")
        
        # Extract JOIN columns
        join_matches = re.findall(r'JOIN\s+(\w+)\s+ON\s+\w+\.(\w+)\s*=\s*\w+\.(\w+)', statement_upper)
        for table, col1, col2 in join_matches:
            suggestions.append(f"CREATE INDEX idx_{table}_{col1} ON {table}({col1})")
        
        return suggestions
    
    def _calculate_severity(self, duration: float, recommendations: List[Dict]) -> str:
        """Calculate overall severity"""
        if duration > 10.0:
            return 'critical'
        elif duration > 5.0 or any(r['severity'] == 'high' for r in recommendations):
            return 'high'
        elif duration > 2.0:
            return 'medium'
        else:
            return 'low'
    
    def log_slow_query(self, analysis: Dict):
        """Log slow query with analysis"""
        self.slow_queries.append(analysis)
        
        # Keep only last 100 slow queries
        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-100:]
        
        self.logger.warning(
            "slow_query_detected",
            duration=analysis['duration'],
            severity=analysis['severity'],
            statement=analysis['statement'][:200],
            recommendations_count=len(analysis['recommendations']),
            index_suggestions_count=len(analysis['index_suggestions'])
        )
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent slow queries"""
        return sorted(
            self.slow_queries,
            key=lambda x: x['duration'],
            reverse=True
        )[:limit]


# Global optimizer instance
_query_optimizer = QueryOptimizer()


def get_query_optimizer() -> QueryOptimizer:
    """Get global query optimizer instance"""
    return _query_optimizer


def setup_query_monitoring(engine: Engine):
    """
    Setup query monitoring on SQLAlchemy engine
    
    Args:
        engine: SQLAlchemy engine
    """
    optimizer = get_query_optimizer()
    
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query start time"""
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Analyze query performance"""
        total_time = time.time() - conn.info['query_start_time'].pop()
        
        # Analyze if slow
        analysis = optimizer.analyze_query(statement, total_time)
        if analysis:
            optimizer.log_slow_query(analysis)
    
    logger.info("Query monitoring enabled", threshold=SLOW_QUERY_THRESHOLD)


# Example usage in main.py:
"""
from backend.core.database.query_optimizer import setup_query_monitoring
from backend.db.database import engine

# Setup query monitoring
setup_query_monitoring(engine)
"""
