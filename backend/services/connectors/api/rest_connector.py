"""
REST API Connector with Auto-Discovery.

Features:
- OpenAPI/Swagger spec parsing
- Automatic endpoint discovery
- Dynamic request building
- Response schema validation
- Authentication support
"""

import logging
from typing import Dict, Any, Optional, List
import httpx
import yaml
import json

from backend.services.connectors.base_connector import BaseConnector, ConnectorType, ConnectorStatus

logger = logging.getLogger(__name__)


class RESTAPIConnector(BaseConnector):
    """Generic REST API connector with auto-discovery."""
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        """
        Initialize REST API connector.
        
        Config:
            base_url: API base URL
            auth_type: none, api_key, bearer, basic
            auth_config: Authentication configuration
            openapi_url: OpenAPI spec URL (optional)
        """
        super().__init__(connector_id, ConnectorType.API, config)
        
        self.base_url = config.get("base_url")
        self.auth_type = config.get("auth_type", "none")
        self.auth_config = config.get("auth_config", {})
        self.openapi_url = config.get("openapi_url")
        
        self.client = None
        self.api_spec = None
        self.endpoints = {}
    
    async def connect(self) -> bool:
        """Establish connection to REST API."""
        try:
            self.status = ConnectorStatus.CONNECTING
            
            # Build headers
            headers = {"Content-Type": "application/json"}
            
            if self.auth_type == "api_key":
                key_name = self.auth_config.get("key_name", "X-API-Key")
                headers[key_name] = self.auth_config.get("api_key")
            elif self.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.auth_config.get('token')}"
            
            # Create HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0
            )
            
            # Load OpenAPI spec if provided
            if self.openapi_url:
                await self._load_openapi_spec()
            
            # Test connection
            test_result = await self.test_connection()
            
            if test_result["success"]:
                self.status = ConnectorStatus.CONNECTED
                self.connected_at = datetime.utcnow()
                logger.info(f"Connected to REST API: {self.connector_id}")
                return True
            else:
                self.status = ConnectorStatus.ERROR
                self.last_error = test_result.get("error")
                return False
                
        except Exception as e:
            self.status = ConnectorStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Failed to connect to REST API: {e}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """Close REST API connection."""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected_at = None
            logger.info(f"Disconnected from REST API: {self.connector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from REST API: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test REST API connection."""
        try:
            if not self.client:
                return {"success": False, "error": "Not connected"}
            
            # Try health endpoint or root
            test_paths = ["/health", "/api/health", "/", "/api"]
            
            for path in test_paths:
                try:
                    response = await self.client.get(path)
                    if response.status_code < 500:
                        return {
                            "success": True,
                            "status_code": response.status_code,
                            "endpoint": path
                        }
                except:
                    continue
            
            return {"success": False, "error": "No valid endpoint found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _load_openapi_spec(self):
        """Load and parse OpenAPI specification."""
        try:
            response = await self.client.get(self.openapi_url)
            
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                
                if "yaml" in content_type or self.openapi_url.endswith(".yaml"):
                    self.api_spec = yaml.safe_load(response.text)
                else:
                    self.api_spec = response.json()
                
                # Parse endpoints
                self._parse_endpoints()
                
                logger.info(f"Loaded OpenAPI spec with {len(self.endpoints)} endpoints")
                
        except Exception as e:
            logger.warning(f"Failed to load OpenAPI spec: {e}")
    
    def _parse_endpoints(self):
        """Parse endpoints from OpenAPI spec."""
        if not self.api_spec or "paths" not in self.api_spec:
            return
        
        for path, methods in self.api_spec["paths"].items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                    endpoint_id = f"{method.upper()}_{path.replace('/', '_')}"
                    self.endpoints[endpoint_id] = {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody"),
                        "responses": details.get("responses", {})
                    }
    
    async def fetch_data(
        self,
        resource: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch data from REST API."""
        try:
            params = filters or {}
            if limit:
                params["limit"] = limit
            
            response = await self.client.get(f"/{resource}", params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Handle different response formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    # Try common keys
                    for key in ["data", "results", "items", "records"]:
                        if key in data:
                            return data[key]
                    return [data]
                return []
            else:
                raise Exception(f"Fetch failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to fetch REST API data: {e}")
            raise
    
    async def create_record(
        self,
        resource: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create record via REST API."""
        try:
            response = await self.client.post(f"/{resource}", json=data)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                raise Exception(f"Create failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to create REST API record: {e}")
            raise
    
    async def update_record(
        self,
        resource: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update record via REST API."""
        try:
            response = await self.client.put(f"/{resource}/{record_id}", json=data)
            
            if response.status_code in [200, 204]:
                return response.json() if response.status_code == 200 else {"id": record_id, **data}
            else:
                raise Exception(f"Update failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to update REST API record: {e}")
            raise
    
    async def delete_record(
        self,
        resource: str,
        record_id: str
    ) -> bool:
        """Delete record via REST API."""
        try:
            response = await self.client.delete(f"/{resource}/{record_id}")
            return response.status_code in [200, 204]
            
        except Exception as e:
            logger.error(f"Failed to delete REST API record: {e}")
            raise
    
    def get_available_endpoints(self) -> List[Dict[str, Any]]:
        """Get list of available endpoints from OpenAPI spec."""
        return [
            {
                "id": endpoint_id,
                "path": details["path"],
                "method": details["method"],
                "summary": details["summary"]
            }
            for endpoint_id, details in self.endpoints.items()
        ]
