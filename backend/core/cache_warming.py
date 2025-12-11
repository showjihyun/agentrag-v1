"""
Cache Warming Strategy

Proactively cache frequently accessed data.
"""

import asyncio
from typing import List, Callable, Any, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from redis import Redis
from sqlalchemy.orm import Session

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class CacheWarmer:
    """Proactively warm cache with frequently accessed data"""
    
    def __init__(self, redis: Redis, db_factory: Callable[[], Session]):
        self.redis = redis
        self.db_factory = db_factory
        self.scheduler = AsyncIOScheduler()
        self.logger = get_logger(__name__)
        self._jobs = []
    
    def start(self):
        """Start cache warming jobs"""
        self.logger.info("cache_warmer_starting")
        
        # Schedule jobs
        self._schedule_popular_workflows()
        self._schedule_user_data()
        self._schedule_analytics()
        
        # Start scheduler
        self.scheduler.start()
        
        self.logger.info(
            "cache_warmer_started",
            jobs_count=len(self._jobs)
        )
    
    def stop(self):
        """Stop cache warming"""
        self.scheduler.shutdown()
        self.logger.info("cache_warmer_stopped")
    
    def _schedule_popular_workflows(self):
        """Schedule popular workflows warming"""
        job = self.scheduler.add_job(
            self.warm_popular_workflows,
            trigger=IntervalTrigger(minutes=5),
            id="warm_popular_workflows",
            name="Warm Popular Workflows",
            replace_existing=True
        )
        self._jobs.append(job)
    
    def _schedule_user_data(self):
        """Schedule user data warming"""
        job = self.scheduler.add_job(
            self.warm_user_data,
            trigger=IntervalTrigger(minutes=10),
            id="warm_user_data",
            name="Warm User Data",
            replace_existing=True
        )
        self._jobs.append(job)
    
    def _schedule_analytics(self):
        """Schedule analytics warming"""
        job = self.scheduler.add_job(
            self.warm_analytics,
            trigger=CronTrigger(hour=0, minute=0),  # Daily at midnight
            id="warm_analytics",
            name="Warm Analytics",
            replace_existing=True
        )
        self._jobs.append(job)
    
    async def warm_popular_workflows(self):
        """Pre-cache popular workflows"""
        try:
            from backend.db.models.flows import Agentflow, Chatflow, FlowExecution
            from sqlalchemy import func
            
            db = self.db_factory()
            
            # Get most executed workflows
            popular_agentflows = db.query(
                FlowExecution.agentflow_id,
                func.count(FlowExecution.id).label('count')
            ).filter(
                FlowExecution.agentflow_id.isnot(None),
                FlowExecution.started_at >= datetime.utcnow() - timedelta(days=7)
            ).group_by(
                FlowExecution.agentflow_id
            ).order_by(
                func.count(FlowExecution.id).desc()
            ).limit(50).all()
            
            popular_chatflows = db.query(
                FlowExecution.chatflow_id,
                func.count(FlowExecution.id).label('count')
            ).filter(
                FlowExecution.chatflow_id.isnot(None),
                FlowExecution.started_at >= datetime.utcnow() - timedelta(days=7)
            ).group_by(
                FlowExecution.chatflow_id
            ).order_by(
                func.count(FlowExecution.id).desc()
            ).limit(50).all()
            
            # Cache agentflows
            warmed_count = 0
            for flow_id, count in popular_agentflows:
                flow = db.query(Agentflow).filter(Agentflow.id == flow_id).first()
                if flow:
                    key = f"agentflow:{flow_id}"
                    await self.redis.setex(
                        key,
                        3600,  # 1 hour
                        str(flow.to_dict())
                    )
                    warmed_count += 1
            
            # Cache chatflows
            for flow_id, count in popular_chatflows:
                flow = db.query(Chatflow).filter(Chatflow.id == flow_id).first()
                if flow:
                    key = f"chatflow:{flow_id}"
                    await self.redis.setex(
                        key,
                        3600,  # 1 hour
                        str(flow.to_dict())
                    )
                    warmed_count += 1
            
            self.logger.info(
                "popular_workflows_warmed",
                count=warmed_count
            )
            
        except Exception as e:
            self.logger.error(
                "workflow_warming_failed",
                error=str(e)
            )
    
    async def warm_user_data(self):
        """Pre-cache active user data"""
        try:
            from backend.db.models.user import User
            from backend.db.models.flows import FlowExecution
            from sqlalchemy import func
            
            db = self.db_factory()
            
            # Get active users (executed workflows in last 24h)
            active_users = db.query(
                FlowExecution.user_id,
                func.count(FlowExecution.id).label('count')
            ).filter(
                FlowExecution.started_at >= datetime.utcnow() - timedelta(hours=24)
            ).group_by(
                FlowExecution.user_id
            ).order_by(
                func.count(FlowExecution.id).desc()
            ).limit(100).all()
            
            # Cache user data
            warmed_count = 0
            for user_id, count in active_users:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    key = f"user:{user_id}"
                    await self.redis.setex(
                        key,
                        1800,  # 30 minutes
                        str(user.to_dict())
                    )
                    warmed_count += 1
            
            self.logger.info(
                "user_data_warmed",
                count=warmed_count
            )
            
        except Exception as e:
            self.logger.error(
                "user_warming_failed",
                error=str(e)
            )
    
    async def warm_analytics(self):
        """Pre-cache analytics data"""
        try:
            from backend.services.agent_builder.services.analytics import InsightsService
            
            db = self.db_factory()
            insights_service = InsightsService(db)
            
            # Get system insights
            system_insights = await insights_service.get_system_insights()
            
            # Cache system insights
            await self.redis.setex(
                "analytics:system",
                86400,  # 24 hours
                str(system_insights)
            )
            
            self.logger.info("analytics_warmed")
            
        except Exception as e:
            self.logger.error(
                "analytics_warming_failed",
                error=str(e)
            )
    
    async def warm_on_demand(
        self,
        keys: List[str],
        fetch_func: Callable[[str], Any],
        ttl: int = 3600
    ):
        """
        Warm specific keys on demand
        
        Args:
            keys: List of cache keys to warm
            fetch_func: Function to fetch data for each key
            ttl: Time to live in seconds
        """
        warmed_count = 0
        
        for key in keys:
            try:
                data = await fetch_func(key)
                if data:
                    await self.redis.setex(key, ttl, str(data))
                    warmed_count += 1
            except Exception as e:
                self.logger.error(
                    "on_demand_warming_failed",
                    key=key,
                    error=str(e)
                )
        
        self.logger.info(
            "on_demand_warming_completed",
            requested=len(keys),
            warmed=warmed_count
        )
    
    async def predictive_warming(
        self,
        user_id: int,
        context: Optional[dict] = None
    ):
        """
        Predictive cache warming based on user behavior
        
        Args:
            user_id: User ID
            context: Additional context for prediction
        """
        try:
            from backend.db.models.flows import FlowExecution
            
            db = self.db_factory()
            
            # Get user's recent workflows
            recent_executions = db.query(FlowExecution).filter(
                FlowExecution.user_id == user_id,
                FlowExecution.started_at >= datetime.utcnow() - timedelta(days=7)
            ).order_by(
                FlowExecution.started_at.desc()
            ).limit(10).all()
            
            # Predict likely next workflows
            workflow_ids = set()
            for execution in recent_executions:
                if execution.agentflow_id:
                    workflow_ids.add(('agentflow', execution.agentflow_id))
                if execution.chatflow_id:
                    workflow_ids.add(('chatflow', execution.chatflow_id))
            
            # Warm predicted workflows
            for flow_type, flow_id in workflow_ids:
                key = f"{flow_type}:{flow_id}"
                # Check if already cached
                if not await self.redis.exists(key):
                    # Fetch and cache
                    if flow_type == 'agentflow':
                        from backend.db.models.flows import Agentflow
                        flow = db.query(Agentflow).filter(Agentflow.id == flow_id).first()
                    else:
                        from backend.db.models.flows import Chatflow
                        flow = db.query(Chatflow).filter(Chatflow.id == flow_id).first()
                    
                    if flow:
                        await self.redis.setex(key, 3600, str(flow.to_dict()))
            
            self.logger.info(
                "predictive_warming_completed",
                user_id=user_id,
                workflows_warmed=len(workflow_ids)
            )
            
        except Exception as e:
            self.logger.error(
                "predictive_warming_failed",
                user_id=user_id,
                error=str(e)
            )


# Global instance
_cache_warmer: Optional[CacheWarmer] = None


def get_cache_warmer(
    redis: Optional[Redis] = None,
    db_factory: Optional[Callable] = None
) -> CacheWarmer:
    """Get global cache warmer instance"""
    global _cache_warmer
    
    if _cache_warmer is None:
        if redis is None or db_factory is None:
            raise ValueError("Redis and db_factory required for first initialization")
        _cache_warmer = CacheWarmer(redis, db_factory)
    
    return _cache_warmer
