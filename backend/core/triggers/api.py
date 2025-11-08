"""API trigger for workflow execution."""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import secrets

from backend.core.triggers.base import BaseTrigger

logger = logging.getLogger(__name__)


class APITrigger(BaseTrigger):
    """
    API trigger for executing workflows via REST API.
    
    Features:
    - API key authentication
    - Rate limiting
    - Request validation
    - Response formatting
    """
    
    def __init__(
        self,
        workflow_id: str,
        config: Dict[str, Any],
        db_session: Session
    ):
        """
        Initialize API trigger.
        
        Args:
            workflow_id: Workflow identifier
            config: API configuration
            db_session: Database session
        """
        super().__init__(workflow_id, config)
        self.db = db_session
        self.api_key = config.get("api_key")
        self.rate_limit = config.get("rate_limit", 100)  # requests per hour
        self.rate_limit_window = config.get("rate_limit_window", 3600)  # seconds
        self._request_counts: Dict[str, list] = {}  # Track requests per API key
    
    async def register(self) -> Dict[str, Any]:
        """
        Register API trigger.
        
        Generates API key and configures rate limiting.
        
        Returns:
            Registration result with API details
        """
        logger.info(f"Registering API trigger for workflow: {self.workflow_id}")
        
        try:
            # Generate API key if not provided
            if not self.api_key:
                self.api_key = self._generate_api_key()
            
            logger.info(
                f"API trigger registered: workflow_id={self.workflow_id}, "
                f"rate_limit={self.rate_limit}"
            )
            
            return {
                "trigger_id": str(uuid.uuid4()),
                "trigger_type": "api",
                "api_key": self.api_key,
                "api_endpoint": f"/api/workflows/{self.workflow_id}/execute",
                "rate_limit": self.rate_limit,
                "rate_limit_window": self.rate_limit_window,
                "is_active": self.is_active,
            }
            
        except Exception as e:
            logger.error(
                f"Failed to register API trigger: workflow_id={self.workflow_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            raise
    
    async def unregister(self):
        """Unregister API trigger."""
        logger.info(f"Unregistering API trigger for workflow: {self.workflow_id}")
        
        # Clear API key
        self.api_key = None
        self.is_active = False
        
        logger.info(f"API trigger unregistered: workflow_id={self.workflow_id}")
    
    async def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow via API.
        
        Args:
            trigger_data: API request data
            
        Returns:
            Execution result
        """
        logger.info(
            f"Executing API trigger: workflow_id={self.workflow_id}"
        )
        
        try:
            # Log trigger execution
            self.log_trigger(
                trigger_type="api",
                success=True,
                trigger_data=trigger_data
            )
            
            return {
                "success": True,
                "workflow_id": self.workflow_id,
            }
            
        except Exception as e:
            logger.error(
                f"API execution failed: workflow_id={self.workflow_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            
            self.log_trigger(
                trigger_type="api",
                success=False,
                trigger_data=trigger_data,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get API trigger status.
        
        Returns:
            Status information
        """
        return {
            "active": self.is_active,
            "workflow_id": self.workflow_id,
            "rate_limit": self.rate_limit,
            "rate_limit_window": self.rate_limit_window,
            "has_api_key": bool(self.api_key),
        }
    
    def validate_api_key(self, provided_key: str) -> bool:
        """
        Validate API key.
        
        Args:
            provided_key: API key from request
            
        Returns:
            True if valid
        """
        if not self.api_key:
            return False
        
        return secrets.compare_digest(provided_key, self.api_key)
    
    def check_rate_limit(self, api_key: str) -> tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit.
        
        Args:
            api_key: API key making the request
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = datetime.utcnow()
        
        # Initialize request tracking for this API key
        if api_key not in self._request_counts:
            self._request_counts[api_key] = []
        
        # Remove old requests outside the window
        window_start = now - timedelta(seconds=self.rate_limit_window)
        self._request_counts[api_key] = [
            req_time for req_time in self._request_counts[api_key]
            if req_time > window_start
        ]
        
        # Check if within rate limit
        if len(self._request_counts[api_key]) >= self.rate_limit:
            # Calculate retry after time
            oldest_request = min(self._request_counts[api_key])
            retry_after = int(
                (oldest_request + timedelta(seconds=self.rate_limit_window) - now).total_seconds()
            )
            return False, max(retry_after, 1)
        
        # Add current request
        self._request_counts[api_key].append(now)
        
        return True, None
    
    def validate_request(self, request_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate API request data.
        
        Args:
            request_data: Request data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if input_data is provided
        if "input_data" not in request_data:
            return False, "Missing required field: input_data"
        
        # Validate input_data is a dictionary
        if not isinstance(request_data["input_data"], dict):
            return False, "input_data must be a dictionary"
        
        return True, None
    
    def format_response(
        self,
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format API response.
        
        Args:
            execution_result: Workflow execution result
            
        Returns:
            Formatted response
        """
        if execution_result.get("success"):
            return {
                "success": True,
                "execution_id": execution_result.get("execution_id"),
                "status": execution_result.get("status"),
                "outputs": execution_result.get("outputs"),
                "message": "Workflow execution completed"
            }
        else:
            return {
                "success": False,
                "error": execution_result.get("error"),
                "message": "Workflow execution failed"
            }
    
    def _generate_api_key(self) -> str:
        """
        Generate secure API key.
        
        Returns:
            API key
        """
        # Generate 32-byte random key and encode as hex
        return f"wf_{secrets.token_hex(32)}"
