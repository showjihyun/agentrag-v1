"""Simple unit tests for trigger system (no conftest dependency)."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import Mock
from datetime import datetime
import uuid
import hmac
import hashlib

from backend.core.triggers.webhook import WebhookTrigger
from backend.core.triggers.schedule import ScheduleTrigger
from backend.core.triggers.api import APITrigger
from backend.core.triggers.chat import ChatTrigger


class TestWebhookTriggerSimple:
    """Simple tests for WebhookTrigger."""
    
    def test_verify_signature_valid(self):
        """Test webhook signature verification with valid signature."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {"http_method": "POST"}
        
        webhook_trigger = WebhookTrigger(workflow_id, config, db_session)
        webhook_trigger.webhook_secret = "test_secret"
        
        payload = b'{"test": "data"}'
        signature = hmac.new(
            webhook_trigger.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert webhook_trigger.verify_signature(payload, signature) is True
    
    def test_verify_signature_invalid(self):
        """Test webhook signature verification with invalid signature."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {"http_method": "POST"}
        
        webhook_trigger = WebhookTrigger(workflow_id, config, db_session)
        webhook_trigger.webhook_secret = "test_secret"
        
        payload = b'{"test": "data"}'
        invalid_signature = "invalid"
        
        assert webhook_trigger.verify_signature(payload, invalid_signature) is False
    
    def test_parse_json_payload(self):
        """Test parsing JSON payload."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {"http_method": "POST"}
        
        webhook_trigger = WebhookTrigger(workflow_id, config, db_session)
        
        payload = b'{"key": "value"}'
        content_type = "application/json"
        
        result = webhook_trigger.parse_payload(payload, content_type)
        
        assert result == {"key": "value"}


class TestScheduleTriggerSimple:
    """Simple tests for ScheduleTrigger."""
    
    def test_validate_cron_expression_valid(self):
        """Test cron expression validation with valid expression."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "cron_expression": "0 * * * *",
            "timezone": "UTC",
        }
        
        schedule_trigger = ScheduleTrigger(workflow_id, config, db_session)
        
        assert schedule_trigger._validate_cron_expression("0 * * * *") is True
        assert schedule_trigger._validate_cron_expression("*/5 * * * *") is True
        assert schedule_trigger._validate_cron_expression("0 0 * * 0") is True
    
    def test_validate_cron_expression_invalid(self):
        """Test cron expression validation with invalid expression."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "cron_expression": "0 * * * *",
            "timezone": "UTC",
        }
        
        schedule_trigger = ScheduleTrigger(workflow_id, config, db_session)
        
        assert schedule_trigger._validate_cron_expression("invalid") is False
        assert schedule_trigger._validate_cron_expression("* * * *") is False


class TestAPITriggerSimple:
    """Simple tests for APITrigger."""
    
    def test_validate_api_key_valid(self):
        """Test API key validation with valid key."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "rate_limit": 100,
            "rate_limit_window": 3600,
        }
        
        api_trigger = APITrigger(workflow_id, config, db_session)
        api_trigger.api_key = "test_key"
        
        assert api_trigger.validate_api_key("test_key") is True
    
    def test_validate_api_key_invalid(self):
        """Test API key validation with invalid key."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "rate_limit": 100,
            "rate_limit_window": 3600,
        }
        
        api_trigger = APITrigger(workflow_id, config, db_session)
        api_trigger.api_key = "test_key"
        
        assert api_trigger.validate_api_key("wrong_key") is False
    
    def test_validate_request_valid(self):
        """Test request validation with valid data."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "rate_limit": 100,
            "rate_limit_window": 3600,
        }
        
        api_trigger = APITrigger(workflow_id, config, db_session)
        
        request_data = {
            "input_data": {"key": "value"}
        }
        
        is_valid, error = api_trigger.validate_request(request_data)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_request_missing_input_data(self):
        """Test request validation with missing input_data."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "rate_limit": 100,
            "rate_limit_window": 3600,
        }
        
        api_trigger = APITrigger(workflow_id, config, db_session)
        
        request_data = {}
        
        is_valid, error = api_trigger.validate_request(request_data)
        
        assert is_valid is False
        assert "input_data" in error


class TestChatTriggerSimple:
    """Simple tests for ChatTrigger."""
    
    def test_handle_message(self):
        """Test handling chat message."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "enable_streaming": True,
            "max_history": 10,
        }
        
        chat_trigger = ChatTrigger(workflow_id, config, db_session)
        
        message = "Hello, workflow!"
        user_id = str(uuid.uuid4())
        
        result = chat_trigger.handle_message(message, user_id)
        
        assert result["success"] is True
        assert "trigger_data" in result
        assert result["trigger_data"]["message"] == message
    
    def test_add_response(self):
        """Test adding response to conversation history."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "enable_streaming": True,
            "max_history": 10,
        }
        
        chat_trigger = ChatTrigger(workflow_id, config, db_session)
        
        response = "Hello, user!"
        
        chat_trigger.add_response(response)
        
        history = chat_trigger.get_full_history()
        assert len(history) == 1
        assert history[0]["role"] == "assistant"
        assert history[0]["content"] == response
    
    def test_clear_history(self):
        """Test clearing conversation history."""
        db_session = Mock()
        workflow_id = str(uuid.uuid4())
        config = {
            "enable_streaming": True,
            "max_history": 10,
        }
        
        chat_trigger = ChatTrigger(workflow_id, config, db_session)
        
        chat_trigger._add_to_history("user", "Test message")
        assert len(chat_trigger.get_full_history()) == 1
        
        chat_trigger.clear_history()
        
        assert len(chat_trigger.get_full_history()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
