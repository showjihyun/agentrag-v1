"""
Cost Management API

Provides endpoints for cost tracking, budget management, optimization, and prediction.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np
from backend.core.dependencies import get_db
from backend.db.repositories.cost_repository import CostRepository
from backend.services.agent_builder.cost_service import CostService
from backend.exceptions.agent_builder import (
    BudgetExceededError,
    InvalidTimeRangeError,
    OptimizationNotFoundError
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/cost", tags=["Cost Management"])


# Models
class CostStats(BaseModel):
    total_cost: float
    total_tokens: int
    budget_used_percentage: float
    avg_cost_per_execution: float
    trend_percentage: float  # vs previous period


class ModelCost(BaseModel):
    model: str
    cost: float
    percentage: float
    executions: int


class AgentCost(BaseModel):
    agent_id: str
    agent_name: str
    cost: float
    executions: int


class CostTrend(BaseModel):
    date: str
    cost: float
    executions: int


class ExpensiveExecution(BaseModel):
    id: str
    agent_name: str
    tokens: int
    cost: float
    timestamp: str


class CostBreakdown(BaseModel):
    by_model: List[ModelCost]
    by_agent: List[AgentCost]
    trend: List[CostTrend]
    expensive_executions: List[ExpensiveExecution]


class BudgetSettings(BaseModel):
    monthly_budget: float = Field(default=1000.0, ge=0)
    alert_threshold_percentage: int = Field(default=80, ge=0, le=100)
    enable_email_alerts: bool = True
    enable_auto_stop: bool = False


class BudgetStatus(BaseModel):
    settings: BudgetSettings
    current_usage: float
    remaining_budget: float
    days_remaining: int
    projected_end_of_month: float
    is_over_budget: bool


class CostOptimization(BaseModel):
    id: str
    type: str  # model_switch, caching, batching, prompt_optimization
    title: str
    description: str
    estimated_savings: float
    savings_percentage: float
    impact: str  # low, medium, high
    effort: str  # low, medium, high
    applicable_to: List[str]  # agent IDs or "all"


class CostPrediction(BaseModel):
    dates: List[str]
    actual: List[float]
    predicted: List[float]
    upper_bound: List[float]
    lower_bound: List[float]
    growth_rate: float
    confidence: float


# Endpoints
@router.get("/stats", response_model=CostStats)
async def get_cost_stats(
    agent_id: Optional[str] = None,
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d|all)$"),
    db: Session = Depends(get_db)
):
    """
    Get cost statistics
    """
    try:
        repository = CostRepository(db)
        agent_uuid = UUID(agent_id) if agent_id else None
        stats = repository.get_stats(agent_uuid, time_range)
        
        # Get budget usage percentage
        budget_settings = repository.get_budget_settings(agent_uuid)
        monthly_cost = repository.get_monthly_cost(agent_uuid)
        
        budget_used_percentage = 0
        if budget_settings and budget_settings.monthly_budget > 0:
            budget_used_percentage = (monthly_cost / budget_settings.monthly_budget) * 100
        
        return CostStats(
            budget_used_percentage=round(budget_used_percentage, 2),
            **stats
        )
        
    except ValueError as e:
        logger.error(f"Invalid agent_id: {e}")
        raise HTTPException(status_code=400, detail="Invalid agent ID")
    except Exception as e:
        logger.error(f"Failed to get cost stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breakdown", response_model=CostBreakdown)
async def get_cost_breakdown(
    agent_id: Optional[str] = None,
    time_range: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """
    Get detailed cost breakdown
    """
    try:
        # Generate mock data
        by_model = [
            ModelCost(model="gpt-4", cost=120.50, percentage=51.4, executions=450),
            ModelCost(model="gpt-3.5-turbo", cost=78.30, percentage=33.4, executions=890),
            ModelCost(model="claude-3-sonnet", cost=35.76, percentage=15.2, executions=234),
        ]
        
        by_agent = [
            AgentCost(agent_id="agent-1", agent_name="Customer Support", cost=98.45, executions=450),
            AgentCost(agent_id="agent-2", agent_name="Data Analyzer", cost=76.23, executions=320),
            AgentCost(agent_id="agent-3", agent_name="Content Writer", cost=59.88, executions=280),
        ]
        
        # Generate trend data
        trend = []
        for i in range(30):
            date = (datetime.utcnow() - timedelta(days=29-i)).strftime("%Y-%m-%d")
            trend.append(CostTrend(
                date=date,
                cost=5.0 + np.random.random() * 3.0 + (i * 0.1),
                executions=30 + int(np.random.random() * 20)
            ))
        
        expensive_executions = [
            ExpensiveExecution(
                id=f"exec-{i}",
                agent_name=["Customer Support", "Data Analyzer", "Content Writer"][i % 3],
                tokens=15000 + i * 1000,
                cost=2.5 + i * 0.3,
                timestamp=(datetime.utcnow() - timedelta(hours=i)).isoformat()
            )
            for i in range(10)
        ]
        
        return CostBreakdown(
            by_model=by_model,
            by_agent=by_agent,
            trend=trend,
            expensive_executions=expensive_executions
        )
        
    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget", response_model=BudgetStatus)
async def get_budget_settings(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get budget settings and status
    """
    try:
        settings = BudgetSettings(
            monthly_budget=1000.0,
            alert_threshold_percentage=80,
            enable_email_alerts=True,
            enable_auto_stop=False
        )
        
        current_usage = 234.56
        remaining_budget = settings.monthly_budget - current_usage
        
        # Calculate days remaining in month
        now = datetime.utcnow()
        last_day = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day
        days_remaining = last_day - now.day
        
        # Project end of month cost
        daily_avg = current_usage / (last_day - days_remaining)
        projected_end_of_month = current_usage + (daily_avg * days_remaining)
        
        return BudgetStatus(
            settings=settings,
            current_usage=current_usage,
            remaining_budget=remaining_budget,
            days_remaining=days_remaining,
            projected_end_of_month=projected_end_of_month,
            is_over_budget=current_usage > settings.monthly_budget
        )
        
    except Exception as e:
        logger.error(f"Failed to get budget settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/budget", response_model=BudgetSettings)
