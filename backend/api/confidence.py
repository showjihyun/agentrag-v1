"""
Confidence API Endpoints

Provides endpoints for confidence prediction and feedback
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from backend.services.confidence_service import get_confidence_service
from backend.ml.confidence_predictor import ConfidenceFeatures

router = APIRouter(prefix="/api/confidence", tags=["confidence"])


class ConfidenceRequest(BaseModel):
    """Request for confidence calculation"""

    query: str = Field(..., description="User query")
    sources: List[Dict] = Field(default_factory=list, description="Retrieved sources")
    response: str = Field(..., description="Generated response")
    mode: str = Field("balanced", description="Query mode")
    reasoning_steps: int = Field(0, description="Number of reasoning steps")
    has_memory: bool = Field(False, description="Has memory context")
    cache_hit: bool = Field(False, description="Cache hit")
    user_history: Optional[Dict] = Field(None, description="User history")


class ConfidenceResponse(BaseModel):
    """Response with confidence score"""

    confidence: float = Field(..., description="Confidence score (0-1)")
    method: str = Field(..., description="Method used (ml/blended/heuristic)")
    uncertainty: Optional[float] = Field(None, description="Uncertainty estimate")
    features: Dict = Field(..., description="Extracted features")


class FeedbackRequest(BaseModel):
    """Request for recording feedback"""

    query: str
    sources: List[Dict]
    response: str
    mode: str
    actual_feedback: float = Field(..., ge=0.0, le=1.0, description="User rating (0-1)")
    reasoning_steps: int = 0
    has_memory: bool = False
    cache_hit: bool = False
    user_history: Optional[Dict] = None


@router.post("/calculate", response_model=ConfidenceResponse)
async def calculate_confidence(request: ConfidenceRequest):
    """
    Calculate confidence score for a query response

    Uses ML-based prediction with heuristic fallback
    """
    try:
        service = get_confidence_service(use_ml=True)

        result = service.calculate_confidence(
            query=request.query,
            sources=request.sources,
            response=request.response,
            mode=request.mode,
            reasoning_steps=request.reasoning_steps,
            has_memory=request.has_memory,
            cache_hit=request.cache_hit,
            user_history=request.user_history,
        )

        return ConfidenceResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Confidence calculation failed: {str(e)}"
        )


@router.post("/feedback")
async def record_feedback(request: FeedbackRequest):
    """
    Record user feedback for model improvement

    Feedback is used to train the ML model
    """
    try:
        service = get_confidence_service(use_ml=True)

        service.record_feedback(
            query=request.query,
            sources=request.sources,
            response=request.response,
            mode=request.mode,
            actual_feedback=request.actual_feedback,
            reasoning_steps=request.reasoning_steps,
            has_memory=request.has_memory,
            cache_hit=request.cache_hit,
            user_history=request.user_history,
        )

        return {"status": "success", "message": "Feedback recorded"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Feedback recording failed: {str(e)}"
        )


@router.post("/train")
async def train_model(learning_rate: float = 0.01, epochs: int = 100):
    """
    Manually trigger model training

    Requires at least 100 feedback samples
    """
    try:
        from backend.ml.confidence_predictor import get_confidence_predictor

        predictor = get_confidence_predictor()

        if len(predictor.training_data) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough training data. Have {len(predictor.training_data)}, need at least 10",
            )

        predictor.train(learning_rate=learning_rate, epochs=epochs)

        return {
            "status": "success",
            "message": "Model trained successfully",
            "samples": len(predictor.training_data),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/stats")
async def get_stats():
    """Get confidence prediction statistics"""
    try:
        from backend.ml.confidence_predictor import get_confidence_predictor
        import os

        predictor = get_confidence_predictor()

        # Check if model exists
        model_exists = os.path.exists(predictor.model_path)

        # Get metadata if available
        metadata = {}
        metadata_path = predictor.model_path.replace(".json", "_metadata.json")
        if os.path.exists(metadata_path):
            import json

            with open(metadata_path, "r") as f:
                metadata = json.load(f)

        return {
            "model_exists": model_exists,
            "model_path": predictor.model_path,
            "training_samples_pending": len(predictor.training_data),
            "metadata": metadata,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")
