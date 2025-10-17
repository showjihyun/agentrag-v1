"""
ReAct Statistics API Endpoints.

Provides real-time statistics and metrics for ReAct improvements:
- Episodic Memory statistics
- Observation Processing metrics
- Retry Handler statistics
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.dependencies import get_aggregator_agent, get_performance_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/react", tags=["react-statistics"])


@router.get("/statistics")
async def get_react_statistics(
    aggregator_agent=Depends(get_aggregator_agent),
) -> Dict[str, Any]:
    """
    Get comprehensive ReAct system statistics.

    Returns statistics for:
    - Episodic Memory (pattern reuse)
    - Observation Processing (relevance filtering)
    - Overall system metrics

    Returns:
        Dictionary with all statistics
    """
    try:
        # Get episodic memory statistics
        episodic_stats = aggregator_agent.episodic_memory.get_statistics()

        # Get observation processor statistics
        observation_stats = aggregator_agent.observation_processor.get_statistics()

        # Calculate derived metrics
        total_queries = episodic_stats.get("total_episodes", 0)
        total_reuses = episodic_stats.get("total_reuses", 0)
        reuse_rate = (
            round(total_reuses / max(total_queries, 1), 3) if total_queries > 0 else 0.0
        )

        return {
            "status": "success",
            "episodic_memory": {**episodic_stats, "reuse_rate": reuse_rate},
            "observation_processing": observation_stats,
            "system_metrics": {
                "total_queries_processed": total_queries,
                "pattern_reuse_rate": reuse_rate,
                "avg_observations_filtered": observation_stats.get("filter_rate", 0.0),
            },
        }

    except Exception as e:
        logger.error(f"Error getting ReAct statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get("/statistics/episodic-memory")
async def get_episodic_memory_statistics(
    aggregator_agent=Depends(get_aggregator_agent),
) -> Dict[str, Any]:
    """
    Get episodic memory statistics.

    Returns:
        Episodic memory statistics including:
        - Total episodes stored
        - Average confidence
        - Average iterations
        - Reuse statistics
    """
    try:
        stats = aggregator_agent.episodic_memory.get_statistics()
        return {"status": "success", "data": stats}

    except Exception as e:
        logger.error(f"Error getting episodic memory statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get episodic memory statistics: {str(e)}",
        )


@router.get("/statistics/observation-processing")
async def get_observation_processing_statistics(
    aggregator_agent=Depends(get_aggregator_agent),
) -> Dict[str, Any]:
    """
    Get observation processing statistics.

    Returns:
        Observation processing statistics including:
        - Total observations processed
        - Filter rate
        - Average relevance score
    """
    try:
        stats = aggregator_agent.observation_processor.get_statistics()
        return {"status": "success", "data": stats}

    except Exception as e:
        logger.error(f"Error getting observation processing statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get observation processing statistics: {str(e)}",
        )


@router.post("/statistics/reset")
async def reset_statistics(
    aggregator_agent=Depends(get_aggregator_agent),
) -> Dict[str, str]:
    """
    Reset all ReAct statistics counters.

    This will reset:
    - Observation processing statistics

    Note: Episodic memory episodes are NOT deleted, only counters are reset.

    Returns:
        Success message
    """
    try:
        # Reset observation processor statistics
        aggregator_agent.observation_processor.reset_statistics()

        logger.info("ReAct statistics reset")

        return {"status": "success", "message": "Statistics reset successfully"}

    except Exception as e:
        logger.error(f"Error resetting statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset statistics: {str(e)}",
        )


@router.get("/health")
async def react_health_check(
    aggregator_agent=Depends(get_aggregator_agent),
) -> Dict[str, Any]:
    """
    Health check for ReAct improvements.

    Returns:
        Health status of all ReAct components
    """
    try:
        health = {
            "status": "healthy",
            "components": {
                "episodic_memory": {
                    "status": "healthy",
                    "episodes_count": len(
                        aggregator_agent.episodic_memory.episode_cache
                    ),
                },
                "observation_processor": {
                    "status": "healthy",
                    "processing_count": aggregator_agent.observation_processor.stats[
                        "processing_count"
                    ],
                },
                "retry_handler": {
                    "status": "healthy",
                    "max_retries": aggregator_agent.retry_handler.max_retries,
                },
            },
        }

        return health

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {"status": "unhealthy", "error": str(e)}
