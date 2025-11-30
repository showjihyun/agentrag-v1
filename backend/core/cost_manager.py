"""
LLM Cost Tracking and Management System

Provides real-time cost tracking, budgeting, and optimization recommendations.
"""

import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

import redis.asyncio as redis


logger = logging.getLogger(__name__)


@dataclass
class CostEntry:
    """Cost entry data."""
    
    user_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: Decimal
    timestamp: str
    request_id: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["cost"] = float(self.cost)
        return data


class CostManager:
    """
    LLM cost tracking and budgeting system.
    
    Features:
    - Real-time cost tracking
    - Budget alerts
    - Cost optimization recommendations
    - Provider comparison
    - Usage analytics
    """
    
    # Token costs (per 1K tokens) - Update with actual pricing
    PRICING = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        },
        "anthropic": {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
        },
        "ollama": {
            "llama3.1": {"input": 0.0, "output": 0.0},  # Local model
            "mistral": {"input": 0.0, "output": 0.0}
        }
    }
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize Cost Manager.
        
        Args:
            redis_client: Redis client
        """
        self.redis = redis_client
    
    async def track_usage(
        self,
        user_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        request_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Decimal:
        """
        Track LLM usage and calculate cost.
        
        Args:
            user_id: User ID
            provider: LLM provider
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
            request_id: Request ID
            metadata: Additional metadata
            
        Returns:
            Cost in USD
        """
        # Calculate cost
        cost = self._calculate_cost(provider, model, input_tokens, output_tokens)
        
        # Create cost entry
        entry = CostEntry(
            user_id=user_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id,
            metadata=metadata
        )
        
        # Update user usage
        await self._update_user_usage(entry)
        
        # Check budget
        await self._check_budget(user_id, cost)
        
        # Log cost
        logger.info(
            f"Cost tracked: ${cost:.4f}",
            extra={
                "user_id": user_id,
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": float(cost)
            }
        )
        
        return cost
    
    def _calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """Calculate cost based on token usage."""
        
        if provider not in self.PRICING:
            logger.warning(f"Unknown provider: {provider}, cost set to 0")
            return Decimal(0)
        
        if model not in self.PRICING[provider]:
            logger.warning(f"Unknown model: {model}, cost set to 0")
            return Decimal(0)
        
        pricing = self.PRICING[provider][model]
        
        input_cost = Decimal(input_tokens / 1000 * pricing["input"])
        output_cost = Decimal(output_tokens / 1000 * pricing["output"])
        
        return input_cost + output_cost
    
    async def _update_user_usage(self, entry: CostEntry):
        """Update user usage statistics."""
        
        # Monthly usage
        month_key = f"cost:user:{entry.user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        await self.redis.incrbyfloat(month_key, float(entry.cost))
        await self.redis.expire(month_key, 86400 * 90)  # 90 days
        
        # Daily usage
        day_key = f"cost:user:{entry.user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        await self.redis.incrbyfloat(day_key, float(entry.cost))
        await self.redis.expire(day_key, 86400 * 30)  # 30 days
        
        # Provider usage
        provider_key = f"cost:user:{entry.user_id}:provider:{entry.provider}"
        await self.redis.incrbyfloat(provider_key, float(entry.cost))
        
        # Model usage
        model_key = f"cost:user:{entry.user_id}:model:{entry.provider}:{entry.model}"
        await self.redis.incrbyfloat(model_key, float(entry.cost))
        
        # Token usage
        token_key = f"tokens:user:{entry.user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        await self.redis.hincrby(token_key, "input", entry.input_tokens)
        await self.redis.hincrby(token_key, "output", entry.output_tokens)
        await self.redis.expire(token_key, 86400 * 90)
    
    async def _check_budget(self, user_id: str, cost: Decimal):
        """Check if user exceeds budget."""
        
        # Get user budget
        budget_key = f"budget:user:{user_id}"
        budget = await self.redis.get(budget_key)
        
        if not budget:
            return
        
        budget = Decimal(budget.decode() if isinstance(budget, bytes) else budget)
        
        # Get current month usage
        month_key = f"cost:user:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        current_usage = await self.redis.get(month_key)
        
        if not current_usage:
            return
        
        current_usage = Decimal(
            current_usage.decode() if isinstance(current_usage, bytes) else current_usage
        )
        
        # Check thresholds
        usage_percent = (current_usage / budget) * 100
        
        if usage_percent >= 100:
            await self._send_budget_alert(
                user_id,
                "exceeded",
                current_usage,
                budget
            )
        elif usage_percent >= 90:
            await self._send_budget_alert(
                user_id,
                "warning_90",
                current_usage,
                budget
            )
        elif usage_percent >= 75:
            await self._send_budget_alert(
                user_id,
                "warning_75",
                current_usage,
                budget
            )
    
    async def _send_budget_alert(
        self,
        user_id: str,
        alert_type: str,
        current_usage: Decimal,
        budget: Decimal
    ):
        """Send budget alert."""
        
        # Store alert
        alert_key = f"alert:user:{user_id}:{alert_type}:{datetime.utcnow().strftime('%Y-%m')}"
        
        # Check if already sent
        exists = await self.redis.exists(alert_key)
        if exists:
            return
        
        # Mark as sent
        await self.redis.setex(alert_key, 86400 * 30, "1")
        
        # Log alert
        logger.warning(
            f"Budget alert: {alert_type}",
            extra={
                "user_id": user_id,
                "current_usage": float(current_usage),
                "budget": float(budget),
                "usage_percent": float((current_usage / budget) * 100)
            }
        )
        
        # Send notifications
        await self._send_budget_notification(user_id, alert_type, current_usage, budget)
    
    async def _send_budget_notification(
        self,
        user_id: str,
        alert_type: str,
        current_usage: Decimal,
        budget: Decimal
    ):
        """Send budget alert notification via multiple channels."""
        usage_percent = (current_usage / budget) * 100
        
        # Prepare notification content
        subject = f"Budget Alert: {alert_type.replace('_', ' ').title()}"
        message = (
            f"Your usage has reached {usage_percent:.1f}% of your budget.\n"
            f"Current usage: ${current_usage:.2f}\n"
            f"Budget limit: ${budget:.2f}"
        )
        
        # Try email notification
        try:
            from backend.services.notification_service import get_notification_service
            notification_service = get_notification_service()
            
            await notification_service.send_notification(
                user_id=user_id,
                title=subject,
                message=message,
                notification_type="budget_alert",
                priority="high" if alert_type == "budget_exceeded" else "medium"
            )
        except Exception as e:
            logger.debug(f"Notification service unavailable: {e}")
        
        # Try Slack webhook if configured
        try:
            from backend.config import settings
            import httpx
            
            webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
            if webhook_url:
                emoji = "🚨" if alert_type == "budget_exceeded" else "⚠️"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(webhook_url, json={
                        "text": f"{emoji} *{subject}*\n{message}"
                    })
        except Exception as e:
            logger.debug(f"Slack notification failed: {e}")
    
    async def set_budget(
        self,
        user_id: str,
        budget: Decimal,
        period: str = "monthly"
    ):
        """
        Set user budget.
        
        Args:
            user_id: User ID
            budget: Budget amount in USD
            period: Budget period (monthly, daily)
        """
        budget_key = f"budget:user:{user_id}"
        await self.redis.set(budget_key, str(budget))
        
        logger.info(
            f"Budget set for user {user_id}: ${budget}",
            extra={"user_id": user_id, "budget": float(budget), "period": period}
        )
    
    async def get_usage(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get user usage statistics.
        
        Args:
            user_id: User ID
            start_date: Start date (default: current month)
            end_date: End date (default: now)
            
        Returns:
            Usage statistics
        """
        if not start_date:
            start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get monthly usage
        month_key = f"cost:user:{user_id}:{start_date.strftime('%Y-%m')}"
        monthly_cost = await self.redis.get(month_key)
        monthly_cost = Decimal(
            monthly_cost.decode() if monthly_cost and isinstance(monthly_cost, bytes) else monthly_cost or 0
        )
        
        # Get token usage
        token_key = f"tokens:user:{user_id}:{start_date.strftime('%Y-%m')}"
        tokens = await self.redis.hgetall(token_key)
        
        input_tokens = int(tokens.get(b"input", 0))
        output_tokens = int(tokens.get(b"output", 0))
        
        # Get budget
        budget_key = f"budget:user:{user_id}"
        budget = await self.redis.get(budget_key)
        budget = Decimal(
            budget.decode() if budget and isinstance(budget, bytes) else budget or 0
        )
        
        # Calculate remaining budget
        remaining = budget - monthly_cost if budget > 0 else None
        usage_percent = (monthly_cost / budget * 100) if budget > 0 else None
        
        return {
            "user_id": user_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "cost": {
                "total": float(monthly_cost),
                "budget": float(budget) if budget else None,
                "remaining": float(remaining) if remaining is not None else None,
                "usage_percent": float(usage_percent) if usage_percent is not None else None
            },
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            }
        }
    
    async def get_cost_breakdown(
        self,
        user_id: str,
        period: str = "month"
    ) -> Dict:
        """
        Get cost breakdown by provider and model.
        
        Args:
            user_id: User ID
            period: Period (month, day)
            
        Returns:
            Cost breakdown
        """
        breakdown = {
            "by_provider": {},
            "by_model": {}
        }
        
        # Get provider costs
        for provider in self.PRICING.keys():
            provider_key = f"cost:user:{user_id}:provider:{provider}"
            cost = await self.redis.get(provider_key)
            
            if cost:
                cost = float(cost.decode() if isinstance(cost, bytes) else cost)
                breakdown["by_provider"][provider] = cost
        
        # Get model costs
        for provider, models in self.PRICING.items():
            for model in models.keys():
                model_key = f"cost:user:{user_id}:model:{provider}:{model}"
                cost = await self.redis.get(model_key)
                
                if cost:
                    cost = float(cost.decode() if isinstance(cost, bytes) else cost)
                    breakdown["by_model"][f"{provider}/{model}"] = cost
        
        return breakdown
    
    async def get_optimization_recommendations(
        self,
        user_id: str
    ) -> List[Dict]:
        """
        Get cost optimization recommendations.
        
        Args:
            user_id: User ID
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Get usage breakdown
        breakdown = await self.get_cost_breakdown(user_id)
        
        # Analyze provider usage
        if breakdown["by_provider"]:
            most_expensive = max(
                breakdown["by_provider"].items(),
                key=lambda x: x[1]
            )
            
            provider, cost = most_expensive
            
            # Recommend cheaper alternatives
            if provider == "openai" and cost > 10:
                recommendations.append({
                    "type": "provider_switch",
                    "priority": "high",
                    "message": f"Consider switching from OpenAI to Anthropic Claude Haiku for cost savings",
                    "estimated_savings": "up to 90%",
                    "current_cost": cost
                })
            
            elif provider == "anthropic" and "claude-3-opus" in str(breakdown["by_model"]):
                recommendations.append({
                    "type": "model_downgrade",
                    "priority": "medium",
                    "message": "Consider using Claude Sonnet or Haiku for non-critical tasks",
                    "estimated_savings": "up to 80%",
                    "current_cost": cost
                })
        
        # Recommend caching
        usage = await self.get_usage(user_id)
        if usage["cost"]["total"] > 5:
            recommendations.append({
                "type": "enable_caching",
                "priority": "high",
                "message": "Enable semantic prompt caching to reduce costs by 30-50%",
                "estimated_savings": "30-50%"
            })
        
        # Recommend batching
        if usage["tokens"]["total"] > 100000:
            recommendations.append({
                "type": "enable_batching",
                "priority": "medium",
                "message": "Enable request batching to reduce costs by up to 50%",
                "estimated_savings": "up to 50%"
            })
        
        return recommendations


# Global cost manager instance
_cost_manager: Optional[CostManager] = None


def get_cost_manager() -> CostManager:
    """Get global cost manager instance."""
    global _cost_manager
    if _cost_manager is None:
        raise RuntimeError("Cost manager not initialized")
    return _cost_manager


async def initialize_cost_manager(
    redis_client: redis.Redis
) -> CostManager:
    """
    Initialize global cost manager.
    
    Args:
        redis_client: Redis client
        
    Returns:
        Cost manager instance
    """
    global _cost_manager
    if _cost_manager is None:
        _cost_manager = CostManager(redis_client)
    return _cost_manager


def cleanup_cost_manager():
    """Cleanup global cost manager."""
    global _cost_manager
    _cost_manager = None
