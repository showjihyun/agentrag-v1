"""
Slack Integration Service

Provides methods to interact with Slack API for sending messages.
"""

import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)


class SlackService:
    """Service for Slack API integration."""
    
    def __init__(self, bot_token: str):
        """
        Initialize Slack service.
        
        Args:
            bot_token: Slack Bot User OAuth Token
        """
        self.bot_token = bot_token
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json",
        }
    
    async def send_message(
        self,
        channel: str,
        text: str,
        username: Optional[str] = "Workflow Bot",
        icon_emoji: Optional[str] = ":robot_face:",
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to a Slack channel.
        
        Args:
            channel: Channel name (without #) or channel ID
            text: Message text (supports Slack markdown)
            username: Bot display name
            icon_emoji: Bot icon emoji
            attachments: Optional rich attachments
            
        Returns:
            Response from Slack API
        """
        try:
            payload = {
                "channel": channel if channel.startswith("C") else f"#{channel}",
                "text": text,
                "username": username,
                "icon_emoji": icon_emoji,
            }
            
            if attachments:
                payload["attachments"] = attachments
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat.postMessage",
                    headers=self.headers,
                    json=payload,
                )
                
                result = response.json()
                
                if not result.get("ok"):
                    logger.error(f"Slack API error: {result.get('error')}")
                    raise Exception(f"Slack API error: {result.get('error')}")
                
                logger.info(f"Message sent to Slack channel: {channel}")
                return result
                
        except httpx.TimeoutException:
            logger.error("Slack API request timeout")
            raise Exception("Slack API request timeout")
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise
    
    async def send_rich_message(
        self,
        channel: str,
        text: str,
        blocks: List[Dict[str, Any]],
        username: Optional[str] = "Workflow Bot",
        icon_emoji: Optional[str] = ":robot_face:",
    ) -> Dict[str, Any]:
        """
        Send a rich message with blocks to Slack.
        
        Args:
            channel: Channel name or ID
            text: Fallback text
            blocks: Slack Block Kit blocks
            username: Bot display name
            icon_emoji: Bot icon emoji
            
        Returns:
            Response from Slack API
        """
        try:
            payload = {
                "channel": channel if channel.startswith("C") else f"#{channel}",
                "text": text,
                "blocks": blocks,
                "username": username,
                "icon_emoji": icon_emoji,
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat.postMessage",
                    headers=self.headers,
                    json=payload,
                )
                
                result = response.json()
                
                if not result.get("ok"):
                    logger.error(f"Slack API error: {result.get('error')}")
                    raise Exception(f"Slack API error: {result.get('error')}")
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to send rich Slack message: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """
        Test Slack API connection.
        
        Returns:
            True if connection is successful
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/auth.test",
                    headers=self.headers,
                )
                
                result = response.json()
                return result.get("ok", False)
                
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False
