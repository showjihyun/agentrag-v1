"""
Slack tool executor.
"""
from typing import Any, Dict, Optional
import httpx

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class SlackExecutor(BaseToolExecutor):
    """Executor for Slack operations."""
    
    def __init__(self):
        super().__init__("slack", "Slack")
        self.category = "communication"
        
        # Define parameter schema
        self.params_schema = {
            "channel": {
                "type": "string",
                "description": "Slack channel name or ID",
                "required": True,
                "placeholder": "#general or C1234567890"
            },
            "message": {
                "type": "textarea",
                "description": "Message to send",
                "required": True,
                "placeholder": "Enter your message here"
            },
            "username": {
                "type": "string",
                "description": "Bot username (optional)",
                "required": False,
                "placeholder": "My Bot"
            },
            "icon_emoji": {
                "type": "string",
                "description": "Bot icon emoji (optional)",
                "required": False,
                "placeholder": ":robot_face:"
            }
        }
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute Slack operation."""
        from ..base_executor import ToolExecutionResult
        
        webhook_url = credentials.get("webhook_url") if credentials else None
        bot_token = credentials.get("bot_token") if credentials else None
        
        if not webhook_url and not bot_token:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="Either webhook_url or bot_token is required"
            )
        
        channel = params.get("channel")
        text = params.get("text")
        blocks = params.get("blocks")
        thread_ts = params.get("thread_ts")
        
        if not text and not blocks:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="Either text or blocks is required"
            )
        
        # Build message payload
        payload = {}
        if channel:
            payload["channel"] = channel
        if text:
            payload["text"] = text
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        try:
            async with httpx.AsyncClient() as client:
                if webhook_url:
                    # Use webhook
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        timeout=30.0,
                    )
                else:
                    # Use bot token
                    response = await client.post(
                        "https://slack.com/api/chat.postMessage",
                        json=payload,
                        headers={"Authorization": f"Bearer {bot_token}"},
                        timeout=30.0,
                    )
                
                response.raise_for_status()
                result = response.json()
                
                return ToolExecutionResult(
                    success=True,
                    output={
                        "message_ts": result.get("ts"),
                        "channel": result.get("channel"),
                    }
                )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=str(e)
            )
