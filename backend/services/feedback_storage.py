"""
Feedback storage abstraction layer.

Supports multiple backends: memory (dev), redis (prod), database (future).
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class FeedbackStorage(ABC):
    """Abstract base class for feedback storage."""

    @abstractmethod
    async def save(self, feedback: Dict[str, Any]) -> str:
        """Save feedback and return feedback_id."""
        pass

    @abstractmethod
    async def get_by_query(self, query_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a query."""
        pass

    @abstractmethod
    async def get_stats(
        self, time_window_hours: int, mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get feedback statistics."""
        pass

    @abstractmethod
    async def delete(self, feedback_id: str) -> bool:
        """Delete feedback by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all feedback (for testing/debugging)."""
        pass


class MemoryFeedbackStorage(FeedbackStorage):
    """In-memory storage for development."""

    def __init__(self):
        self._storage: List[Dict[str, Any]] = []
        logger.info("Initialized MemoryFeedbackStorage")

    async def save(self, feedback: Dict[str, Any]) -> str:
        self._storage.append(feedback)
        logger.debug(f"Saved feedback {feedback['feedback_id']} to memory")
        return feedback["feedback_id"]

    async def get_by_query(self, query_id: str) -> List[Dict[str, Any]]:
        return [f for f in self._storage if f["query_id"] == query_id]

    async def get_stats(
        self, time_window_hours: int, mode: Optional[str] = None
    ) -> Dict[str, Any]:
        threshold = datetime.now().timestamp() - (time_window_hours * 3600)

        filtered = [
            f
            for f in self._storage
            if datetime.fromisoformat(f["timestamp"]).timestamp() >= threshold
            and (mode is None or f.get("mode_used") == mode)
        ]

        total = len(filtered)
        thumbs_up = sum(1 for f in filtered if f["feedback_type"] == "thumbs_up")
        thumbs_down = total - thumbs_up

        # Category breakdown
        category_counts = {}
        for f in filtered:
            if f["feedback_type"] == "thumbs_down":
                for cat in f.get("categories", []):
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        # Mode breakdown
        mode_breakdown = {}
        for f in filtered:
            m = f.get("mode_used", "unknown")
            if m not in mode_breakdown:
                mode_breakdown[m] = {"thumbs_up": 0, "thumbs_down": 0}

            if f["feedback_type"] == "thumbs_up":
                mode_breakdown[m]["thumbs_up"] += 1
            else:
                mode_breakdown[m]["thumbs_down"] += 1

        return {
            "total_feedback": total,
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "satisfaction_rate": thumbs_up / total if total > 0 else 0.0,
            "category_breakdown": category_counts,
            "mode_breakdown": mode_breakdown,
        }

    async def delete(self, feedback_id: str) -> bool:
        original_len = len(self._storage)
        self._storage = [f for f in self._storage if f["feedback_id"] != feedback_id]
        return len(self._storage) < original_len

    async def get_all(self) -> List[Dict[str, Any]]:
        return self._storage.copy()

    def clear(self):
        """Clear all feedback (for testing)."""
        self._storage.clear()


class RedisFeedbackStorage(FeedbackStorage):
    """Redis-based storage for production."""

    def __init__(self, redis_client: redis.Redis, ttl: int = 7776000):  # 90 days
        self.redis = redis_client
        self.ttl = ttl
        self.prefix = "feedback:"
        logger.info(f"Initialized RedisFeedbackStorage with TTL={ttl}s")

    async def save(self, feedback: Dict[str, Any]) -> str:
        feedback_id = feedback["feedback_id"]
        key = f"{self.prefix}{feedback_id}"

        # Store feedback
        await self.redis.setex(key, self.ttl, json.dumps(feedback, default=str))

        # Add to query index
        query_key = f"{self.prefix}query:{feedback['query_id']}"
        await self.redis.sadd(query_key, feedback_id)
        await self.redis.expire(query_key, self.ttl)

        # Add to time-series index
        timestamp = datetime.fromisoformat(feedback["timestamp"]).timestamp()
        await self.redis.zadd(f"{self.prefix}timeline", {feedback_id: timestamp})

        logger.info(f"Saved feedback {feedback_id} to Redis")
        return feedback_id

    async def get_by_query(self, query_id: str) -> List[Dict[str, Any]]:
        query_key = f"{self.prefix}query:{query_id}"
        feedback_ids = await self.redis.smembers(query_key)

        feedbacks = []
        for fid in feedback_ids:
            key = f"{self.prefix}{fid.decode() if isinstance(fid, bytes) else fid}"
            data = await self.redis.get(key)
            if data:
                feedbacks.append(json.loads(data))

        return feedbacks

    async def get_stats(
        self, time_window_hours: int, mode: Optional[str] = None
    ) -> Dict[str, Any]:
        threshold = datetime.now().timestamp() - (time_window_hours * 3600)

        # Get feedback IDs in time window
        feedback_ids = await self.redis.zrangebyscore(
            f"{self.prefix}timeline", threshold, "+inf"
        )

        # Load feedback data
        feedbacks = []
        for fid in feedback_ids:
            key = f"{self.prefix}{fid.decode() if isinstance(fid, bytes) else fid}"
            data = await self.redis.get(key)
            if data:
                feedback = json.loads(data)
                if mode is None or feedback.get("mode_used") == mode:
                    feedbacks.append(feedback)

        # Calculate stats
        total = len(feedbacks)
        thumbs_up = sum(1 for f in feedbacks if f["feedback_type"] == "thumbs_up")
        thumbs_down = total - thumbs_up

        # Category breakdown
        category_counts = {}
        for f in feedbacks:
            if f["feedback_type"] == "thumbs_down":
                for cat in f.get("categories", []):
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        # Mode breakdown
        mode_breakdown = {}
        for f in feedbacks:
            m = f.get("mode_used", "unknown")
            if m not in mode_breakdown:
                mode_breakdown[m] = {"thumbs_up": 0, "thumbs_down": 0}

            if f["feedback_type"] == "thumbs_up":
                mode_breakdown[m]["thumbs_up"] += 1
            else:
                mode_breakdown[m]["thumbs_down"] += 1

        return {
            "total_feedback": total,
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "satisfaction_rate": thumbs_up / total if total > 0 else 0.0,
            "category_breakdown": category_counts,
            "mode_breakdown": mode_breakdown,
        }

    async def delete(self, feedback_id: str) -> bool:
        key = f"{self.prefix}{feedback_id}"

        # Get feedback to find query_id
        data = await self.redis.get(key)
        if not data:
            return False

        feedback = json.loads(data)

        # Remove from query index
        query_key = f"{self.prefix}query:{feedback['query_id']}"
        await self.redis.srem(query_key, feedback_id)

        # Remove from timeline
        await self.redis.zrem(f"{self.prefix}timeline", feedback_id)

        # Delete feedback
        result = await self.redis.delete(key)

        logger.info(f"Deleted feedback {feedback_id} from Redis")
        return result > 0

    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all feedback (for testing/debugging)."""
        # Get all feedback IDs from timeline
        feedback_ids = await self.redis.zrange(f"{self.prefix}timeline", 0, -1)

        feedbacks = []
        for fid in feedback_ids:
            key = f"{self.prefix}{fid.decode() if isinstance(fid, bytes) else fid}"
            data = await self.redis.get(key)
            if data:
                feedbacks.append(json.loads(data))

        return feedbacks


# Singleton instance
_feedback_storage: Optional[FeedbackStorage] = None


def get_feedback_storage() -> FeedbackStorage:
    """Get singleton feedback storage instance."""
    global _feedback_storage
    if _feedback_storage is None:
        # Default to memory storage
        _feedback_storage = MemoryFeedbackStorage()
    return _feedback_storage


def initialize_feedback_storage(
    backend: str = "memory",
    redis_client: Optional[redis.Redis] = None,
    ttl: int = 7776000,  # 90 days
) -> FeedbackStorage:
    """
    Initialize singleton feedback storage.

    Args:
        backend: "memory" or "redis"
        redis_client: Redis client (required for redis backend)
        ttl: TTL in seconds (default: 90 days)

    Returns:
        FeedbackStorage instance
    """
    global _feedback_storage

    if backend == "redis":
        if redis_client is None:
            raise ValueError("Redis client required for redis backend")
        _feedback_storage = RedisFeedbackStorage(redis_client, ttl)
    else:
        _feedback_storage = MemoryFeedbackStorage()

    logger.info(f"Initialized feedback storage with backend: {backend}")
    return _feedback_storage
