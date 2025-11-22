"""DuckDuckGo Search tool executor."""

from typing import Dict, Any, Optional
from duckduckgo_search import DDGS

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class DuckDuckGoExecutor(BaseToolExecutor):
    """Executor for DuckDuckGo Search tool."""
    
    def __init__(self):
        super().__init__("duckduckgo_search", "DuckDuckGo Search")
        self.category = "search"
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute DuckDuckGo search."""
        
        self.validate_params(params, ["query"])
        
        query = params.get("query")
        max_results = params.get("max_results", 10)
        region = params.get("region", "wt-wt")
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    region=region,
                    max_results=max_results
                ))
                
                return ToolExecutionResult(
                    success=True,
                    output={
                        "results": results,
                        "count": len(results)
                    },
                    metadata={
                        "query": query,
                        "region": region
                    }
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Search failed: {str(e)}"
            )
