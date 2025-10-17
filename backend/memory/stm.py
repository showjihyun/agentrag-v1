"""
Short-Term Memory (STM) implementation using Redis.

This module provides conversation context management with TTL-based expiration.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class Message(dict):
    """Represents a message in the conversation."""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            role=role,
            content=content,
            timestamp=(timestamp or datetime.now()).isoformat(),
            metadata=metadata or {},
        )


class ShortTermMemory:
    """
    Short-Term Memory manager using Redis for conversation context.

    Features:
    - Session-based message storage with TTL
    - Conversation history retrieval with limits
    - Working memory for intermediate results
    - Automatic expiration of old sessions
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: int = 3600,
        max_retries: int = 3,
    ):
        """
        Initialize ShortTermMemory with Redis connection.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
            ttl: Time-to-live for sessions in seconds (default: 1 hour)
            max_retries: Maximum connection retry attempts

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If Redis connection fails
        """
        if not host:
            raise ValueError("host cannot be empty")
        if port <= 0:
            raise ValueError("port must be positive")
        if ttl <= 0:
            raise ValueError("ttl must be positive")

        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ttl = ttl
        self.max_retries = max_retries

        # Initialize Redis client (will be connected async)
        self._client: Optional[Redis] = None
        self._connected = False

        logger.info(
            f"ShortTermMemory initialized with Redis at {host}:{port}, "
            f"db={db}, ttl={ttl}s (async mode)"
        )

    async def _connect(self) -> None:
        """
        Establish connection to Redis (async).

        Raises:
            RuntimeError: If connection fails
        """
        try:
            self._client = Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=10,
            )

            # Test connection
            await self._client.ping()
            self._connected = True

            logger.info(f"Successfully connected to Redis at {self.host}:{self.port}")

        except RedisError as e:
            error_msg = f"Failed to connect to Redis: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is established."""
        if not self._connected or self._client is None:
            await self._connect()

    def _get_messages_key(self, session_id: str) -> str:
        """Get Redis key for conversation messages."""
        return f"stm:messages:{session_id}"

    def _get_working_memory_key(self, session_id: str) -> str:
        """Get Redis key for working memory."""
        return f"stm:working:{session_id}"

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to the conversation history (async).

        Args:
            session_id: Unique session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata for the message

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If Redis operation fails
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")
        if not role:
            raise ValueError("role cannot be empty")
        if not content:
            raise ValueError("content cannot be empty")

        try:
            # Ensure connection
            await self._ensure_connected()

            # Create message
            message = Message(
                role=role, content=content, timestamp=datetime.now(), metadata=metadata
            )

            # Serialize message
            message_json = json.dumps(message)

            # Get key
            key = self._get_messages_key(session_id)

            # Add to list and set TTL (async)
            await self._client.rpush(key, message_json)
            await self._client.expire(key, self.ttl)

            logger.debug(
                f"Added {role} message to session {session_id}, "
                f"content length: {len(content)}"
            )

        except RedisError as e:
            error_msg = f"Failed to add message to Redis: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error adding message: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def get_conversation_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session (async).

        Args:
            session_id: Unique session identifier
            limit: Maximum number of recent messages to retrieve (None = all)

        Returns:
            List of message dictionaries, ordered from oldest to newest

        Raises:
            ValueError: If session_id is invalid
            RuntimeError: If Redis operation fails
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        try:
            # Ensure connection
            await self._ensure_connected()

            key = self._get_messages_key(session_id)

            # Get messages (async)
            if limit is None:
                # Get all messages
                messages_json = await self._client.lrange(key, 0, -1)
            else:
                # Get last N messages
                if limit <= 0:
                    raise ValueError("limit must be positive")
                messages_json = await self._client.lrange(key, -limit, -1)

            # Deserialize messages
            messages = []
            for msg_json in messages_json:
                try:
                    message = json.loads(msg_json)
                    messages.append(message)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse message: {e}")
                    continue

            logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")

            return messages

        except RedisError as e:
            error_msg = f"Failed to retrieve conversation history: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except ValueError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error retrieving history: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def store_working_memory(self, session_id: str, key: str, value: Any) -> None:
        """
        Store intermediate results in working memory (async).

        Args:
            session_id: Unique session identifier
            key: Key for the working memory item
            value: Value to store (will be JSON serialized)

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If Redis operation fails
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")
        if not key:
            raise ValueError("key cannot be empty")

        try:
            # Ensure connection
            await self._ensure_connected()

            # Serialize value
            value_json = json.dumps(value)

            # Get Redis key
            redis_key = self._get_working_memory_key(session_id)

            # Store in hash and set TTL (async)
            await self._client.hset(redis_key, key, value_json)
            await self._client.expire(redis_key, self.ttl)

            logger.debug(f"Stored working memory '{key}' for session {session_id}")

        except (RedisError, TypeError) as e:
            error_msg = f"Failed to store working memory: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def get_working_memory(
        self, session_id: str, key: Optional[str] = None
    ) -> Any:
        """
        Retrieve working memory for a session (async).

        Args:
            session_id: Unique session identifier
            key: Specific key to retrieve (None = all working memory)

        Returns:
            Value for specific key, or dict of all working memory

        Raises:
            ValueError: If session_id is invalid
            RuntimeError: If Redis operation fails
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        try:
            # Ensure connection
            await self._ensure_connected()

            redis_key = self._get_working_memory_key(session_id)

            if key is not None:
                # Get specific key (async)
                value_json = await self._client.hget(redis_key, key)
                if value_json is None:
                    return None

                try:
                    return json.loads(value_json)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse working memory value: {e}")
                    return None
            else:
                # Get all working memory (async)
                all_values = await self._client.hgetall(redis_key)

                # Deserialize all values
                result = {}
                for k, v in all_values.items():
                    try:
                        result[k] = json.loads(v)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Failed to parse working memory value for '{k}': {e}"
                        )
                        result[k] = v

                return result

        except RedisError as e:
            error_msg = f"Failed to retrieve working memory: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except ValueError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error retrieving working memory: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def clear_session(self, session_id: str) -> None:
        """
        Clear all data for a session (async).

        Args:
            session_id: Unique session identifier

        Raises:
            ValueError: If session_id is invalid
            RuntimeError: If Redis operation fails
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        try:
            # Ensure connection
            await self._ensure_connected()

            # Delete both messages and working memory (async)
            messages_key = self._get_messages_key(session_id)
            working_key = self._get_working_memory_key(session_id)

            deleted = await self._client.delete(messages_key, working_key)

            logger.info(f"Cleared session {session_id}, deleted {deleted} keys")

        except RedisError as e:
            error_msg = f"Failed to clear session: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a session (async).

        Args:
            session_id: Unique session identifier

        Returns:
            Dictionary with session information
        """
        try:
            # Ensure connection
            await self._ensure_connected()

            messages_key = self._get_messages_key(session_id)
            working_key = self._get_working_memory_key(session_id)

            # Get message count and TTL (async)
            message_count = await self._client.llen(messages_key)
            messages_ttl = await self._client.ttl(messages_key)

            # Get working memory keys (async)
            working_keys = list(await self._client.hkeys(working_key))
            working_ttl = await self._client.ttl(working_key)

            return {
                "session_id": session_id,
                "message_count": message_count,
                "messages_ttl": messages_ttl if messages_ttl > 0 else None,
                "working_memory_keys": working_keys,
                "working_memory_ttl": working_ttl if working_ttl > 0 else None,
                "exists": message_count > 0 or len(working_keys) > 0,
            }

        except RedisError as e:
            logger.error(f"Failed to get session info: {str(e)}")
            return {"session_id": session_id, "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Redis connection health (async).

        Returns:
            Dictionary with health status
        """
        try:
            # Ensure connection
            await self._ensure_connected()

            # Ping Redis (async)
            await self._client.ping()

            # Get Redis info (async)
            info = await self._client.info()

            return {
                "status": "healthy",
                "connected": True,
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
            }

        except RedisError as e:
            return {"status": "unhealthy", "connected": False, "error": str(e)}

    async def close(self) -> None:
        """Close Redis connection (async)."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __repr__(self) -> str:
        return (
            f"ShortTermMemory(host={self.host}, port={self.port}, "
            f"db={self.db}, ttl={self.ttl}s)"
        )
