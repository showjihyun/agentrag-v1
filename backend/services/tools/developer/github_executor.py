"""
GitHub tool executor.
"""
from typing import Any, Dict, Optional
import httpx

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class GitHubExecutor(BaseToolExecutor):
    """Executor for GitHub operations."""
    
    def __init__(self):
        super().__init__("github", "GitHub")
        self.category = "developer"
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute GitHub operation."""
        from ..base_executor import ToolExecutionResult
        
        self.validate_params(params, ["operation", "owner", "repo"])
        
        token = credentials.get("token") if credentials else None
        if not token:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="GitHub token is required"
            )
        
        operation = params.get("operation")
        owner = params.get("owner")
        repo = params.get("repo")
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                if operation == "create_issue":
                    result = await self._create_issue(client, headers, owner, repo, params)
                elif operation == "create_pr":
                    result = await self._create_pr(client, headers, owner, repo, params)
                elif operation == "get_repo":
                    result = await self._get_repo(client, headers, owner, repo)
                elif operation == "list_issues":
                    result = await self._list_issues(client, headers, owner, repo, params)
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
    
    async def _create_issue(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        owner: str,
        repo: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a GitHub issue."""
        title = parameters.get("title")
        body = parameters.get("body", "")
        labels = parameters.get("labels", [])
        
        if not title:
            raise ValueError("title is required for create_issue")
        
        payload = {
            "title": title,
            "body": body,
        }
        if labels:
            payload["labels"] = labels
        
        response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "issue_number": result["number"],
            "url": result["html_url"],
            "state": result["state"],
        }
    
    async def _create_pr(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        owner: str,
        repo: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a GitHub pull request."""
        title = parameters.get("title")
        body = parameters.get("body", "")
        head = parameters.get("branch")
        base = parameters.get("base", "main")
        
        if not all([title, head]):
            raise ValueError("title and branch are required for create_pr")
        
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        
        response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/pulls",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "pr_number": result["number"],
            "url": result["html_url"],
            "state": result["state"],
        }
    
    async def _get_repo(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        owner: str,
        repo: str,
    ) -> Dict[str, Any]:
        """Get repository information."""
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "name": result["name"],
            "full_name": result["full_name"],
            "description": result["description"],
            "stars": result["stargazers_count"],
            "forks": result["forks_count"],
            "url": result["html_url"],
        }
    
    async def _list_issues(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        owner: str,
        repo: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """List repository issues."""
        state = parameters.get("state", "open")
        per_page = parameters.get("per_page", 30)
        
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page},
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        issues = response.json()
        return {
            "count": len(issues),
            "issues": [
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "url": issue["html_url"],
                }
                for issue in issues
            ],
        }
    

