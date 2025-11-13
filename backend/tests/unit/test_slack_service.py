"""
Unit tests for Slack Service
"""

import pytest
from unittest.mock import AsyncMock, patch
from backend.services.integrations.slack_service import SlackService


@pytest.mark.asyncio
async def test_slack_send_message():
    """Test sending Slack message."""
    slack = SlackService(bot_token="xoxb-test-token")
    
    # Mock httpx client
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C1234567890",
        }
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        result = await slack.send_message(
            channel="general",
            text="Test message",
            username="Test Bot",
        )
        
        assert result["ok"] is True
        assert "ts" in result


@pytest.mark.asyncio
async def test_slack_connection_test():
    """Test Slack connection."""
    slack = SlackService(bot_token="xoxb-test-token")
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"ok": True}
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        is_connected = await slack.test_connection()
        
        assert is_connected is True
