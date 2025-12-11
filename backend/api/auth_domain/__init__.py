"""
Authentication domain API routers

This package provides organized access to authentication-related endpoints.
The actual router implementations are in the parent api directory for
backward compatibility.

Related files:
- ../auth.py: Login, register, token management
- ../auth_sessions.py: Session management
- ../permissions.py: Permission checks
"""

# Note: Do not import routers here to avoid circular imports.
# Use direct imports from backend.api.auth (the .py file) instead.

__all__ = []
