"""
Quota and Rate Limiting for Agent Builder.

Manages execution quotas, token usage limits, and resource constraints.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum

from redis.asyncio import Redis
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.db.models.user import User
from backend.db.models.agent_builder import AgentExecution
from backend.core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class QuotaTier(str, Enum):
    """User quota tiers."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class QuotaLimits:
    """Quota limits for different tiers."""
    
    LIMITS = {
        QuotaTier.FREE: {
            "executions_per_day": 10,
            "executions_per_month": 100,
            "tokens_per_day": 10000,
            "tokens_per_month": 100000,
            "max_execution_duration_seconds": 60,
            "max_concurrent_executions": 1,
            "max_agents": 5,
            "max_workflows": 3,
            "max_knowledgebases": 2,
        },
        QuotaTier.BASIC: {
            "executions_per_day": 100,
            "executions_per_month": 2000,
            "tokens_per_day": 100000,
            "tokens_per_month": 2000000,
            "max_execution_duration_seconds": 180,
            "max_concurrent_executions": 3,
            "max_agents": 20,
            "max_workflows": 10,
            "max_knowledgebases": 10,
        },
        QuotaTier.PREMIUM: {
            "executions_per_day": 1000,
            "executions_per_month": 20000,
            "tokens_per_day": 1000000,
            "tokens_per_month": 20000000,
            "max_execution_duration_seconds": 300,
            "max_concurrent_executions": 10,
            "max_agents": 100,
            "max_workflows": 50,
            "max_knowledgebases": 50,
        },
        QuotaTier.ENTERPRISE: {
            "executions_per_day": -1,  # Unlimited
            "executions_per_month": -1,
            "tokens_per_day": -1,
            "tokens_per_month": -1,
            "max_execution_duration_seconds": 600,
            "max_concurrent_executions": 50,
            "max_agents": -1,
            "max_workflows": -1,
            "max_knowledgebases": -1,
        }
    }
    
    @classmethod
    def get_limits(cls, tier: QuotaTier) -> Dict[str, int]:
        """Get limits for a tier."""
        return cls.LIMITS.get(tier, cls.LIMITS[QuotaTier.FREE])


