"""
Memory Cleanup Service
AgentMemory 테이블 자동 정리 서비스
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from backend.db.models.agent_builder import AgentMemory

logger = logging.getLogger(__name__)


class MemoryCleanupService:
    """메모리 자동 정리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def cleanup_expired_memories(self) -> dict:
        """
        만료된 메모리 정리
        
        Returns:
            dict: 정리 통계 (stm_deleted, ltm_deleted, episodic_deleted)
        """
        
        stats = {
            'stm_deleted': 0,
            'ltm_deleted': 0,
            'episodic_deleted': 0,
            'total_deleted': 0
        }
        
        try:
            # 1. STM 정리 (24시간 이상 경과)
            stm_cutoff = datetime.utcnow() - timedelta(hours=24)
            stm_deleted = self.db.query(AgentMemory)\
                .filter(
                    AgentMemory.type == 'short_term',
                    AgentMemory.created_at < stm_cutoff
                )\
                .delete(synchronize_session=False)
            stats['stm_deleted'] = stm_deleted
            
            # 2. 중요도 낮은 LTM 정리 (90일 이상, 접근 없음)
            ltm_cutoff = datetime.utcnow() - timedelta(days=90)
            ltm_deleted = self.db.query(AgentMemory)\
                .filter(
                    AgentMemory.type == 'long_term',
                    AgentMemory.importance == 'low',
                    AgentMemory.last_accessed_at < ltm_cutoff
                )\
                .delete(synchronize_session=False)
            stats['ltm_deleted'] = ltm_deleted
            
            # 3. 오래된 Episodic 메모리 정리 (30일 이상, 중요도 낮음)
            episodic_cutoff = datetime.utcnow() - timedelta(days=30)
            episodic_deleted = self.db.query(AgentMemory)\
                .filter(
                    AgentMemory.type == 'episodic',
                    AgentMemory.created_at < episodic_cutoff,
                    AgentMemory.importance == 'low'
                )\
                .delete(synchronize_session=False)
            stats['episodic_deleted'] = episodic_deleted
            
            stats['total_deleted'] = stm_deleted + ltm_deleted + episodic_deleted
            
            self.db.commit()
            
            logger.info(f"Memory cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Memory cleanup failed: {e}", exc_info=True)
            raise
    
    def consolidate_memories(self, agent_id: str) -> int:
        """
        메모리 통합 (STM → LTM 승격)
        
        자주 접근되는 STM을 LTM으로 승격시킵니다.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            int: 승격된 메모리 수
        """
        
        try:
            # 자주 접근되는 STM을 LTM으로 승격
            threshold_date = datetime.utcnow() - timedelta(hours=12)
            
            memories = self.db.query(AgentMemory)\
                .filter(
                    AgentMemory.agent_id == agent_id,
                    AgentMemory.type == 'short_term',
                    AgentMemory.access_count >= 3,  # 3회 이상 접근
                    AgentMemory.created_at < threshold_date
                )\
                .all()
            
            consolidated = 0
            for memory in memories:
                memory.type = 'long_term'
                memory.importance = 'medium'
                consolidated += 1
            
            self.db.commit()
            logger.info(f"Consolidated {consolidated} memories for agent {agent_id}")
            return consolidated
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Memory consolidation failed: {e}", exc_info=True)
            raise
    
    def get_memory_stats(self) -> dict:
        """
        메모리 통계 조회
        
        Returns:
            dict: 메모리 타입별 통계
        """
        
        try:
            stats = {}
            
            # 타입별 카운트
            type_counts = self.db.query(
                AgentMemory.type,
                func.count(AgentMemory.id).label('count')
            ).group_by(AgentMemory.type).all()
            
            for memory_type, count in type_counts:
                stats[f'{memory_type}_count'] = count
            
            # 중요도별 카운트
            importance_counts = self.db.query(
                AgentMemory.importance,
                func.count(AgentMemory.id).label('count')
            ).group_by(AgentMemory.importance).all()
            
            for importance, count in importance_counts:
                stats[f'{importance}_importance_count'] = count
            
            # 오래된 메모리 카운트 (정리 대상)
            stm_cutoff = datetime.utcnow() - timedelta(hours=24)
            old_stm = self.db.query(AgentMemory)\
                .filter(
                    AgentMemory.type == 'short_term',
                    AgentMemory.created_at < stm_cutoff
                )\
                .count()
            stats['old_stm_count'] = old_stm
            
            ltm_cutoff = datetime.utcnow() - timedelta(days=90)
            old_ltm = self.db.query(AgentMemory)\
                .filter(
                    AgentMemory.type == 'long_term',
                    AgentMemory.importance == 'low',
                    AgentMemory.last_accessed_at < ltm_cutoff
                )\
                .count()
            stats['old_ltm_count'] = old_ltm
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}", exc_info=True)
            return {}
