"""
Performance Monitoring API
성능 모니터링 API - 실시간 성능 최적화
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from backend.core.performance_optimizer import get_performance_optimizer, PerformanceOptimizer
from backend.core.structured_logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/performance",
    tags=["performance-monitoring"]
)

# Request/Response Models
class CachePreloadRequest(BaseModel):
    """캐시 사전 로드 요청"""
    preload_config: Dict[str, bool] = Field(description="사전 로드할 데이터 설정")

class CacheInvalidateRequest(BaseModel):
    """캐시 무효화 요청"""
    pattern: str = Field(description="무효화할 캐시 키 패턴")

class PerformanceMetricsResponse(BaseModel):
    """성능 메트릭 응답"""
    cache_hit_rate: float
    cache_size: int
    average_response_time: float
    active_connections: int
    cpu_usage: float
    memory_usage: float
    total_requests: int
    batch_queues: Dict[str, int]

class CacheStatsResponse(BaseModel):
    """캐시 통계 응답"""
    total_entries: int
    cache_size_mb: float
    hit_rate: float
    most_accessed_keys: List[Dict[str, Any]]
    expired_entries: int
    cleanup_stats: Dict[str, Any]

class OptimizationRecommendationsResponse(BaseModel):
    """최적화 권장사항 응답"""
    recommendations: List[Dict[str, Any]]
    priority_actions: List[str]
    performance_score: float
    bottlenecks: List[str]

@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)
):
    """
    성능 메트릭 조회
    
    시스템의 전반적인 성능 메트릭을 반환합니다.
    """
    try:
        logger.info("Getting performance metrics")
        
        metrics = optimizer.get_performance_metrics()
        
        response = PerformanceMetricsResponse(
            cache_hit_rate=metrics["cache_hit_rate"],
            cache_size=metrics["cache_size"],
            average_response_time=metrics["average_response_time"],
            active_connections=metrics["active_connections"],
            cpu_usage=metrics["cpu_usage"],
            memory_usage=metrics["memory_usage"],
            total_requests=metrics["total_requests"],
            batch_queues=metrics["batch_queues"]
        )
        
        logger.info("Performance metrics retrieved successfully")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)
):
    """
    캐시 통계 조회
    
    메모리 캐시의 상세한 통계 정보를 반환합니다.
    """
    try:
        logger.info("Getting cache statistics")
        
        # 캐시 엔트리 분석
        cache_entries = optimizer.memory_cache
        total_entries = len(cache_entries)
        
        # 캐시 크기 계산 (대략적)
        import sys
        cache_size_bytes = sum(sys.getsizeof(entry.data) for entry in cache_entries.values())
        cache_size_mb = cache_size_bytes / (1024 * 1024)
        
        # 히트율 계산
        total_requests = optimizer.metrics.cache_hits + optimizer.metrics.cache_misses
        hit_rate = optimizer.metrics.cache_hits / total_requests if total_requests > 0 else 0.0
        
        # 가장 많이 접근된 키들
        most_accessed = sorted(
            [
                {
                    "key": key,
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed.isoformat(),
                    "ttl_remaining": max(0, entry.ttl - (datetime.now() - entry.timestamp).total_seconds())
                }
                for key, entry in cache_entries.items()
            ],
            key=lambda x: x["access_count"],
            reverse=True
        )[:10]
        
        # 만료된 엔트리 수
        now = datetime.now()
        expired_entries = sum(
            1 for entry in cache_entries.values()
            if (now - entry.timestamp).total_seconds() > entry.ttl
        )
        
        # 정리 통계
        cleanup_stats = {
            "last_cleanup": "N/A",  # 실제로는 마지막 정리 시간을 추적해야 함
            "entries_cleaned": 0,   # 실제로는 정리된 엔트리 수를 추적해야 함
            "cleanup_frequency": optimizer.cache_config["cleanup_interval"]
        }
        
        response = CacheStatsResponse(
            total_entries=total_entries,
            cache_size_mb=cache_size_mb,
            hit_rate=hit_rate,
            most_accessed_keys=most_accessed,
            expired_entries=expired_entries,
            cleanup_stats=cleanup_stats
        )
        
        logger.info(f"Cache statistics retrieved: {total_entries} entries, {cache_size_mb:.2f} MB")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/cache/preload")
async def preload_cache(
    request: CachePreloadRequest,
    optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)
):
    """
    캐시 사전 로드
    
    자주 사용되는 데이터를 미리 캐시에 로드합니다.
    """
    try:
        logger.info(f"Preloading cache with config: {request.preload_config}")
        
        await optimizer.preload_cache(request.preload_config)
        
        return {
            "success": True,
            "message": "Cache preloading completed",
            "preloaded_items": list(request.preload_config.keys()),
            "cache_size_after": len(optimizer.memory_cache),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to preload cache: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to preload cache: {str(e)}")

@router.post("/cache/invalidate")
async def invalidate_cache(
    request: CacheInvalidateRequest,
    optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)
):
    """
    캐시 무효화
    
    지정된 패턴에 맞는 캐시 엔트리들을 무효화합니다.
    """
    try:
        logger.info(f"Invalidating cache with pattern: {request.pattern}")
        
        invalidated_count = optimizer.invalidate_cache(request.pattern)
        
        return {
            "success": True,
            "message": f"Cache invalidation completed",
            "pattern": request.pattern,
            "invalidated_entries": invalidated_count,
            "remaining_entries": len(optimizer.memory_cache),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

@router.delete("/cache/clear")
async def clear_cache(
    optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)
):
    """
    캐시 전체 삭제
    
    모든 캐시 엔트리를 삭제합니다.
    """
    try:
        logger.info("Clearing all cache entries")
        
        entries_before = len(optimizer.memory_cache)
        optimizer.memory_cache.clear()
        
        return {
            "success": True,
            "message": "All cache entries cleared",
            "cleared_entries": entries_before,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/optimization/recommendations", response_model=OptimizationRecommendationsResponse)
async def get_optimization_recommendations(
    optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)
):
    """
    최적화 권장사항 조회
    
    현재 성능 상태를 분석하여 최적화 권장사항을 제공합니다.
    """
    try:
        logger.info("Generating optimization recommendations")
        
        metrics = optimizer.get_performance_metrics()
        recommendations = []
        priority_actions = []
        bottlenecks = []
        
        # 캐시 히트율 분석
        if metrics["cache_hit_rate"] < 0.6:
            recommendations.append({
                "category": "caching",
                "title": "Improve Cache Hit Rate",
                "description": f"Current hit rate is {metrics['cache_hit_rate']:.2%}. Consider increasing cache TTL or preloading frequently accessed data.",
                "priority": "high",
                "impact": "high"
            })
            priority_actions.append("Optimize caching strategy")
            bottlenecks.append("Low cache hit rate")
        
        # CPU 사용률 분석
        if metrics["cpu_usage"] > 80:
            recommendations.append({
                "category": "cpu",
                "title": "High CPU Usage Detected",
                "description": f"CPU usage is at {metrics['cpu_usage']:.1f}%. Consider scaling up or optimizing algorithms.",
                "priority": "critical",
                "impact": "high"
            })
            priority_actions.append("Address high CPU usage")
            bottlenecks.append("High CPU utilization")
        
        # 메모리 사용률 분석
        if metrics["memory_usage"] > 85:
            recommendations.append({
                "category": "memory",
                "title": "High Memory Usage",
                "description": f"Memory usage is at {metrics['memory_usage']:.1f}%. Consider clearing unused cache or increasing memory.",
                "priority": "high",
                "impact": "medium"
            })
            priority_actions.append("Optimize memory usage")
            bottlenecks.append("High memory utilization")
        
        # 응답 시간 분석
        if metrics["average_response_time"] > 2.0:
            recommendations.append({
                "category": "response_time",
                "title": "Slow Response Times",
                "description": f"Average response time is {metrics['average_response_time']:.2f}s. Consider implementing request batching or caching.",
                "priority": "medium",
                "impact": "high"
            })
            bottlenecks.append("Slow response times")
        
        # 배치 큐 분석
        total_queued = sum(metrics["batch_queues"].values())
        if total_queued > 100:
            recommendations.append({
                "category": "batching",
                "title": "High Batch Queue Size",
                "description": f"Total queued requests: {total_queued}. Consider increasing batch processing frequency.",
                "priority": "medium",
                "impact": "medium"
            })
            bottlenecks.append("Request queue backlog")
        
        # 성능 점수 계산
        performance_score = (
            metrics["cache_hit_rate"] * 30 +
            max(0, (100 - metrics["cpu_usage"]) / 100) * 25 +
            max(0, (100 - metrics["memory_usage"]) / 100) * 25 +
            max(0, (5 - metrics["average_response_time"]) / 5) * 20
        )
        
        # 기본 권장사항 (성능이 좋을 때)
        if not recommendations:
            recommendations.append({
                "category": "general",
                "title": "System Performance is Optimal",
                "description": "All performance metrics are within acceptable ranges. Continue monitoring.",
                "priority": "low",
                "impact": "low"
            })
        
        response = OptimizationRecommendationsResponse(
            recommendations=recommendations,
            priority_actions=priority_actions,
            performance_score=performance_score,
            bottlenecks=bottlenecks
        )
        
        logger.info(f"Generated {len(recommendations)} optimization recommendations")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get optimization recommendations: {str(e)}")

@router.get("/batch-queues")
async def get_batch_queue_status(
    optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)
):
    """
    배치 큐 상태 조회
    
    현재 배치 처리 큐의 상태를 반환합니다.
    """
    try:
        batch_queues = {}
        
        for endpoint, queue in optimizer.batch_queues.items():
            queue_list = list(queue)
            batch_queues[endpoint] = {
                "queue_size": len(queue_list),
                "oldest_request": queue_list[0]["timestamp"] if queue_list else None,
                "newest_request": queue_list[-1]["timestamp"] if queue_list else None,
                "average_wait_time": 0  # 실제로는 계산해야 함
            }
        
        return {
            "batch_queues": batch_queues,
            "total_queued_requests": sum(q["queue_size"] for q in batch_queues.values()),
            "batch_config": optimizer.batch_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get batch queue status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get batch queue status: {str(e)}")

@router.get("/health")
async def get_performance_health(
    optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)
):
    """
    성능 건강 상태 조회
    
    시스템의 전반적인 성능 건강 상태를 간단히 반환합니다.
    """
    try:
        metrics = optimizer.get_performance_metrics()
        
        # 건강 상태 계산
        health_score = 100
        issues = []
        
        if metrics["cache_hit_rate"] < 0.5:
            health_score -= 20
            issues.append("Low cache hit rate")
        
        if metrics["cpu_usage"] > 90:
            health_score -= 30
            issues.append("Critical CPU usage")
        elif metrics["cpu_usage"] > 80:
            health_score -= 15
            issues.append("High CPU usage")
        
        if metrics["memory_usage"] > 95:
            health_score -= 25
            issues.append("Critical memory usage")
        elif metrics["memory_usage"] > 85:
            health_score -= 10
            issues.append("High memory usage")
        
        if metrics["average_response_time"] > 5:
            health_score -= 20
            issues.append("Very slow response times")
        elif metrics["average_response_time"] > 2:
            health_score -= 10
            issues.append("Slow response times")
        
        # 상태 결정
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 60:
            status = "fair"
        elif health_score >= 40:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": max(0, health_score),
            "issues": issues,
            "metrics_summary": {
                "cache_hit_rate": f"{metrics['cache_hit_rate']:.1%}",
                "cpu_usage": f"{metrics['cpu_usage']:.1f}%",
                "memory_usage": f"{metrics['memory_usage']:.1f}%",
                "avg_response_time": f"{metrics['average_response_time']:.2f}s"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance health: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get performance health: {str(e)}")