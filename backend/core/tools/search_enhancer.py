"""
Search API Enhancer
Improves reliability and handles various search API responses.
"""

import asyncio
import logging
import httpx
from typing import Dict, List, Any, Optional
import json
import time

logger = logging.getLogger(__name__)


class SearchAPIEnhancer:
    """Enhances search API reliability with retry logic and fallbacks."""
    
    def __init__(self):
        self.timeout = 10.0
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def enhanced_duckduckgo_search(
        self, 
        query: str, 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Enhanced DuckDuckGo search with retry logic and fallbacks.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Search results dictionary
        """
        # Try multiple DuckDuckGo endpoints
        endpoints = [
            # Instant Answer API
            {
                "url": "https://api.duckduckgo.com/",
                "params": {
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                },
                "parser": self._parse_duckduckgo_instant
            },
            # HTML scraping fallback (simplified)
            {
                "url": "https://html.duckduckgo.com/html/",
                "params": {
                    "q": query
                },
                "parser": self._parse_duckduckgo_html
            }
        ]
        
        for endpoint in endpoints:
            try:
                result = await self._try_search_endpoint(
                    endpoint["url"],
                    endpoint["params"],
                    endpoint["parser"]
                )
                
                if result and result.get("results"):
                    # Limit results
                    results = result["results"][:max_results]
                    return {
                        "results": results,
                        "total_results": len(results),
                        "source": "duckduckgo",
                        "query": query
                    }
                    
            except Exception as e:
                logger.warning(f"DuckDuckGo endpoint failed: {e}")
                continue
        
        # If all endpoints fail, return empty results
        return {
            "results": [],
            "total_results": 0,
            "source": "duckduckgo",
            "query": query,
            "error": "All search endpoints failed"
        }
    
    async def enhanced_wikipedia_search(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Enhanced Wikipedia search with multiple endpoints.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Search results dictionary
        """
        endpoints = [
            # Wikipedia API search
            {
                "url": "https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
                "parser": self._parse_wikipedia_summary
            },
            # Wikipedia search API
            {
                "url": "https://en.wikipedia.org/w/api.php",
                "params": {
                    "action": "query",
                    "format": "json",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": max_results
                },
                "parser": self._parse_wikipedia_search
            }
        ]
        
        for endpoint in endpoints:
            try:
                if "{query}" in endpoint["url"]:
                    # Direct page summary
                    url = endpoint["url"].format(query=query.replace(" ", "_"))
                    result = await self._try_search_endpoint(
                        url, {}, endpoint["parser"]
                    )
                else:
                    # Search API
                    result = await self._try_search_endpoint(
                        endpoint["url"],
                        endpoint["params"],
                        endpoint["parser"]
                    )
                
                if result and result.get("results"):
                    return {
                        "results": result["results"][:max_results],
                        "total_results": len(result["results"]),
                        "source": "wikipedia",
                        "query": query
                    }
                    
            except Exception as e:
                logger.warning(f"Wikipedia endpoint failed: {e}")
                continue
        
        return {
            "results": [],
            "total_results": 0,
            "source": "wikipedia", 
            "query": query,
            "error": "All Wikipedia endpoints failed"
        }
    
    async def _try_search_endpoint(
        self,
        url: str,
        params: Dict[str, Any],
        parser: callable
    ) -> Optional[Dict[str, Any]]:
        """
        Try a search endpoint with retry logic.
        
        Args:
            url: Endpoint URL
            params: Query parameters
            parser: Response parser function
            
        Returns:
            Parsed results or None
        """
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)
                    
                    # Handle different status codes
                    if response.status_code == 200:
                        data = response.json()
                        return parser(data)
                    elif response.status_code == 202:
                        # Accepted - wait and retry
                        logger.info(f"Received 202, waiting {self.retry_delay}s...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    elif response.status_code == 403:
                        # Forbidden - try different user agent
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                        response = await client.get(url, params=params, headers=headers)
                        if response.status_code == 200:
                            data = response.json()
                            return parser(data)
                    else:
                        logger.warning(f"HTTP {response.status_code} from {url}")
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def _parse_duckduckgo_instant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DuckDuckGo Instant Answer API response."""
        results = []
        
        # Check for abstract
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "DuckDuckGo Result"),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("Abstract", ""),
                "source": "duckduckgo_instant"
            })
        
        # Check for definition
        if data.get("Definition"):
            results.append({
                "title": data.get("DefinitionSource", "Definition"),
                "url": data.get("DefinitionURL", ""),
                "snippet": data.get("Definition", ""),
                "source": "duckduckgo_definition"
            })
        
        # Check for related topics
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0],
                    "url": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                    "source": "duckduckgo_related"
                })
        
        return {"results": results}
    
    def _parse_duckduckgo_html(self, data: Any) -> Dict[str, Any]:
        """Parse DuckDuckGo HTML response (simplified)."""
        # This would require HTML parsing - simplified for now
        return {"results": []}
    
    def _parse_wikipedia_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Wikipedia summary API response."""
        if data.get("type") == "standard":
            return {
                "results": [{
                    "title": data.get("title", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "snippet": data.get("extract", ""),
                    "source": "wikipedia_summary"
                }]
            }
        return {"results": []}
    
    def _parse_wikipedia_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Wikipedia search API response."""
        results = []
        
        search_results = data.get("query", {}).get("search", [])
        for item in search_results:
            results.append({
                "title": item.get("title", ""),
                "url": f"https://en.wikipedia.org/wiki/{item.get('title', '').replace(' ', '_')}",
                "snippet": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                "source": "wikipedia_search"
            })
        
        return {"results": results}
    
    async def test_search_apis(self) -> Dict[str, Any]:
        """
        Test various search APIs to check availability.
        
        Returns:
            Test results dictionary
        """
        test_query = "artificial intelligence"
        results = {}
        
        # Test DuckDuckGo
        start_time = time.time()
        try:
            duckduckgo_result = await self.enhanced_duckduckgo_search(test_query, 3)
            results["duckduckgo"] = {
                "status": "success" if duckduckgo_result.get("results") else "no_results",
                "response_time": (time.time() - start_time) * 1000,
                "results_count": len(duckduckgo_result.get("results", [])),
                "error": duckduckgo_result.get("error")
            }
        except Exception as e:
            results["duckduckgo"] = {
                "status": "error",
                "response_time": (time.time() - start_time) * 1000,
                "error": str(e)
            }
        
        # Test Wikipedia
        start_time = time.time()
        try:
            wikipedia_result = await self.enhanced_wikipedia_search(test_query, 3)
            results["wikipedia"] = {
                "status": "success" if wikipedia_result.get("results") else "no_results",
                "response_time": (time.time() - start_time) * 1000,
                "results_count": len(wikipedia_result.get("results", [])),
                "error": wikipedia_result.get("error")
            }
        except Exception as e:
            results["wikipedia"] = {
                "status": "error",
                "response_time": (time.time() - start_time) * 1000,
                "error": str(e)
            }
        
        return results


# Global instance
search_enhancer = SearchAPIEnhancer()