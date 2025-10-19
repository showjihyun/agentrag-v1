"""
Multi-Provider Web Search Service

Google, Bing, DuckDuckGo를 우선순위에 따라 사용하는 통합 검색 서비스
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from enum import Enum

logger = logging.getLogger(__name__)


class SearchProvider(Enum):
    """검색 제공자"""
    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"


class WebSearchService:
    """
    멀티 프로바이더 웹 검색 서비스
    
    Features:
    - Google Custom Search API (우선순위 1)
    - Bing Search API (우선순위 2)
    - DuckDuckGo (폴백)
    - 자동 폴백 (API 실패 시)
    - 결과 통합 및 중복 제거
    """
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cse_id: Optional[str] = None,
        bing_api_key: Optional[str] = None,
        provider_priority: List[SearchProvider] = None,
        timeout: float = 10.0
    ):
        """
        초기화
        
        Args:
            google_api_key: Google Custom Search API 키
            google_cse_id: Google Custom Search Engine ID
            bing_api_key: Bing Search API 키
            provider_priority: 검색 제공자 우선순위
            timeout: HTTP 요청 타임아웃
        """
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id
        self.bing_api_key = bing_api_key
        self.timeout = timeout
        
        # 우선순위 설정
        if provider_priority is None:
            # 기본 우선순위: Google > Bing > DuckDuckGo
            self.provider_priority = [
                SearchProvider.GOOGLE,
                SearchProvider.BING,
                SearchProvider.DUCKDUCKGO
            ]
        else:
            self.provider_priority = provider_priority
        
        # 사용 가능한 제공자 확인
        self.available_providers = self._check_available_providers()
        
        logger.info(
            f"WebSearchService initialized: "
            f"providers={[p.value for p in self.available_providers]}, "
            f"timeout={timeout}s"
        )
    
    def _check_available_providers(self) -> List[SearchProvider]:
        """사용 가능한 검색 제공자 확인"""
        available = []
        
        # Google 확인
        if self.google_api_key and self.google_cse_id:
            available.append(SearchProvider.GOOGLE)
            logger.info("✅ Google Search API 사용 가능")
        else:
            logger.info("ℹ️  Google Search API 미설정 (API 키 또는 CSE ID 필요)")
        
        # Bing 확인
        if self.bing_api_key:
            available.append(SearchProvider.BING)
            logger.info("✅ Bing Search API 사용 가능")
        else:
            logger.info("ℹ️  Bing Search API 미설정 (API 키 필요)")
        
        # DuckDuckGo는 항상 사용 가능 (API 키 불필요)
        available.append(SearchProvider.DUCKDUCKGO)
        logger.info("✅ DuckDuckGo Search 사용 가능 (폴백)")
        
        return available
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        language: str = "ko",
        region: str = "kr"
    ) -> List[Dict[str, Any]]:
        """
        웹 검색 실행 (우선순위에 따라 자동 폴백)
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            language: 언어 코드 (ko, en 등)
            region: 지역 코드 (kr, us 등)
            
        Returns:
            검색 결과 리스트
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        logger.info(f"🔍 Web search: '{query[:50]}...' (max={max_results})")
        
        # 우선순위에 따라 검색 시도
        for provider in self.provider_priority:
            if provider not in self.available_providers:
                continue
            
            try:
                logger.info(f"   Trying {provider.value}...")
                
                if provider == SearchProvider.GOOGLE:
                    results = await self._search_google(query, max_results, language, region)
                elif provider == SearchProvider.BING:
                    results = await self._search_bing(query, max_results, language, region)
                elif provider == SearchProvider.DUCKDUCKGO:
                    results = await self._search_duckduckgo(query, max_results, region)
                else:
                    continue
                
                if results:
                    logger.info(f"   ✅ {provider.value}: {len(results)} results")
                    return results
                else:
                    logger.warning(f"   ⚠️  {provider.value}: No results")
                    
            except Exception as e:
                logger.warning(f"   ❌ {provider.value} failed: {e}")
                continue
        
        # 모든 제공자 실패
        logger.error("All search providers failed")
        return []
    
    async def _search_google(
        self,
        query: str,
        max_results: int,
        language: str,
        region: str
    ) -> List[Dict[str, Any]]:
        """
        Google Custom Search API로 검색
        
        API 키 발급: https://developers.google.com/custom-search/v1/overview
        CSE ID 생성: https://programmablesearchengine.google.com/
        """
        if not self.google_api_key or not self.google_cse_id:
            raise ValueError("Google API key or CSE ID not configured")
        
        url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": query,
            "num": min(max_results, 10),  # Google API 최대 10개
            "lr": f"lang_{language}",
            "gl": region
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "google",
                "metadata": {
                    "displayLink": item.get("displayLink"),
                    "formattedUrl": item.get("formattedUrl")
                }
            })
        
        return results
    
    async def _search_bing(
        self,
        query: str,
        max_results: int,
        language: str,
        region: str
    ) -> List[Dict[str, Any]]:
        """
        Bing Search API로 검색
        
        API 키 발급: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
        """
        if not self.bing_api_key:
            raise ValueError("Bing API key not configured")
        
        url = "https://api.bing.microsoft.com/v7.0/search"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.bing_api_key
        }
        
        params = {
            "q": query,
            "count": max_results,
            "mkt": f"{language}-{region.upper()}",  # ko-KR, en-US 등
            "responseFilter": "Webpages"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("webPages", {}).get("value", []):
            results.append({
                "title": item.get("name", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
                "source": "bing",
                "metadata": {
                    "dateLastCrawled": item.get("dateLastCrawled"),
                    "language": item.get("language")
                }
            })
        
        return results
    
    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
        region: str
    ) -> List[Dict[str, Any]]:
        """
        DuckDuckGo로 검색 (폴백)
        """
        try:
            from duckduckgo_search import DDGS
            
            ddgs = DDGS()
            results = []
            
            # 동기 API를 비동기로 래핑
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None,
                lambda: list(ddgs.text(query, max_results=max_results, region=region))
            )
            
            for item in search_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                    "source": "duckduckgo"
                })
            
            return results
            
        except ImportError:
            logger.warning("duckduckgo-search not installed, using HTML fallback")
            return await self._search_duckduckgo_html(query, max_results, region)
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def _search_duckduckgo_html(
        self,
        query: str,
        max_results: int,
        region: str
    ) -> List[Dict[str, Any]]:
        """DuckDuckGo HTML 검색 (최종 폴백)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query, "kl": f"{region}-{region}"},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                response.raise_for_status()
                
                # HTML 파싱
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                
                results = []
                result_divs = soup.find_all("div", class_="result", limit=max_results)
                
                for div in result_divs:
                    title_elem = div.find("a", class_="result__a")
                    if not title_elem:
                        continue
                    
                    snippet_elem = div.find("a", class_="result__snippet")
                    
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": title_elem.get("href", ""),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                        "source": "duckduckgo"
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"DuckDuckGo HTML search failed: {e}")
            return []
    
    async def search_with_fallback(
        self,
        query: str,
        max_results: int = 10,
        language: str = "ko",
        region: str = "kr"
    ) -> Dict[str, Any]:
        """
        폴백을 포함한 검색 (어떤 제공자를 사용했는지 반환)
        
        Returns:
            {
                "results": [...],
                "provider": "google",
                "total": 10,
                "query": "...",
                "timestamp": "..."
            }
        """
        for provider in self.provider_priority:
            if provider not in self.available_providers:
                continue
            
            try:
                if provider == SearchProvider.GOOGLE:
                    results = await self._search_google(query, max_results, language, region)
                elif provider == SearchProvider.BING:
                    results = await self._search_bing(query, max_results, language, region)
                else:
                    results = await self._search_duckduckgo(query, max_results, region)
                
                if results:
                    return {
                        "results": results,
                        "provider": provider.value,
                        "total": len(results),
                        "query": query,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
            except Exception as e:
                logger.warning(f"{provider.value} failed: {e}")
                continue
        
        # 모든 제공자 실패
        return {
            "results": [],
            "provider": "none",
            "total": 0,
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "error": "All search providers failed"
        }


# 싱글톤 인스턴스
_web_search_service = None


def get_web_search_service(
    google_api_key: Optional[str] = None,
    google_cse_id: Optional[str] = None,
    bing_api_key: Optional[str] = None
) -> WebSearchService:
    """Web Search Service 싱글톤 인스턴스 반환"""
    global _web_search_service
    
    if _web_search_service is None:
        # 환경 변수에서 API 키 로드
        from backend.config import settings
        import os
        
        google_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        google_cse = google_cse_id or os.getenv("GOOGLE_CSE_ID")
        bing_key = bing_api_key or os.getenv("BING_API_KEY")
        
        _web_search_service = WebSearchService(
            google_api_key=google_key,
            google_cse_id=google_cse,
            bing_api_key=bing_key
        )
    
    return _web_search_service
