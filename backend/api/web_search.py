"""
Web Search API Endpoint

DuckDuckGo를 사용한 무료 웹 검색 API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from backend.services.web_search_service import get_web_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web-search", tags=["web-search"])


class SearchResult(BaseModel):
    """검색 결과 모델"""
    title: str
    url: str
    snippet: str
    source: str
    metadata: Optional[dict] = None


class SearchResponse(BaseModel):
    """검색 응답 모델"""
    results: List[SearchResult]
    provider: str
    total: int
    query: str
    timestamp: str
    error: Optional[str] = None


@router.get("/search", response_model=SearchResponse)
async def search_web(
    q: str = Query(..., description="검색 쿼리", min_length=1),
    max_results: int = Query(10, description="최대 결과 수", ge=1, le=50),
    language: str = Query("ko", description="언어 코드 (ko, en 등)"),
    region: str = Query("kr", description="지역 코드 (kr, us 등)")
):
    """
    웹 검색 실행
    
    DuckDuckGo를 사용하여 웹 검색을 수행합니다.
    
    - **q**: 검색 쿼리 (필수)
    - **max_results**: 최대 결과 수 (기본값: 10)
    - **language**: 언어 코드 (기본값: ko)
    - **region**: 지역 코드 (기본값: kr)
    """
    try:
        logger.info(f"Web search request: query='{q}', max_results={max_results}")
        
        # Web Search Service 가져오기
        search_service = get_web_search_service()
        
        # 검색 실행
        response = await search_service.search_with_fallback(
            query=q,
            max_results=max_results,
            language=language,
            region=region
        )
        
        return SearchResponse(**response)
        
    except Exception as e:
        logger.error(f"Web search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Web search failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Web Search 서비스 상태 확인
    """
    try:
        search_service = get_web_search_service()
        
        return {
            "status": "healthy",
            "available_providers": [p.value for p in search_service.available_providers],
            "priority": [p.value for p in search_service.provider_priority]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
