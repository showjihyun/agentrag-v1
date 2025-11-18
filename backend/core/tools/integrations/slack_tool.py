"""
Slack Integration Tool - n8n level functionality.
Supports messaging, channels, users, files, and more.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

from backend.core.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class SlackTool:
    """Slack integration with comprehensive n8n-level features."""
    
    BASE_URL = "https://slack.com/api"
    
    @staticmethod
    async def send_message(
        token: str,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        icon_url: Optional[str] = None,
        as_user: bool = False
    ) -> Dict[str, Any]:
        """Send a message to a Slack channel."""
        async with httpx.AsyncClient() as client:
            payload = {
                "channel": channel,
                "as_user": as_user
            }
            
            if text:
                payload["text"] = text
            if blocks:
                payload["blocks"] = blocks
            if attachments:
                payload["attachments"] = attachments
            if thread_ts:
                payload["thread_ts"] = thread_ts
            if username:
                payload["username"] = username
            if icon_emoji:
                payload["icon_emoji"] = icon_emoji
            if icon_url:
                payload["icon_url"] = icon_url
            
            response = await client.post(
                f"{SlackTool.BASE_URL}/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            return {
                "success": True,
                "message_ts": result.get("ts"),
                "channel": result.get("channel"),
                "message": result.get("message")
            }
    
    @staticmethod
    async def send_direct_message(
        token: str,
        user: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send a direct message to a user."""
        # First, open a DM channel
        async with httpx.AsyncClient() as client:
            dm_response = await client.post(
                f"{SlackTool.BASE_URL}/conversations.open",
                headers={"Authorization": f"Bearer {token}"},
                json={"users": user}
            )
            
            dm_result = dm_response.json()
            if not dm_result.get("ok"):
                raise Exception(f"Failed to open DM: {dm_result.get('error')}")
            
            channel_id = dm_result["channel"]["id"]
            
            # Send message to the DM channel
            return await SlackTool.send_message(
                token=token,
                channel=channel_id,
                text=text,
                blocks=blocks,
                attachments=attachments
            )
    
    @staticmethod
    async def update_message(
        token: str,
        channel: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Update an existing message."""
        async with httpx.AsyncClient() as client:
            payload = {
                "channel": channel,
                "ts": ts
            }
            
            if text:
                payload["text"] = text
            if blocks:
                payload["blocks"] = blocks
            if attachments:
                payload["attachments"] = attachments
            
            response = await client.post(
                f"{SlackTool.BASE_URL}/chat.update",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            return {
                "success": True,
                "message_ts": result.get("ts"),
                "channel": result.get("channel")
            }
    
    @staticmethod
    async def delete_message(
        token: str,
        channel: str,
        ts: str
    ) -> Dict[str, Any]:
        """Delete a message."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SlackTool.BASE_URL}/chat.delete",
                headers={"Authorization": f"Bearer {token}"},
                json={"channel": channel, "ts": ts}
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            return {"success": True}
    
    @staticmethod
    async def get_channel(
        token: str,
        channel: str
    ) -> Dict[str, Any]:
        """Get channel information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SlackTool.BASE_URL}/conversations.info",
                headers={"Authorization": f"Bearer {token}"},
                params={"channel": channel}
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            channel_info = result["channel"]
            return {
                "id": channel_info.get("id"),
                "name": channel_info.get("name"),
                "is_channel": channel_info.get("is_channel"),
                "is_private": channel_info.get("is_private"),
                "is_archived": channel_info.get("is_archived"),
                "topic": channel_info.get("topic", {}).get("value"),
                "purpose": channel_info.get("purpose", {}).get("value"),
                "num_members": channel_info.get("num_members")
            }
    
    @staticmethod
    async def create_channel(
        token: str,
        name: str,
        is_private: bool = False
    ) -> Dict[str, Any]:
        """Create a new channel."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SlackTool.BASE_URL}/conversations.create",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": name, "is_private": is_private}
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            channel = result["channel"]
            return {
                "success": True,
                "channel_id": channel.get("id"),
                "channel_name": channel.get("name")
            }
    
    @staticmethod
    async def archive_channel(
        token: str,
        channel: str
    ) -> Dict[str, Any]:
        """Archive a channel."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SlackTool.BASE_URL}/conversations.archive",
                headers={"Authorization": f"Bearer {token}"},
                json={"channel": channel}
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            return {"success": True}
    
    @staticmethod
    async def get_user(
        token: str,
        user: str
    ) -> Dict[str, Any]:
        """Get user information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SlackTool.BASE_URL}/users.info",
                headers={"Authorization": f"Bearer {token}"},
                params={"user": user}
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            user_info = result["user"]
            return {
                "id": user_info.get("id"),
                "name": user_info.get("name"),
                "real_name": user_info.get("real_name"),
                "email": user_info.get("profile", {}).get("email"),
                "is_bot": user_info.get("is_bot"),
                "is_admin": user_info.get("is_admin"),
                "timezone": user_info.get("tz")
            }
    
    @staticmethod
    async def get_user_presence(
        token: str,
        user: str
    ) -> Dict[str, Any]:
        """Get user presence status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SlackTool.BASE_URL}/users.getPresence",
                headers={"Authorization": f"Bearer {token}"},
                params={"user": user}
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            return {
                "presence": result.get("presence"),
                "online": result.get("online"),
                "auto_away": result.get("auto_away")
            }
    
    @staticmethod
    async def upload_file(
        token: str,
        channels: str,
        file_content: bytes,
        filename: str,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file to Slack."""
        async with httpx.AsyncClient() as client:
            files = {"file": (filename, file_content)}
            data = {"channels": channels}
            
            if title:
                data["title"] = title
            if initial_comment:
                data["initial_comment"] = initial_comment
            
            response = await client.post(
                f"{SlackTool.BASE_URL}/files.upload",
                headers={"Authorization": f"Bearer {token}"},
                files=files,
                data=data
            )
            
            result = response.json()
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error')}")
            
            file_info = result["file"]
            return {
                "success": True,
                "file_id": file_info.get("id"),
                "file_url": file_info.get("url_private")
            }


