"""
Notion tool executor.
"""
from typing import Any, Dict, Optional
import httpx

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class NotionExecutor(BaseToolExecutor):
    """Executor for Notion operations."""
    
    def __init__(self):
        super().__init__("notion", "Notion")
        self.category = "productivity"
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute Notion operation."""
        
        api_key = credentials.get("api_key") if credentials else None
        if not api_key:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="Notion API key is required"
            )
        
        self.validate_params(params, ["operation"])
        operation = params.get("operation")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                if operation == "create_page":
                    result = await self._create_page(client, headers, params)
                elif operation == "query_database":
                    result = await self._query_database(client, headers, params)
                elif operation == "update_page":
                    result = await self._update_page(client, headers, params)
                else:
                    return ToolExecutionResult(
                        success=False,
                        output=None,
                        error=f"Unknown operation: {operation}"
                    )
                
                return ToolExecutionResult(success=True, output=result)
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    async def _create_page(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a Notion page."""
        self.validate_params(params, ["database_id"])
        
        database_id = params.get("database_id")
        properties = params.get("properties", {})
        content = params.get("content", [])
        
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        
        if content:
            payload["children"] = content
        
        response = await client.post(
            "https://api.notion.com/v1/pages",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "page_id": result["id"],
            "url": result["url"],
            "created_time": result["created_time"],
        }
    
    async def _query_database(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Query a Notion database."""
        self.validate_params(params, ["database_id"])
        
        database_id = params.get("database_id")
        filter_params = params.get("filter")
        sorts = params.get("sorts")
        page_size = params.get("page_size", 100)
        
        payload = {"page_size": page_size}
        if filter_params:
            payload["filter"] = filter_params
        if sorts:
            payload["sorts"] = sorts
        
        response = await client.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        result = response.json()
        pages = result.get("results", [])
        
        return {
            "count": len(pages),
            "has_more": result.get("has_more", False),
            "pages": [
                {
                    "id": page["id"],
                    "url": page["url"],
                    "properties": page.get("properties", {}),
                }
                for page in pages
            ],
        }
    
    async def _update_page(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a Notion page."""
        self.validate_params(params, ["page_id"])
        
        page_id = params.get("page_id")
        properties = params.get("properties", {})
        
        payload = {"properties": properties}
        
        response = await client.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "page_id": result["id"],
            "url": result["url"],
            "last_edited_time": result["last_edited_time"],
        }
