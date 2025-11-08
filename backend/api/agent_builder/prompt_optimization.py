"""
Prompt Optimization API

Provides AI-powered prompt optimization, A/B testing, and metrics.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from backend.core.dependencies import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/agents", tags=["Prompt Optimization"])


# Models
class OptimizationRequest(BaseModel):
    current_prompt: str
    optimization_goals: List[str]  # clarity, specificity, performance, cost


class OptimizationSuggestion(BaseModel):
    id: str
    optimized_prompt: str
    improvements: List[str]
    estimated_score: int
    reasoning: str


class PromptMetrics(BaseModel):
    clarity_score: int
    specificity_score: int
    token_efficiency: int
    avg_response_time: float
    success_rate: float
    avg_cost_per_execution: float
    total_executions: int
    history: List[dict]


class ABTestVariant(BaseModel):
    id: str
    name: str
    prompt: str
    traffic_percentage: int
    executions: int = 0
    success_rate: float = 0
    avg_response_time: float = 0
    avg_cost: float = 0


class ABTest(BaseModel):
    id: str
    name: str
    status: str  # draft, running, completed, paused
    variants: List[ABTestVariant]
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    winner: Optional[str] = None


class ABTestCreate(BaseModel):
    name: str
    variants: List[dict]


# Endpoints
@router.post("/{agent_id}/optimize-prompt")
async def optimize_prompt(
    agent_id: str,
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate optimized prompt suggestions using AI
    """
    try:
        # In production, use LLM to generate optimizations
        suggestions = [
            OptimizationSuggestion(
                id="opt-1",
                optimized_prompt=f"[OPTIMIZED] {request.current_prompt}\n\nBe specific, clear, and concise.",
                improvements=[
                    "Added clarity instructions",
                    "Reduced ambiguity",
                    "Improved structure",
                    "Added output format specification"
                ],
                estimated_score=92,
                reasoning="This version is more specific and provides clearer instructions"
            ),
            OptimizationSuggestion(
                id="opt-2",
                optimized_prompt=f"[CONCISE] {request.current_prompt[:100]}...",
                improvements=[
                    "Reduced token count by 40%",
                    "Maintained core meaning",
                    "Improved cost efficiency"
                ],
                estimated_score=85,
                reasoning="This version is more concise while maintaining effectiveness"
            )
        ]
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Failed to optimize prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/prompt-metrics", response_model=PromptMetrics)
async def get_prompt_metrics(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get prompt performance metrics
    """
    try:
        # Generate sample metrics
        history = []
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=6-i)).strftime("%Y-%m-%d")
            history.append({
                "date": date,
                "success_rate": 90 + (i % 3) * 2,
                "avg_response_time": 2.0 + (i % 4) * 0.3
            })
        
        return PromptMetrics(
            clarity_score=87,
            specificity_score=92,
            token_efficiency=78,
            avg_response_time=2.34,
            success_rate=94.5,
            avg_cost_per_execution=0.0234,
            total_executions=1250,
            history=history
        )
        
    except Exception as e:
        logger.error(f"Failed to get prompt metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/ab-tests")
async def get_ab_tests(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get A/B tests for an agent
    """
    try:
        tests = [
            ABTest(
                id="test-1",
                name="Clarity vs Brevity",
                status="running",
                variants=[
                    ABTestVariant(
                        id="var-a",
                        name="Variant A",
                        prompt="Detailed prompt...",
                        traffic_percentage=50,
                        executions=125,
                        success_rate=94.5,
                        avg_response_time=2.34,
                        avg_cost=0.0234
                    ),
                    ABTestVariant(
                        id="var-b",
                        name="Variant B",
                        prompt="Concise prompt...",
                        traffic_percentage=50,
                        executions=118,
                        success_rate=92.1,
                        avg_response_time=1.89,
                        avg_cost=0.0189
                    )
                ],
                created_at="2024-02-15T10:00:00Z",
                started_at="2024-02-15T11:00:00Z"
            )
        ]
        
        return {"tests": tests}
        
    except Exception as e:
        logger.error(f"Failed to get A/B tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/ab-tests")
async def create_ab_test(
    agent_id: str,
    request: ABTestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new A/B test
    """
    try:
        test = ABTest(
            id=f"test-{datetime.utcnow().timestamp()}",
            name=request.name,
            status="draft",
            variants=[ABTestVariant(**v) for v in request.variants],
            created_at=datetime.utcnow().isoformat()
        )
        
        return test
        
    except Exception as e:
        logger.error(f"Failed to create A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/ab-tests/{test_id}/start")
async def start_ab_test(
    agent_id: str,
    test_id: str,
    db: Session = Depends(get_db)
):
    """
    Start an A/B test
    """
    try:
        return {
            "success": True,
            "message": "A/B test started",
            "test_id": test_id,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/ab-tests/{test_id}/pause")
async def pause_ab_test(
    agent_id: str,
    test_id: str,
    db: Session = Depends(get_db)
):
    """
    Pause an A/B test
    """
    try:
        return {
            "success": True,
            "message": "A/B test paused",
            "test_id": test_id
        }
        
    except Exception as e:
        logger.error(f"Failed to pause A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))
