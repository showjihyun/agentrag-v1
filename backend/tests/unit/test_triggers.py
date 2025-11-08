"""Unit tests for trigger system."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid

from backend.core.triggers.manager import TriggerManager
from backend.core.triggers.webhook import WebhookTrigger
from backend.core.triggers.schedule import ScheduleTrigger
from backend.core.triggers.api import APITrigger
from backend.core.triggers.chat import ChatTrigger


class TestTriggerManager:
    """Tests for TriggerManager."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def trigger_manager(self, db_session):
        """Create TriggerManager instance."""
        return TriggerManager(db_session)
    
    @pytest.mark.asyncio
    async def test_register_webhook_trigger(self, trigger_manager, db_session):
        """Test registering a webhook trigger."""
        workflow_id = str(uuid.uuid4())
        config = {
            "http_method": "POST",
        }
        
        with patch.object(WebhookTrigger, 'register', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = {
                "trigger_id": str(uuid.uuid4()),
                "trigger_type": "webhook",
                "webhook_url": "/api/webhooks/test",
            }
            
            result = await trigger_manager.register_trigger(
                workflow_id=workflow_id,
                trigger_type="webhook",
                config=config
            )
            
            assert result["trigger_type"] == "webhook"
            assert "trigger_id" in result
    
    @pytest.mark.asyncio
    async def test_register_schedule_trigger(self, trigger_manager, db_session):
        """Test registering a schedule trigger."""
        workflow_id = str(uuid.uuid4())
        config = {
            "cron_expression": "0 * * * *",
            "timezone": "UTC",
        }
        
        with patch.object(ScheduleTrigger, 'register', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = {
                "trigger_id": str(uuid.uuid4()),
                "trigger_type": "schedule",
                "cron_expression": "0 * * * *",
            }
            
            result = await trigger_manager.register_trigger(
                workflow_id=workflow_id,
                trigger_type="schedule",
                config=config
            )
            
            assert result["trigger_type"] == "schedule"
            assert result["cron_expression"] == "0 * * * *"
    
    @pytest.mark.asyncio
    async def test_execute_trigger(self, trigger_manager, db_session):
        """Test executing a trigger."""
        workflow_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        trigger_data = {"test": "data"}
        
        with patch.object(trigger_manager.executor, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_context = Mock()
            mock_context.execution_id = str(uuid.uuid4())
            mock_context.status = "completed"
            mock_context.get_final_outputs = Mock(return_value={"result": "success"})
            mock_execute.return_value = mock_context
            
            result = await trigger_manager.execute_trigger(
                workflow_id=workflow_id,
                trigger_type="webhook",
                trigger_data=trigger_data,
                user_id=user_id
            )
            
            assert result["success"] is True
            assert "execution_id" in result


class TestWebhookTrigger:
    """Tests for WebhookTrigger."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session
    
    @pytest.fixture
    def webhook_trigger(self, db_session):
        """Create WebhookTrigger instance."""
        workflow_id = str(uuid.uuid4())
        config = {
            "http_method": "POST",
        }
        return WebhookTrigger(workflow_id, config, db_session)
    
    @pytest.mark.asyncio
    async def test_register_webhook(self, webhook_trigger, db_session):
        """Test webhook registration."""
        result = await webhook_trigger.register()
        
        assert result["trigger_type"] == "webhook"
        assert "webhook_url" in result
        assert "webhook_secret" in result
        assert result["http_method"] == "POST"
    
    def test_verify_signature_valid(self, webhook_trigger):
        """Test webhook signature verification with valid signature."""
        webhook_trigger.webhook_secret = "test_secret"
        payload = b'{"test": "data"}'
        
        import hmac
        import hashlib
        signature = hmac.new(
            webhook_trigger.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert webhook_trigger.verify_signature(payload, signature) is True
    
    def test_verify_signature_invalid(self, webhook_trigger):
        """Test webhook signature verification with invalid signature."""
        webhook_trigger.webhook_secret = "test_secret"
        payload = b'{"test": "data"}'
        invalid_signature = "invalid"
        
        assert webhook_trigger.verify_signature(payload, invalid_signature) is False
    
    def test_parse_json_payload(self, webhook_trigger):
        """Test parsing JSON payload."""
        payload = b'{"key": "value"}'
        content_type = "application/json"
        
        result = webhook_trigger.parse_payload(payload, content_type)
        
        assert result == {"key": "value"}


class TestScheduleTrigger:
    """Tests for ScheduleTrigger."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session
    
    @pytest.fixture
    def schedule_trigger(self, db_session):
        """Create ScheduleTrigger instance."""
        workflow_id = str(uuid.uuid4())
        config = {
            "cron_expression": "0 * * * *",
            "timezone": "UTC",
        }
        return ScheduleTrigger(workflow_id, config, db_session)
    
    def test_validate_cron_expression_valid(self, schedule_trigger):
        """Test cron expression validation with valid expression."""
        assert schedule_trigger._validate_cron_expression("0 * * * *") is True
        assert schedule_trigger._validate_cron_expression("*/5 * * * *") is True
        assert schedule_trigger._validate_cron_expression("0 0 * * 0") is True
    
    def test_validate_cron_expression_invalid(self, schedule_trigger):
        """Test cron expression validation with invalid expression."""
        assert schedule_trigger._validate_cron_expression("invalid") is False
        assert schedule_trigger._validate_cron_expression("* * * *") is False
    
    def test_calculate_next_execution(self, schedule_trigger):
        """Test calculating next execution time."""
        next_execution = schedule_trigger._calculate_next_execution()
        
        assert next_execution is not None
        assert isinstance(next_execution, datetime)
        assert next_execution > datetime.now(next_execution.tzinfo)


class TestAPITrigger:
    """Tests for APITrigger."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def api_trigger(self, db_session):
        """Create APITrigger instance."""
        workflow_id = str(uuid.uuid4())
        config = {
            "rate_limit": 100,
            "rate_limit_window": 3600,
        }
        return APITrigger(workflow_id, config, db_session)
    
    @pytest.mark.asyncio
    async def test_register_api_trigger(self, api_trigger):
        """Test API trigger registration."""
        result = await api_trigger.register()
        
        assert result["trigger_type"] == "api"
        assert "api_key" in result
        assert result["api_key"].startswith("wf_")
        assert result["rate_limit"] == 100
    
    def test_validate_api_key_valid(self, api_trigger):
        """Test API key validation with valid key."""
        api_trigger.api_key = "test_key"
        
        assert api_trigger.validate_api_key("test_key") is True
    
    def test_validate_api_key_invalid(self, api_trigger):
        """Test API key validation with invalid key."""
        api_trigger.api_key = "test_key"
        
        assert api_trigger.validate_api_key("wrong_key") is False
    
    def test_check_rate_limit_allowed(self, api_trigger):
        """Test rate limit check when within limit."""
        api_key = "test_key"
        
        is_allowed, retry_after = api_trigger.check_rate_limit(api_key)
        
        assert is_allowed is True
        assert retry_after is None
    
    def test_validate_request_valid(self, api_trigger):
        """Test request validation with valid data."""
        request_data = {
            "input_data": {"key": "value"}
        }
        
        is_valid, error = api_trigger.validate_request(request_data)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_request_missing_input_data(self, api_trigger):
        """Test request validation with missing input_data."""
        request_data = {}
        
        is_valid, error = api_trigger.validate_request(request_data)
        
        assert is_valid is False
        assert "input_data" in error


class TestChatTrigger:
    """Tests for ChatTrigger."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def chat_trigger(self, db_session):
        """Create ChatTrigger instance."""
        workflow_id = str(uuid.uuid4())
        config = {
            "enable_streaming": True,
            "max_history": 10,
        }
        return ChatTrigger(workflow_id, config, db_session)
    
    @pytest.mark.asyncio
    async def test_register_chat_trigger(self, chat_trigger):
        """Test chat trigger registration."""
        result = await chat_trigger.register()
        
        assert result["trigger_type"] == "chat"
        assert "chat_id" in result
        assert "session_id" in result
        assert result["enable_streaming"] is True
    
    def test_handle_message(self, chat_trigger):
        """Test handling chat message."""
        message = "Hello, workflow!"
        user_id = str(uuid.uuid4())
        
        result = chat_trigger.handle_message(message, user_id)
        
        assert result["success"] is True
        assert "trigger_data" in result
        assert result["trigger_data"]["message"] == message
    
    def test_add_response(self, chat_trigger):
        """Test adding response to conversation history."""
        response = "Hello, user!"
        
        chat_trigger.add_response(response)
        
        history = chat_trigger.get_full_history()
        assert len(history) == 1
        assert history[0]["role"] == "assistant"
        assert history[0]["content"] == response
    
    def test_get_conversation_context(self, chat_trigger):
        """Test getting conversation context."""
        # Add multiple messages
        for i in range(15):
            chat_trigger._add_to_history("user", f"Message {i}")
        
        context = chat_trigger.get_conversation_context()
        
        # Should return last max_history messages
        assert len(context) == chat_trigger.max_history
    
    def test_clear_history(self, chat_trigger):
        """Test clearing conversation history."""
        chat_trigger._add_to_history("user", "Test message")
        assert len(chat_trigger.get_full_history()) == 1
        
        chat_trigger.clear_history()
        
        assert len(chat_trigger.get_full_history()) == 0
