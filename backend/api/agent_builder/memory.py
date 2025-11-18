"""
Memory Management API

Provides endpoints for managing agent memory (STM, LTM, episodic, semantic).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from uuid import UUID
from backend.core.dependencies import get_db
from backend.db.repositories.memory_repository import MemoryRepository
from backend.services.agent_builder.memory_service import MemoryService
from backend.exceptions.agent_builder import (
    MemoryNotFoundException,
    MemoryQuotaExceededError,
    InvalidMemoryTypeError
)
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/agents/{agent_id}/memory", tags=["Memory Management"])


# Simple in-memory cache for stats (5 minutes TTL)
_stats_cache = {}
_cache_ttl = 300  # 5 minutes


def get_cached_stats(agent_id: str) -> Optional[Dict]:
    """Get cached stats if available and not expired"""
    if agent_id in _stats_cache:
        cached_data, timestamp = _stats_cache[agent_id]
        if (datetime.utcnow() - timestamp).total_seconds() < _cache_ttl:
            return cached_data
        else:
            del _stats_cache[agent_id]
    return None


def set_cached_stats(agent_id: str, data: Dict):
    """Cache stats data"""
    _stats_cache[agent_id] = (data, datetime.utcnow())


# Models
class MemoryStats(BaseModel):
    short_term: Dict[str, Any] = Field(default_factory=lambda: {"count": 0, "size_mb": 0})
    long_term: Dict[str, Any] = Field(default_factory=lambda: {"count": 0, "size_mb": 0})
    episodic: Dict[str, Any] = Field(default_factory=lambda: {"count": 0, "size_mb": 0})
    semantic: Dict[str, Any] = Field(default_factory=lambda: {"count": 0, "size_mb": 0})
    total_size_mb: float = 0
    compression_ratio: float = 0
    retrieval_speed_ms: float = 0


class Memory(BaseModel):
    id: str
    type: str  # short_term, long_term, episodic, semantic
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance: str  # high, medium, low
    access_count: int = 0
    created_at: str
    last_accessed_at: Optional[str] = None


class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    memory_type: Optional[str] = None


class MemorySearchResult(BaseModel):
    memory: Memory
    relevance_score: float


class MemoryTimelineEvent(BaseModel):
    id: str
    type: str  # created, accessed, updated, consolidated
    memory_id: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySettings(BaseModel):
    short_term_retention_hours: int = Field(default=24, ge=1, le=168)
    auto_cleanup: bool = True
    auto_consolidation: bool = True
    consolidation_threshold: int = Field(default=100, ge=10, le=1000)
    enable_compression: bool = True
    max_memory_size_mb: int = Field(default=1000, ge=100, le=10000)
    importance_threshold: str = "low"  # low, medium, high


# Endpoints
@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats(
    agent_id: str,
    db: Session = Depends(get_db),
    use_cache: bool = Query(True, description="Use cached data if available")
):
    """
    Get memory statistics for an agent (cached for 5 minutes)
    """
    try:
        # Check cache first
        if use_cache:
            cached = get_cached_stats(agent_id)
            if cached:
                logger.debug(f"Returning cached stats for agent {agent_id}")
                return MemoryStats(**cached)
        
        # Get from database
        repository = MemoryRepository(db)
        stats = repository.get_stats(UUID(agent_id))
        
        # Cache the result
        set_cached_stats(agent_id, stats)
        
        return MemoryStats(**stats)
        
    except ValueError as e:
        logger.error(f"Invalid agent_id: {e}")
        raise HTTPException(status_code=400, detail="Invalid agent ID")
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[Memory])
async def get_memories(
    agent_id: str,
    memory_type: Optional[str] = Query(None, pattern="^(short_term|long_term|episodic|semantic)$"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get memories for an agent with optional type filtering
    """
    try:
        # Mock data - replace with actual DB queries
        memories = []
        types = [memory_type] if memory_type else ["short_term", "long_term", "episodic", "semantic"]
        
        for i in range(min(limit, 20)):
            mem_type = types[i % len(types)]
            memories.append(Memory(
                id=f"mem-{i}",
                type=mem_type,
                content=f"Sample memory content {i}",
                metadata={"source": "user_interaction", "context": "chat"},
                importance=["high", "medium", "low"][i % 3],
                access_count=i * 3,
                created_at=(datetime.utcnow() - timedelta(days=i)).isoformat(),
                last_accessed_at=(datetime.utcnow() - timedelta(hours=i)).isoformat()
            ))
        
        return memories
        
    except Exception as e:
        logger.error(f"Failed to get memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    agent_id: str,
    memory_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a specific memory
    """
    try:
        # In production, delete from DB
        logger.info(f"Deleted memory {memory_id} for agent {agent_id}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[MemorySearchResult])
async def search_memories(
    agent_id: str,
    request: MemorySearchRequest,
    db: Session = Depends(get_db)
):
    """
    Semantic search across agent memories
    """
    try:
        # Mock data - replace with actual vector search
        results = []
        for i in range(min(request.top_k, 5)):
            results.append(MemorySearchResult(
                memory=Memory(
                    id=f"mem-{i}",
                    type=request.memory_type or "semantic",
                    content=f"Memory matching '{request.query}' - result {i}",
                    metadata={"relevance": "high"},
                    importance="high",
                    access_count=10 + i,
                    created_at=(datetime.utcnow() - timedelta(days=i)).isoformat()
                ),
                relevance_score=0.95 - (i * 0.1)
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline", response_model=List[MemoryTimelineEvent])
async def get_memory_timeline(
    agent_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get memory timeline events
    """
    try:
        # Mock data - replace with actual DB queries
        events = []
        event_types = ["created", "accessed", "updated", "consolidated"]
        
        for i in range(min(limit, 20)):
            events.append(MemoryTimelineEvent(
                id=f"event-{i}",
                type=event_types[i % len(event_types)],
                memory_id=f"mem-{i}",
                timestamp=(datetime.utcnow() - timedelta(hours=i)).isoformat(),
                metadata={"user": "system", "reason": "automatic"}
            ))
        
        return events
        
    except Exception as e:
        logger.error(f"Failed to get memory timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings", response_model=MemorySettings)
async def get_memory_settings(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get memory management settings for an agent
    """
    try:
        # Mock data - replace with actual DB query
        return MemorySettings(
            short_term_retention_hours=24,
            auto_cleanup=True,
            auto_consolidation=True,
            consolidation_threshold=100,
            enable_compression=True,
            max_memory_size_mb=1000,
            importance_threshold="low"
        )
        
    except Exception as e:
        logger.error(f"Failed to get memory settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", response_model=MemorySettings)
async def update_memory_settings(
    agent_id: str,
    settings: MemorySettings,
    db: Session = Depends(get_db)
):
    """
    Update memory management settings for an agent
    """
    try:
        # In production, save to DB
        logger.info(f"Updated memory settings for agent {agent_id}")
        return settings
        
    except Exception as e:
        logger.error(f"Failed to update memory settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consolidate")
async def consolidate_memories(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually trigger memory consolidation
    """
    try:
        # In production, run consolidation process
        return {
            "success": True,
            "message": "Memory consolidation started",
            "consolidated_count": 45,
            "estimated_time_seconds": 30
        }
        
    except Exception as e:
        logger.error(f"Failed to consolidate memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
