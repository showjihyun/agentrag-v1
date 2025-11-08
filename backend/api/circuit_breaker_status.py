"""
Circuit Breaker Status API

Provides endpoints for monitoring and managing circuit breakers.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.core.circuit_breaker import get_circuit_breaker_registry
from backend.core.enhanced_logging import get_logger

router = APIRouter(prefix="/api/circuit-breakers", tags=["Circuit Breakers"])
logger = get_logger(__name__)


@router.get("/status")
async def get_circuit_breaker_status() -> Dict[str, Any]:
    """
    Get status of all circuit breakers.
    
    Returns circuit breaker states and statistics.
    """
    registry = get_circuit_breaker_registry()
    
    states = registry.get_all_states()
    
    return {
        "circuit_breakers": states,
        "total_count": len(states),
        "open_count": sum(
            1 for state in states.values()
            if state["state"] == "open"
        ),
        "half_open_count": sum(
            1 for state in states.values()
            if state["state"] == "half_open"
        ),
    }


@router.post("/reset/{breaker_name}")
async def reset_circuit_breaker(breaker_name: str):
    """
    Manually reset a circuit breaker.
    
    Args:
        breaker_name: Name of circuit breaker to reset
    """
    registry = get_circuit_breaker_registry()
    
    breaker = registry.get(breaker_name)
    if not breaker:
        raise HTTPException(
            status_code=404,
            detail=f"Circuit breaker '{breaker_name}' not found"
        )
    
    await breaker.reset()
    
    logger.info(f"Circuit breaker reset: {breaker_name}")
    
    return {
        "message": f"Circuit breaker '{breaker_name}' reset successfully",
        "state": breaker.get_state()
    }


@router.post("/reset-all")
async def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    registry = get_circuit_breaker_registry()
    
    await registry.reset_all()
    
    logger.info("All circuit breakers reset")
    
    return {
        "message": "All circuit breakers reset successfully",
        "states": registry.get_all_states()
    }
