"""Agent Builder API endpoints for LLM cost and token tracking."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/cost-tracking",
    tags=["agent-builder-cost-tracking"],
)


# Model pricing (per 1K tokens) - Updated Nov 2024
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # Anthropic
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    # Google
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-1.0-pro": {"input": 0.0005, "output": 0.0015},
    # Mistral
    "mistral-large": {"input": 0.002, "output": 0.006},
    "mistral-medium": {"input": 0.0027, "output": 0.0081},
    "mistral-small": {"input": 0.001, "output": 0.003},
    # Local (Ollama) - Free
    "llama3.1": {"input": 0, "output": 0},
    "llama3": {"input": 0, "output": 0},
    "mistral": {"input": 0, "output": 0},
    "codellama": {"input": 0, "output": 0},
}


class TokenUsageRecord(BaseModel):
    """Token usage record model."""
    
    id: str
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: datetime
    node_id: Optional[str] = None
    node_type: Optional[str] = None


class UsageSummary(BaseModel):
    """Usage summary model."""
    
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost_usd: float
    request_count: int
    avg_tokens_per_request: float
    avg_cost_per_request: float


class ModelUsage(BaseModel):
    """Per-model usage breakdown."""
    
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    request_count: int
    percentage: float


class DailyUsage(BaseModel):
    """Daily usage data point."""
    
    date: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    request_count: int


class CostDashboardResponse(BaseModel):
    """Cost dashboard response model."""
    
    summary: UsageSummary
    by_model: List[ModelUsage]
    daily_usage: List[DailyUsage]
    recent_records: List[TokenUsageRecord]
    budget_status: Optional[Dict[str, Any]] = None


class RecordUsageRequest(BaseModel):
    """Request to record token usage."""
    
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    model: str = Field(..., description="Model name (e.g., gpt-4o)")
    provider: str = Field(..., description="Provider (openai, anthropic, google, etc.)")
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    node_id: Optional[str] = None
    node_type: Optional[str] = None


# In-memory storage for demo (replace with DB in production)
_usage_records: List[Dict[str, Any]] = []


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost based on model pricing."""
    pricing = MODEL_PRICING.get(model, {"input": 0.001, "output": 0.002})
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    return round(input_cost + output_cost, 6)


