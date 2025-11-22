"""
Agent statistics service with caching.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.cache_decorator import cache_result
from backend.core.cache_strategy import cache_with_strategy, CacheStrategy
from backend.db.models.agent_builder import AgentExecution
import logging

logger = logging.getLogger(__name__)


class AgentStatsService:
    """Service for agent statistics with caching."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @cache_with_strategy(
        strategy="short",
        key_prefix=CacheStrategy.PREFIX_AGENT_STATS,
        invalidate_on=["agent_execution_completed"]
    )
    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent execution statistics with caching.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Statistics dictionary
        """
        # Get execution statistics
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id
        ).all()
        
        total_runs = len(executions)
        successful_runs = sum(1 for e in executions if e.status == 'completed')
        failed_runs = sum(1 for e in executions if e.status == 'failed')
        
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0.0
        
        # Calculate average duration
        completed_executions = [
            e for e in executions 
            if e.status == 'completed' and e.started_at and e.completed_at
        ]
        
        if completed_executions:
            durations = [
                (e.completed_at - e.started_at).total_seconds() * 1000 
                for e in completed_executions
            ]
            avg_duration_ms = sum(durations) / len(durations)
        else:
            avg_duration_ms = None
        
        # Get last run time
        last_run_at = max(
            [e.started_at for e in executions], 
            default=None
        ) if executions else None
        
        return {
            "agent_id": agent_id,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration_ms,
            "last_run_at": last_run_at.isoformat() if last_run_at else None,
        }
    
    @cache_with_strategy(
        strategy="medium",
        key_prefix=CacheStrategy.PREFIX_USER_STATS,
        invalidate_on=["agent_created", "agent_execution_completed"]
    )
    async def get_user_stats_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's overall statistics with caching.
        
        Args:
            user_id: User ID
            
        Returns:
            Summary statistics
        """
        from backend.db.models.agent_builder import Agent
        
        # Count agents
        total_agents = self.db.query(func.count(Agent.id)).filter(
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        ).scalar()
        
        # Count executions
        total_executions = self.db.query(func.count(AgentExecution.id)).join(
            Agent, AgentExecution.agent_id == Agent.id
        ).filter(
            Agent.user_id == user_id
        ).scalar()
        
        # Success rate
        successful_executions = self.db.query(func.count(AgentExecution.id)).join(
            Agent, AgentExecution.agent_id == Agent.id
        ).filter(
            Agent.user_id == user_id,
            AgentExecution.status == 'completed'
        ).scalar()
        
        success_rate = (
            (successful_executions / total_executions * 100) 
            if total_executions > 0 else 0.0
        )
        
        return {
            "user_id": user_id,
            "total_agents": total_agents or 0,
            "total_executions": total_executions or 0,
            "successful_executions": successful_executions or 0,
            "success_rate": success_rate,
        }
    
    async def invalidate_agent_cache(self, agent_id: str):
        """Invalidate cache for specific agent."""
        from backend.core.cache_decorator import invalidate_cache
        await invalidate_cache(f"cache:get_agent_stats:*{agent_id}*")
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate cache for specific user."""
        from backend.core.cache_decorator import invalidate_cache
        await invalidate_cache(f"cache:get_user_stats_summary:*{user_id}*")
