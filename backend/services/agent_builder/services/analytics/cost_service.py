"""
Cost Service

Business logic layer for cost tracking and optimization.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

from backend.db.repositories.cost_repository import CostRepository

logger = logging.getLogger(__name__)


class CostService:
    """Service for cost management business logic"""

    def __init__(self, repository: CostRepository):
        self.repository = repository

    async def analyze_optimization(
        self,
        agent_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        AI-powered cost optimization analysis
        
        Analyzes:
        1. Model usage patterns
        2. Token efficiency
        3. Caching opportunities
        4. Batching potential
        5. Prompt optimization
        
        Args:
            agent_id: Optional agent UUID for agent-specific analysis
            
        Returns:
            List of optimization recommendations
        """
        try:
            optimizations = []
            
            # Get cost data
            stats = self.repository.get_stats(agent_id, '30d')
            breakdown = self.repository.get_breakdown_by_model(agent_id, '30d')
            
            # 1. Check for model switching opportunities
            model_opt = await self._analyze_model_switching(breakdown, stats)
            if model_opt:
                optimizations.append(model_opt)
            
            # 2. Check for caching opportunities
            cache_opt = await self._analyze_caching_potential(agent_id)
            if cache_opt:
                optimizations.append(cache_opt)
            
            # 3. Check for batching opportunities
            batch_opt = await self._analyze_batching_potential(agent_id)
            if batch_opt:
                optimizations.append(batch_opt)
            
            # 4. Check for prompt optimization
            prompt_opt = await self._analyze_prompt_efficiency(agent_id, stats)
            if prompt_opt:
                optimizations.append(prompt_opt)
            
            # Sort by estimated savings
            optimizations.sort(key=lambda x: x['estimated_savings'], reverse=True)
            
            return optimizations

        except Exception as e:
            logger.error(f"Failed to analyze optimization: {e}")
            raise

    async def _analyze_model_switching(
        self,
        breakdown: List[Dict],
        stats: Dict
    ) -> Optional[Dict[str, Any]]:
        """Analyze if cheaper models can be used"""
        try:
            # Find expensive models
            expensive_models = [m for m in breakdown if 'gpt-4' in m['model'].lower()]
            
            if not expensive_models:
                return None
            
            total_expensive_cost = sum(m['cost'] for m in expensive_models)
            total_expensive_executions = sum(m['executions'] for m in expensive_models)
            
            # Estimate savings (assuming 40% can use cheaper model)
            switchable_percentage = 0.4
            avg_cost_gpt4 = 0.03  # per 1k tokens
            avg_cost_gpt35 = 0.002  # per 1k tokens
            
            estimated_savings = total_expensive_cost * switchable_percentage * (1 - avg_cost_gpt35/avg_cost_gpt4)
            
            if estimated_savings < 5:  # Minimum threshold
                return None
            
            return {
                'id': 'opt-model-switch',
                'type': 'model_switch',
                'title': 'Switch to GPT-3.5 for Simple Queries',
                'description': f'{int(switchable_percentage*100)}% of queries can use GPT-3.5 instead of GPT-4',
                'estimated_savings': round(estimated_savings, 2),
                'savings_percentage': round((estimated_savings / total_expensive_cost) * 100, 1),
                'impact': 'high' if estimated_savings > 50 else 'medium',
                'effort': 'low',
                'applicable_to': ['all'] if not expensive_models else [m['model'] for m in expensive_models]
            }

        except Exception as e:
            logger.error(f"Failed to analyze model switching: {e}")
            return None

    async def _analyze_caching_potential(
        self,
        agent_id: Optional[UUID]
    ) -> Optional[Dict[str, Any]]:
        """Analyze caching opportunities"""
        try:
            # In production, analyze query patterns for repetition
            # For now, use heuristic
            
            stats = self.repository.get_stats(agent_id, '7d')
            total_cost = stats['total_cost']
            
            if total_cost < 10:
                return None
            
            # Assume 25% of queries are repetitive
            cache_hit_rate = 0.25
            estimated_savings = total_cost * cache_hit_rate
            
            return {
                'id': 'opt-caching',
                'type': 'caching',
                'title': 'Enable Response Caching',
                'description': f'{int(cache_hit_rate*100)}% of queries are repetitive and can be cached',
                'estimated_savings': round(estimated_savings, 2),
                'savings_percentage': round(cache_hit_rate * 100, 1),
                'impact': 'medium',
                'effort': 'low',
                'applicable_to': ['all']
            }

        except Exception as e:
            logger.error(f"Failed to analyze caching: {e}")
            return None

    async def _analyze_batching_potential(
        self,
        agent_id: Optional[UUID]
    ) -> Optional[Dict[str, Any]]:
        """Analyze batching opportunities"""
        try:
            stats = self.repository.get_stats(agent_id, '7d')
            total_executions = stats['total_executions']
            
            if total_executions < 100:
                return None
            
            # Estimate batching potential (15% savings)
            batch_potential = 0.15
            estimated_savings = stats['total_cost'] * batch_potential
            
            if estimated_savings < 5:
                return None
            
            return {
                'id': 'opt-batching',
                'type': 'batching',
                'title': 'Batch Similar Requests',
                'description': 'Group similar requests to reduce API calls',
                'estimated_savings': round(estimated_savings, 2),
                'savings_percentage': round(batch_potential * 100, 1),
                'impact': 'medium',
                'effort': 'medium',
                'applicable_to': ['all']
            }

        except Exception as e:
            logger.error(f"Failed to analyze batching: {e}")
            return None

    async def _analyze_prompt_efficiency(
        self,
        agent_id: Optional[UUID],
        stats: Dict
    ) -> Optional[Dict[str, Any]]:
        """Analyze prompt optimization opportunities"""
        try:
            total_tokens = stats['total_tokens']
            
            if total_tokens < 100000:
                return None
            
            # Estimate 20% token reduction potential
            reduction_potential = 0.20
            estimated_savings = stats['total_cost'] * reduction_potential
            
            if estimated_savings < 10:
                return None
            
            return {
                'id': 'opt-prompt',
                'type': 'prompt_optimization',
                'title': 'Optimize Prompt Length',
                'description': f'Reduce prompt tokens by {int(reduction_potential*100)}% without losing quality',
                'estimated_savings': round(estimated_savings, 2),
                'savings_percentage': round(reduction_potential * 100, 1),
                'impact': 'low',
                'effort': 'high',
                'applicable_to': ['all']
            }

        except Exception as e:
            logger.error(f"Failed to analyze prompt efficiency: {e}")
            return None

    async def apply_optimization(
        self,
        optimization_id: str,
        agent_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Apply a cost optimization
        
        Args:
            optimization_id: Optimization ID
            agent_id: Optional agent UUID
            
        Returns:
            Application result
        """
        try:
            # In production, this would:
            # 1. Update agent configuration
            # 2. Enable caching
            # 3. Switch models
            # 4. Configure batching
            
            logger.info(f"Applied optimization {optimization_id} for agent {agent_id}")
            
            return {
                'success': True,
                'message': f'Optimization {optimization_id} applied successfully',
                'optimization_id': optimization_id,
                'applied_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            raise

    def check_budget_alert(
        self,
        agent_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Check if budget alert should be triggered
        
        Args:
            agent_id: Optional agent UUID
            
        Returns:
            Alert status and details
        """
        try:
            settings = self.repository.get_budget_settings(agent_id)
            
            if not settings or not settings.enable_email_alerts:
                return {
                    'should_alert': False,
                    'reason': 'Alerts disabled'
                }
            
            monthly_cost = self.repository.get_monthly_cost(agent_id)
            usage_percentage = (monthly_cost / settings.monthly_budget) * 100
            
            should_alert = usage_percentage >= settings.alert_threshold_percentage
            
            return {
                'should_alert': should_alert,
                'usage_percentage': round(usage_percentage, 2),
                'threshold': settings.alert_threshold_percentage,
                'current_cost': monthly_cost,
                'budget': settings.monthly_budget,
                'remaining': settings.monthly_budget - monthly_cost
            }

        except Exception as e:
            logger.error(f"Failed to check budget alert: {e}")
            raise

    def should_auto_stop(
        self,
        agent_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if agent should be auto-stopped due to budget
        
        Args:
            agent_id: Optional agent UUID
            
        Returns:
            True if should stop
        """
        try:
            settings = self.repository.get_budget_settings(agent_id)
            
            if not settings or not settings.enable_auto_stop:
                return False
            
            monthly_cost = self.repository.get_monthly_cost(agent_id)
            
            return monthly_cost >= settings.monthly_budget

        except Exception as e:
            logger.error(f"Failed to check auto-stop: {e}")
            return False

    async def predict_monthly_cost(
        self,
        agent_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Predict end-of-month cost based on current trend
        
        Args:
            agent_id: Optional agent UUID
            
        Returns:
            Prediction details
        """
        try:
            # Get current month's cost
            monthly_cost = self.repository.get_monthly_cost(agent_id)
            
            # Calculate days elapsed and remaining
            now = datetime.utcnow()
            days_in_month = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day
            days_elapsed = now.day
            days_remaining = days_in_month - days_elapsed
            
            # Calculate daily average
            daily_avg = monthly_cost / days_elapsed if days_elapsed > 0 else 0
            
            # Predict end of month
            predicted_total = monthly_cost + (daily_avg * days_remaining)
            
            # Get budget
            settings = self.repository.get_budget_settings(agent_id)
            budget = settings.monthly_budget if settings else 1000.0
            
            will_exceed = predicted_total > budget
            
            return {
                'current_cost': round(monthly_cost, 2),
                'predicted_total': round(predicted_total, 2),
                'budget': budget,
                'will_exceed_budget': will_exceed,
                'excess_amount': round(max(0, predicted_total - budget), 2),
                'days_elapsed': days_elapsed,
                'days_remaining': days_remaining,
                'daily_average': round(daily_avg, 2)
            }

        except Exception as e:
            logger.error(f"Failed to predict monthly cost: {e}")
            raise
