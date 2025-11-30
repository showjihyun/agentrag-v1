"""
Session Management API

Provides endpoints for managing user sessions:
- List active sessions
- Revoke specific session
- Revoke all sessions
"""

import logging
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.core.audit_logger import get_audit_logger, AuditEventType

logger = logging.getLogger(__name__)
audit = get_audit_logger()

router = APIRouter(prefix="/api/auth/sessions", tags=["Sessions"])


# ============================================================================
# Models
# ============================================================================

class SessionInfo(BaseModel):
    """Session information."""
    id: str
    device: str
    browser: str
    location: str
    ip_address: str
    last_active: str
    created_at: str
    is_current: bool


class SessionListResponse(BaseModel):
    """List of sessions response."""
    sessions: List[SessionInfo]
    total: int


# In-memory session storage (production would use Redis/DB)
_user_sessions: dict[str, List[dict]] = {}


def _get_device_info(user_agent: str) -> tuple[str, str]:
    """Extract device and browser from user agent."""
    user_agent_lower = user_agent.lower()
    
    # Detect device
    if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
        device = 'Mobile'
    elif 'ipad' in user_agent_lower or 'tablet' in user_agent_lower:
        device = 'Tablet'
    elif 'macintosh' in user_agent_lower or 'mac os' in user_agent_lower:
        device = 'MacBook'
    elif 'windows' in user_agent_lower:
        device = 'Windows PC'
    elif 'linux' in user_agent_lower:
        device = 'Linux PC'
    else:
        device = 'Unknown Device'
    
    # Detect browser
    if 'chrome' in user_agent_lower and 'edg' not in user_agent_lower:
        browser = 'Chrome'
    elif 'firefox' in user_agent_lower:
        browser = 'Firefox'
    elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
        browser = 'Safari'
    elif 'edg' in user_agent_lower:
        browser = 'Edge'
    else:
        browser = 'Unknown Browser'
    
    return device, browser


def _create_session(user_id: str, request: Request) -> dict:
    """Create a new session record."""
    user_agent = request.headers.get('User-Agent', '')
    device, browser = _get_device_info(user_agent)
    
    # Get IP
    forwarded = request.headers.get('X-Forwarded-For')
    ip = forwarded.split(',')[0].strip() if forwarded else (request.client.host if request.client else 'unknown')
    
    session = {
        'id': str(uuid4()),
        'device': device,
        'browser': browser,
        'location': 'Unknown',  # Would use IP geolocation in production
        'ip_address': ip,
        'last_active': datetime.utcnow().isoformat() + 'Z',
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'user_agent': user_agent,
    }
    
    if user_id not in _user_sessions:
        _user_sessions[user_id] = []
    
    _user_sessions[user_id].append(session)
    
    return session


def get_or_create_current_session(user_id: str, request: Request) -> str:
    """Get current session ID or create new one."""
    # In production, this would check JWT token's session ID
    # For now, create a session if none exists
    if user_id not in _user_sessions or not _user_sessions[user_id]:
        session = _create_session(user_id, request)
        return session['id']
    
    # Return most recent session
    return _user_sessions[user_id][-1]['id']


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=SessionListResponse)
async def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all active sessions for the current user.
    """
    user_id = str(current_user.id)
    
    # Ensure at least current session exists
    current_session_id = get_or_create_current_session(user_id, request)
    
    sessions = _user_sessions.get(user_id, [])
    
    session_list = [
        SessionInfo(
            id=s['id'],
            device=s['device'],
            browser=s['browser'],
            location=s['location'],
            ip_address=s['ip_address'],
            last_active=s['last_active'],
            created_at=s['created_at'],
            is_current=(s['id'] == current_session_id)
        )
        for s in sessions
    ]
    
    return SessionListResponse(
        sessions=session_list,
        total=len(session_list)
    )


@router.delete("/{session_id}")
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke a specific session.
    """
    user_id = str(current_user.id)
    
    if user_id not in _user_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Find and remove session
    sessions = _user_sessions[user_id]
    original_count = len(sessions)
    _user_sessions[user_id] = [s for s in sessions if s['id'] != session_id]
    
    if len(_user_sessions[user_id]) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Audit log
    audit.log(
        event_type=AuditEventType.AUTH_LOGOUT,
        action=f"Session revoked: {session_id}",
        request=request,
        user_id=user_id,
        user_email=current_user.email
    )
    
    logger.info(f"User {user_id} revoked session {session_id}")
    
    return {"message": "Session revoked successfully"}


@router.delete("")
async def revoke_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke all sessions except the current one.
    """
    user_id = str(current_user.id)
    current_session_id = get_or_create_current_session(user_id, request)
    
    if user_id not in _user_sessions:
        return {"message": "No sessions to revoke", "revoked_count": 0}
    
    # Keep only current session
    sessions = _user_sessions[user_id]
    revoked_count = len([s for s in sessions if s['id'] != current_session_id])
    _user_sessions[user_id] = [s for s in sessions if s['id'] == current_session_id]
    
    # Audit log
    audit.log(
        event_type=AuditEventType.AUTH_LOGOUT,
        action=f"All other sessions revoked ({revoked_count} sessions)",
        request=request,
        user_id=user_id,
        user_email=current_user.email
    )
    
    logger.info(f"User {user_id} revoked {revoked_count} sessions")
    
    return {
        "message": f"Revoked {revoked_count} sessions",
        "revoked_count": revoked_count
    }


@router.post("/refresh")
async def refresh_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Refresh current session's last active time.
    """
    user_id = str(current_user.id)
    current_session_id = get_or_create_current_session(user_id, request)
    
    if user_id in _user_sessions:
        for session in _user_sessions[user_id]:
            if session['id'] == current_session_id:
                session['last_active'] = datetime.utcnow().isoformat() + 'Z'
                break
    
    return {"message": "Session refreshed"}
