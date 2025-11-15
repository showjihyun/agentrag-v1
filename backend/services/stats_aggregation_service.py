"""
Statistics Aggregation Service
일별 통계 집계 서비스 (Priority 5)
"""

from datetime import date, datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
import logging

from backend.db.models.agent_builder import (
    AgentExecution,
    AgentExecutionStats,
    WorkflowExecution,
    WorkflowExecutionStats,
    ExecutionMetrics
)

logger = logging.getLogger(__name__)


class StatsAggregationService:
    """통계 집계 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def aggregate_daily_agent_stats(self, target_date: date = None) -> int:
        """
        일별 에이전트 통계 집계
        
        Args:
            target_date: 집계 대상 날짜 (기본값: 어제)
            
        Returns:
            int: 집계된 레코드 수
        """
        
        if target_date is None:
            target_date = date.today() - timedelta(days=1)  # 어제
        
        try:
            # 해당 날짜의 시작과 끝
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            # Agent별, User별 그룹화하여 집계
            stats_query = self.db.query(
                AgentExecution.agent_id,
                AgentExecution.user_id,
                func.count(AgentExecution.id).label('execution_count'),
                func.sum(
                    func.case((AgentExecution.status == 'completed', 1), else_=0)
                ).label('success_count'),
                func.sum(
                    func.case((AgentExecution.status == 'failed', 1), else_=0)
                ).label('failed_count'),
                func.sum(
                    func.case((AgentExecution.status == 'cancelled', 1), else_=0)
                ).label('cancelled_count'),
                func.avg(AgentExecution.duration_ms).label('avg_duration_ms'),
                func.min(AgentExecution.duration_ms).label('min_duration_ms'),
                func.max(AgentExecution.duration_ms).label('max_duration_ms')
            )\
            .filter(
                AgentExecution.started_at >= start_dt,
                AgentExecution.started_at <= end_dt
            )\
            .group_by(AgentExecution.agent_id, AgentExecution.user_id)\
            .all()
            
            # 집계 결과 저장
            aggregated_count = 0
            for stat in stats_query:
                # 기존 레코드 확인
                existing = self.db.query(AgentExecutionStats)\
                    .filter(
                        AgentExecutionStats.agent_id == stat.agent_id,
                        AgentExecutionStats.user_id == stat.user_id,
                        AgentExecutionStats.date == start_dt
                    )\
                    .first()
                
                if existing:
                    # 업데이트
                    existing.execution_count = stat.execution_count
                    existing.success_count = stat.success_count
                    existing.failed_count = stat.failed_count
                    existing.cancelled_count = stat.cancelled_count
                    existing.avg_duration_ms = int(stat.avg_duration_ms) if stat.avg_duration_ms else 0
                    existing.min_duration_ms = stat.min_duration_ms
                    existing.max_duration_ms = stat.max_duration_ms
                    existing.updated_at = datetime.utcnow()
                else:
                    # 신규 생성
                    new_stat = AgentExecutionStats(
                        agent_id=stat.agent_id,
                        user_id=stat.user_id,
                        date=start_dt,
                        execution_count=stat.execution_count,
                        success_count=stat.success_count,
                        failed_count=stat.failed_count,
                        cancelled_count=stat.cancelled_count,
                        avg_duration_ms=int(stat.avg_duration_ms) if stat.avg_duration_ms else 0,
                        min_duration_ms=stat.min_duration_ms,
                        max_duration_ms=stat.max_duration_ms
                    )
                    self.db.add(new_stat)
                
                aggregated_count += 1
            
            self.db.commit()
            logger.info(f"Aggregated {aggregated_count} agent stats for {target_date}")
            return aggregated_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Agent stats aggregation failed: {e}", exc_info=True)
            raise
    
    def aggregate_daily_workflow_stats(self, target_date: date = None) -> int:
        """
        일별 워크플로우 통계 집계
        
        Args:
            target_date: 집계 대상 날짜 (기본값: 어제)
            
        Returns:
            int: 집계된 레코드 수
        """
        
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        try:
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            # Workflow별, User별 그룹화하여 집계
            stats_query = self.db.query(
                WorkflowExecution.workflow_id,
                WorkflowExecution.user_id,
                func.count(WorkflowExecution.id).label('execution_count'),
                func.sum(
                    func.case((WorkflowExecution.status == 'completed', 1), else_=0)
                ).label('success_count'),
                func.sum(
                    func.case((WorkflowExecution.status == 'failed', 1), else_=0)
                ).label('failed_count'),
                func.avg(WorkflowExecution.duration_ms).label('avg_duration_ms')
            )\
            .filter(
                WorkflowExecution.started_at >= start_dt,
                WorkflowExecution.started_at <= end_dt
            )\
            .group_by(WorkflowExecution.workflow_id, WorkflowExecution.user_id)\
            .all()
            
            aggregated_count = 0
            for stat in stats_query:
                existing = self.db.query(WorkflowExecutionStats)\
                    .filter(
                        WorkflowExecutionStats.workflow_id == stat.workflow_id,
                        WorkflowExecutionStats.user_id == stat.user_id,
                        WorkflowExecutionStats.date == start_dt
                    )\
                    .first()
                
                if existing:
                    existing.execution_count = stat.execution_count
                    existing.success_count = stat.success_count
                    existing.failed_count = stat.failed_count
                    existing.avg_duration_ms = int(stat.avg_duration_ms) if stat.avg_duration_ms else 0
                    existing.updated_at = datetime.utcnow()
                else:
                    new_stat = WorkflowExecutionStats(
                        workflow_id=stat.workflow_id,
                        user_id=stat.user_id,
                        date=start_dt,
                        execution_count=stat.execution_count,
                        success_count=stat.success_count,
                        failed_count=stat.failed_count,
                        avg_duration_ms=int(stat.avg_duration_ms) if stat.avg_duration_ms else 0
                    )
                    self.db.add(new_stat)
                
                aggregated_count += 1
            
            self.db.commit()
            logger.info(f"Aggregated {aggregated_count} workflow stats for {target_date}")
            return aggregated_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Workflow stats aggregation failed: {e}", exc_info=True)
            raise
    
    def get_agent_stats_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> dict:
        """
        에이전트 통계 요약 조회 (집계 테이블 사용)
        
        Args:
            user_id: User ID
            days: 조회 기간 (일)
            
        Returns:
            dict: 통계 요약
        """
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            stats = self.db.query(
                func.sum(AgentExecutionStats.execution_count).label('total_executions'),
                func.sum(AgentExecutionStats.success_count).label('total_success'),
                func.avg(AgentExecutionStats.avg_duration_ms).label('avg_duration')
            )\
            .filter(
                AgentExecutionStats.user_id == user_id,
                AgentExecutionStats.date >= start_date
            )\
            .first()
            
            return {
                'total_executions': stats.total_executions or 0,
                'total_success': stats.total_success or 0,
                'avg_duration_ms': int(stats.avg_duration) if stats.avg_duration else 0,
                'success_rate': (stats.total_success / stats.total_executions * 100) 
                    if stats.total_executions else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent stats summary: {e}", exc_info=True)
            return {}
