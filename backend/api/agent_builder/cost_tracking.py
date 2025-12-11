"""Agent Builder API endpoints for LLM cost and token tracking.

All data is stored in the database (TokenUsage, ModelPricing tables).
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.flows import TokenUsage, ModelPricing

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/cost-tracking",
    tags=["agent-builder-cost-tracking"],
)


# ============ Pydantic Models ============

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


class ModelPricingRequest(BaseModel):
    """Request to create/update model pricing."""
    provider: str
    model: str
    input_price_per_1k: float = Field(..., ge=0)
    output_price_per_1k: float = Field(..., ge=0)
    currency: str = "USD"


# ============ Helper Functions ============

def get_model_pricing(db: Session, provider: str, model: str) -> tuple:
    """Get pricing for a model from DB or return defaults."""
    pricing = db.query(ModelPricing).filter(
        ModelPricing.provider == provider.lower(),
        ModelPricing.model == model.lower(),
        ModelPricing.is_active == True
    ).first()
    
    if pricing:
        return pricing.input_price_per_1k, pricing.output_price_per_1k
    
    # Default pricing for common models (fallback)
    defaults = {
        ("openai", "gpt-4o"): (0.0025, 0.01),
        ("openai", "gpt-4o-mini"): (0.00015, 0.0006),
        ("openai", "gpt-4-turbo"): (0.01, 0.03),
        ("openai", "gpt-3.5-turbo"): (0.0005, 0.0015),
        ("anthropic", "claude-3-5-sonnet"): (0.003, 0.015),
        ("anthropic", "claude-3-opus"): (0.015, 0.075),
        ("anthropic", "claude-3-haiku"): (0.00025, 0.00125),
        ("google", "gemini-1.5-pro"): (0.00125, 0.005),
        ("google", "gemini-1.5-flash"): (0.000075, 0.0003),
        ("ollama", "llama3.1"): (0, 0),
        ("ollama", "llama3"): (0, 0),
        ("ollama", "mistral"): (0, 0),
    }
    
    return defaults.get((provider.lower(), model.lower()), (0.001, 0.002))


def calculate_cost(db: Session, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost based on model pricing."""
    input_price, output_price = get_model_pricing(db, provider, model)
    input_cost = (input_tokens / 1000) * input_price
    output_cost = (output_tokens / 1000) * output_price
    return round(input_cost + output_cost, 6)


# ============ Endpoints ============