async def update_budget_settings(
    settings: BudgetSettings,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update budget settings
    """
    try:
        # In production, save to DB
        logger.info(f"Updated budget settings: {settings}")
        return settings
        
    except Exception as e:
        logger.error(f"Failed to update budget settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=List[CostOptimization])
async def analyze_cost_optimization(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Analyze and generate AI-powered cost optimization recommendations
    """
    try:
        repository = CostRepository(db)
        service = CostService(repository)
        
        agent_uuid = UUID(agent_id) if agent_id else None
        optimizations = await service.analyze_optimization(agent_uuid)
        
        return [CostOptimization(**opt) for opt in optimizations]
        
    except ValueError as e:
        logger.error(f"Invalid agent_id: {e}")
        raise HTTPException(status_code=400, detail="Invalid agent ID")
    except Exception as e:
        logger.error(f"Failed to analyze cost optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/{optimization_id}")
async def apply_cost_optimization(
    optimization_id: str,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Apply a cost optimization recommendation
    """
    try:
        repository = CostRepository(db)
        service = CostService(repository)
        
        agent_uuid = UUID(agent_id) if agent_id else None
        result = await service.apply_optimization(optimization_id, agent_uuid)
        
        return result
        
    except ValueError as e:
        logger.error(f"Invalid agent_id: {e}")
        raise HTTPException(status_code=400, detail="Invalid agent ID")
    except Exception as e:
        logger.error(f"Failed to apply cost optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict", response_model=CostPrediction)
async def predict_costs(
    agent_id: Optional[str] = None,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """
    Predict future costs using linear regression
    """
    try:
        # Generate historical data (last 30 days)
        historical_days = 30
        dates = []
        actual = []
        
        for i in range(historical_days):
            date = (datetime.utcnow() - timedelta(days=historical_days-1-i)).strftime("%Y-%m-%d")
            dates.append(date)
            # Simulate increasing trend
            cost = 5.0 + (i * 0.15) + np.random.random() * 2.0
            actual.append(round(cost, 2))
        
        # Linear regression for prediction
        x = np.arange(len(actual))
        y = np.array(actual)
        
        # Calculate slope and intercept
        n = len(x)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
        intercept = (np.sum(y) - slope * np.sum(x)) / n
        
        # Predict future
        predicted = []
        upper_bound = []
        lower_bound = []
        
        for i in range(days):
            date = (datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d")
            dates.append(date)
            actual.append(None)  # No actual data for future
            
            pred_value = slope * (len(y) + i) + intercept
            predicted.append(round(pred_value, 2))
            
            # Confidence interval (±20%)
            upper_bound.append(round(pred_value * 1.2, 2))
            lower_bound.append(round(pred_value * 0.8, 2))
        
        # Fill predicted for historical data
        for i in range(len(y)):
            predicted.insert(i, round(slope * i + intercept, 2))
            upper_bound.insert(i, round((slope * i + intercept) * 1.1, 2))
            lower_bound.insert(i, round((slope * i + intercept) * 0.9, 2))
        
        # Calculate growth rate
        growth_rate = (slope / y.mean()) * 100 if y.mean() > 0 else 0
        
        return CostPrediction(
            dates=dates,
            actual=actual,
            predicted=predicted,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            growth_rate=round(growth_rate, 2),
            confidence=78.5
        )
        
    except Exception as e:
        logger.error(f"Failed to predict costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
