"""
Conversations domain API routers

Groups all conversation-related endpoints:
- conversations.py: Conversation CRUD
- chat_history.py: Chat history management
- bookmarks.py: Message bookmarks
- share.py: Conversation sharing
- export.py/exports.py: Export functionality
"""

# Re-export routers for easy access
# Usage: from backend.api.conversations import conversations_router

__all__ = [
    "conversations",
    "chat_history",
    "bookmarks",
    "share",
    "export",
    "exports",
]