@router.post("/record")
async def record_usage(
    request: RecordUsageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record token usage for an LLM call."""
    try:
        cost = calculate_cost(db, request.provider, request.model, request.input_tokens, request.output_tokens)
        
        # Parse UUIDs if provided
        workflow_uuid = None
        execution_uuid = None
        
        if request.workflow_id:
            try:
                workflow_uuid = uuid.UUID(request.workflow_id)
            except ValueError:
                pass
        
        if request.execution_id:
            try:
                execution_uuid = uuid.UUID(request.execution_id)
            except ValueError:
                pass
        
        record = TokenUsage(
            user_id=current_user.id,
            workflow_id=workflow_uuid,
            flow_execution_id=execution_uuid,
            provider=request.provider,
            model=request.model,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            total_tokens=request.input_tokens + request.output_tokens,
            cost_usd=cost,
            node_id=request.node_id,
            node_type=request.node_type,
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        logger.info(f"Recorded usage: {request.model} - {request.input_tokens + request.output_tokens} tokens, ${cost}")
        
        return TokenUsageRecord(
            id=str(record.id),
            workflow_id=str(record.workflow_id) if record.workflow_id else None,
            execution_id=str(record.flow_execution_id) if record.flow_execution_id else None,
            model=record.model,
            provider=record.provider,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            total_tokens=record.total_tokens,
            cost_usd=record.cost_usd,
            timestamp=record.created_at,
            node_id=record.node_id,
            node_type=record.node_type,
        )
        
    except Exception as e:
        db.rollback()
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
    """Get cost tracking dashboard data."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query
        query = db.query(TokenUsage).filter(
            TokenUsage.user_id == current_user.id,
            TokenUsage.created_at >= cutoff_date
        )
        
        if workflow_id:
            try:
                workflow_uuid = uuid.UUID(workflow_id)
                query = query.filter(TokenUsage.workflow_id == workflow_uuid)
            except ValueError:
                pass
        
        records = query.all()
        
        if not records:
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
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        total_tokens = total_input + total_output
        total_cost = sum(r.cost_usd for r in records)
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
            key = r.model
            if key not in model_usage:
                model_usage[key] = {
                    "model": r.model,
                    "provider": r.provider,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0,
                    "request_count": 0,
                }
            model_usage[key]["input_tokens"] += r.input_tokens
            model_usage[key]["output_tokens"] += r.output_tokens
            model_usage[key]["total_tokens"] += r.total_tokens
            model_usage[key]["cost_usd"] += r.cost_usd
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
            date_key = r.created_at.strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": date_key,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0,
                    "request_count": 0,
                }
            daily_data[date_key]["input_tokens"] += r.input_tokens
            daily_data[date_key]["output_tokens"] += r.output_tokens
            daily_data[date_key]["total_tokens"] += r.total_tokens
            daily_data[date_key]["cost_usd"] += r.cost_usd
            daily_data[date_key]["request_count"] += 1
        
        daily_usage = [
            DailyUsage(**{**v, "cost_usd": round(v["cost_usd"], 4)})
            for v in sorted(daily_data.values(), key=lambda x: x["date"])
        ]
        
        # Recent records
        recent = sorted(records, key=lambda x: x.created_at, reverse=True)[:20]
        recent_records = [
            TokenUsageRecord(
                id=str(r.id),
                workflow_id=str(r.workflow_id) if r.workflow_id else None,
                execution_id=str(r.flow_execution_id) if r.flow_execution_id else None,
                model=r.model,
                provider=r.provider,
                input_tokens=r.input_tokens,
                output_tokens=r.output_tokens,
                total_tokens=r.total_tokens,
                cost_usd=r.cost_usd,
                timestamp=r.created_at,
                node_id=r.node_id,
                node_type=r.node_type,
            )
            for r in recent
        ]
        
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
async def get_model_pricing_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current model pricing information from database."""
    try:
        pricings = db.query(ModelPricing).filter(ModelPricing.is_active == True).all()
        
        pricing_dict = {}
        for p in pricings:
            pricing_dict[p.model] = {
                "input": p.input_price_per_1k,
                "output": p.output_price_per_1k,
                "provider": p.provider,
            }
        
        # Add defaults if not in DB
        defaults = {
            "gpt-4o": {"input": 0.0025, "output": 0.01, "provider": "openai"},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006, "provider": "openai"},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03, "provider": "openai"},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015, "provider": "openai"},
            "claude-3-5-sonnet": {"input": 0.003, "output": 0.015, "provider": "anthropic"},
            "claude-3-opus": {"input": 0.015, "output": 0.075, "provider": "anthropic"},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125, "provider": "anthropic"},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005, "provider": "google"},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003, "provider": "google"},
            "llama3.1": {"input": 0, "output": 0, "provider": "ollama"},
            "llama3": {"input": 0, "output": 0, "provider": "ollama"},
            "mistral": {"input": 0, "output": 0, "provider": "ollama"},
        }
        
        for model, prices in defaults.items():
            if model not in pricing_dict:
                pricing_dict[model] = prices
        
        return {
            "pricing": pricing_dict,
            "currency": "USD",
            "unit": "per 1K tokens",
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "database" if pricings else "defaults",
        }
        
    except Exception as e:
        logger.error(f"Failed to get pricing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pricing"
        )


@router.post("/pricing")
async def create_or_update_pricing(
    request: ModelPricingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update model pricing."""
    try:
        existing = db.query(ModelPricing).filter(
            ModelPricing.provider == request.provider.lower(),
            ModelPricing.model == request.model.lower()
        ).first()
        
        if existing:
            existing.input_price_per_1k = request.input_price_per_1k
            existing.output_price_per_1k = request.output_price_per_1k
            existing.currency = request.currency
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
        else:
            pricing = ModelPricing(
                provider=request.provider.lower(),
                model=request.model.lower(),
                input_price_per_1k=request.input_price_per_1k,
                output_price_per_1k=request.output_price_per_1k,
                currency=request.currency,
                is_active=True,
            )
            db.add(pricing)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Pricing updated for {request.provider}/{request.model}",
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update pricing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pricing"
        )


@router.get("/estimate")
async def estimate_cost(
    model: str = Query(..., description="Model name"),
    provider: str = Query("openai", description="Provider name"),
    input_tokens: int = Query(..., ge=0, description="Estimated input tokens"),
    output_tokens: int = Query(..., ge=0, description="Estimated output tokens"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Estimate cost for a given model and token count."""
    input_price, output_price = get_model_pricing(db, provider, model)
    
    input_cost = (input_tokens / 1000) * input_price
    output_cost = (output_tokens / 1000) * output_price
    total_cost = input_cost + output_cost
    
    return {
        "model": model,
        "provider": provider,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "pricing_per_1k": {
            "input": input_price,
            "output": output_price,
        },
    }


@router.delete("/records")
async def clear_usage_records(
    days: Optional[int] = Query(None, description="Clear records older than N days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear usage records for the current user."""
    try:
        query = db.query(TokenUsage).filter(TokenUsage.user_id == current_user.id)
        
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(TokenUsage.created_at < cutoff)
        
        count = query.count()
        query.delete(synchronize_session=False)
        db.commit()
        
        return {"cleared": count, "message": f"Cleared {count} records"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear records: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear records"
        )