class QuotaManager:
    """
    Manages user quotas and resource limits.
    
    Features:
    - Execution count tracking
    - Token usage tracking
    - Resource limit enforcement
    - Quota reset scheduling
    """
    
    def __init__(
        self,
        db: Session,
        redis_client: Redis,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """
        Initialize quota manager.
        
        Args:
            db: Database session
            redis_client: Redis client for tracking
            rate_limiter: Optional rate limiter instance
        """
        self.db = db
        self.redis = redis_client
        self.rate_limiter = rate_limiter or RateLimiter(
            redis_client=redis_client,
            requests_per_minute=100,
            requests_per_hour=1000,
            requests_per_day=10000
        )
        
        logger.info("QuotaManager initialized")
    
    def get_user_tier(self, user: User) -> QuotaTier:
        """
        Get user's quota tier.
        
        Args:
            user: User object
            
        Returns:
            QuotaTier
        """
        # Map user role to quota tier
        role_to_tier = {
            "user": QuotaTier.FREE,
            "basic": QuotaTier.BASIC,
            "premium": QuotaTier.PREMIUM,
            "admin": QuotaTier.ENTERPRISE,
            "enterprise": QuotaTier.ENTERPRISE,
        }
        
        return role_to_tier.get(user.role, QuotaTier.FREE)
    
    def get_user_limits(self, user: User) -> Dict[str, int]:
        """
        Get user's quota limits.
        
        Args:
            user: User object
            
        Returns:
            Dictionary of limits
        """
        tier = self.get_user_tier(user)
        return QuotaLimits.get_limits(tier)
    
    # ========================================================================
    # Execution Quota
    # ========================================================================
    
    async def check_execution_quota(
        self,
        user_id: str,
        user: Optional[User] = None
    ) -> bool:
        """
        Check if user has execution quota available.
        
        Args:
            user_id: User ID
            user: Optional User object (fetched if not provided)
            
        Returns:
            True if quota available, False otherwise
            
        Raises:
            HTTPException: If quota exceeded
        """
        if user is None:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        limits = self.get_user_limits(user)
        
        # Check daily quota
        daily_count = await self._get_execution_count(user_id, "day")
        daily_limit = limits["executions_per_day"]
        
        if daily_limit > 0 and daily_count >= daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily execution quota exceeded ({daily_limit} executions/day)"
            )
        
        # Check monthly quota
        monthly_count = await self._get_execution_count(user_id, "month")
        monthly_limit = limits["executions_per_month"]
        
        if monthly_limit > 0 and monthly_count >= monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly execution quota exceeded ({monthly_limit} executions/month)"
            )
        
        return True
    
    async def increment_execution_count(self, user_id: str):
        """
        Increment execution count for user.
        
        Args:
            user_id: User ID
        """
        now = datetime.now(timezone.utc)
        
        # Increment daily counter
        daily_key = f"quota:executions:daily:{user_id}:{now.strftime('%Y%m%d')}"
        await self.redis.incr(daily_key)
        await self.redis.expire(daily_key, 86400)  # 24 hours
        
        # Increment monthly counter
        monthly_key = f"quota:executions:monthly:{user_id}:{now.strftime('%Y%m')}"
        await self.redis.incr(monthly_key)
        await self.redis.expire(monthly_key, 2592000)  # 30 days
    
    async def _get_execution_count(
        self,
        user_id: str,
        period: str
    ) -> int:
        """
        Get execution count for period.
        
        Args:
            user_id: User ID
            period: "day" or "month"
            
        Returns:
            Execution count
        """
        now = datetime.now(timezone.utc)
        
        if period == "day":
            key = f"quota:executions:daily:{user_id}:{now.strftime('%Y%m%d')}"
        elif period == "month":
            key = f"quota:executions:monthly:{user_id}:{now.strftime('%Y%m')}"
        else:
            raise ValueError(f"Invalid period: {period}")
        
        count = await self.redis.get(key)
        return int(count) if count else 0
    
    # ========================================================================
    # Token Quota
    # ========================================================================
    
    async def check_token_quota(
        self,
        user_id: str,
        tokens_needed: int,
        user: Optional[User] = None
    ) -> bool:
        """
        Check if user has token quota available.
        
        Args:
            user_id: User ID
            tokens_needed: Number of tokens needed
            user: Optional User object
            
        Returns:
            True if quota available, False otherwise
            
        Raises:
            HTTPException: If quota exceeded
        """
        if user is None:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        limits = self.get_user_limits(user)
        
        # Check daily quota
        daily_usage = await self._get_token_usage(user_id, "day")
        daily_limit = limits["tokens_per_day"]
        
        if daily_limit > 0 and (daily_usage + tokens_needed) > daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily token quota exceeded ({daily_limit} tokens/day)"
            )
        
        # Check monthly quota
        monthly_usage = await self._get_token_usage(user_id, "month")
        monthly_limit = limits["tokens_per_month"]
        
        if monthly_limit > 0 and (monthly_usage + tokens_needed) > monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly token quota exceeded ({monthly_limit} tokens/month)"
            )
        
        return True
    
    async def increment_token_usage(
        self,
        user_id: str,
        tokens_used: int
    ):
        """
        Increment token usage for user.
        
        Args:
            user_id: User ID
            tokens_used: Number of tokens used
        """
        now = datetime.now(timezone.utc)
        
        # Increment daily counter
        daily_key = f"quota:tokens:daily:{user_id}:{now.strftime('%Y%m%d')}"
        await self.redis.incrby(daily_key, tokens_used)
        await self.redis.expire(daily_key, 86400)
        
        # Increment monthly counter
        monthly_key = f"quota:tokens:monthly:{user_id}:{now.strftime('%Y%m')}"
        await self.redis.incrby(monthly_key, tokens_used)
        await self.redis.expire(monthly_key, 2592000)
    
    async def _get_token_usage(
        self,
        user_id: str,
        period: str
    ) -> int:
        """
        Get token usage for period.
        
        Args:
            user_id: User ID
            period: "day" or "month"
            
        Returns:
            Token usage count
        """
        now = datetime.now(timezone.utc)
        
        if period == "day":
            key = f"quota:tokens:daily:{user_id}:{now.strftime('%Y%m%d')}"
        elif period == "month":
            key = f"quota:tokens:monthly:{user_id}:{now.strftime('%Y%m')}"
        else:
            raise ValueError(f"Invalid period: {period}")
        
        usage = await self.redis.get(key)
        return int(usage) if usage else 0
    
    # ========================================================================
    # Resource Limits
    # ========================================================================
    
    async def check_resource_limit(
        self,
        user_id: str,
        resource_type: str,
        user: Optional[User] = None
    ) -> bool:
        """
        Check if user can create more resources.
        
        Args:
            user_id: User ID
            resource_type: "agents", "workflows", or "knowledgebases"
            user: Optional User object
            
        Returns:
            True if limit not reached
            
        Raises:
            HTTPException: If limit exceeded
        """
        if user is None:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        limits = self.get_user_limits(user)
        limit_key = f"max_{resource_type}"
        
        if limit_key not in limits:
            raise ValueError(f"Invalid resource type: {resource_type}")
        
        limit = limits[limit_key]
        
        # -1 means unlimited
        if limit < 0:
            return True
        
        # Count current resources
        current_count = await self._count_resources(user_id, resource_type)
        
        if current_count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Resource limit exceeded ({limit} {resource_type} maximum)"
            )
        
        return True
    
    async def _count_resources(
        self,
        user_id: str,
        resource_type: str
    ) -> int:
        """
        Count user's resources.
        
        Args:
            user_id: User ID
            resource_type: Resource type
            
        Returns:
            Resource count
        """
        from backend.db.models.agent_builder import Agent, Workflow, Knowledgebase
        
        if resource_type == "agents":
            return self.db.query(Agent).filter(
                Agent.user_id == user_id,
                Agent.deleted_at.is_(None)
            ).count()
        elif resource_type == "workflows":
            return self.db.query(Workflow).filter(
                Workflow.user_id == user_id
            ).count()
        elif resource_type == "knowledgebases":
            return self.db.query(Knowledgebase).filter(
                Knowledgebase.user_id == user_id
            ).count()
        else:
            return 0
    
    # ========================================================================
    # Concurrent Execution Limits
    # ========================================================================
    
    async def check_concurrent_execution_limit(
        self,
        user_id: str,
        user: Optional[User] = None
    ) -> bool:
        """
        Check if user can start another concurrent execution.
        
        Args:
            user_id: User ID
            user: Optional User object
            
        Returns:
            True if limit not reached
            
        Raises:
            HTTPException: If limit exceeded
        """
        if user is None:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        limits = self.get_user_limits(user)
        max_concurrent = limits["max_concurrent_executions"]
        
        # Count running executions
        running_count = self.db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.status == "running"
        ).count()
        
        if running_count >= max_concurrent:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Concurrent execution limit exceeded ({max_concurrent} maximum)"
            )
        
        return True
    
    # ========================================================================
    # Quota Information
    # ========================================================================
    
    async def get_quota_usage(
        self,
        user_id: str,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Get user's quota usage information.
        
        Args:
            user_id: User ID
            user: Optional User object
            
        Returns:
            Dictionary with quota usage
        """
        if user is None:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        tier = self.get_user_tier(user)
        limits = self.get_user_limits(user)
        
        # Get current usage
        daily_executions = await self._get_execution_count(user_id, "day")
        monthly_executions = await self._get_execution_count(user_id, "month")
        daily_tokens = await self._get_token_usage(user_id, "day")
        monthly_tokens = await self._get_token_usage(user_id, "month")
        
        # Count resources
        agent_count = await self._count_resources(user_id, "agents")
        workflow_count = await self._count_resources(user_id, "workflows")
        kb_count = await self._count_resources(user_id, "knowledgebases")
        
        # Count running executions
        running_count = self.db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.status == "running"
        ).count()
        
        return {
            "tier": tier.value,
            "limits": limits,
            "usage": {
                "executions": {
                    "daily": {
                        "used": daily_executions,
                        "limit": limits["executions_per_day"],
                        "remaining": max(0, limits["executions_per_day"] - daily_executions) if limits["executions_per_day"] > 0 else -1
                    },
                    "monthly": {
                        "used": monthly_executions,
                        "limit": limits["executions_per_month"],
                        "remaining": max(0, limits["executions_per_month"] - monthly_executions) if limits["executions_per_month"] > 0 else -1
                    }
                },
                "tokens": {
                    "daily": {
                        "used": daily_tokens,
                        "limit": limits["tokens_per_day"],
                        "remaining": max(0, limits["tokens_per_day"] - daily_tokens) if limits["tokens_per_day"] > 0 else -1
                    },
                    "monthly": {
                        "used": monthly_tokens,
                        "limit": limits["tokens_per_month"],
                        "remaining": max(0, limits["tokens_per_month"] - monthly_tokens) if limits["tokens_per_month"] > 0 else -1
                    }
                },
                "resources": {
                    "agents": {
                        "used": agent_count,
                        "limit": limits["max_agents"]
                    },
                    "workflows": {
                        "used": workflow_count,
                        "limit": limits["max_workflows"]
                    },
                    "knowledgebases": {
                        "used": kb_count,
                        "limit": limits["max_knowledgebases"]
                    }
                },
                "concurrent_executions": {
                    "running": running_count,
                    "limit": limits["max_concurrent_executions"]
                }
            }
        }
