"""
Background Scheduler for periodic tasks
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from backend.db.database import SessionLocal
from backend.services.memory_cleanup_service import MemoryCleanupService
from backend.services.stats_aggregation_service import StatsAggregationService

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()


def cleanup_memories_job():
    """메모리 정리 작업 (매일 새벽 3시 실행)"""
    db = SessionLocal()
    try:
        logger.info("Starting scheduled memory cleanup...")
        service = MemoryCleanupService(db)
        stats = service.cleanup_expired_memories()
        logger.info(f"Memory cleanup completed: {stats}")
    except Exception as e:
        logger.error(f"Memory cleanup job failed: {e}", exc_info=True)
    finally:
        db.close()


def aggregate_stats_job():
    """통계 집계 작업 (매일 새벽 2시 실행)"""
    db = SessionLocal()
    try:
        logger.info("Starting scheduled stats aggregation...")
        service = StatsAggregationService(db)
        
        # 어제 데이터 집계
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)
        
        agent_count = service.aggregate_daily_agent_stats(yesterday)
        workflow_count = service.aggregate_daily_workflow_stats(yesterday)
        
        logger.info(f"Stats aggregation completed: {agent_count} agents, {workflow_count} workflows")
    except Exception as e:
        logger.error(f"Stats aggregation job failed: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """스케줄러 시작"""
    
    # 통계 집계 작업 (매일 새벽 2시)
    scheduler.add_job(
        aggregate_stats_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='stats_aggregation',
        name='Stats Aggregation Job',
        replace_existing=True
    )
    
    # 메모리 정리 작업 (매일 새벽 3시)
    scheduler.add_job(
        cleanup_memories_job,
        trigger=CronTrigger(hour=3, minute=0),
        id='memory_cleanup',
        name='Memory Cleanup Job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started")
    logger.info(f"Scheduled jobs: {[job.id for job in scheduler.get_jobs()]}")


def stop_scheduler():
    """스케줄러 중지"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")


def get_scheduler_status():
    """스케줄러 상태 조회"""
    return {
        'running': scheduler.running,
        'jobs': [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }
