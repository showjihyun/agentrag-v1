"""
Cost Repository

Data access layer for cost tracking and budget management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from backend.db.models.agent_builder import CostRecord, BudgetSettings
import logging

logger = logging.getLogger(__name__)


class CostRepository:
    """Repository for cost tracking operations"""

    def __init__(self, db: Session):
        self.db = db

    def _calculate_start_date(self, time_range: str) -> datetime:
        """Calculate start date from time range string"""
        now = datetime.utcnow()
        
        if time_range == "24h":
            return now - timedelta(hours=24)
        elif time_range == "7d":
            return now - timedelta(days=7)
        elif time_range == "30d":
            return now - timedelta(days=30)
        elif time_range == "90d":
            return now - timedelta(days=90)
        else:  # all
            return datetime(2000, 1, 1)

    def get_stats(
        self,
        agent_id: Optional[UUID],
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get cost statistics"""
        try:
            start_date = self._calculate_start_date(time_range)

            query = self.db.query(
                func.sum(CostRecord.cost).label('total_cost'),
                func.sum(CostRecord.tokens).label('total_tokens'),
                func.avg(CostRecord.cost).label('avg_cost'),
                func.count(CostRecord.id).label('total_executions')
            ).filter(CostRecord.timestamp >= start_date)

            if agent_id:
                query = query.filter(CostRecord.agent_id == agent_id)

            result = query.first()

            # Calculate previous period for trend
            prev_start = start_date - (datetime.utcnow() - start_date)
            prev_query = self.db.query(
                func.sum(CostRecord.cost).label('prev_cost')
            ).filter(
                and_(
                    CostRecord.timestamp >= prev_start,
                    CostRecord.timestamp < start_date
                )
            )

            if agent_id:
                prev_query = prev_query.filter(CostRecord.agent_id == agent_id)

            prev_result = prev_query.first()

            # Calculate trend
            trend_percentage = 0
            if prev_result and prev_result.prev_cost and result.total_cost:
                trend_percentage = ((result.total_cost - prev_result.prev_cost) / prev_result.prev_cost) * 100

            return {
                'total_cost': float(result.total_cost or 0),
                'total_tokens': int(result.total_tokens or 0),
                'avg_cost_per_execution': float(result.avg_cost or 0),
                'total_executions': int(result.total_executions or 0),
                'trend_percentage': round(trend_percentage, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get cost stats: {e}")
            raise

    def get_breakdown_by_model(
        self,
        agent_id: Optional[UUID],
        time_range: str = "30d"
    ) -> List[Dict[str, Any]]:
        """Get cost breakdown by model"""
        try:
            start_date = self._calculate_start_date(time_range)

            query = self.db.query(
                CostRecord.model,
                func.sum(CostRecord.cost).label('cost'),
                func.count(CostRecord.id).label('executions')
            ).filter(
                CostRecord.timestamp >= start_date
            ).group_by(CostRecord.model)

            if agent_id:
                query = query.filter(CostRecord.agent_id == agent_id)

            results = query.all()

            # Calculate total for percentages
            total_cost = sum(r.cost for r in results)

            breakdown = []
            for model, cost, executions in results:
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                breakdown.append({
                    'model': model,
                    'cost': float(cost),
                    'percentage': round(percentage, 1),
                    'executions': executions
                })

            return sorted(breakdown, key=lambda x: x['cost'], reverse=True)

        except Exception as e:
            logger.error(f"Failed to get cost breakdown by model: {e}")
            raise

    def get_breakdown_by_agent(
        self,
        time_range: str = "30d",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get cost breakdown by agent"""
        try:
            start_date = self._calculate_start_date(time_range)

            results = self.db.query(
                CostRecord.agent_id,
                func.sum(CostRecord.cost).label('cost'),
                func.count(CostRecord.id).label('executions')
            ).filter(
                and_(
                    CostRecord.timestamp >= start_date,
                    CostRecord.agent_id.isnot(None)
                )
            ).group_by(
                CostRecord.agent_id
            ).order_by(
                desc('cost')
            ).limit(limit).all()

            breakdown = []
            for agent_id, cost, executions in results:
                breakdown.append({
                    'agent_id': str(agent_id),
                    'agent_name': f"Agent {str(agent_id)[:8]}",  # TODO: Join with agents table
                    'cost': float(cost),
                    'executions': executions
                })

            return breakdown

        except Exception as e:
            logger.error(f"Failed to get cost breakdown by agent: {e}")
            raise

    def get_cost_trend(
        self,
        agent_id: Optional[UUID],
        time_range: str = "30d"
    ) -> List[Dict[str, Any]]:
        """Get daily cost trend"""
        try:
            start_date = self._calculate_start_date(time_range)

            query = self.db.query(
                func.date(CostRecord.timestamp).label('date'),
                func.sum(CostRecord.cost).label('cost'),
                func.count(CostRecord.id).label('executions')
            ).filter(
                CostRecord.timestamp >= start_date
            ).group_by(
                func.date(CostRecord.timestamp)
            ).order_by('date')

            if agent_id:
                query = query.filter(CostRecord.agent_id == agent_id)

            results = query.all()

            trend = []
            for date, cost, executions in results:
                trend.append({
                    'date': date.isoformat(),
                    'cost': float(cost),
                    'executions': executions
                })

            return trend

        except Exception as e:
            logger.error(f"Failed to get cost trend: {e}")
            raise

    def get_expensive_executions(
        self,
        agent_id: Optional[UUID],
        time_range: str = "30d",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most expensive executions"""
        try:
            start_date = self._calculate_start_date(time_range)

            query = self.db.query(CostRecord).filter(
                CostRecord.timestamp >= start_date
            ).order_by(
                desc(CostRecord.cost)
            ).limit(limit)

            if agent_id:
                query = query.filter(CostRecord.agent_id == agent_id)

            results = query.all()

            executions = []
            for record in results:
                executions.append({
                    'id': str(record.execution_id or record.id),
                    'agent_name': f"Agent {str(record.agent_id)[:8]}" if record.agent_id else "Unknown",
                    'tokens': record.tokens,
                    'cost': float(record.cost),
                    'timestamp': record.timestamp.isoformat()
                })

            return executions

        except Exception as e:
            logger.error(f"Failed to get expensive executions: {e}")
            raise

    def create_cost_record(
        self,
        agent_id: Optional[UUID],
        execution_id: Optional[UUID],
        model: str,
        tokens: int,
        cost: float,
        metadata: Dict = None
    ) -> CostRecord:
        """Create a new cost record"""
        try:
            record = CostRecord(
                agent_id=agent_id,
                execution_id=execution_id,
                model=model,
                tokens=tokens,
                cost=cost,
                meta_data=metadata or {},
                timestamp=datetime.utcnow()
            )

            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)

            return record

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create cost record: {e}")
            raise

    def get_budget_settings(self, agent_id: Optional[UUID] = None) -> Optional[BudgetSettings]:
        """Get budget settings"""
        try:
            query = self.db.query(BudgetSettings)
            
            if agent_id:
                query = query.filter(BudgetSettings.agent_id == agent_id)
            else:
                query = query.filter(BudgetSettings.agent_id.is_(None))

            return query.first()

        except Exception as e:
            logger.error(f"Failed to get budget settings: {e}")
            raise

    def create_or_update_budget_settings(
        self,
        settings_data: Dict[str, Any],
        agent_id: Optional[UUID] = None
    ) -> BudgetSettings:
        """Create or update budget settings"""
        try:
            settings = self.get_budget_settings(agent_id)

            if settings:
                # Update existing
                for key, value in settings_data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                settings.updated_at = datetime.utcnow()
            else:
                # Create new
                settings = BudgetSettings(
                    agent_id=agent_id,
                    **settings_data
                )
                self.db.add(settings)

            self.db.commit()
            self.db.refresh(settings)

            return settings

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create/update budget settings: {e}")
            raise

    def get_monthly_cost(self, agent_id: Optional[UUID] = None) -> float:
        """Get current month's cost"""
        try:
            now = datetime.utcnow()
            start_of_month = datetime(now.year, now.month, 1)

            query = self.db.query(
                func.sum(CostRecord.cost).label('total')
            ).filter(
                CostRecord.timestamp >= start_of_month
            )

            if agent_id:
                query = query.filter(CostRecord.agent_id == agent_id)

            result = query.first()

            return float(result.total or 0)

        except Exception as e:
            logger.error(f"Failed to get monthly cost: {e}")
            raise
