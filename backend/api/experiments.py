"""
A/B Testing Experiments API

Endpoints for managing and analyzing A/B tests
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from backend.services.ab_testing_framework import (
    ABTestingFramework,
    ExperimentStatus,
    VariantType,
    Experiment,
    ExperimentResult,
)
from backend.core.dependencies import get_ab_testing_framework

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


# Request/Response Models


class VariantConfig(BaseModel):
    """Variant configuration"""

    name: str = Field(..., description="Variant name")
    type: str = Field(
        default="treatment", description="Variant type: control or treatment"
    )
    traffic_percentage: float = Field(
        ..., ge=0.0, le=1.0, description="Traffic percentage (0-1)"
    )
    config: Dict[str, Any] = Field(..., description="Variant configuration")
    description: str = Field(default="", description="Variant description")


class CreateExperimentRequest(BaseModel):
    """Create experiment request"""

    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description")
    variants: List[VariantConfig] = Field(
        ..., min_items=2, description="Experiment variants"
    )
    min_sample_size: int = Field(
        default=1000, ge=10, description="Minimum sample size per variant"
    )
    confidence_level: float = Field(
        default=0.95, ge=0.5, le=0.99, description="Statistical confidence level"
    )


class ExperimentResponse(BaseModel):
    """Experiment response"""

    id: str
    name: str
    description: str
    status: str
    variants: List[Dict[str, Any]]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    min_sample_size: int
    confidence_level: float
    winner: Optional[str]
    statistical_significance: Optional[float]
    results: Dict[str, Any]


class RecordOutcomeRequest(BaseModel):
    """Record outcome request"""

    experiment_id: str
    variant_id: str
    metrics: Dict[str, float] = Field(
        ...,
        description="Metrics: latency, satisfaction, error_rate, cache_hit_rate, routing_accuracy",
    )


class AnalysisResponse(BaseModel):
    """Analysis response"""

    experiment_id: str
    winner: Optional[str]
    statistical_significance: float
    confidence_level: float
    metrics_comparison: Dict[str, Dict[str, float]]
    recommendation: str
    details: Dict[str, Any]


# Endpoints


@router.post(
    "/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED
)
async def create_experiment(
    request: CreateExperimentRequest,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """
    Create a new A/B test experiment

    Example:
    ```json
    {
      "name": "Threshold Optimization Test",
      "description": "Test different complexity thresholds",
      "variants": [
        {
          "name": "control",
          "type": "control",
          "traffic_percentage": 0.5,
          "config": {
            "simple_threshold": 0.35,
            "complex_threshold": 0.70
          }
        },
        {
          "name": "treatment_a",
          "type": "treatment",
          "traffic_percentage": 0.5,
          "config": {
            "simple_threshold": 0.30,
            "complex_threshold": 0.75
          }
        }
      ],
      "min_sample_size": 1000,
      "confidence_level": 0.95
    }
    ```
    """
    try:
        variants_data = [v.dict() for v in request.variants]

        experiment = await framework.create_experiment(
            name=request.name,
            description=request.description,
            variants=variants_data,
            min_sample_size=request.min_sample_size,
            confidence_level=request.confidence_level,
        )

        return _experiment_to_response(experiment)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments(
    status_filter: Optional[str] = None,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """
    List all experiments

    Query parameters:
    - status: Filter by status (draft, running, paused, completed, cancelled)
    """
    try:
        experiment_status = ExperimentStatus(status_filter) if status_filter else None
        experiments = await framework.list_experiments(status=experiment_status)

        return [_experiment_to_response(e) for e in experiments]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_filter}",
        )


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """Get experiment by ID"""
    experiment = await framework.get_experiment(experiment_id)

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment not found: {experiment_id}",
        )

    return _experiment_to_response(experiment)


@router.post("/{experiment_id}/start", response_model=ExperimentResponse)
async def start_experiment(
    experiment_id: str,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """Start an experiment"""
    try:
        await framework.start_experiment(experiment_id)
        experiment = await framework.get_experiment(experiment_id)
        return _experiment_to_response(experiment)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{experiment_id}/pause", response_model=ExperimentResponse)
async def pause_experiment(
    experiment_id: str,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """Pause a running experiment"""
    try:
        await framework.pause_experiment(experiment_id)
        experiment = await framework.get_experiment(experiment_id)
        return _experiment_to_response(experiment)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{experiment_id}/resume", response_model=ExperimentResponse)
async def resume_experiment(
    experiment_id: str,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """Resume a paused experiment"""
    try:
        await framework.resume_experiment(experiment_id)
        experiment = await framework.get_experiment(experiment_id)
        return _experiment_to_response(experiment)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{experiment_id}/stop", response_model=ExperimentResponse)
async def stop_experiment(
    experiment_id: str,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """Stop an experiment"""
    try:
        await framework.stop_experiment(experiment_id)
        experiment = await framework.get_experiment(experiment_id)
        return _experiment_to_response(experiment)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/outcomes", status_code=status.HTTP_204_NO_CONTENT)
async def record_outcome(
    request: RecordOutcomeRequest,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """
    Record experiment outcome

    Example:
    ```json
    {
      "experiment_id": "abc123",
      "variant_id": "abc123_treatment_a",
      "metrics": {
        "latency": 2.5,
        "satisfaction": 4.5,
        "error_rate": 0.01,
        "cache_hit_rate": 0.65,
        "routing_accuracy": 0.88
      }
    }
    ```
    """
    await framework.record_outcome(
        experiment_id=request.experiment_id,
        variant_id=request.variant_id,
        metrics=request.metrics,
    )


@router.get("/{experiment_id}/analysis", response_model=AnalysisResponse)
async def analyze_experiment(
    experiment_id: str,
    framework: ABTestingFramework = Depends(get_ab_testing_framework),
):
    """
    Analyze experiment results

    Returns statistical analysis with winner determination
    """
    try:
        result = await framework.analyze_results(experiment_id)

        return AnalysisResponse(
            experiment_id=result.experiment_id,
            winner=result.winner,
            statistical_significance=result.statistical_significance,
            confidence_level=result.confidence_level,
            metrics_comparison=result.metrics_comparison,
            recommendation=result.recommendation,
            details=result.details,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Helper functions


def _experiment_to_response(experiment: Experiment) -> ExperimentResponse:
    """Convert Experiment to response model"""
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        description=experiment.description,
        status=experiment.status.value,
        variants=[
            {
                "id": v.id,
                "name": v.name,
                "type": v.type.value,
                "traffic_percentage": v.traffic_percentage,
                "config": v.config,
                "description": v.description,
                "queries_count": v.queries_count,
                "avg_latency": v.avg_latency,
                "avg_satisfaction": v.avg_satisfaction,
                "error_rate": v.error_rate,
                "cache_hit_rate": v.cache_hit_rate,
                "routing_accuracy": v.routing_accuracy,
            }
            for v in experiment.variants
        ],
        start_date=experiment.start_date,
        end_date=experiment.end_date,
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        min_sample_size=experiment.min_sample_size,
        confidence_level=experiment.confidence_level,
        winner=experiment.winner,
        statistical_significance=experiment.statistical_significance,
        results=experiment.results,
    )
