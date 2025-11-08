"""
Memory Repository

Data access layer for agent memory operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from backend.db.models.agent_builder import AgentMemory, MemorySettings
import logging

logger = logging.getLogger(__name__)


class MemoryRepository:
    """Repository for agent memory operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get memory statistics by type
        
        Returns:
            Dict with stats for each memory type
        """
        try:
            stats = self.db.query(
                AgentMemory.type,
                func.count(AgentMemory.id).label('count'),
                func.sum(func.length(AgentMemory.content)).label('total_size')
            ).filter(
                AgentMemory.agent_id == agent_id
            ).group_by(AgentMemory.type).all()

            result = {
                'short_term': {'count': 0, 'size_mb': 0},
                'long_term': {'count': 0, 'size_mb': 0},
                'episodic': {'count': 0, 'size_mb': 0},
                'semantic': {'count': 0, 'size_mb': 0},
            }

            total_size = 0
            for mem_type, count, size in stats:
                size_mb = (size or 0) / (1024 * 1024)  # Convert to MB
                result[mem_type] = {'count': count, 'size_mb': round(size_mb, 2)}
                total_size += size_mb

            result['total_size_mb'] = round(total_size, 2)
            result['compression_ratio'] = 2.3  # TODO: Calculate actual compression
            result['retrieval_speed_ms'] = 45.2  # TODO: Calculate from metrics

            return result

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            raise

    def get_memories(
        self,
        agent_id: UUID,
        memory_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AgentMemory]:
        """Get memories with optional type filtering"""
        try:
            query = self.db.query(AgentMemory).filter(
                AgentMemory.agent_id == agent_id
            )

            if memory_type:
                query = query.filter(AgentMemory.type == memory_type)

            memories = query.order_by(
                AgentMemory.created_at.desc()
            ).limit(limit).offset(offset).all()

            return memories

        except Exception as e:
            logger.error(f"Failed to get memories: {e}")
            raise

    def get_memory_by_id(self, agent_id: UUID, memory_id: UUID) -> Optional[AgentMemory]:
        """Get a specific memory"""
        try:
            return self.db.query(AgentMemory).filter(
                and_(
                    AgentMemory.id == memory_id,
                    AgentMemory.agent_id == agent_id
                )
            ).first()

        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            raise

    def create_memory(
        self,
        agent_id: UUID,
        memory_type: str,
        content: str,
        metadata: Dict = None,
        importance: str = "medium"
    ) -> AgentMemory:
        """Create a new memory"""
        try:
            memory = AgentMemory(
                agent_id=agent_id,
                type=memory_type,
                content=content,
                meta_data=metadata or {},
                importance=importance,
                access_count=0,
                created_at=datetime.utcnow()
            )

            self.db.add(memory)
            self.db.commit()
            self.db.refresh(memory)

            return memory

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create memory: {e}")
            raise

    def delete_memory(self, agent_id: UUID, memory_id: UUID) -> bool:
        """Delete a memory"""
        try:
            result = self.db.query(AgentMemory).filter(
                and_(
                    AgentMemory.id == memory_id,
                    AgentMemory.agent_id == agent_id
                )
            ).delete()

            self.db.commit()
            return result > 0

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete memory: {e}")
            raise

    def update_access(self, memory_id: UUID) -> None:
        """Update memory access count and timestamp"""
        try:
            self.db.query(AgentMemory).filter(
                AgentMemory.id == memory_id
            ).update({
                'access_count': AgentMemory.access_count + 1,
                'last_accessed_at': datetime.utcnow()
            })

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update memory access: {e}")
            raise

    def get_old_short_term(self, agent_id: UUID, retention_hours: int) -> List[AgentMemory]:
        """Get short-term memories older than retention period"""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=retention_hours)

            memories = self.db.query(AgentMemory).filter(
                and_(
                    AgentMemory.agent_id == agent_id,
                    AgentMemory.type == 'short_term',
                    AgentMemory.created_at < cutoff
                )
            ).all()

            return memories

        except Exception as e:
            logger.error(f"Failed to get old short-term memories: {e}")
            raise

    def get_settings(self, agent_id: UUID) -> Optional[MemorySettings]:
        """Get memory settings for an agent"""
        try:
            return self.db.query(MemorySettings).filter(
                MemorySettings.agent_id == agent_id
            ).first()

        except Exception as e:
            logger.error(f"Failed to get memory settings: {e}")
            raise

    def create_or_update_settings(
        self,
        agent_id: UUID,
        settings_data: Dict[str, Any]
    ) -> MemorySettings:
        """Create or update memory settings"""
        try:
            settings = self.get_settings(agent_id)

            if settings:
                # Update existing
                for key, value in settings_data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                settings.updated_at = datetime.utcnow()
            else:
                # Create new
                settings = MemorySettings(
                    agent_id=agent_id,
                    **settings_data
                )
                self.db.add(settings)

            self.db.commit()
            self.db.refresh(settings)

            return settings

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create/update memory settings: {e}")
            raise

    def get_timeline_events(
        self,
        agent_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get memory timeline events
        
        Note: This is a simplified version. In production, you might want
        a separate events table for better performance.
        """
        try:
            # Get recent memories with their creation/access times
            memories = self.db.query(AgentMemory).filter(
                AgentMemory.agent_id == agent_id
            ).order_by(
                AgentMemory.created_at.desc()
            ).limit(limit).all()

            events = []
            for memory in memories:
                # Created event
                events.append({
                    'id': f"event-created-{memory.id}",
                    'type': 'created',
                    'memory_id': str(memory.id),
                    'timestamp': memory.created_at.isoformat(),
                    'metadata': {'memory_type': memory.type}
                })

                # Accessed event (if accessed)
                if memory.last_accessed_at:
                    events.append({
                        'id': f"event-accessed-{memory.id}",
                        'type': 'accessed',
                        'memory_id': str(memory.id),
                        'timestamp': memory.last_accessed_at.isoformat(),
                        'metadata': {'access_count': memory.access_count}
                    })

            # Sort by timestamp
            events.sort(key=lambda x: x['timestamp'], reverse=True)

            return events[:limit]

        except Exception as e:
            logger.error(f"Failed to get timeline events: {e}")
            raise
