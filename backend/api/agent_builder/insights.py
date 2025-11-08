"""
AI Insights API

Provides AI-powered insights, anomaly detection, and predictive analytics
for Agent Builder.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np
from backend.core.dependencies import get_db
from backend.services.agent_builder.agent_service_refactored import AgentServiceRefactored
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/insights", tags=["AI Insights"])


# Models
class InsightImpact(BaseModel):
    metric: str
    current: float
    predicted: float
    change: float
    change_percent: float


class InsightAction(BaseModel):
    id: str
    label: str
    type: str  # primary, secondary, danger
    requires_confirmation: bool
    estimated_impact: Optional[Dict[str, Any]] = None


class Insight(BaseModel):
    id: str
    type: str  # performance, cost, quality, security, optimization, anomaly, prediction, alert, trend
    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    impact: Optional[InsightImpact] = None
    actions: List[InsightAction] = []
    related_data: Optional[Dict[str, Any]] = None
    confidence: int  # 0-100
    timestamp: str
    expires_at: Optional[str] = None
    tags: List[str] = []


class AnalyticsOverview(BaseModel):
    total_executions: int
    success_rate: float
    avg_response_time: float
    total_users: int
    top_performing_agents: List[Dict[str, Any]]
    insights: List[Insight]


class PerformanceMetrics(BaseModel):
    response_time_trend: List[Dict[str, Any]]
    throughput: List[Dict[str, Any]]
    error_rate: List[Dict[str, Any]]


class UsageMetrics(BaseModel):
    usage_by_agent: List[Dict[str, Any]]
    usage_by_user: List[Dict[str, Any]]
    peak_usage_times: List[Dict[str, Any]]
    most_used_features: List[Dict[str, Any]]


class QualityMetrics(BaseModel):
    accuracy_score: float
    relevance_score: float
    consistency_score: float
    total_evaluations: int
    common_issues: List[Dict[str, Any]]
    positive_feedback: int
    neutral_feedback: int
    negative_feedback: int


# Helper functions
def detect_performance_anomalies(executions: List[Dict]) -> List[Insight]:
    """Detect performance anomalies using statistical analysis"""
    insights = []
    
    if len(executions) < 10:
        return insights
    
    durations = [e.get('duration', 0) for e in executions]
    mean = np.mean(durations)
    std = np.std(durations)
    
    # 3-sigma rule for anomaly detection
    anomalies = [e for e in executions if abs(e.get('duration', 0) - mean) > 3 * std]
    
    if len(anomalies) > 0:
        insights.append(Insight(
            id=f"anomaly-{datetime.utcnow().timestamp()}",
            type="anomaly",
            severity="medium",
            category="agent_performance",
            title="Performance Anomalies Detected",
            description=f"{len(anomalies)} executions deviated significantly from normal (3σ rule)",
            confidence=85,
            timestamp=datetime.utcnow().isoformat(),
            tags=["anomaly", "performance", "statistical"],
            actions=[
                InsightAction(
                    id="investigate",
                    label="Investigate Anomalies",
                    type="primary",
                    requires_confirmation=False
                )
            ]
        ))
    
    return insights


def detect_cost_spikes(executions: List[Dict]) -> List[Insight]:
    """Detect cost spikes"""
    insights = []
    
    if len(executions) < 20:
        return insights
    
    recent_10 = executions[-10:]
    prev_10 = executions[-20:-10]
    
    recent_avg = np.mean([e.get('cost', 0) for e in recent_10])
    prev_avg = np.mean([e.get('cost', 0) for e in prev_10])
    
    if recent_avg > prev_avg * 1.5:
        increase_pct = ((recent_avg - prev_avg) / prev_avg) * 100
        
        insights.append(Insight(
            id=f"cost-spike-{datetime.utcnow().timestamp()}",
            type="cost",
            severity="high",
            category="cost_optimization",
            title="Cost Spike Detected",
            description=f"Recent execution costs increased by {increase_pct:.1f}%",
            impact=InsightImpact(
                metric="cost",
                current=recent_avg,
                predicted=recent_avg * 1.3,
                change=recent_avg * 0.3,
                change_percent=30
            ),
            confidence=95,
            timestamp=datetime.utcnow().isoformat(),
            tags=["cost", "spike", "optimization"],
            actions=[
                InsightAction(
                    id="optimize-model",
                    label="Optimize Model",
                    type="primary",
                    requires_confirmation=True,
                    estimated_impact={"metric": "cost", "value": -40, "unit": "%"}
                ),
                InsightAction(
                    id="enable-caching",
                    label="Enable Caching",
                    type="secondary",
                    requires_confirmation=False,
                    estimated_impact={"metric": "cost", "value": -25, "unit": "%"}
                )
            ]
        ))
    
    return insights


def predict_trends(historical_data: List[float]) -> Optional[Insight]:
    """Predict trends using linear regression"""
    if len(historical_data) < 7:
        return None
    
    n = len(historical_data)
    x = np.arange(n)
    y = np.array(historical_data)
    
    # Linear regression
    slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
    
    if slope > 0:
        predicted_7_days = y[-1] + slope * 7
        increase_pct = ((predicted_7_days - y[-1]) / y[-1]) * 100
        
        if increase_pct > 20:
            return Insight(
                id=f"trend-cost-{datetime.utcnow().timestamp()}",
                type="prediction",
                severity="medium",
                category="cost_optimization",
                title="Cost Increase Trend Predicted",
                description=f"Current trend suggests {increase_pct:.1f}% cost increase in 7 days",
                impact=InsightImpact(
                    metric="cost",
                    current=float(y[-1]),
                    predicted=float(predicted_7_days),
                    change=float(predicted_7_days - y[-1]),
                    change_percent=increase_pct
                ),
                confidence=78,
                timestamp=datetime.utcnow().isoformat(),
                expires_at=(datetime.utcnow() + timedelta(days=7)).isoformat(),
                tags=["prediction", "cost", "trend"],
                actions=[
                    InsightAction(
                        id="set-budget-alert",
                        label="Set Budget Alert",
                        type="primary",
                        requires_confirmation=False
                    )
                ]
            )
    
    return None


# API Endpoints
@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    agent_id: Optional[str] = None,
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d|all)$"),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered analytics overview with insights
    """
    try:
        # Mock data for now - replace with actual DB queries
        insights = []
        
        # Add sample insights
        insights.append(Insight(
            id="sample-1",
            type="performance",
            severity="high",
            category="agent_performance",
            title="Response Time Degradation",
            description="Average response time increased by 35% compared to last week",
            impact=InsightImpact(
                metric="response_time",
                current=2.34,
                predicted=3.16,
                change=0.82,
                change_percent=35
            ),
            confidence=92,
            timestamp=datetime.utcnow().isoformat(),
            tags=["performance", "response-time"],
            actions=[
                InsightAction(
                    id="optimize-prompt",
                    label="Optimize Prompt",
                    type="primary",
                    requires_confirmation=False,
                    estimated_impact={"metric": "response_time", "value": -30, "unit": "%"}
                )
            ]
        ))
        
        return AnalyticsOverview(
            total_executions=1250,
            success_rate=94.5,
            avg_response_time=2.34,
            total_users=45,
            top_performing_agents=[
                {"id": "agent-1", "name": "Customer Support", "success_rate": 98.2, "execution_count": 450},
                {"id": "agent-2", "name": "Data Analyzer", "success_rate": 96.5, "execution_count": 320},
            ],
            insights=insights
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_analytics(
    agent_id: Optional[str] = None,
    time_range: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get performance analytics"""
    try:
        # Generate sample data
        dates = [(datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, 0, -1)]
        
        return PerformanceMetrics(
            response_time_trend=[
                {"date": date, "avg_time": 2.0 + np.random.random(), "p95_time": 3.5 + np.random.random()}
                for date in dates
            ],
            throughput=[
                {"hour": f"{i:02d}:00", "count": int(50 + np.random.random() * 50)}
                for i in range(24)
            ],
            error_rate=[
                {"date": date, "error_rate": 2.0 + np.random.random() * 3}
                for date in dates
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage", response_model=UsageMetrics)
async def get_usage_analytics(
    agent_id: Optional[str] = None,
    time_range: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get usage analytics"""
    try:
        return UsageMetrics(
            usage_by_agent=[
                {"name": "Customer Support", "value": 450},
                {"name": "Data Analyzer", "value": 320},
                {"name": "Content Writer", "value": 280},
            ],
            usage_by_user=[
                {"user": "user1@example.com", "count": 234},
                {"user": "user2@example.com", "count": 189},
                {"user": "user3@example.com", "count": 156},
            ],
            peak_usage_times=[
                {"hour": f"{i:02d}:00", "count": int(30 + np.random.random() * 70)}
                for i in range(24)
            ],
            most_used_features=[
                {"name": "Query Processing", "count": 1250, "percentage": 45.5},
                {"name": "Document Upload", "count": 890, "percentage": 32.4},
                {"name": "Workflow Execution", "count": 605, "percentage": 22.1},
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to get usage analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality", response_model=QualityMetrics)
async def get_quality_analytics(
    agent_id: Optional[str] = None,
    time_range: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get quality analytics"""
    try:
        return QualityMetrics(
            accuracy_score=87.5,
            relevance_score=92.3,
            consistency_score=89.1,
            total_evaluations=1250,
            common_issues=[
                {
                    "title": "Inconsistent Responses",
                    "description": "Similar queries producing different answers",
                    "count": 23,
                    "suggestion": "Review and standardize prompt templates"
                },
                {
                    "title": "Slow Response Times",
                    "description": "Responses taking longer than expected",
                    "count": 18,
                    "suggestion": "Optimize prompt length and enable caching"
                }
            ],
            positive_feedback=945,
            neutral_feedback=234,
            negative_feedback=71
        )
        
    except Exception as e:
        logger.error(f"Failed to get quality analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_executions(
    executions: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Analyze execution data and generate insights
    """
    try:
        insights = []
        
        # Performance anomaly detection
        insights.extend(detect_performance_anomalies(executions))
        
        # Cost spike detection
        insights.extend(detect_cost_spikes(executions))
        
        # Trend prediction
        if len(executions) >= 7:
            costs = [e.get('cost', 0) for e in executions[-30:]]
            trend_insight = predict_trends(costs)
            if trend_insight:
                insights.append(trend_insight)
        
        return {"insights": insights}
        
    except Exception as e:
        logger.error(f"Failed to analyze executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