@router.post("/record")
async def record_usage(
    request: RecordUsageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Record token usage for an LLM call.
    
    **Request Body:**
    - model: Model name
    - provider: Provider name
    - input_tokens: Number of input tokens
    - output_tokens: Number of output tokens
    - workflow_id: Optional workflow ID
    - execution_id: Optional execution ID
    - node_id: Optional node ID
    - node_type: Optional node type
    
    **Returns:**
    - Recorded usage with calculated cost
    """
    try:
        import uuid
        
        cost = calculate_cost(request.model, request.input_tokens, request.output_tokens)
        
        record = {
            "id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "workflow_id": request.workflow_id,
            "execution_id": request.execution_id,
            "model": request.model,
            "provider": request.provider,
            "input_tokens": request.input_tokens,
            "output_tokens": request.output_tokens,
            "total_tokens": request.input_tokens + request.output_tokens,
            "cost_usd": cost,
            "timestamp": datetime.utcnow(),
            "node_id": request.node_id,
            "node_type": request.node_type,
        }
        
        _usage_records.append(record)
        
        logger.info(f"Recorded usage: {request.model} - {request.input_tokens + request.output_tokens} tokens, ${cost}")
        
        return TokenUsageRecord(**record)
        
    except Exception as e:
        logger.error(f"Failed to record usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record usage"
        )


@router.get("/dashboard")
async def get_cost_dashboard(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get cost tracking dashboard data.
    
    **Query Parameters:**
    - days: Number of days to include (default: 30)
    - workflow_id: Optional workflow filter
    
    **Returns:**
    - Summary statistics
    - Usage by model
    - Daily usage trend
    - Recent records
    """
    try:
        user_id = str(current_user.id)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter records
        records = [
            r for r in _usage_records
            if r["user_id"] == user_id 
            and r["timestamp"] >= cutoff_date
            and (workflow_id is None or r["workflow_id"] == workflow_id)
        ]
        
        if not records:
            # Return empty dashboard
            return CostDashboardResponse(
                summary=UsageSummary(
                    total_input_tokens=0,
                    total_output_tokens=0,
                    total_tokens=0,
                    total_cost_usd=0,
                    request_count=0,
                    avg_tokens_per_request=0,
                    avg_cost_per_request=0,
                ),
                by_model=[],
                daily_usage=[],
                recent_records=[],
            )
        
        # Calculate summary
        total_input = sum(r["input_tokens"] for r in records)
        total_output = sum(r["output_tokens"] for r in records)
        total_tokens = total_input + total_output
        total_cost = sum(r["cost_usd"] for r in records)
        request_count = len(records)
        
        summary = UsageSummary(
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 4),
            request_count=request_count,
            avg_tokens_per_request=round(total_tokens / request_count, 1) if request_count > 0 else 0,
            avg_cost_per_request=round(total_cost / request_count, 6) if request_count > 0 else 0,
        )
        
        # Group by model
        model_usage: Dict[str, Dict] = {}
        for r in records:
            key = r["model"]
            if key not in model_usage:
                model_usage[key] = {
                    "model": r["model"],
                    "provider": r["provider"],
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0,
                    "request_count": 0,
                }
            model_usage[key]["input_tokens"] += r["input_tokens"]
            model_usage[key]["output_tokens"] += r["output_tokens"]
            model_usage[key]["total_tokens"] += r["total_tokens"]
            model_usage[key]["cost_usd"] += r["cost_usd"]
            model_usage[key]["request_count"] += 1
        
        by_model = [
            ModelUsage(
                **{**v, "cost_usd": round(v["cost_usd"], 4), "percentage": round(v["cost_usd"] / total_cost * 100, 1) if total_cost > 0 else 0}
            )
            for v in sorted(model_usage.values(), key=lambda x: x["cost_usd"], reverse=True)
        ]
        
        # Group by day
        daily_data: Dict[str, Dict] = {}
        for r in records:
            date_key = r["timestamp"].strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": date_key,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0,
                    "request_count": 0,
                }
            daily_data[date_key]["input_tokens"] += r["input_tokens"]
            daily_data[date_key]["output_tokens"] += r["output_tokens"]
            daily_data[date_key]["total_tokens"] += r["total_tokens"]
            daily_data[date_key]["cost_usd"] += r["cost_usd"]
            daily_data[date_key]["request_count"] += 1
        
        daily_usage = [
            DailyUsage(**{**v, "cost_usd": round(v["cost_usd"], 4)})
            for v in sorted(daily_data.values(), key=lambda x: x["date"])
        ]
        
        # Recent records
        recent = sorted(records, key=lambda x: x["timestamp"], reverse=True)[:20]
        recent_records = [TokenUsageRecord(**r) for r in recent]
        
        return CostDashboardResponse(
            summary=summary,
            by_model=by_model,
            daily_usage=daily_usage,
            recent_records=recent_records,
        )
        
    except Exception as e:
        logger.error(f"Failed to get cost dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cost dashboard"
        )


@router.get("/pricing")
async def get_model_pricing(
    current_user: User = Depends(get_current_user),
):
    """
    Get current model pricing information.
    
    **Returns:**
    - Dictionary of model pricing (per 1K tokens)
    """
    return {
        "pricing": MODEL_PRICING,
        "currency": "USD",
        "unit": "per 1K tokens",
        "last_updated": "2024-11-30",
    }


@router.get("/estimate")
async def estimate_cost(
    model: str = Query(..., description="Model name"),
    input_tokens: int = Query(..., ge=0, description="Estimated input tokens"),
    output_tokens: int = Query(..., ge=0, description="Estimated output tokens"),
    current_user: User = Depends(get_current_user),
):
    """
    Estimate cost for a given model and token count.
    
    **Query Parameters:**
    - model: Model name
    - input_tokens: Estimated input tokens
    - output_tokens: Estimated output tokens
    
    **Returns:**
    - Estimated cost breakdown
    """
    pricing = MODEL_PRICING.get(model, {"input": 0.001, "output": 0.002})
    
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    total_cost = input_cost + output_cost
    
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "pricing_per_1k": pricing,
    }


@router.delete("/records")
async def clear_usage_records(
    days: Optional[int] = Query(None, description="Clear records older than N days"),
    current_user: User = Depends(get_current_user),
):
    """
    Clear usage records (admin only in production).
    
    **Query Parameters:**
    - days: Optional, clear records older than N days
    
    **Returns:**
    - Number of records cleared
    """
    global _usage_records
    
    user_id = str(current_user.id)
    
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        before_count = len(_usage_records)
        _usage_records = [
            r for r in _usage_records
            if r["user_id"] != user_id or r["timestamp"] >= cutoff
        ]
        cleared = before_count - len(_usage_records)
    else:
        before_count = len([r for r in _usage_records if r["user_id"] == user_id])
        _usage_records = [r for r in _usage_records if r["user_id"] != user_id]
        cleared = before_count
    
    return {"cleared": cleared, "message": f"Cleared {cleared} records"}
