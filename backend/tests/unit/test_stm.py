"""Unit tests for Short-Term Memory (STM)."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from backend.memory.stm import ShortTermMemory, Message
from redis.exceptions import RedisError


class TestMessage:
    """Test Message class."""

    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")

        assert msg["role"] == "user"
        assert msg["content"] == "Hello"
        assert "timestamp" in msg
        assert msg["metadata"] == {}

    def test_message_with_metadata(self):
        """Test message with metadata."""
        metadata = {"source": "test"}
        msg = Message(role="assistant", content="Hi", metadata=metadata)

        assert msg["metadata"] == metadata


class TestShortTermMemory:
    """Test ShortTermMemory class."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        with patch("backend.memory.stm.redis.Redis") as mock:
            client = MagicMock()
            client.ping.return_value = True
            mock.return_value = client
            yield client

    def test_initialization(self, mock_redis):
        """Test STM initialization."""
        stm = ShortTermMemory(host="localhost", port=6379, ttl=3600)

        assert stm.host == "localhost"
        assert stm.port == 6379
        assert stm.ttl == 3600
        mock_redis.ping.assert_called_once()

    def test_initialization_invalid_params(self):
        """Test initialization with invalid parameters."""
        with pytest.raises(ValueError, match="host cannot be empty"):
            ShortTermMemory(host="")

        with pytest.raises(ValueError, match="port must be positive"):
            ShortTermMemory(port=-1)

        with pytest.raises(ValueError, match="ttl must be positive"):
            ShortTermMemory(ttl=0)

    def test_connection_failure(self):
        """Test connection failure handling."""
        with patch("backend.memory.stm.redis.Redis") as mock:
            client = MagicMock()
            client.ping.side_effect = RedisError("Connection failed")
            mock.return_value = client

            with pytest.raises(RuntimeError, match="Failed to connect to Redis"):
                ShortTermMemory()

    def test_add_message(self, mock_redis):
        """Test adding a message."""
        stm = ShortTermMemory()

        stm.add_message(session_id="session1", role="user", content="Hello")

        # Verify Redis operations
        assert mock_redis.rpush.called
        assert mock_redis.expire.called

        # Check the key format
        call_args = mock_redis.rpush.call_args
        assert "stm:messages:session1" in str(call_args)

    def test_add_message_invalid_params(self, mock_redis):
        """Test add_message with invalid parameters."""
        stm = ShortTermMemory()

        with pytest.raises(ValueError, match="session_id cannot be empty"):
            stm.add_message(session_id="", role="user", content="test")

        with pytest.raises(ValueError, match="role cannot be empty"):
            stm.add_message(session_id="s1", role="", content="test")

        with pytest.raises(ValueError, match="content cannot be empty"):
            stm.add_message(session_id="s1", role="user", content="")

    def test_get_conversation_history(self, mock_redis):
        """Test retrieving conversation history."""
        stm = ShortTermMemory()

        # Mock Redis response
        mock_redis.lrange.return_value = [
            '{"role": "user", "content": "Hello", "timestamp": "2024-01-01T12:00:00", "metadata": {}}',
            '{"role": "assistant", "content": "Hi", "timestamp": "2024-01-01T12:00:01", "metadata": {}}',
        ]

        history = stm.get_conversation_history(session_id="session1")

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        mock_redis.lrange.assert_called_once()

    def test_get_conversation_history_with_limit(self, mock_redis):
        """Test retrieving conversation history with limit."""
        stm = ShortTermMemory()

        mock_redis.lrange.return_value = [
            '{"role": "user", "content": "Hello", "timestamp": "2024-01-01T12:00:00", "metadata": {}}'
        ]

        history = stm.get_conversation_history(session_id="session1", limit=5)

        # Verify limit is used in lrange call
        call_args = mock_redis.lrange.call_args
        assert call_args[0][1] == -5  # Start from -limit
        assert call_args[0][2] == -1  # End at -1

    def test_get_conversation_history_invalid_json(self, mock_redis):
        """Test handling of invalid JSON in history."""
        stm = ShortTermMemory()

        # Mock Redis response with invalid JSON
        mock_redis.lrange.return_value = [
            '{"role": "user", "content": "Hello"}',
            "invalid json",
            '{"role": "assistant", "content": "Hi"}',
        ]

        history = stm.get_conversation_history(session_id="session1")

        # Should skip invalid JSON and return valid messages
        assert len(history) == 2

    def test_store_working_memory(self, mock_redis):
        """Test storing working memory."""
        stm = ShortTermMemory()

        stm.store_working_memory(
            session_id="session1",
            key="current_task",
            value={"task": "search", "status": "in_progress"},
        )

        # Verify Redis operations
        assert mock_redis.hset.called
        assert mock_redis.expire.called

        # Check the key format
        call_args = mock_redis.hset.call_args
        assert "stm:working:session1" in str(call_args)

    def test_get_working_memory_specific_key(self, mock_redis):
        """Test retrieving specific working memory key."""
        stm = ShortTermMemory()

        mock_redis.hget.return_value = '{"task": "search"}'

        value = stm.get_working_memory(session_id="session1", key="current_task")

        assert value == {"task": "search"}
        mock_redis.hget.assert_called_once()

    def test_get_working_memory_all(self, mock_redis):
        """Test retrieving all working memory."""
        stm = ShortTermMemory()

        mock_redis.hgetall.return_value = {
            "task1": '{"status": "done"}',
            "task2": '{"status": "pending"}',
        }

        memory = stm.get_working_memory(session_id="session1")

        assert len(memory) == 2
        assert memory["task1"] == {"status": "done"}
        assert memory["task2"] == {"status": "pending"}

    def test_clear_session(self, mock_redis):
        """Test clearing a session."""
        stm = ShortTermMemory()

        mock_redis.delete.return_value = 2

        stm.clear_session(session_id="session1")

        # Verify both keys are deleted
        call_args = mock_redis.delete.call_args
        assert len(call_args[0]) == 2  # Two keys

    def test_get_session_info(self, mock_redis):
        """Test getting session information."""
        stm = ShortTermMemory()

        mock_redis.llen.return_value = 5
        mock_redis.ttl.return_value = 3000
        mock_redis.hkeys.return_value = ["task1", "task2"]

        info = stm.get_session_info(session_id="session1")

        assert info["session_id"] == "session1"
        assert info["message_count"] == 5
        assert info["messages_ttl"] == 3000
        assert len(info["working_memory_keys"]) == 2
        assert info["exists"] is True

    def test_health_check_healthy(self, mock_redis):
        """Test health check when Redis is healthy."""
        stm = ShortTermMemory()

        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            "redis_version": "7.0.0",
            "used_memory_human": "1M",
            "connected_clients": 5,
        }

        health = stm.health_check()

        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert "redis_version" in health

    def test_health_check_unhealthy(self, mock_redis):
        """Test health check when Redis is unhealthy."""
        stm = ShortTermMemory()

        mock_redis.ping.side_effect = RedisError("Connection lost")

        health = stm.health_check()

        assert health["status"] == "unhealthy"
        assert health["connected"] is False
        assert "error" in health

    def test_context_manager(self, mock_redis):
        """Test using STM as context manager."""
        with ShortTermMemory() as stm:
            assert stm is not None

        # Verify close was called
        mock_redis.close.assert_called_once()
