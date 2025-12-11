# Event Store API endpoints

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.core.events import get_event_store, DomainEvent
from backend.db.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/api/events", tags=["Event Store"])


class EventResponse(BaseModel):
    """Event response model."""
    aggregate_id: str
    aggregate_type: str
    event_type: str
    event_data: dict
    user_id: Optional[int]
    metadata: Optional[dict]
    timestamp: datetime
    version: int


class AuditLogResponse(BaseModel):
    """Audit log response model."""
    events: List[EventResponse]
    total_count: int


@router.get("/aggregate/{aggregate_id}", response_model=List[EventResponse])
async def get_aggregate_events(
    aggregate_id: str,
    aggregate_type: Optional[str] = None,
    from_version: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all events for an aggregate.
    
    Args:
        aggregate_id: Aggregate identifier
        aggregate_type: Optional aggregate type filter
        from_version: Start from this version
        
    Returns:
        List of events
    """
    store = get_event_store(db)
    events = await store.get_events(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        from_version=from_version
    )
    
    return [
        EventResponse(
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            event_type=event.event_type,
            event_data=event.event_data,
            user_id=event.user_id,
            metadata=event.metadata,
            timestamp=event.timestamp,
            version=event.version
        )
        for event in events
    ]


@router.get("/replay/{aggregate_id}", response_model=List[EventResponse])
async def replay_aggregate_events(
    aggregate_id: str,
    aggregate_type: str,
    to_version: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Replay events up to a specific version (time-travel debugging).
    
    Args:
        aggregate_id: Aggregate identifier
        aggregate_type: Aggregate type
        to_version: Replay up to this version (None = all)
        
    Returns:
        List of events up to version
    """
    store = get_event_store(db)
    events = await store.replay(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        to_version=to_version
    )
    
    return [
        EventResponse(
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            event_type=event.event_type,
            event_data=event.event_data,
            user_id=event.user_id,
            metadata=event.metadata,
            timestamp=event.timestamp,
            version=event.version
        )
        for event in events
    ]


@router.get("/audit", response_model=AuditLogResponse)
async def get_audit_log(
    user_id: Optional[int] = Query(None),
    aggregate_type: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit log with filters.
    
    Args:
        user_id: Filter by user
        aggregate_type: Filter by aggregate type
        event_type: Filter by event type
        from_date: Start date
        to_date: End date
        limit: Maximum number of events
        
    Returns:
        Audit log with events
    """
    store = get_event_store(db)
    events = await store.get_audit_log(
        user_id=user_id,
        aggregate_type=aggregate_type,
        event_type=event_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )
    
    event_responses = [
        EventResponse(
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            event_type=event.event_type,
            event_data=event.event_data,
            user_id=event.user_id,
            metadata=event.metadata,
            timestamp=event.timestamp,
            version=event.version
        )
        for event in events
    ]
    
    return AuditLogResponse(
        events=event_responses,
        total_count=len(event_responses)
    )
