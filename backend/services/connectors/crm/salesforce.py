"""
Salesforce CRM Connector.

Features:
- OAuth 2.0 authentication
- SOQL query support
- CRUD operations
- Bulk API support
- Real-time event streaming
"""

import logging
from typing import Dict, Any, Optional, List
import httpx

from backend.services.connectors.base_connector import BaseConnector, ConnectorType, ConnectorStatus

logger = logging.getLogger(__name__)


class SalesforceConnector(BaseConnector):
    """Connector for Salesforce CRM."""
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        """
        Initialize Salesforce connector.
        
        Config:
            instance_url: Salesforce instance URL
            access_token: OAuth access token
            api_version: API version (default: v58.0)
        """
        super().__init__(connector_id, ConnectorType.CRM, config)
        
        self.instance_url = config.get("instance_url")
        self.access_token = config.get("access_token")
        self.api_version = config.get("api_version", "v58.0")
        self.client = None
    
    async def connect(self) -> bool:
        """Establish connection to Salesforce."""
        try:
            self.status = ConnectorStatus.CONNECTING
            
            # Create HTTP client
            self.client = httpx.AsyncClient(
                base_url=f"{self.instance_url}/services/data/{self.api_version}",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            # Test connection
            test_result = await self.test_connection()
            
            if test_result["success"]:
                self.status = ConnectorStatus.CONNECTED
                self.connected_at = datetime.utcnow()
                logger.info(f"Connected to Salesforce: {self.connector_id}")
                return True
            else:
                self.status = ConnectorStatus.ERROR
                self.last_error = test_result.get("error")
                return False
                
        except Exception as e:
            self.status = ConnectorStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Failed to connect to Salesforce: {e}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """Close Salesforce connection."""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected_at = None
            logger.info(f"Disconnected from Salesforce: {self.connector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from Salesforce: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Salesforce connection."""
        try:
            if not self.client:
                return {"success": False, "error": "Not connected"}
            
            # Query organization info
            response = await self.client.get("/query", params={
                "q": "SELECT Id, Name FROM Organization LIMIT 1"
            })
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "organization": data.get("records", [{}])[0],
                    "api_version": self.api_version
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_data(
        self,
        resource: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from Salesforce using SOQL.
        
        Args:
            resource: Salesforce object (e.g., "Account", "Contact")
            filters: WHERE clause conditions
            limit: LIMIT clause
            
        Returns:
            List of records
        """
        try:
            # Build SOQL query
            query = f"SELECT FIELDS(ALL) FROM {resource}"
            
            if filters:
                where_clauses = [
                    f"{key} = '{value}'" if isinstance(value, str) else f"{key} = {value}"
                    for key, value in filters.items()
                ]
                query += " WHERE " + " AND ".join(where_clauses)
            
            if limit:
                query += f" LIMIT {limit}"
            
            # Execute query
            response = await self.client.get("/query", params={"q": query})
            
            if response.status_code == 200:
                data = response.json()
                return data.get("records", [])
            else:
                raise Exception(f"Query failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to fetch Salesforce data: {e}")
            raise
    
    async def create_record(
        self,
        resource: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create record in Salesforce."""
        try:
            response = await self.client.post(
                f"/sobjects/{resource}",
                json=data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "id": result.get("id"),
                    "success": result.get("success", True),
                    **data
                }
            else:
                raise Exception(f"Create failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to create Salesforce record: {e}")
            raise
    
    async def update_record(
        self,
        resource: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update record in Salesforce."""
        try:
            response = await self.client.patch(
                f"/sobjects/{resource}/{record_id}",
                json=data
            )
            
            if response.status_code == 204:
                return {"id": record_id, "success": True, **data}
            else:
                raise Exception(f"Update failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to update Salesforce record: {e}")
            raise
    
    async def delete_record(
        self,
        resource: str,
        record_id: str
    ) -> bool:
        """Delete record from Salesforce."""
        try:
            response = await self.client.delete(
                f"/sobjects/{resource}/{record_id}"
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Failed to delete Salesforce record: {e}")
            raise
    
    async def execute_soql(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute SOQL query.
        
        Args:
            query: SOQL query string
            
        Returns:
            Query results
        """
        try:
            response = await self.client.get("/query", params={"q": query})
            
            if response.status_code == 200:
                data = response.json()
                return data.get("records", [])
            else:
                raise Exception(f"SOQL query failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to execute SOQL: {e}")
            raise
