"""Base trigger class for workflow execution."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseTrigger(ABC):
    """
    Base class for all trigger types.
    
    Triggers initiate workflow execution in response to events.
    """
    
    def __init__(self, workflow_id: str, config: Dict[str, Any]):
        """
        Initialize trigger.
        
        Args:
            workflow_id: Workflow identifier
            config: Trigger configuration
        """
        self.workflow_id = workflow_id
        self.config = config
        self.is_active = config.get("is_active", True)
    
    @abstractmethod
    async def register(self) -> Dict[str, Any]:
        """
        Register the trigger.
        
        Returns:
            Registration result with trigger details
        """
        pass
    
    @abstractmethod
    async def unregister(self):
        """Unregister the trigger."""
        pass
    
    @abstractmethod
    async def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow in response to trigger.
        
        Args:
            trigger_data: Data from trigger event
            
        Returns:
            Execution result
        """
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get trigger status.
        
        Returns:
            Status information
        """
        pass
    
    def log_trigger(
        self,
        trigger_type: str,
        success: bool,
        trigger_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Log trigger execution.
        
        Args:
            trigger_type: Type of trigger
            success: Whether trigger was successful
            trigger_data: Trigger data
            error: Error message if failed
        """
        log_data = {
            "workflow_id": self.workflow_id,
            "trigger_type": trigger_type,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if trigger_data:
            log_data["trigger_data"] = trigger_data
        
        if error:
            log_data["error"] = error
        
        if success:
            logger.info(f"Trigger executed: {log_data}")
        else:
            logger.error(f"Trigger failed: {log_data}")
