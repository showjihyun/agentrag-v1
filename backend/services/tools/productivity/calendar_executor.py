"""
Calendar tool executor (Google Calendar).
"""
from typing import Any, Dict, Optional
from datetime import datetime
import httpx

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class CalendarExecutor(BaseToolExecutor):
    """Executor for Google Calendar operations."""
    
    def __init__(self):
        super().__init__("google_calendar", "Google Calendar")
        self.category = "productivity"
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute calendar operation."""
        
        access_token = credentials.get("access_token") if credentials else None
        if not access_token:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="Google Calendar access token is required"
            )
        
        self.validate_params(params, ["operation"])
        operation = params.get("operation")
        calendar_id = params.get("calendar_id", "primary")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                if operation == "create_event":
                    result = await self._create_event(client, headers, calendar_id, params)
                elif operation == "list_events":
                    result = await self._list_events(client, headers, calendar_id, params)
                elif operation == "delete_event":
                    result = await self._delete_event(client, headers, calendar_id, params)
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
    
    async def _create_event(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        calendar_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a calendar event."""
        self.validate_params(params, ["summary", "start_time", "end_time"])
        
        summary = params.get("summary")
        start_time = params.get("start_time")
        end_time = params.get("end_time")
        description = params.get("description", "")
        attendees = params.get("attendees", [])
        
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": "UTC"},
            "end": {"dateTime": end_time, "timeZone": "UTC"},
        }
        
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        
        response = await client.post(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            json=event,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "event_id": result["id"],
            "html_link": result.get("htmlLink"),
            "status": result.get("status"),
        }
    
    async def _list_events(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        calendar_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """List calendar events."""
        time_min = params.get("time_min", datetime.utcnow().isoformat() + "Z")
        max_results = params.get("max_results", 10)
        
        response = await client.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            params={
                "timeMin": time_min,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
            },
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        result = response.json()
        events = result.get("items", [])
        
        return {
            "count": len(events),
            "events": [
                {
                    "id": event["id"],
                    "summary": event.get("summary"),
                    "start": event.get("start", {}).get("dateTime"),
                    "end": event.get("end", {}).get("dateTime"),
                    "html_link": event.get("htmlLink"),
                }
                for event in events
            ],
        }
    
    async def _delete_event(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        calendar_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Delete a calendar event."""
        self.validate_params(params, ["event_id"])
        
        event_id = params.get("event_id")
        
        response = await client.delete(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        
        return {"success": True, "event_id": event_id}
