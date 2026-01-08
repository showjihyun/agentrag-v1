"""Session cleanup and archiving service."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import json
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.repositories.chat_session_repository import ChatSessionRepository
from backend.db.repositories.chat_message_repository import ChatMessageRepository
from backend.db.models.flows import ChatSession, ChatMessage, ChatSummary

logger = logging.getLogger(__name__)

class SessionCleanupService:
    """Service for cleaning up and archiving old chat sessions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = ChatSessionRepository(db)
        self.message_repo = ChatMessageRepository(db)
    
    async def cleanup_inactive_sessions(
        self,
        inactive_days: int = 30,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Clean up sessions that have been inactive for specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=inactive_days)
        
        try:
            # Find inactive sessions
            inactive_sessions = await self.session_repo.find_inactive_sessions(
                cutoff_date=cutoff_date,
                limit=1000
            )
            
            cleanup_stats = {
                'sessions_found': len(inactive_sessions),
                'sessions_archived': 0,
                'sessions_deleted': 0,
                'messages_archived': 0,
                'messages_deleted': 0,
                'storage_freed_mb': 0,
                'errors': []
            }
            
            if dry_run:
                logger.info(f"DRY RUN: Would process {len(inactive_sessions)} inactive sessions")
                return cleanup_stats
            
            for session in inactive_sessions:
                try:
                    # Get session statistics
                    session_stats = await self._get_session_stats(session.id)
                    
                    # Decide whether to archive or delete
                    if self._should_archive_session(session, session_stats):
                        await self._archive_session(session)
                        cleanup_stats['sessions_archived'] += 1
                        cleanup_stats['messages_archived'] += session_stats['message_count']
                    else:
                        await self._delete_session(session)
                        cleanup_stats['sessions_deleted'] += 1
                        cleanup_stats['messages_deleted'] += session_stats['message_count']
                    
                    # Estimate storage freed (rough calculation)
                    cleanup_stats['storage_freed_mb'] += session_stats['estimated_size_mb']
                    
                except Exception as e:
                    error_msg = f"Failed to process session {session.id}: {e}"
                    logger.error(error_msg)
                    cleanup_stats['errors'].append(error_msg)
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            raise
    
    async def archive_session(
        self,
        session_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Archive a specific session."""
        try:
            session = await self.session_repo.get_session(
                session_id,
                user_id,
                include_messages=True
            )
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Create archive
            archive_data = await self._create_session_archive(session)
            
            # Store archive
            archive_path = await self._store_archive(session_id, archive_data)
            
            # Update session status
            await self.session_repo.update_session_status(
                session_id,
                status='archived',
                archive_path=archive_path
            )
            
            # Clean up messages (keep only summary)
            await self._cleanup_archived_session_messages(session_id)
            
            return {
                'success': True,
                'session_id': str(session_id),
                'archive_path': archive_path,
                'messages_archived': len(archive_data['messages']),
                'archive_size_mb': len(json.dumps(archive_data)) / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Session archiving failed: {e}")
            raise
    
    async def restore_session(
        self,
        session_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Restore an archived session."""
        try:
            session = await self.session_repo.get_session(session_id, user_id)
            
            if not session or session.status != 'archived':
                raise ValueError(f"Archived session {session_id} not found")
            
            # Load archive
            archive_data = await self._load_archive(session.archive_path)
            
            # Restore messages
            restored_count = await self._restore_session_messages(session_id, archive_data)
            
            # Update session status
            await self.session_repo.update_session_status(
                session_id,
                status='active',
                archive_path=None
            )
            
            return {
                'success': True,
                'session_id': str(session_id),
                'messages_restored': restored_count
            }
            
        except Exception as e:
            logger.error(f"Session restoration failed: {e}")
            raise
    
    async def get_cleanup_statistics(self) -> Dict[str, Any]:
        """Get cleanup statistics and recommendations."""
        try:
            # Get session statistics
            total_sessions = await self.session_repo.count_sessions()
            active_sessions = await self.session_repo.count_active_sessions()
            archived_sessions = await self.session_repo.count_archived_sessions()
            
            # Get old sessions
            cutoff_30_days = datetime.utcnow() - timedelta(days=30)
            cutoff_90_days = datetime.utcnow() - timedelta(days=90)
            
            old_30_days = await self.session_repo.count_inactive_sessions(cutoff_30_days)
            old_90_days = await self.session_repo.count_inactive_sessions(cutoff_90_days)
            
            # Get storage estimates
            storage_stats = await self._estimate_storage_usage()
            
            return {
                'session_counts': {
                    'total': total_sessions,
                    'active': active_sessions,
                    'archived': archived_sessions,
                    'inactive_30_days': old_30_days,
                    'inactive_90_days': old_90_days
                },
                'storage_estimates': storage_stats,
                'recommendations': self._generate_cleanup_recommendations(
                    old_30_days, old_90_days, storage_stats
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get cleanup statistics: {e}")
            raise
    
    def _should_archive_session(
        self,
        session: ChatSession,
        stats: Dict[str, Any]
    ) -> bool:
        """Determine if session should be archived vs deleted."""
        # Archive if:
        # - Has significant conversation (>10 messages)
        # - Has high token usage (>1000 tokens)
        # - Has important messages (high importance scores)
        
        return (
            stats['message_count'] > 10 or
            stats['total_tokens'] > 1000 or
            stats['avg_importance_score'] > 0.7
        )
    
    async def _get_session_stats(self, session_id: UUID) -> Dict[str, Any]:
        """Get statistics for a session."""
        messages = await self.message_repo.get_session_messages(session_id)
        
        total_tokens = 0
        importance_scores = []
        total_content_length = 0
        
        for message in messages:
            # Token count from metadata
            if message.message_metadata:
                tokens = message.message_metadata.get('tokens_used', {})
                if isinstance(tokens, dict):
                    total_tokens += tokens.get('total_tokens', 0)
                
                # Importance score
                importance = message.message_metadata.get('importance_score', 0.5)
                importance_scores.append(importance)
            
            # Content length
            total_content_length += len(message.content or '')
        
        return {
            'message_count': len(messages),
            'total_tokens': total_tokens,
            'avg_importance_score': sum(importance_scores) / len(importance_scores) if importance_scores else 0.5,
            'total_content_length': total_content_length,
            'estimated_size_mb': total_content_length / (1024 * 1024)
        }
    
    async def _create_session_archive(self, session: ChatSession) -> Dict[str, Any]:
        """Create archive data for a session."""
        messages = await self.message_repo.get_session_messages(session.id)
        summaries = await self.message_repo.get_session_summaries(session.id)
        
        return {
            'session': {
                'id': str(session.id),
                'chatflow_id': str(session.chatflow_id),
                'user_id': str(session.user_id) if session.user_id else None,
                'title': session.title,
                'memory_type': session.memory_type,
                'memory_config': session.memory_config,
                'created_at': session.created_at.isoformat(),
                'last_activity_at': session.last_activity_at.isoformat() if session.last_activity_at else None,
                'message_count': session.message_count,
                'total_tokens_used': session.total_tokens_used
            },
            'messages': [
                {
                    'id': str(msg.id),
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat(),
                    'metadata': msg.message_metadata
                }
                for msg in messages
            ],
            'summaries': [
                {
                    'id': str(summary.id),
                    'summary_text': summary.summary_text,
                    'message_range_start': summary.message_range_start,
                    'message_range_end': summary.message_range_end,
                    'created_at': summary.created_at.isoformat()
                }
                for summary in summaries
            ],
            'archived_at': datetime.utcnow().isoformat(),
            'archive_version': '1.0'
        }
    
    async def _store_archive(self, session_id: UUID, archive_data: Dict[str, Any]) -> str:
        """Store archive data (implement based on storage backend)."""
        # For now, store in database as JSON
        # In production, you might want to use S3, file system, etc.
        
        archive_json = json.dumps(archive_data, ensure_ascii=False, indent=2)
        
        # Store in session metadata for now
        await self.session_repo.update_session_metadata(
            session_id,
            {'archive_data': archive_data}
        )
        
        return f"db://session_metadata/{session_id}"
    
    async def _load_archive(self, archive_path: str) -> Dict[str, Any]:
        """Load archive data from storage."""
        if archive_path.startswith("db://session_metadata/"):
            session_id = UUID(archive_path.split("/")[-1])
            session = await self.session_repo.get_session(session_id)
            
            if session and session.session_metadata:
                return session.session_metadata.get('archive_data', {})
        
        raise ValueError(f"Archive not found: {archive_path}")
    
    async def _cleanup_archived_session_messages(self, session_id: UUID) -> None:
        """Remove messages from archived session, keeping only summaries."""
        await self.message_repo.delete_session_messages(
            session_id,
            keep_summaries=True
        )
    
    async def _restore_session_messages(
        self,
        session_id: UUID,
        archive_data: Dict[str, Any]
    ) -> int:
        """Restore messages from archive data."""
        restored_count = 0
        
        for msg_data in archive_data.get('messages', []):
            await self.message_repo.create_message_from_archive(
                session_id=session_id,
                message_data=msg_data
            )
            restored_count += 1
        
        return restored_count
    
    async def _delete_session(self, session: ChatSession) -> None:
        """Permanently delete a session and all its data."""
        await self.session_repo.delete_session(session.id)
    
    async def _estimate_storage_usage(self) -> Dict[str, Any]:
        """Estimate storage usage by sessions."""
        # This is a simplified estimation
        # In production, you'd want more accurate measurements
        
        total_messages = await self.message_repo.count_all_messages()
        avg_message_size = 200  # bytes, rough estimate
        
        return {
            'total_messages': total_messages,
            'estimated_total_mb': (total_messages * avg_message_size) / (1024 * 1024),
            'estimated_per_session_kb': avg_message_size * 20 / 1024  # Assume 20 messages per session
        }
    
    def _generate_cleanup_recommendations(
        self,
        old_30_days: int,
        old_90_days: int,
        storage_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate cleanup recommendations."""
        recommendations = []
        
        if old_30_days > 100:
            recommendations.append(
                f"Consider archiving {old_30_days} sessions inactive for 30+ days"
            )
        
        if old_90_days > 50:
            recommendations.append(
                f"Consider deleting {old_90_days} sessions inactive for 90+ days"
            )
        
        if storage_stats['estimated_total_mb'] > 1000:
            recommendations.append(
                f"High storage usage detected ({storage_stats['estimated_total_mb']:.1f} MB). "
                "Consider implementing regular cleanup schedule."
            )
        
        if not recommendations:
            recommendations.append("No immediate cleanup needed. System is healthy.")
        
        return recommendations