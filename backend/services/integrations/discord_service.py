"""
Discord Integration Service

Provides methods to interact with Discord webhooks.
"""

import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)


class DiscordService:
    """Service for Discord webhook integration."""
    
    async def send_webhook(
        self,
        webhook_url: str,
        content: str,
        username: Optional[str] = "Workflow Bot",
        avatar_url: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        tts: bool = False,
    ) -> Dict[str, Any]:
        """
        Send a message via Discord webhook.
        
        Args:
            webhook_url: Discord webhook URL
            content: Message content (supports Discord markdown)
            username: Bot display name
            avatar_url: Bot avatar URL
            embeds: Optional rich embeds
            tts: Text-to-speech flag
            
        Returns:
            Response status
        """
        try:
            payload = {
                "content": content,
                "username": username,
                "tts": tts,
            }
            
            if avatar_url:
                payload["avatar_url"] = avatar_url
            
            if embeds:
                payload["embeds"] = embeds
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                )
                
                # Discord webhooks return 204 on success
                if response.status_code == 204:
                    logger.info("Message sent to Discord webhook")
                    return {"success": True, "status_code": 204}
                else:
                    logger.error(f"Discord webhook error: {response.status_code}")
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text,
                    }
                    
        except httpx.TimeoutException:
            logger.error("Discord webhook request timeout")
            raise Exception("Discord webhook request timeout")
        except Exception as e:
            logger.error(f"Failed to send Discord webhook: {e}")
            raise
    
    async def send_embed(
        self,
        webhook_url: str,
        title: str,
        description: str,
        color: int = 0x5865F2,  # Discord blue
        username: Optional[str] = "Workflow Bot",
        avatar_url: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[Dict[str, str]] = None,
        thumbnail_url: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a rich embed message via Discord webhook.
        
        Args:
            webhook_url: Discord webhook URL
            title: Embed title
            description: Embed description
            color: Embed color (integer)
            username: Bot display name
            avatar_url: Bot avatar URL
            fields: List of embed fields
            footer: Footer dict with 'text' and optional 'icon_url'
            thumbnail_url: Thumbnail image URL
            image_url: Main image URL
            
        Returns:
            Response status
        """
        embed = {
            "title": title,
            "description": description,
            "color": color,
        }
        
        if fields:
            embed["fields"] = fields
        
        if footer:
            embed["footer"] = footer
        
        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}
        
        if image_url:
            embed["image"] = {"url": image_url}
        
        return await self.send_webhook(
            webhook_url=webhook_url,
            content="",  # Content can be empty when using embeds
            username=username,
            avatar_url=avatar_url,
            embeds=[embed],
        )
    
    async def test_webhook(self, webhook_url: str) -> bool:
        """
        Test Discord webhook connection.
        
        Args:
            webhook_url: Discord webhook URL
            
        Returns:
            True if webhook is valid
        """
        try:
            result = await self.send_webhook(
                webhook_url=webhook_url,
                content="🔔 Webhook connection test successful!",
                username="Test Bot",
            )
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Discord webhook test failed: {e}")
            return False
    
    @staticmethod
    def hex_to_int_color(hex_color: str) -> int:
        """
        Convert hex color to integer for Discord embeds.
        
        Args:
            hex_color: Hex color string (e.g., "#5865F2")
            
        Returns:
            Integer color value
        """
        hex_color = hex_color.lstrip("#")
        return int(hex_color, 16)
