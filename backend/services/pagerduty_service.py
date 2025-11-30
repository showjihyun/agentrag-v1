"""
PagerDuty Integration Service

Provides incident management and alerting:
- Create incidents
- Trigger alerts
- Acknowledge/resolve incidents
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import os

import httpx

logger = logging.getLogger(__name__)


class PagerDutySeverity(str, Enum):
    """PagerDuty event severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class PagerDutyEventAction(str, Enum):
    """PagerDuty event actions."""
    TRIGGER = "trigger"
    ACKNOWLEDGE = "acknowledge"
    RESOLVE = "resolve"


class PagerDutyService:
    """
    PagerDuty integration service for incident management.
    """
    
    EVENTS_API_URL = "https://events.pagerduty.com/v2/enqueue"
    
    def __init__(
        self,
        routing_key: Optional[str] = None,
        service_name: str = "Agentic RAG System",
    ):
        self._routing_key = routing_key or os.getenv("PAGERDUTY_ROUTING_KEY")
        self._service_name = service_name
        self._enabled = bool(self._routing_key)
        
        if not self._enabled:
            logger.info("PagerDuty not configured (no routing key)")

    async def trigger_alert(
        self,
        summary: str,
        severity: PagerDutySeverity = PagerDutySeverity.ERROR,
        source: str = "backend",
        dedup_key: Optional[str] = None,
        custom_details: Optional[Dict[str, Any]] = None,
        links: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Trigger a PagerDuty alert.
        
        Args:
            summary: Alert summary (max 1024 chars)
            severity: Alert severity level
            source: Source of the alert
            dedup_key: Deduplication key for grouping alerts
            custom_details: Additional details to include
            links: Related links [{href, text}]
        
        Returns:
            dict with 'success', 'dedup_key', and 'message' keys
        """
        if not self._enabled:
            logger.warning(f"PagerDuty not enabled, would trigger: {summary}")
            return {"success": False, "error": "PagerDuty not configured"}
        
        payload = {
            "routing_key": self._routing_key,
            "event_action": PagerDutyEventAction.TRIGGER.value,
            "payload": {
                "summary": summary[:1024],
                "severity": severity.value,
                "source": source,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "component": self._service_name,
                "custom_details": custom_details or {},
            },
        }
        
        if dedup_key:
            payload["dedup_key"] = dedup_key
        
        if links:
            payload["links"] = links
        
        return await self._send_event(payload)
    
    async def acknowledge_alert(
        self,
        dedup_key: str,
    ) -> Dict[str, Any]:
        """Acknowledge an existing alert."""
        if not self._enabled:
            return {"success": False, "error": "PagerDuty not configured"}
        
        payload = {
            "routing_key": self._routing_key,
            "event_action": PagerDutyEventAction.ACKNOWLEDGE.value,
            "dedup_key": dedup_key,
        }
        
        return await self._send_event(payload)
    
    async def resolve_alert(
        self,
        dedup_key: str,
    ) -> Dict[str, Any]:
        """Resolve an existing alert."""
        if not self._enabled:
            return {"success": False, "error": "PagerDuty not configured"}
        
        payload = {
            "routing_key": self._routing_key,
            "event_action": PagerDutyEventAction.RESOLVE.value,
            "dedup_key": dedup_key,
        }
        
        return await self._send_event(payload)
    
    async def _send_event(self, payload: dict) -> Dict[str, Any]:
        """Send event to PagerDuty Events API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.EVENTS_API_URL,
                    json=payload,
                    timeout=10.0,
                )
                
                if response.status_code == 202:
                    data = response.json()
                    logger.info(f"PagerDuty event sent: {data.get('dedup_key')}")
                    return {
                        "success": True,
                        "dedup_key": data.get("dedup_key"),
                        "message": data.get("message"),
                    }
                else:
                    logger.error(f"PagerDuty API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                    }
                    
        except Exception as e:
            logger.error(f"PagerDuty send failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def trigger_workflow_failure(
        self,
        workflow_name: str,
        execution_id: str,
        error_message: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience method for workflow failure alerts."""
        return await self.trigger_alert(
            summary=f"Workflow Failed: {workflow_name}",
            severity=PagerDutySeverity.ERROR,
            source="workflow_executor",
            dedup_key=f"workflow-{execution_id}",
            custom_details={
                "workflow_name": workflow_name,
                "execution_id": execution_id,
                "error_message": error_message,
                "user_id": user_id,
            },
        )
    
    async def trigger_system_alert(
        self,
        component: str,
        message: str,
        severity: PagerDutySeverity = PagerDutySeverity.WARNING,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Convenience method for system alerts."""
        return await self.trigger_alert(
            summary=f"System Alert: {component} - {message}",
            severity=severity,
            source=component,
            dedup_key=f"system-{component}-{message[:50]}",
            custom_details={
                "component": component,
                "message": message,
                "metrics": metrics or {},
            },
        )


# Global instance
_pagerduty_service: Optional[PagerDutyService] = None


def get_pagerduty_service() -> PagerDutyService:
    """Get or create PagerDuty service instance."""
    global _pagerduty_service
    if _pagerduty_service is None:
        _pagerduty_service = PagerDutyService()
    return _pagerduty_service
