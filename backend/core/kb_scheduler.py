"""
KB Cache Warming Scheduler.

Automatically warms cache for popular agents on a schedule.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class KBCacheScheduler:
    """
    Scheduler for automatic KB cache warming.
    
    Features:
    - Scheduled cache warming
    - Popular agent detection
    - Error handling and retry
    - Performance tracking
    """
    
    def __init__(self):
        """Initialize scheduler"""
        self.scheduler = AsyncIOScheduler()
        self.warming_history: List[Dict[str, Any]] = []
        self.is_running = False
        
        logger.info("KBCacheScheduler initialized")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule cache warming jobs
        self._schedule_jobs()
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info("KBCacheScheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        
        logger.info("KBCacheScheduler stopped")
    
    def _schedule_jobs(self):
        """Schedule warming jobs"""
        
        # Daily warming at 2 AM
        self.scheduler.add_job(
            self._warm_popular_agents,
            CronTrigger(hour=2, minute=0),
            id='daily_cache_warming',
            name='Daily Cache Warming',
            replace_existing=True
        )
        
        # Hourly warming for top agents
        self.scheduler.add_job(
            self._warm_top_agents,
            CronTrigger(minute=0),  # Every hour
            id='hourly_top_agents_warming',
            name='Hourly Top Agents Warming',
            replace_existing=True
        )
        
        logger.info("Scheduled 2 warming jobs")
    
    async def _warm_popular_agents(self):
        """Warm cache for popular agents (daily)"""
        try:
            logger.info("Starting daily cache warming for popular agents")
            start_time = datetime.utcnow()
            
            # Get popular agents
            agents = await self._get_popular_agents(limit=20)
            
            if not agents:
                logger.info("No popular agents found")
                return
            
            # Warm each agent
            results = await self._warm_agents(agents)
            
            # Track results
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.warming_history.append({
                'type': 'daily',
                'timestamp': start_time.isoformat(),
                'agents_warmed': len(results),
                'total_queries': sum(r['queries_warmed'] for r in results),
                'errors': sum(r['errors'] for r in results),
                'duration_seconds': duration
            })
            
            # Keep only last 30 entries
            if len(self.warming_history) > 30:
                self.warming_history = self.warming_history[-30:]
            
            logger.info(
                f"Daily warming completed: {len(results)} agents, "
                f"{sum(r['queries_warmed'] for r in results)} queries, "
                f"{duration:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Daily warming failed: {e}", exc_info=True)
    
    async def _warm_top_agents(self):
        """Warm cache for top agents (hourly)"""
        try:
            logger.info("Starting hourly cache warming for top agents")
            start_time = datetime.utcnow()
            
            # Get top 5 agents
            agents = await self._get_popular_agents(limit=5)
            
            if not agents:
                return
            
            # Warm with fewer queries (faster)
            results = await self._warm_agents(agents, query_count=5)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Hourly warming completed: {len(results)} agents, "
                f"{sum(r['queries_warmed'] for r in results)} queries, "
                f"{duration:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Hourly warming failed: {e}", exc_info=True)
    
    async def _get_popular_agents(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get popular agents based on recent usage.
        
        Args:
            limit: Maximum number of agents
            
        Returns:
            List of agent configs
        """
        try:
            from backend.db.database import SessionLocal
            from backend.db.models.agent_builder import Agent, AgentExecution
            from sqlalchemy import func, desc
            from sqlalchemy.orm import joinedload
            from datetime import timedelta
            
            db = SessionLocal()
            try:
                # Get agents with most executions in last 7 days
                cutoff = datetime.utcnow() - timedelta(days=7)
                
                popular = db.query(
                    Agent.id,
                    Agent.name,
                    func.count(AgentExecution.id).label('execution_count')
                ).join(
                    AgentExecution,
                    AgentExecution.agent_id == Agent.id
                ).filter(
                    Agent.deleted_at.is_(None),
                    AgentExecution.started_at >= cutoff
                ).group_by(
                    Agent.id, Agent.name
                ).order_by(
                    desc('execution_count')
                ).limit(limit).all()
                
                # Get full agent info with KBs
                agent_configs = []
                for agent_id, agent_name, exec_count in popular:
                    agent = db.query(Agent).options(
                        joinedload(Agent.knowledgebases)
                    ).filter(Agent.id == agent_id).first()
                    
                    if agent and agent.knowledgebases:
                        kb_ids = [str(kb.knowledgebase_id) for kb in agent.knowledgebases]
                        agent_configs.append({
                            'agent_id': str(agent.id),
                            'agent_name': agent.name,
                            'kb_ids': kb_ids,
                            'execution_count': exec_count
                        })
                
                logger.info(f"Found {len(agent_configs)} popular agents with KBs")
                return agent_configs
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get popular agents: {e}", exc_info=True)
            return []
    
    async def _warm_agents(
        self,
        agent_configs: List[Dict[str, Any]],
        query_count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Warm cache for multiple agents.
        
        Args:
            agent_configs: List of agent configurations
            query_count: Number of queries per agent
            
        Returns:
            List of warming results
        """
        try:
            from backend.services.kb_cache_warmer import KBCacheWarmer
            from backend.services.speculative_processor import SpeculativeProcessor
            from backend.core.dependencies import (
                get_embedding_service,
                get_milvus_manager,
                get_llm_manager,
                get_redis_client
            )
            
            # Initialize processor
            embedding_service = await get_embedding_service()
            milvus_manager = await get_milvus_manager()
            llm_manager = await get_llm_manager()
            redis_client = await get_redis_client()
            
            processor = SpeculativeProcessor(
                embedding_service=embedding_service,
                milvus_manager=milvus_manager,
                llm_manager=llm_manager,
                redis_client=redis_client
            )
            
            warmer = KBCacheWarmer(processor)
            
            # Get default queries (limited)
            default_queries = warmer._get_default_queries()[:query_count]
            
            # Warm each agent
            results = []
            for config in agent_configs:
                try:
                    result = await warmer.warm_agent_cache(
                        agent_id=config['agent_id'],
                        kb_ids=config['kb_ids'],
                        common_queries=default_queries
                    )
                    results.append(result)
                    
                    # Small delay between agents
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(
                        f"Failed to warm agent {config['agent_id']}: {e}"
                    )
                    results.append({
                        'agent_id': config['agent_id'],
                        'queries_warmed': 0,
                        'errors': 1
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to warm agents: {e}", exc_info=True)
            return []
    
    def get_warming_history(self) -> List[Dict[str, Any]]:
        """
        Get warming history.
        
        Returns:
            List of warming events
        """
        return self.warming_history
    
    def get_next_run_times(self) -> Dict[str, str]:
        """
        Get next run times for scheduled jobs.
        
        Returns:
            Dictionary of job IDs and next run times
        """
        next_runs = {}
        
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            next_runs[job.id] = next_run.isoformat() if next_run else None
        
        return next_runs


# Global scheduler instance
_scheduler: KBCacheScheduler = None


def get_kb_scheduler() -> KBCacheScheduler:
    """
    Get or create global KB cache scheduler.
    
    Returns:
        KBCacheScheduler instance
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = KBCacheScheduler()
    
    return _scheduler


def start_kb_scheduler():
    """Start the global KB cache scheduler"""
    scheduler = get_kb_scheduler()
    scheduler.start()
    logger.info("KB cache scheduler started")


def stop_kb_scheduler():
    """Stop the global KB cache scheduler"""
    scheduler = get_kb_scheduler()
    scheduler.stop()
    logger.info("KB cache scheduler stopped")