async def execute_slack_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Slack tool operations."""
    operation = parameters.get("operation", "Send Message")
    token = parameters.get("token")
    
    if not token:
        raise ValueError("Slack token is required")
    
    try:
        if operation == "Send Message":
            return await SlackTool.send_message(
                token=token,
                channel=parameters.get("channel"),
                text=parameters.get("text"),
                blocks=parameters.get("blocks"),
                attachments=parameters.get("attachments"),
                thread_ts=parameters.get("thread_ts"),
                username=parameters.get("username"),
                icon_emoji=parameters.get("icon_emoji"),
                icon_url=parameters.get("icon_url"),
                as_user=parameters.get("as_user", False)
            )
        
        elif operation == "Send Direct Message":
            return await SlackTool.send_direct_message(
                token=token,
                user=parameters.get("user"),
                text=parameters.get("text"),
                blocks=parameters.get("blocks"),
                attachments=parameters.get("attachments")
            )
        
        elif operation == "Update Message":
            return await SlackTool.update_message(
                token=token,
                channel=parameters.get("channel"),
                ts=parameters.get("message_ts"),
                text=parameters.get("text"),
                blocks=parameters.get("blocks"),
                attachments=parameters.get("attachments")
            )
        
        elif operation == "Delete Message":
            return await SlackTool.delete_message(
                token=token,
                channel=parameters.get("channel"),
                ts=parameters.get("message_ts")
            )
        
        elif operation == "Get Channel":
            return await SlackTool.get_channel(
                token=token,
                channel=parameters.get("channel")
            )
        
        elif operation == "Create Channel":
            return await SlackTool.create_channel(
                token=token,
                name=parameters.get("channel_name"),
                is_private=parameters.get("is_private", False)
            )
        
        elif operation == "Archive Channel":
            return await SlackTool.archive_channel(
                token=token,
                channel=parameters.get("channel")
            )
        
        elif operation == "Get User":
            return await SlackTool.get_user(
                token=token,
                user=parameters.get("user")
            )
        
        elif operation == "Get User Presence":
            return await SlackTool.get_user_presence(
                token=token,
                user=parameters.get("user")
            )
        
        elif operation == "Upload File":
            return await SlackTool.upload_file(
                token=token,
                channels=parameters.get("channels"),
                file_content=parameters.get("file_content"),
                filename=parameters.get("filename"),
                title=parameters.get("title"),
                initial_comment=parameters.get("initial_comment")
            )
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"Slack tool error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
