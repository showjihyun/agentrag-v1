"""Usage statistics service with async optimization."""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from functools import lru_cache

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from sqlalchemy.exc import OperationalError

from backend.models.query_log import QueryLog
from backend.db.models.document import Document
from backend.models.enums import TimeRange
from backend.core.enhanced_error_handler import DatabaseError

logger = logging.getLogger(__name__)


class UsageService:
    """Service for usage statistics and analytics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_usage_stats(
        self,
        user_id: Optional[UUID] = None,
        time_range: str = "week",
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage statistics for specified time range.
        
        Args:
            user_id: Optional user ID filter
            time_range: Time range (day, week, month, year)
            limit: Maximum number of data points
            
        Returns:
            Usage statistics
        """
        try:
            # Calculate date range
            days_map = {"day": 1, "week": 7, "month": 30, "year": 365}
            days = days_map.get(time_range, 7)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = self.db.query(
                func.date(QueryLog.created_at).label('date'),
                func.count(QueryLog.id).label('queries'),
                func.sum(QueryLog.tokens_used).label('tokens')
            ).filter(QueryLog.created_at >= start_date)
            
            if user_id:
                query = query.filter(QueryLog.user_id == user_id)
            
            # Group by date
            query = query.group_by(func.date(QueryLog.created_at))
            query = query.order_by(func.date(QueryLog.created_at))
            
            # Execute query
            results = query.limit(limit).all()
            
            # Format usage data
            usage_data = []
            for row in results:
                date_str = row.date.strftime("%Y-%m-%d") if row.date else "Unknown"
                usage_data.append({
                    "date": date_str,
                    "queries": row.queries or 0,
                    "tokens": row.tokens or 0,
                    "cost": self._calculate_cost(row.tokens or 0),
                })
            
            # Calculate summary
            total_queries = sum(d["queries"] for d in usage_data)
            total_tokens = sum(d["tokens"] for d in usage_data)
            total_cost = sum(d["cost"] for d in usage_data)
            avg_queries_per_day = total_queries / len(usage_data) if usage_data else 0
            
            # Find peak day
            peak_day = max(usage_data, key=lambda x: x["queries"]) if usage_data else None
            peak_usage_day = peak_day["date"] if peak_day else "N/A"
            
            # Get document count
            doc_query = self.db.query(func.count(Document.id)).filter(
                Document.created_at >= start_date
            )
            if user_id:
                doc_query = doc_query.filter(Document.user_id == user_id)
            total_documents = doc_query.scalar() or 0
            
            return {
                "usage": usage_data,
                "summary": {
                    "totalQueries": total_queries,
                    "totalDocuments": total_documents,
                    "totalTokens": total_tokens,
                    "estimatedCost": round(total_cost, 2),
                    "avgQueriesPerDay": round(avg_queries_per_day, 1),
                    "peakUsageDay": peak_usage_day,
                }
            }
            
        except Exception as e:
            logger.error(
                "Failed to get usage stats",
                extra={
                    "user_id": str(user_id) if user_id else None,
                    "time_range": time_range,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to retrieve usage statistics",
                details={"user_id": str(user_id) if user_id else None, "time_range": time_range},
                original_error=e
            )
    
    async def get_usage_summary(
        self,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get overall usage summary with parallel queries.
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            Usage summary
        """
        try:
            # Execute queries in parallel for better performance
            total_queries_task = asyncio.create_task(
                self._get_total_queries(user_id)
            )
            total_documents_task = asyncio.create_task(
                self._get_total_documents(user_id)
            )
            total_tokens_task = asyncio.create_task(
                self._get_total_tokens(user_id)
            )
            recent_queries_task = asyncio.create_task(
                self._get_recent_queries(user_id)
            )
            peak_day_task = asyncio.create_task(
                self._get_peak_usage_day(user_id)
            )
            month_tokens_task = asyncio.create_task(
                self._get_month_tokens(user_id)
            )
            
            # Wait for all queries to complete
            (
                total_queries,
                total_documents,
                total_tokens,
                recent_queries,
                peak_usage_day,
                month_tokens
            ) = await asyncio.gather(
                total_queries_task,
                total_documents_task,
                total_tokens_task,
                recent_queries_task,
                peak_day_task,
                month_tokens_task
            )
            
            # Calculate costs
            estimated_cost = self._calculate_cost(total_tokens)
            avg_queries_per_day = recent_queries / 30
            current_month_cost = self._calculate_cost(month_tokens)
            
            # Projected month cost
            days_in_month = (datetime.utcnow().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            days_in_month = days_in_month.day
            days_elapsed = datetime.utcnow().day
            projected_month_cost = (current_month_cost / days_elapsed) * days_in_month if days_elapsed > 0 else 0
            
            return {
                "totalQueries": total_queries,
                "totalDocuments": total_documents,
                "totalTokens": total_tokens,
                "estimatedCost": round(estimated_cost, 2),
                "avgQueriesPerDay": round(avg_queries_per_day, 1),
                "peakUsageDay": peak_usage_day,
                "currentMonthCost": round(current_month_cost, 2),
                "projectedMonthCost": round(projected_month_cost, 2),
            }
            
        except Exception as e:
            logger.error(
                "Failed to get usage summary",
                extra={
                    "user_id": str(user_id) if user_id else None,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to retrieve usage summary",
                details={"user_id": str(user_id) if user_id else None},
                original_error=e
            )
    
    async def get_cost_breakdown(
        self,
        user_id: Optional[UUID] = None,
        time_range: str = "month"
    ) -> Dict[str, Any]:
        """
        Get detailed cost breakdown.
        
        Args:
            user_id: Optional user ID filter
            time_range: Time range (week, month, year)
            
        Returns:
            Cost breakdown
        """
        try:
            # Calculate date range
            days_map = {"week": 7, "month": 30, "year": 365}
            days = days_map.get(time_range, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get query logs
            query = self.db.query(QueryLog).filter(QueryLog.created_at >= start_date)
            if user_id:
                query = query.filter(QueryLog.user_id == user_id)
            
            logs = query.all()
            
            # Calculate breakdown by model
            model_costs = {}
            for log in logs:
                model = log.model_used or "unknown"
                tokens = log.tokens_used or 0
                cost = self._calculate_cost(tokens)
                
                if model not in model_costs:
                    model_costs[model] = {
                        "model": model,
                        "queries": 0,
                        "tokens": 0,
                        "cost": 0.0
                    }
                
                model_costs[model]["queries"] += 1
                model_costs[model]["tokens"] += tokens
                model_costs[model]["cost"] += cost
            
            # Format breakdown
            breakdown = [
                {
                    "model": data["model"],
                    "queries": data["queries"],
                    "tokens": data["tokens"],
                    "cost": round(data["cost"], 2),
                    "percentage": 0.0  # Will calculate below
                }
                for data in model_costs.values()
            ]
            
            # Calculate percentages
            total_cost = sum(item["cost"] for item in breakdown)
            if total_cost > 0:
                for item in breakdown:
                    item["percentage"] = round((item["cost"] / total_cost) * 100, 1)
            
            # Sort by cost descending
            breakdown.sort(key=lambda x: x["cost"], reverse=True)
            
            return {
                "breakdown": breakdown,
                "totalCost": round(total_cost, 2),
                "timeRange": time_range
            }
            
        except Exception as e:
            logger.error(
                "Failed to get cost breakdown",
                extra={
                    "user_id": str(user_id) if user_id else None,
                    "time_range": time_range,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to retrieve cost breakdown",
                details={"user_id": str(user_id) if user_id else None, "time_range": time_range},
                original_error=e
            )
    
    @lru_cache(maxsize=1000)
    def _calculate_cost(self, tokens: int) -> float:
        """
        Calculate cost based on tokens (cached for performance).
        
        Args:
            tokens: Number of tokens
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimate: $0.002 per 1K tokens (GPT-3.5 pricing)
        return (tokens / 1000) * 0.002
    
    # Helper methods for parallel execution
    async def _get_total_queries(self, user_id: Optional[UUID]) -> int:
        """Get total query count."""
        try:
            query = self.db.query(func.count(QueryLog.id))
            if user_id:
                query = query.filter(QueryLog.user_id == user_id)
            return query.scalar() or 0
        except Exception as e:
            logger.error(
                "Failed to get total queries",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
            return 0
    
    async def _get_total_documents(self, user_id: Optional[UUID]) -> int:
        """Get total document count."""
        try:
            query = self.db.query(func.count(Document.id))
            if user_id:
                query = query.filter(Document.user_id == user_id)
            return query.scalar() or 0
        except Exception as e:
            logger.error(
                "Failed to get total documents",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
            return 0
    
    async def _get_total_tokens(self, user_id: Optional[UUID]) -> int:
        """Get total tokens used."""
        try:
            query = self.db.query(func.sum(QueryLog.tokens_used))
            if user_id:
                query = query.filter(QueryLog.user_id == user_id)
            return query.scalar() or 0
        except Exception as e:
            logger.error(
                "Failed to get total tokens",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
            return 0
    
    async def _get_recent_queries(self, user_id: Optional[UUID]) -> int:
        """Get recent queries (last 30 days)."""
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            query = self.db.query(func.count(QueryLog.id)).filter(
                QueryLog.created_at >= thirty_days_ago
            )
            if user_id:
                query = query.filter(QueryLog.user_id == user_id)
            return query.scalar() or 0
        except Exception as e:
            logger.error(
                "Failed to get recent queries",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
            return 0
    
    async def _get_peak_usage_day(self, user_id: Optional[UUID]) -> str:
        """Get peak usage day."""
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            query = self.db.query(
                func.date(QueryLog.created_at).label('date'),
                func.count(QueryLog.id).label('count')
            ).filter(QueryLog.created_at >= thirty_days_ago)
            
            if user_id:
                query = query.filter(QueryLog.user_id == user_id)
            
            query = query.group_by(func.date(QueryLog.created_at))
            query = query.order_by(desc('count'))
            result = query.first()
            
            return result.date.strftime("%Y-%m-%d") if result else "N/A"
        except Exception as e:
            logger.error(
                "Failed to get peak usage day",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
            return "N/A"
    
    async def _get_month_tokens(self, user_id: Optional[UUID]) -> int:
        """Get current month tokens."""
        try:
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = self.db.query(func.sum(QueryLog.tokens_used)).filter(
                QueryLog.created_at >= month_start
            )
            if user_id:
                query = query.filter(QueryLog.user_id == user_id)
            return query.scalar() or 0
        except Exception as e:
            logger.error(
                "Failed to get month tokens",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
            return 0


def get_usage_service(db: Session) -> UsageService:
    """Get usage service instance."""
    return UsageService(db)
