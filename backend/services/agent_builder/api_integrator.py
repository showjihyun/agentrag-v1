"""
Auto API Integrator for Agent Builder.

Automatically integrates APIs from OpenAPI/Swagger specifications.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
import json
import yaml
import httpx

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class APIAuthType(str, Enum):
    """API authentication types."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class APIEndpoint:
    """Represents an API endpoint."""
    
    def __init__(
        self,
        path: str,
        method: HTTPMethod,
        operation_id: str,
        summary: str,
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        responses: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        self.path = path
        self.method = method
        self.operation_id = operation_id
        self.summary = summary
        self.description = description
        self.parameters = parameters or []
        self.request_body = request_body
        self.responses = responses or {}
        self.tags = tags or []


class APITool:
    """Represents a tool generated from an API endpoint."""
    
    def __init__(
        self,
        tool_id: str,
        name: str,
        description: str,
        endpoint: APIEndpoint,
        base_url: str,
        auth_config: Optional[Dict[str, Any]] = None
    ):
        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.base_url = base_url
        self.auth_config = auth_config or {}
        
        self.created_at = datetime.now(timezone.utc)
        self.last_tested = None
        self.test_status = "untested"
        self.test_results = {}


class AutoAPIIntegrator:
    """
    Automatically integrates APIs from OpenAPI specifications.
    
    Features:
    - OpenAPI 3.0/Swagger 2.0 parsing
    - Automatic tool generation
    - Authentication configuration
    - Endpoint testing
    - Error handling
    """
    
    def __init__(
        self,
        db: Session,
        http_client: Optional[httpx.AsyncClient] = None
    ):
        """
        Initialize API integrator.
        
        Args:
            db: Database session
            http_client: HTTP client for API calls
        """
        self.db = db
        
        # Use connection pooling for better performance
        if http_client is None:
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
            # Try to enable HTTP/2 if available
            try:
                self.http_client = httpx.AsyncClient(
                    timeout=30.0,
                    limits=limits,
                    http2=True  # Enable HTTP/2 for better performance
                )
            except Exception:
                # Fallback to HTTP/1.1 if HTTP/2 not available
                self.http_client = httpx.AsyncClient(
                    timeout=30.0,
                    limits=limits
                )
            self._owns_client = True
        else:
            self.http_client = http_client
            self._owns_client = False
        
        # Storage
        self.api_specs: Dict[str, Dict[str, Any]] = {}
        self.generated_tools: Dict[str, List[APITool]] = {}
        
        logger.info("AutoAPIIntegrator initialized")
    
    async def integrate_from_openapi(
        self,
        spec_url: str,
        auth_config: Optional[Dict[str, Any]] = None,
        filter_tags: Optional[List[str]] = None,
        max_endpoints: int = 50
    ) -> List[APITool]:
        """
        Integrate API from OpenAPI specification URL.
        
        Args:
            spec_url: URL to OpenAPI spec (JSON or YAML)
            auth_config: Authentication configuration
            filter_tags: Only include endpoints with these tags
            max_endpoints: Maximum number of endpoints to integrate
            
        Returns:
            List of generated API tools
        """
        logger.info(f"Integrating API from: {spec_url}")
        
        # Fetch and parse spec
        spec = await self._fetch_openapi_spec(spec_url)
        
        if not spec:
            raise ValueError("Failed to fetch or parse OpenAPI spec")
        
        # Store spec
        spec_id = self._generate_spec_id(spec_url)
        self.api_specs[spec_id] = spec
        
        # Extract base URL
        base_url = self._extract_base_url(spec)
        
        # Parse endpoints
        endpoints = self._parse_endpoints(spec, filter_tags, max_endpoints)
        
        logger.info(f"Found {len(endpoints)} endpoints")
        
        # Generate tools
        tools = []
        for endpoint in endpoints:
            tool = self._generate_tool_from_endpoint(
                endpoint,
                base_url,
                auth_config
            )
            tools.append(tool)
        
        # Store tools
        self.generated_tools[spec_id] = tools
        
        logger.info(f"Generated {len(tools)} API tools")
        
        return tools
    
    async def integrate_from_spec_file(
        self,
        spec_content: str,
        spec_format: str = "json",
        auth_config: Optional[Dict[str, Any]] = None
    ) -> List[APITool]:
        """
        Integrate API from OpenAPI spec content.
        
        Args:
            spec_content: OpenAPI spec content
            spec_format: Format (json or yaml)
            auth_config: Authentication configuration
            
        Returns:
            List of generated API tools
        """
        logger.info(f"Integrating API from {spec_format} spec")
        
        # Parse spec
        if spec_format == "json":
            spec = json.loads(spec_content)
        elif spec_format == "yaml":
            spec = yaml.safe_load(spec_content)
        else:
            raise ValueError(f"Unsupported format: {spec_format}")
        
        # Extract base URL
        base_url = self._extract_base_url(spec)
        
        # Parse endpoints
        endpoints = self._parse_endpoints(spec)
        
        # Generate tools
        tools = []
        for endpoint in endpoints:
            tool = self._generate_tool_from_endpoint(
                endpoint,
                base_url,
                auth_config
            )
            tools.append(tool)
        
        logger.info(f"Generated {len(tools)} API tools from spec")
        
        return tools
    
    async def test_api_tool(
        self,
        tool: APITool,
        test_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Test an API tool.
        
        Args:
            tool: API tool to test
            test_params: Test parameters
            
        Returns:
            Test results
        """
        logger.info(f"Testing API tool: {tool.name}")
        
        try:
            # Build request
            url = f"{tool.base_url}{tool.endpoint.path}"
            method = tool.endpoint.method.value
            
            # Replace path parameters
            if test_params:
                for param_name, param_value in test_params.items():
                    url = url.replace(f"{{{param_name}}}", str(param_value))
            
            # Prepare headers
            headers = {}
            if tool.auth_config:
                headers.update(self._build_auth_headers(tool.auth_config))
            
            # Prepare query params and body
            query_params = {}
            body = None
            
            if test_params:
                # Separate query params and body params
                for param in tool.endpoint.parameters:
                    param_name = param.get("name")
                    if param_name in test_params:
                        if param.get("in") == "query":
                            query_params[param_name] = test_params[param_name]
                
                # Body for POST/PUT/PATCH
                if method in ["POST", "PUT", "PATCH"] and tool.endpoint.request_body:
                    body = test_params.get("body", {})
            
            # Make request
            start_time = datetime.now(timezone.utc)
            
            response = await self.http_client.request(
                method=method,
                url=url,
                params=query_params,
                json=body if body else None,
                headers=headers
            )
            
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Update tool
            tool.last_tested = datetime.now(timezone.utc)
            tool.test_status = "success" if response.is_success else "failed"
            tool.test_results = {
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response": response_data,
                "success": response.is_success
            }
            
            logger.info(
                f"API tool test completed: {tool.name} - "
                f"Status: {response.status_code}, Duration: {duration_ms}ms"
            )
            
            return tool.test_results
            
        except Exception as e:
            logger.error(f"API tool test failed: {e}")
            
            tool.last_tested = datetime.now(timezone.utc)
            tool.test_status = "error"
            tool.test_results = {
                "error": str(e),
                "success": False
            }
            
            return tool.test_results
    
    async def execute_api_tool(
        self,
        tool: APITool,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an API tool.
        
        Args:
            tool: API tool to execute
            params: Execution parameters
            
        Returns:
            Execution result
        """
        logger.info(f"Executing API tool: {tool.name}")
        
        try:
            # Build request
            url = f"{tool.base_url}{tool.endpoint.path}"
            method = tool.endpoint.method.value
            
            # Replace path parameters
            for param in tool.endpoint.parameters:
                if param.get("in") == "path":
                    param_name = param.get("name")
                    if param_name in params:
                        url = url.replace(f"{{{param_name}}}", str(params[param_name]))
            
            # Prepare headers
            headers = {}
            if tool.auth_config:
                headers.update(self._build_auth_headers(tool.auth_config))
            
            # Prepare query params
            query_params = {}
            for param in tool.endpoint.parameters:
                if param.get("in") == "query":
                    param_name = param.get("name")
                    if param_name in params:
                        query_params[param_name] = params[param_name]
            
            # Prepare body
            body = None
            if method in ["POST", "PUT", "PATCH"] and tool.endpoint.request_body:
                body = params.get("body", {})
            
            # Make request
            response = await self.http_client.request(
                method=method,
                url=url,
                params=query_params,
                json=body if body else None,
                headers=headers
            )
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                "success": response.is_success,
                "status_code": response.status_code,
                "data": response_data
            }
            
        except Exception as e:
            logger.error(f"API tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fetch_openapi_spec(
        self,
        spec_url: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch OpenAPI spec from URL."""
        try:
            response = await self.http_client.get(spec_url)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "")
            
            if "json" in content_type:
                return response.json()
            elif "yaml" in content_type or "yml" in content_type:
                return yaml.safe_load(response.text)
            else:
                # Try JSON first, then YAML
                try:
                    return response.json()
                except:
                    return yaml.safe_load(response.text)
                    
        except Exception as e:
            logger.error(f"Failed to fetch OpenAPI spec: {e}")
            return None
    
    def _extract_base_url(
        self,
        spec: Dict[str, Any]
    ) -> str:
        """Extract base URL from OpenAPI spec."""
        # OpenAPI 3.0
        if "servers" in spec and spec["servers"]:
            return spec["servers"][0]["url"]
        
        # Swagger 2.0
        if "host" in spec:
            scheme = spec.get("schemes", ["https"])[0]
            base_path = spec.get("basePath", "")
            return f"{scheme}://{spec['host']}{base_path}"
        
        return ""
    
    def _parse_endpoints(
        self,
        spec: Dict[str, Any],
        filter_tags: Optional[List[str]] = None,
        max_endpoints: int = 50
    ) -> List[APIEndpoint]:
        """Parse endpoints from OpenAPI spec."""
        endpoints = []
        paths = spec.get("paths", {})
        
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue
                
                operation = path_item[method]
                
                # Filter by tags
                if filter_tags:
                    op_tags = operation.get("tags", [])
                    if not any(tag in filter_tags for tag in op_tags):
                        continue
                
                endpoint = APIEndpoint(
                    path=path,
                    method=HTTPMethod(method.upper()),
                    operation_id=operation.get("operationId", f"{method}_{path}"),
                    summary=operation.get("summary", ""),
                    description=operation.get("description"),
                    parameters=operation.get("parameters", []),
                    request_body=operation.get("requestBody"),
                    responses=operation.get("responses", {}),
                    tags=operation.get("tags", [])
                )
                
                endpoints.append(endpoint)
                
                if len(endpoints) >= max_endpoints:
                    break
            
            if len(endpoints) >= max_endpoints:
                break
        
        return endpoints
    
    def _generate_tool_from_endpoint(
        self,
        endpoint: APIEndpoint,
        base_url: str,
        auth_config: Optional[Dict[str, Any]]
    ) -> APITool:
        """Generate tool from endpoint."""
        tool_id = self._generate_tool_id(endpoint)
        
        # Generate tool name
        name = endpoint.operation_id or f"{endpoint.method.value.lower()}_{endpoint.path}"
        name = name.replace("/", "_").replace("{", "").replace("}", "")
        
        # Generate description
        description = endpoint.summary or endpoint.description or f"{endpoint.method.value} {endpoint.path}"
        
        tool = APITool(
            tool_id=tool_id,
            name=name,
            description=description,
            endpoint=endpoint,
            base_url=base_url,
            auth_config=auth_config
        )
        
        return tool
    
    def _build_auth_headers(
        self,
        auth_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Build authentication headers."""
        headers = {}
        
        auth_type = auth_config.get("type", APIAuthType.NONE)
        
        if auth_type == APIAuthType.API_KEY:
            key_name = auth_config.get("key_name", "X-API-Key")
            key_value = auth_config.get("key_value", "")
            headers[key_name] = key_value
        
        elif auth_type == APIAuthType.BEARER_TOKEN:
            token = auth_config.get("token", "")
            headers["Authorization"] = f"Bearer {token}"
        
        elif auth_type == APIAuthType.BASIC_AUTH:
            import base64
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        
        return headers
    
    def _generate_spec_id(self, spec_url: str) -> str:
        """Generate unique spec ID."""
        import hashlib
        return hashlib.sha256(spec_url.encode()).hexdigest()[:16]
    
    def _generate_tool_id(self, endpoint: APIEndpoint) -> str:
        """Generate unique tool ID."""
        import hashlib
        content = f"{endpoint.method.value}:{endpoint.path}:{endpoint.operation_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def close(self):
        """Close HTTP client if we own it."""
        if self._owns_client:
            await self.http_client.aclose()
            logger.info("HTTP client closed")


# Example usage
EXAMPLE_INTEGRATION = """
# Initialize
integrator = AutoAPIIntegrator(db)

# Integrate from OpenAPI URL
tools = await integrator.integrate_from_openapi(
    spec_url="https://api.example.com/openapi.json",
    auth_config={
        "type": "api_key",
        "key_name": "X-API-Key",
        "key_value": "your-api-key"
    },
    filter_tags=["users", "posts"],
    max_endpoints=20
)

# Test a tool
test_result = await integrator.test_api_tool(
    tool=tools[0],
    test_params={"user_id": "123"}
)

# Execute a tool
result = await integrator.execute_api_tool(
    tool=tools[0],
    params={"user_id": "123", "include": "profile"}
)

# Close
await integrator.close()
"""
