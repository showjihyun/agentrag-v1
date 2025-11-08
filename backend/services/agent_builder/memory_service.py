"""
Memory Service

Business logic layer for agent memory management.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

from backend.db.repositories.memory_repository import MemoryRepository
from backend.db.models.agent_builder import AgentMemory

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for memory management business logic"""

    def __init__(self, repository: MemoryRepository):
        self.repository = repository

    async def consolidate_memories(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Consolidate short-term memories to long-term storage
        
        Process:
        1. Get short-term memories older than retention period
        2. Analyze importance and relevance
        3. Merge similar memories
        4. Move important ones to long-term storage
        5. Delete old short-term memories
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Dict with consolidation results
        """
        try:
            # Get settings
            settings = self.repository.get_settings(agent_id)
            if not settings:
                # Use default retention
                retention_hours = 24
            else:
                retention_hours = settings.short_term_retention_hours

            # Get old short-term memories
            old_memories = self.repository.get_old_short_term(agent_id, retention_hours)
            
            if not old_memories:
                return {
                    'success': True,
                    'consolidated_count': 0,
                    'deleted_count': 0,
                    'message': 'No memories to consolidate'
                }

            # Analyze and consolidate
            consolidated = await self._analyze_and_consolidate(old_memories)
            
            # Save consolidated memories to long-term
            saved_count = 0
            for memory_data in consolidated:
                self.repository.create_memory(
                    agent_id=agent_id,
                    memory_type='long_term',
                    content=memory_data['content'],
                    metadata=memory_data['metadata'],
                    importance=memory_data['importance']
                )
                saved_count += 1

            # Delete old short-term memories
            deleted_count = 0
            for memory in old_memories:
                if self.repository.delete_memory(agent_id, memory.id):
                    deleted_count += 1

            logger.info(
                f"Consolidated {saved_count} memories, deleted {deleted_count} for agent {agent_id}"
            )

            return {
                'success': True,
                'consolidated_count': saved_count,
                'deleted_count': deleted_count,
                'estimated_time_seconds': len(old_memories) * 0.5
            }

        except Exception as e:
            logger.error(f"Failed to consolidate memories: {e}")
            raise

    async def _analyze_and_consolidate(
        self,
        memories: List[AgentMemory]
    ) -> List[Dict[str, Any]]:
        """
        Analyze memories and create consolidated versions
        
        This is a simplified version. In production, you would:
        1. Use LLM to analyze importance
        2. Detect similar/duplicate memories
        3. Merge related memories
        4. Extract key information
        
        Args:
            memories: List of memories to consolidate
            
        Returns:
            List of consolidated memory data
        """
        consolidated = []
        
        # Group by importance
        high_importance = [m for m in memories if m.importance == 'high']
        medium_importance = [m for m in memories if m.importance == 'medium']
        
        # Keep all high importance
        for memory in high_importance:
            consolidated.append({
                'content': memory.content,
                'metadata': {
                    **memory.meta_data,
                    'consolidated_from': str(memory.id),
                    'original_type': memory.type,
                    'access_count': memory.access_count
                },
                'importance': 'high'
            })
        
        # Keep frequently accessed medium importance
        for memory in medium_importance:
            if memory.access_count >= 3:  # Threshold
                consolidated.append({
                    'content': memory.content,
                    'metadata': {
                        **memory.meta_data,
                        'consolidated_from': str(memory.id),
                        'original_type': memory.type,
                        'access_count': memory.access_count
                    },
                    'importance': 'medium'
                })
        
        return consolidated

    async def search_memories_semantic(
        self,
        agent_id: UUID,
        query: str,
        top_k: int = 10,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across memories
        
        In production, this would:
        1. Generate query embedding
        2. Search in Milvus vector database
        3. Rank by relevance
        4. Return top-k results
        
        Args:
            agent_id: Agent UUID
            query: Search query
            top_k: Number of results
            memory_type: Optional type filter
            
        Returns:
            List of search results with relevance scores
        """
        try:
            # Get all memories (in production, use vector search)
            memories = self.repository.get_memories(
                agent_id=agent_id,
                memory_type=memory_type,
                limit=100
            )
            
            # Simple keyword matching (replace with vector similarity)
            results = []
            query_lower = query.lower()
            
            for memory in memories:
                # Calculate simple relevance score
                content_lower = memory.content.lower()
                if query_lower in content_lower:
                    # Simple scoring based on position and frequency
                    position_score = 1.0 - (content_lower.index(query_lower) / len(content_lower))
                    frequency_score = content_lower.count(query_lower) / 10.0
                    relevance = min((position_score + frequency_score) / 2, 1.0)
                    
                    results.append({
                        'memory': {
                            'id': str(memory.id),
                            'type': memory.type,
                            'content': memory.content,
                            'metadata': memory.meta_data,
                            'importance': memory.importance,
                            'access_count': memory.access_count,
                            'created_at': memory.created_at.isoformat()
                        },
                        'relevance_score': round(relevance, 3)
                    })
            
            # Sort by relevance and return top-k
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            raise

    async def cleanup_old_memories(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Clean up old memories based on settings
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Cleanup results
        """
        try:
            settings = self.repository.get_settings(agent_id)
            
            if not settings or not settings.auto_cleanup:
                return {
                    'success': False,
                    'message': 'Auto cleanup is disabled'
                }

            # Get old short-term memories
            old_memories = self.repository.get_old_short_term(
                agent_id,
                settings.short_term_retention_hours
            )
            
            # Delete low importance memories
            deleted_count = 0
            for memory in old_memories:
                if memory.importance == 'low' and memory.access_count < 2:
                    if self.repository.delete_memory(agent_id, memory.id):
                        deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} memories for agent {agent_id}")

            return {
                'success': True,
                'deleted_count': deleted_count
            }

        except Exception as e:
            logger.error(f"Failed to cleanup memories: {e}")
            raise

    def get_memory_health(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get memory system health metrics
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Health metrics
        """
        try:
            stats = self.repository.get_stats(agent_id)
            settings = self.repository.get_settings(agent_id)
            
            # Calculate health score
            total_size = stats.get('total_size_mb', 0)
            max_size = settings.max_memory_size_mb if settings else 1000
            
            size_ratio = total_size / max_size if max_size > 0 else 0
            
            # Health status
            if size_ratio < 0.7:
                status = 'healthy'
            elif size_ratio < 0.9:
                status = 'warning'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'size_ratio': round(size_ratio, 2),
                'total_size_mb': total_size,
                'max_size_mb': max_size,
                'recommendations': self._get_health_recommendations(size_ratio, stats)
            }

        except Exception as e:
            logger.error(f"Failed to get memory health: {e}")
            raise

    def _get_health_recommendations(
        self,
        size_ratio: float,
        stats: Dict[str, Any]
    ) -> List[str]:
        """Generate health recommendations"""
        recommendations = []
        
        if size_ratio > 0.9:
            recommendations.append("Critical: Memory usage above 90%. Enable auto-cleanup.")
            recommendations.append("Consider increasing max_memory_size_mb.")
        elif size_ratio > 0.7:
            recommendations.append("Warning: Memory usage above 70%. Run consolidation.")
        
        # Check short-term memory
        stm_count = stats.get('short_term', {}).get('count', 0)
        if stm_count > 100:
            recommendations.append(f"High short-term memory count ({stm_count}). Run consolidation.")
        
        if not recommendations:
            recommendations.append("Memory system is healthy.")
        
        return recommendations
