"""
Memory Manager for coordinating Short-Term and Long-Term Memory.

This module provides a unified interface for memory operations across both
STM (Redis) and LTM (Milvus) systems.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.memory.stm import ShortTermMemory
from backend.memory.ltm import LongTermMemory, Interaction

logger = logging.getLogger(__name__)


class MemoryContext:
    """Represents combined memory context for a query."""

    def __init__(
        self,
        recent_history: List[Dict[str, Any]],
        similar_interactions: List[Interaction],
        working_memory: Dict[str, Any],
        session_info: Dict[str, Any],
    ):
        self.recent_history = recent_history
        self.similar_interactions = similar_interactions
        self.working_memory = working_memory
        self.session_info = session_info

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recent_history": self.recent_history,
            "similar_interactions": [
                interaction.to_dict() for interaction in self.similar_interactions
            ],
            "working_memory": self.working_memory,
            "session_info": self.session_info,
        }

    def get_summary(self) -> str:
        """Get a human-readable summary of the memory context."""
        summary_parts = []

        if self.recent_history:
            summary_parts.append(
                f"{len(self.recent_history)} recent messages in conversation"
            )

        if self.similar_interactions:
            summary_parts.append(
                f"{len(self.similar_interactions)} similar past interactions found"
            )

        if self.working_memory:
            summary_parts.append(f"{len(self.working_memory)} working memory items")

        return (
            ", ".join(summary_parts) if summary_parts else "No memory context available"
        )


class MemoryManager:
    """
    Unified manager for Short-Term and Long-Term Memory.

    Features:
    - Coordinate STM and LTM operations
    - Retrieve combined context for queries
    - Consolidate memory from STM to LTM
    - Optimize memory retrieval
    """

    def __init__(
        self,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
        max_history_length: int = 20,
        ltm_similarity_threshold: float = 0.7,
    ):
        """
        Initialize MemoryManager.

        Args:
            stm: ShortTermMemory instance
            ltm: LongTermMemory instance
            max_history_length: Maximum conversation history to retrieve
            ltm_similarity_threshold: Minimum similarity score for LTM retrieval

        Raises:
            ValueError: If parameters are invalid
        """
        if not stm:
            raise ValueError("stm cannot be None")
        if not ltm:
            raise ValueError("ltm cannot be None")
        if max_history_length <= 0:
            raise ValueError("max_history_length must be positive")
        if not 0 <= ltm_similarity_threshold <= 1:
            raise ValueError("ltm_similarity_threshold must be between 0 and 1")

        self.stm = stm
        self.ltm = ltm
        self.max_history_length = max_history_length
        self.ltm_similarity_threshold = ltm_similarity_threshold

        logger.info(
            f"MemoryManager initialized with max_history={max_history_length}, "
            f"ltm_threshold={ltm_similarity_threshold}"
        )

    async def get_context_for_query(
        self,
        session_id: str,
        query: str,
        include_similar_interactions: bool = True,
        max_similar: int = 3,
    ) -> MemoryContext:
        """
        Get combined memory context for a query.

        Retrieves relevant information from both STM and LTM to provide
        comprehensive context for query processing.

        Args:
            session_id: Session identifier
            query: Current query
            include_similar_interactions: Whether to retrieve similar past interactions
            max_similar: Maximum number of similar interactions to retrieve

        Returns:
            MemoryContext with combined information

        Raises:
            ValueError: If parameters are invalid
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")
        if not query:
            raise ValueError("query cannot be empty")

        try:
            # Parallel execution of independent STM operations (now async)
            import asyncio

            # Execute STM operations in parallel (all are now async)
            recent_history, working_memory, session_info = await asyncio.gather(
                self.stm.get_conversation_history(
                    session_id=session_id, limit=self.max_history_length
                ),
                self.stm.get_working_memory(session_id=session_id),
                self.stm.get_session_info(session_id=session_id),
                return_exceptions=True,
            )

            # Handle exceptions
            if isinstance(recent_history, Exception):
                logger.error(f"Error getting recent history: {recent_history}")
                recent_history = []

            if isinstance(working_memory, Exception):
                logger.error(f"Error getting working memory: {working_memory}")
                working_memory = {}

            if isinstance(session_info, Exception):
                logger.error(f"Error getting session info: {session_info}")
                session_info = {"session_id": session_id}

            # Get similar past interactions from LTM (requires query embedding)
            similar_interactions = []
            if include_similar_interactions:
                try:
                    similar_interactions = await self.ltm.retrieve_similar_interactions(
                        query=query,
                        top_k=max_similar,
                        min_success_score=self.ltm_similarity_threshold,
                    )
                except Exception as e:
                    logger.warning(f"Failed to retrieve similar interactions: {e}")

            # Create memory context
            context = MemoryContext(
                recent_history=recent_history,
                similar_interactions=similar_interactions,
                working_memory=working_memory,
                session_info=session_info,
            )

            logger.info(
                f"Retrieved memory context for session {session_id}: "
                f"{context.get_summary()}"
            )

            return context

        except Exception as e:
            error_msg = f"Failed to get context for query: {str(e)}"
            logger.error(error_msg)
            # Return empty context on error rather than failing
            return MemoryContext(
                recent_history=[],
                similar_interactions=[],
                working_memory={},
                session_info={"session_id": session_id, "error": str(e)},
            )

    async def consolidate_memory(
        self,
        session_id: str,
        query: str,
        response: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Consolidate memory by moving successful interactions from STM to LTM.

        This method should be called after a successful query-response cycle
        to persist valuable interactions for future learning.

        Args:
            session_id: Session identifier
            query: Original query
            response: Generated response
            success: Whether the interaction was successful
            metadata: Optional metadata (source_count, action_count, etc.)

        Returns:
            str: ID of stored interaction in LTM, or None if not stored

        Raises:
            ValueError: If parameters are invalid
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")
        if not query:
            raise ValueError("query cannot be empty")
        if not response:
            raise ValueError("response cannot be empty")

        try:
            # Add to STM conversation history (now async)
            await self.stm.add_message(
                session_id=session_id, role="user", content=query
            )

            await self.stm.add_message(
                session_id=session_id, role="assistant", content=response
            )

            # If successful, also store in LTM
            if success:
                metadata = metadata or {}

                # Calculate success score based on metadata
                success_score = self._calculate_success_score(metadata)

                # Extract counts from metadata
                source_count = metadata.get("source_count", 0)
                action_count = metadata.get("action_count", 0)

                # Store in LTM
                interaction_id = await self.ltm.store_interaction(
                    query=query,
                    response=response,
                    session_id=session_id,
                    success_score=success_score,
                    source_count=source_count,
                    action_count=action_count,
                    metadata=metadata,
                )

                logger.info(
                    f"Consolidated memory for session {session_id}, "
                    f"stored as {interaction_id} in LTM"
                )

                return interaction_id
            else:
                logger.debug(
                    f"Interaction not stored in LTM (success=False) for session {session_id}"
                )
                return None

        except Exception as e:
            error_msg = f"Failed to consolidate memory: {str(e)}"
            logger.error(error_msg)
            # Don't raise - memory consolidation failure shouldn't break the flow
            return None

    def _calculate_success_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate success score based on interaction metadata.

        Args:
            metadata: Interaction metadata

        Returns:
            float: Success score between 0 and 1
        """
        # Start with base score
        score = 0.8

        # Adjust based on source count (more sources = better)
        source_count = metadata.get("source_count", 0)
        if source_count > 0:
            score += min(0.1, source_count * 0.02)

        # Adjust based on action count (reasonable number of actions is good)
        action_count = metadata.get("action_count", 0)
        if 1 <= action_count <= 5:
            score += 0.1
        elif action_count > 10:
            score -= 0.1  # Too many actions might indicate inefficiency

        # Check for explicit success indicators
        if metadata.get("has_citations", False):
            score += 0.05

        if metadata.get("user_feedback") == "positive":
            score = 1.0
        elif metadata.get("user_feedback") == "negative":
            score = 0.3

        # Ensure score is in valid range
        return max(0.0, min(1.0, score))

    async def add_working_memory(self, session_id: str, key: str, value: Any) -> None:
        """
        Add item to working memory for current session.

        Args:
            session_id: Session identifier
            key: Memory key
            value: Memory value
        """
        try:
            await self.stm.store_working_memory(
                session_id=session_id, key=key, value=value
            )
            logger.debug(f"Added working memory '{key}' for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to add working memory: {e}")

    async def get_working_memory(
        self, session_id: str, key: Optional[str] = None
    ) -> Any:
        """
        Get working memory for current session.

        Args:
            session_id: Session identifier
            key: Specific key to retrieve (None = all)

        Returns:
            Value for key, or dict of all working memory
        """
        try:
            return await self.stm.get_working_memory(session_id=session_id, key=key)
        except Exception as e:
            logger.error(f"Failed to get working memory: {e}")
            return None if key else {}

    async def clear_session(self, session_id: str) -> None:
        """
        Clear all memory for a session.

        Args:
            session_id: Session identifier
        """
        try:
            await self.stm.clear_session(session_id=session_id)
            logger.info(f"Cleared session {session_id}")
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")

    async def get_relevant_patterns(
        self, pattern_type: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get relevant learned patterns from LTM.

        Args:
            pattern_type: Type of pattern to retrieve (None = all)
            limit: Maximum number of patterns

        Returns:
            List of pattern dictionaries
        """
        try:
            patterns = await self.ltm.retrieve_patterns(
                pattern_type=pattern_type,
                min_success_score=self.ltm_similarity_threshold,
                limit=limit,
            )

            logger.debug(f"Retrieved {len(patterns)} patterns from LTM")
            return patterns

        except Exception as e:
            logger.error(f"Failed to retrieve patterns: {e}")
            return []

    async def store_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        description: str,
        success_score: float = 1.0,
    ) -> Optional[str]:
        """
        Store a learned pattern in LTM.

        Args:
            pattern_type: Type of pattern
            pattern_data: Pattern data
            description: Pattern description
            success_score: Effectiveness score

        Returns:
            str: Pattern ID, or None if storage failed
        """
        try:
            pattern_id = await self.ltm.store_learned_pattern(
                pattern_type=pattern_type,
                pattern_data=pattern_data,
                description=description,
                success_score=success_score,
            )

            logger.info(f"Stored pattern {pattern_id} of type '{pattern_type}'")
            return pattern_id

        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
            return None

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about memory systems.

        Returns:
            Dictionary with memory statistics
        """
        try:
            stm_health = await self.stm.health_check()
            ltm_stats = self.ltm.get_stats()

            return {
                "stm": {
                    "status": stm_health.get("status"),
                    "connected": stm_health.get("connected"),
                    "ttl": self.stm.ttl,
                },
                "ltm": {
                    "status": ltm_stats.get("status"),
                    "total_interactions": ltm_stats.get("total_interactions", 0),
                    "collection": ltm_stats.get("collection_name"),
                },
                "config": {
                    "max_history_length": self.max_history_length,
                    "ltm_similarity_threshold": self.ltm_similarity_threshold,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}

    def __repr__(self) -> str:
        return (
            f"MemoryManager(max_history={self.max_history_length}, "
            f"ltm_threshold={self.ltm_similarity_threshold})"
        )
