"""Main client for Agentic RAG SDK."""
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

from .exceptions import (
    AgenticRAGError,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
    InsufficientCreditsError,
)
from .resources import (
    AgentsResource,
    WorkflowsResource,
    CreditsResource,
    WebhooksResource,
    MarketplaceResource,
    OrganizationsResource,
)


class AgenticRAGClient:
    """
    Main client for interacting with Agentic RAG API.
    
    Example:
        >>> client = AgenticRAGClient(api_key="your-api-key")
        >>> agents = client.agents.list()
        >>> workflow = client.workflows.execute(workflow_id="123", input_data={"query": "test"})
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.agenticrag.com",
        timeout: int = 30,
    ):
        """
        Initialize Agentic RAG client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API (default: https://api.agenticrag.com)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Initialize resource managers
        self.agents = AgentsResource(self)
        self.workflows = WorkflowsResource(self)
        self.credits = CreditsResource(self)
        self.webhooks = WebhooksResource(self)
        self.marketplace = MarketplaceResource(self)
        self.organizations = OrganizationsResource(self)
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            AgenticRAGError: On API errors
        """
        url = urljoin(self.base_url, endpoint)
        
        # Prepare headers
        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "agentic-rag-python-sdk/0.1.0",
        }
        if headers:
            request_headers.update(headers)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=self.timeout,
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise RateLimitError(
                    "Rate limit exceeded",
                    status_code=429,
                    retry_after=int(retry_after),
                    response=response.json() if response.content else None,
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your API key.",
                    status_code=401,
                    response=response.json() if response.content else None,
                )
            
            # Handle not found
            if response.status_code == 404:
                raise ResourceNotFoundError(
                    "Resource not found",
                    status_code=404,
                    response=response.json() if response.content else None,
                )
            
            # Handle validation errors
            if response.status_code == 422:
                raise ValidationError(
                    "Validation error",
                    status_code=422,
                    response=response.json() if response.content else None,
                )
            
            # Handle insufficient credits
            if response.status_code == 402:
                raise InsufficientCreditsError(
                    "Insufficient credits",
                    status_code=402,
                    response=response.json() if response.content else None,
                )
            
            # Handle other errors
            if not response.ok:
                error_data = response.json() if response.content else {}
                raise AgenticRAGError(
                    error_data.get("detail", f"HTTP {response.status_code}"),
                    status_code=response.status_code,
                    response=error_data,
                )
            
            # Return response data
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.Timeout:
            raise AgenticRAGError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise AgenticRAGError(f"Connection error to {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise AgenticRAGError(f"Request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._request("POST", endpoint, data=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return self._request("PUT", endpoint, data=data)
    
    def patch(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PATCH request."""
        return self._request("PATCH", endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._request("DELETE", endpoint)
