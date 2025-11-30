"""
Resilience API v1

Provides endpoints for monitoring and managing resilience patterns:
- Circuit breaker status
- Service health
- Retry statistics
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.core.api_response import api_response
from backend.core.circuit_breaker import (
    get_circuit_breaker_registry,
    CircuitState,
)


router = APIRouter(prefix="/api/v1/resilience", tags=["Resilience v1"])


# ============================================================================
# Response Models
# ============================================================================

class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status."""
    name: str
    state: str
    failure_count: int
    success_count: int
    last_failure_time: Optional[str] = None


class CircuitBreakerSummary(BaseModel):
    """Summary of all circuit breakers."""
    total: int
    closed: int
    open: int
    half_open: int
    breakers: Dict[str, CircuitBreakerStatus]


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/circuit-breakers",
    response_model=CircuitBreakerSummary,
    summary="Circuit Breaker Status",
    description="Get status of all circuit breakers.",
)
async def get_circuit_breakers():
    """Get status of all circuit breakers."""
    registry = get_circuit_breaker_registry()
    summary = registry.get_summary()
    
    return CircuitBreakerSummary(
        total=summary["total"],
        closed=summary["closed"],
        open=summary["open"],
        half_open=summary["half_open"],
        breakers={
            name: CircuitBreakerStatus(
                name=name,
                state=status["state"],
                failure_count=status["failure_count"],
                success_count=status["success_count"],
                last_failure_time=status["last_failure_time"],
            )
            for name, status in summary["breakers"].items()
        },
    )


@router.get(
    "/circuit-breakers/{name}",
    response_model=CircuitBreakerStatus,
    summary="Get Circuit Breaker",
    description="Get status of a specific circuit breaker.",
)
async def get_circuit_breaker(name: str):
    """Get status of a specific circuit breaker."""
    registry = get_circuit_breaker_registry()
    breaker = registry.get(name)
    
    if not breaker:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Circuit breaker not found: {name}"}
        )
    
    state = breaker.get_state()
    
    return CircuitBreakerStatus(
        name=name,
        state=state["state"],
        failure_count=state["failure_count"],
        success_count=state["success_count"],
        last_failure_time=state["last_failure_time"],
    )


@router.post(
    "/circuit-breakers/{name}/reset",
    summary="Reset Circuit Breaker",
    description="Manually reset a circuit breaker to closed state.",
)
async def reset_circuit_breaker(name: str):
    """Reset a circuit breaker to closed state."""
    registry = get_circuit_breaker_registry()
    breaker = registry.get(name)
    
    if not breaker:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Circuit breaker not found: {name}"}
        )
    
    await breaker.reset()
    
    return api_response(
        data={
            "name": name,
            "state": "closed",
            "message": f"Circuit breaker '{name}' reset successfully",
        }
    )


@router.post(
    "/circuit-breakers/reset-all",
    summary="Reset All Circuit Breakers",
    description="Reset all circuit breakers to closed state.",
)
async def reset_all_circuit_breakers():
    """Reset all circuit breakers."""
    registry = get_circuit_breaker_registry()
    await registry.reset_all()
    
    return api_response(
        data={
            "message": "All circuit breakers reset successfully",
            "count": len(registry._breakers),
        }
    )


@router.get(
    "/circuit-breakers/unhealthy",
    summary="Get Unhealthy Circuit Breakers",
    description="Get list of circuit breakers in OPEN state.",
)
async def get_unhealthy_circuit_breakers():
    """Get list of unhealthy (open) circuit breakers."""
    registry = get_circuit_breaker_registry()
    unhealthy = registry.get_unhealthy()
    
    return api_response(
        data={
            "unhealthy": unhealthy,
            "count": len(unhealthy),
            "all_healthy": len(unhealthy) == 0,
        }
    )


@router.get(
    "/health",
    summary="Resilience Health",
    description="Get overall resilience health status.",
)
async def get_resilience_health():
    """Get overall resilience health status."""
    registry = get_circuit_breaker_registry()
    summary = registry.get_summary()
    
    # Determine overall health
    if summary["open"] > 0:
        health_status = "degraded"
        health_message = f"{summary['open']} circuit breaker(s) are OPEN"
    elif summary["half_open"] > 0:
        health_status = "recovering"
        health_message = f"{summary['half_open']} circuit breaker(s) are recovering"
    else:
        health_status = "healthy"
        health_message = "All circuit breakers are healthy"
    
    return api_response(
        data={
            "status": health_status,
            "message": health_message,
            "circuit_breakers": {
                "total": summary["total"],
                "closed": summary["closed"],
                "open": summary["open"],
                "half_open": summary["half_open"],
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )
