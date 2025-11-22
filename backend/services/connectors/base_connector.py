"""
Base Connector for External Data Sources.

Provides common functionality for all connectors:
- Connection management
- Authentication
- Rate limiting
- Error handling
- Retry logic
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ConnectorType(str, Enum):
    """Types of data connectors."""
    CRM = "crm"
    DATABASE = "database"
    API = "api"
    FILE = "file"
    CLOUD_STORAGE = "cloud_storage"


class ConnectorStatus(str, Enum):
    """Connector connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


class BaseConnector(ABC):
    """
    Base class for all external data connectors.
    
    Features:
    - Connection lifecycle management
    - Authentication handling
    - Rate limiting
    - Error handling with retry
    - Connection pooling
    """
    
    def __init__(
        self,
        connector_id: str,
        connector_type: ConnectorType,
        config: Dict[str, Any]
    ):
        """
        Initialize base connector.
        
        Args:
            connector_id: Unique connector identifier
            connector_type: Type of connector
            config: Connector configuration
        """
        self.connector_id = connector_id
        self.connector_type = connector_type
        self.config = config
        self.status = ConnectorStatus.DISCONNECTED
        self.connection = None
        self.last_error = None
        self.connected_at = None
        
        # Rate limiting
        self.rate_limit = config.get("rate_limit", 100)  # requests per minute
        self.rate_limit_window = 60  # seconds
        self.request_count = 0
        self.window_start = datetime.utcnow()
        
        # Retry configuration
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        
        logger.info(f"Initialized {connector_type} connector: {connector_id}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to external system.
        
        Returns:
            True if connected successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to external system.
        
        Returns:
            True if disconnected successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to external system.
        
        Returns:
            Connection test result with status and details
        """
        pass
    
    @abstractmethod
    async def fetch_data(
        self,
        resource: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from external system.
        
        Args:
            resource: Resource/table/endpoint to fetch from
            filters: Optional filters to apply
            limit: Maximum number of records to fetch
            
        Returns:
            List of records
        """
        pass
    
    @abstractmethod
    async def create_record(
        self,
        resource: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new record in external system.
        
        Args:
            resource: Resource/table/endpoint
            data: Record data
            
        Returns:
            Created record with ID
        """
        pass
    
    @abstractmethod
    async def update_record(
        self,
        resource: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update existing record in external system.
        
        Args:
            resource: Resource/table/endpoint
            record_id: Record identifier
            data: Updated data
            
        Returns:
            Updated record
        """
        pass
    
    @abstractmethod
    async def delete_record(
        self,
        resource: str,
        record_id: str
    ) -> bool:
        """
        Delete record from external system.
        
        Args:
            resource: Resource/table/endpoint
            record_id: Record identifier
            
        Returns:
            True if deleted successfully
        """
        pass
    
    async def execute_with_retry(
        self,
        func,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Check rate limit
                await self._check_rate_limit()
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Increment request count
                self.request_count += 1
                
                return result
                
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed: {e}",
                        exc_info=True
                    )
        
        raise last_error
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = datetime.utcnow()
        elapsed = (now - self.window_start).total_seconds()
        
        # Reset window if expired
        if elapsed >= self.rate_limit_window:
            self.request_count = 0
            self.window_start = now
            return
        
        # Check if rate limit exceeded
        if self.request_count >= self.rate_limit:
            # Calculate wait time
            wait_time = self.rate_limit_window - elapsed
            logger.warning(
                f"Rate limit reached ({self.rate_limit} requests/{self.rate_limit_window}s). "
                f"Waiting {wait_time:.1f}s..."
            )
            await asyncio.sleep(wait_time)
            
            # Reset window
            self.request_count = 0
            self.window_start = datetime.utcnow()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get connector status.
        
        Returns:
            Status information
        """
        return {
            "connector_id": self.connector_id,
            "connector_type": self.connector_type.value,
            "status": self.status.value,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_error": str(self.last_error) if self.last_error else None,
            "request_count": self.request_count,
            "rate_limit": self.rate_limit
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
