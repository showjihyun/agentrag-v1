"""Conversation export and import service."""

import logging
import json
import csv
import io
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import UUID
import zipfile
import tempfile
import os

from sqlalchemy.orm import Session

from backend.db.repositories.chat_session_repository import ChatSessionRepository
from backend.db.repositories.chat_message_repository import ChatMessageRepository
from backend.db.models.flows import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

class ConversationExportService:
    """Service for exporting and importing conversation data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = ChatSessionRepository(db)
        self.message_repo = ChatMessageRepository(db)
    
    async def export_session(
        self,
        session_id: UUID,
        user_id: Optional[UUID] = None,
        format: str = 'json',
        include_metadata: bool = True,
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """Export a single session in specified format."""
        try:
            # Get session with messages
            session = await self.session_repo.get_session(
                session_id,
                user_id,
                include_messages=True
            )
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Get messages
            messages = await self.message_repo.get_session_messages(session.id)
            
            # Get summaries if available
            summaries = await self.message_repo.get_session_summaries(session.id)
            
            # Create export data
            export_data = await self._create_export_data(
                session,
                messages,
                summaries,
                include_metadata,
                include_analysis
            )
            
            # Format data based on requested format
            if format == 'json':
                content = json.dumps(export_data, ensure_ascii=False, indent=2)
                content_type = 'application/json'
                filename = f"conversation_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            elif format == 'csv':
                content = self._export_to_csv(export_data)
                content_type = 'text/csv'
                filename = f"conversation_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            elif format == 'txt':
                content = self._export_to_text(export_data)
                content_type = 'text/plain'
                filename = f"conversation_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            elif format == 'markdown':
                content = self._export_to_markdown(export_data)
                content_type = 'text/markdown'
                filename = f"conversation_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            return {
                'success': True,
                'content': content,
                'content_type': content_type,
                'filename': filename,
                'size_bytes': len(content.encode('utf-8')),
                'message_count': len(messages),
                'export_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Session export failed: {e}")
            raise
    
    async def export_multiple_sessions(
        self,
        session_ids: List[UUID],
        user_id: Optional[UUID] = None,
        format: str = 'json',
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Export multiple sessions as a ZIP archive."""
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                exported_files = []
                total_messages = 0
                
                # Export each session
                for session_id in session_ids:
                    try:
                        export_result = await self.export_session(
                            session_id,
                            user_id,
                            format,
                            include_metadata
                        )
                        
                        if export_result['success']:
                            # Write to temporary file
                            file_path = os.path.join(temp_dir, export_result['filename'])
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(export_result['content'])
                            
                            exported_files.append({
                                'session_id': str(session_id),
                                'filename': export_result['filename'],
                                'message_count': export_result['message_count']
                            })
                            total_messages += export_result['message_count']
                    
                    except Exception as e:
                        logger.error(f"Failed to export session {session_id}: {e}")
                        continue
                
                if not exported_files:
                    raise ValueError("No sessions could be exported")
                
                # Create ZIP archive
                zip_filename = f"conversations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = os.path.join(temp_dir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add exported files
                    for file_info in exported_files:
                        file_path = os.path.join(temp_dir, file_info['filename'])
                        zipf.write(file_path, file_info['filename'])
                    
                    # Add manifest
                    manifest = {
                        'export_timestamp': datetime.utcnow().isoformat(),
                        'total_sessions': len(exported_files),
                        'total_messages': total_messages,
                        'format': format,
                        'files': exported_files
                    }
                    
                    manifest_content = json.dumps(manifest, ensure_ascii=False, indent=2)
                    zipf.writestr('manifest.json', manifest_content)
                
                # Read ZIP content
                with open(zip_path, 'rb') as f:
                    zip_content = f.read()
                
                return {
                    'success': True,
                    'content': zip_content,
                    'content_type': 'application/zip',
                    'filename': zip_filename,
                    'size_bytes': len(zip_content),
                    'sessions_exported': len(exported_files),
                    'total_messages': total_messages
                }
        
        except Exception as e:
            logger.error(f"Multiple sessions export failed: {e}")
            raise
    
    async def import_session(
        self,
        import_data: Union[str, Dict[str, Any]],
        user_id: UUID,
        chatflow_id: UUID,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """Import session data."""
        try:
            # Parse import data
            if isinstance(import_data, str):
                if format == 'json':
                    data = json.loads(import_data)
                else:
                    raise ValueError(f"String import only supported for JSON format")
            else:
                data = import_data
            
            # Validate import data structure
            self._validate_import_data(data)
            
            # Create new session
            session_data = data['session']
            memory_config = session_data.get('memory_config', {})
            
            new_session = await self.session_repo.create_session(
                chatflow_id=chatflow_id,
                user_id=user_id,
                memory_type=session_data.get('memory_type', 'buffer'),
                memory_config=memory_config,
                title=f"Imported: {session_data.get('title', 'Conversation')}"
            )
            
            # Import messages
            imported_messages = 0
            for msg_data in data.get('messages', []):
                try:
                    await self.message_repo.add_message(
                        session_id=new_session.id,
                        role=msg_data['role'],
                        content=msg_data['content'],
                        metadata=msg_data.get('metadata', {}),
                        created_at=datetime.fromisoformat(msg_data['created_at']) if 'created_at' in msg_data else None
                    )
                    imported_messages += 1
                
                except Exception as e:
                    logger.warning(f"Failed to import message: {e}")
                    continue
            
            # Import summaries if available
            imported_summaries = 0
            for summary_data in data.get('summaries', []):
                try:
                    await self.message_repo.add_summary(
                        session_id=new_session.id,
                        summary_text=summary_data['summary_text'],
                        message_range_start=summary_data['message_range_start'],
                        message_range_end=summary_data['message_range_end']
                    )
                    imported_summaries += 1
                
                except Exception as e:
                    logger.warning(f"Failed to import summary: {e}")
                    continue
            
            # Update session statistics
            await self.session_repo.update_session_activity(
                new_session.id,
                message_count_delta=imported_messages
            )
            
            return {
                'success': True,
                'session_id': str(new_session.id),
                'messages_imported': imported_messages,
                'summaries_imported': imported_summaries,
                'import_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Session import failed: {e}")
            raise
    
    async def _create_export_data(
        self,
        session: ChatSession,
        messages: List[ChatMessage],
        summaries: List,
        include_metadata: bool,
        include_analysis: bool
    ) -> Dict[str, Any]:
        """Create structured export data."""
        export_data = {
            'export_version': '1.0',
            'export_timestamp': datetime.utcnow().isoformat(),
            'session': {
                'id': str(session.id),
                'title': session.title,
                'memory_type': session.memory_type,
                'memory_config': session.memory_config,
                'created_at': session.created_at.isoformat(),
                'last_activity_at': session.last_activity_at.isoformat() if session.last_activity_at else None,
                'message_count': session.message_count,
                'total_tokens_used': session.total_tokens_used
            },
            'messages': []
        }
        
        # Add messages
        for message in messages:
            msg_data = {
                'id': str(message.id),
                'role': message.role,
                'content': message.content,
                'created_at': message.created_at.isoformat()
            }
            
            if include_metadata and message.message_metadata:
                msg_data['metadata'] = message.message_metadata
            
            if include_analysis and message.message_metadata:
                # Extract analysis data
                analysis_data = {}
                metadata = message.message_metadata
                
                if 'intent' in metadata:
                    analysis_data['intent'] = metadata['intent']
                if 'is_followup' in metadata:
                    analysis_data['is_followup'] = metadata['is_followup']
                if 'requires_context' in metadata:
                    analysis_data['requires_context'] = metadata['requires_context']
                if 'references' in metadata:
                    analysis_data['references'] = metadata['references']
                if 'confidence' in metadata:
                    analysis_data['confidence'] = metadata['confidence']
                
                if analysis_data:
                    msg_data['analysis'] = analysis_data
            
            export_data['messages'].append(msg_data)
        
        # Add summaries if available
        if summaries:
            export_data['summaries'] = [
                {
                    'id': str(summary.id),
                    'summary_text': summary.summary_text,
                    'message_range_start': summary.message_range_start,
                    'message_range_end': summary.message_range_end,
                    'created_at': summary.created_at.isoformat()
                }
                for summary in summaries
            ]
        
        return export_data
    
    def _export_to_csv(self, data: Dict[str, Any]) -> str:
        """Export data to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Timestamp', 'Role', 'Content', 'Intent', 'Is_Followup', 
            'Requires_Context', 'Confidence', 'Tokens_Used'
        ])
        
        # Write messages
        for message in data['messages']:
            analysis = message.get('analysis', {})
            metadata = message.get('metadata', {})
            
            writer.writerow([
                message['created_at'],
                message['role'],
                message['content'],
                analysis.get('intent', ''),
                analysis.get('is_followup', ''),
                analysis.get('requires_context', ''),
                analysis.get('confidence', ''),
                metadata.get('tokens_used', {}).get('total_tokens', '') if isinstance(metadata.get('tokens_used'), dict) else ''
            ])
        
        return output.getvalue()
    
    def _export_to_text(self, data: Dict[str, Any]) -> str:
        """Export data to plain text format."""
        lines = []
        
        # Header
        session = data['session']
        lines.append(f"Conversation Export")
        lines.append(f"Session: {session['title']}")
        lines.append(f"Created: {session['created_at']}")
        lines.append(f"Memory Type: {session['memory_type']}")
        lines.append(f"Messages: {session['message_count']}")
        lines.append(f"Tokens Used: {session['total_tokens_used']}")
        lines.append("=" * 50)
        lines.append("")
        
        # Messages
        for message in data['messages']:
            timestamp = datetime.fromisoformat(message['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            role = message['role'].upper()
            content = message['content']
            
            lines.append(f"[{timestamp}] {role}:")
            lines.append(content)
            lines.append("")
        
        return "\n".join(lines)
    
    def _export_to_markdown(self, data: Dict[str, Any]) -> str:
        """Export data to Markdown format."""
        lines = []
        
        # Header
        session = data['session']
        lines.append(f"# Conversation Export")
        lines.append("")
        lines.append(f"**Session:** {session['title']}")
        lines.append(f"**Created:** {session['created_at']}")
        lines.append(f"**Memory Type:** {session['memory_type']}")
        lines.append(f"**Messages:** {session['message_count']}")
        lines.append(f"**Tokens Used:** {session['total_tokens_used']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Messages
        for message in data['messages']:
            timestamp = datetime.fromisoformat(message['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            role = message['role']
            content = message['content']
            
            if role == 'user':
                lines.append(f"## 👤 User ({timestamp})")
            elif role == 'assistant':
                lines.append(f"## 🤖 Assistant ({timestamp})")
            else:
                lines.append(f"## {role.title()} ({timestamp})")
            
            lines.append("")
            lines.append(content)
            lines.append("")
            
            # Add analysis info if available
            if 'analysis' in message:
                analysis = message['analysis']
                lines.append("**Analysis:**")
                if 'intent' in analysis:
                    lines.append(f"- Intent: {analysis['intent']}")
                if 'confidence' in analysis:
                    lines.append(f"- Confidence: {analysis['confidence']:.2f}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _validate_import_data(self, data: Dict[str, Any]) -> None:
        """Validate import data structure."""
        required_fields = ['session', 'messages']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate session data
        session = data['session']
        if 'title' not in session:
            raise ValueError("Session must have a title")
        
        # Validate messages
        messages = data['messages']
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list")
        
        for i, message in enumerate(messages):
            if 'role' not in message or 'content' not in message:
                raise ValueError(f"Message {i} missing required fields (role, content)")
            
            if message['role'] not in ['user', 'assistant', 'system']:
                raise ValueError(f"Message {i} has invalid role: {message['role']}")

# Global export service instance
_export_service = None

def get_export_service(db: Session) -> ConversationExportService:
    """Get export service instance."""
    return ConversationExportService(db)