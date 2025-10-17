"""
Episodic Memory Service for ReAct Pattern Reuse.

Stores and retrieves successful ReAct episodes to accelerate
similar query processing.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class ReActEpisode:
    """
    Represents a single ReAct episode.

    An episode contains:
    - Query and its embedding
    - Sequence of actions taken
    - Success metrics
    - Metadata
    """

    def __init__(
        self,
        query: str,
        query_embedding: np.ndarray,
        actions: List[Dict[str, Any]],
        success: bool,
        confidence: float,
        total_iterations: int,
        elapsed_time: float,
        retrieved_docs_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize ReAct episode.

        Args:
            query: Original query text
            query_embedding: Query embedding vector
            actions: List of actions taken
            success: Whether episode was successful
            confidence: Confidence score (0.0-1.0)
            total_iterations: Number of ReAct iterations
            elapsed_time: Total time in seconds
            retrieved_docs_count: Number of documents retrieved
            metadata: Additional metadata
        """
        self.query = query
        self.query_embedding = query_embedding
        self.actions = actions
        self.success = success
        self.confidence = confidence
        self.total_iterations = total_iterations
        self.elapsed_time = elapsed_time
        self.retrieved_docs_count = retrieved_docs_count
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.reuse_count = 0
        self.success_rate = 1.0 if success else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert episode to dictionary."""
        return {
            "query": self.query,
            "query_embedding": (
                self.query_embedding.tolist()
                if isinstance(self.query_embedding, np.ndarray)
                else self.query_embedding
            ),
            "actions": self.actions,
            "success": self.success,
            "confidence": self.confidence,
            "total_iterations": self.total_iterations,
            "elapsed_time": self.elapsed_time,
            "retrieved_docs_count": self.retrieved_docs_count,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "reuse_count": self.reuse_count,
            "success_rate": self.success_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReActEpisode":
        """Create episode from dictionary."""
        episode = cls(
            query=data["query"],
            query_embedding=np.array(data["query_embedding"]),
            actions=data["actions"],
            success=data["success"],
            confidence=data["confidence"],
            total_iterations=data["total_iterations"],
            elapsed_time=data["elapsed_time"],
            retrieved_docs_count=data["retrieved_docs_count"],
            metadata=data.get("metadata", {}),
        )
        episode.timestamp = datetime.fromisoformat(data["timestamp"])
        episode.reuse_count = data.get("reuse_count", 0)
        episode.success_rate = data.get("success_rate", 1.0)
        return episode


class EpisodicMemory:
    """
    Episodic Memory for storing and retrieving successful ReAct patterns.

    Features:
    - Store successful ReAct episodes
    - Retrieve similar episodes by semantic similarity
    - Track reuse statistics
    - Automatic cleanup of old/unsuccessful episodes
    """

    def __init__(
        self,
        embedding_service,
        ltm_manager,
        max_episodes: int = 1000,
        similarity_threshold: float = 0.85,
        min_confidence: float = 0.7,
        retention_days: int = 30,
    ):
        """
        Initialize episodic memory.

        Args:
            embedding_service: Service for generating embeddings
            ltm_manager: Long-term memory manager
            max_episodes: Maximum number of episodes to store
            similarity_threshold: Minimum similarity for episode reuse
            min_confidence: Minimum confidence to store episode
            retention_days: Days to retain episodes
        """
        self.embedding_service = embedding_service
        self.ltm = ltm_manager
        self.max_episodes = max_episodes
        self.similarity_threshold = similarity_threshold
        self.min_confidence = min_confidence
        self.retention_days = retention_days

        # In-memory cache for fast access
        self.episode_cache: List[ReActEpisode] = []

        logger.info(
            f"EpisodicMemory initialized: max_episodes={max_episodes}, "
            f"similarity_threshold={similarity_threshold}, "
            f"min_confidence={min_confidence}"
        )

    async def store_episode(
        self,
        query: str,
        actions: List[Dict[str, Any]],
        success: bool,
        confidence: float,
        total_iterations: int,
        elapsed_time: float,
        retrieved_docs_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store a ReAct episode if it meets quality criteria.

        Args:
            query: Original query
            actions: List of actions taken
            success: Whether episode was successful
            confidence: Confidence score
            total_iterations: Number of iterations
            elapsed_time: Total time
            retrieved_docs_count: Number of docs retrieved
            metadata: Additional metadata

        Returns:
            True if episode was stored
        """
        try:
            # Only store successful episodes with high confidence
            if not success or confidence < self.min_confidence:
                logger.debug(
                    f"Episode not stored: success={success}, confidence={confidence:.2f}"
                )
                return False

            # Generate query embedding
            query_embedding = await self.embedding_service.embed(query)

            # Create episode
            episode = ReActEpisode(
                query=query,
                query_embedding=query_embedding,
                actions=actions,
                success=success,
                confidence=confidence,
                total_iterations=total_iterations,
                elapsed_time=elapsed_time,
                retrieved_docs_count=retrieved_docs_count,
                metadata=metadata,
            )

            # Add to cache
            self.episode_cache.append(episode)

            # Maintain cache size
            if len(self.episode_cache) > self.max_episodes:
                # Remove oldest episode
                self.episode_cache.pop(0)

            # Store in LTM
            await self._store_in_ltm(episode)

            logger.info(
                f"Episode stored: query='{query[:50]}...', "
                f"iterations={total_iterations}, confidence={confidence:.2f}"
            )

            return True

        except Exception as e:
            logger.error(f"Error storing episode: {e}")
            return False

    async def _store_in_ltm(self, episode: ReActEpisode):
        """Store episode in long-term memory."""
        try:
            # Store in LTM with episode data
            await self.ltm.store_interaction(
                session_id="episodic_memory",
                query=episode.query,
                response=json.dumps(episode.to_dict()),
                metadata={
                    "type": "react_episode",
                    "confidence": episode.confidence,
                    "iterations": episode.total_iterations,
                    "timestamp": episode.timestamp.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error storing episode in LTM: {e}")

    async def retrieve_similar_episode(
        self, query: str, top_k: int = 3
    ) -> Optional[Tuple[ReActEpisode, float]]:
        """
        Retrieve most similar successful episode.

        Args:
            query: Query to match
            top_k: Number of candidates to consider

        Returns:
            Tuple of (episode, similarity) if found, None otherwise
        """
        try:
            if not self.episode_cache:
                logger.debug("No episodes in cache")
                return None

            # Generate query embedding
            query_embedding = await self.embedding_service.embed(query)

            # Calculate similarities
            similarities = []
            for episode in self.episode_cache:
                similarity = self._calculate_similarity(
                    query_embedding, episode.query_embedding
                )
                similarities.append((episode, similarity))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Get best match
            best_episode, best_similarity = similarities[0]

            # Check threshold
            if best_similarity >= self.similarity_threshold:
                logger.info(
                    f"Similar episode found: similarity={best_similarity:.3f}, "
                    f"original_query='{best_episode.query[:50]}...', "
                    f"reuse_count={best_episode.reuse_count}"
                )

                # Update reuse statistics
                best_episode.reuse_count += 1

                return best_episode, best_similarity
            else:
                logger.debug(
                    f"No similar episode above threshold: "
                    f"best_similarity={best_similarity:.3f} < {self.similarity_threshold}"
                )
                return None

        except Exception as e:
            logger.error(f"Error retrieving similar episode: {e}")
            return None

    def _calculate_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0.0-1.0)
        """
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )

        # Normalize to 0-1 range
        normalized = (similarity + 1) / 2

        return float(normalized)

    async def get_suggested_actions(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get suggested actions from similar episode.

        Args:
            query: Query to match

        Returns:
            List of suggested actions if found
        """
        result = await self.retrieve_similar_episode(query)

        if result:
            episode, similarity = result

            # Return actions with metadata
            suggested_actions = []
            for action in episode.actions:
                suggested_actions.append(
                    {
                        **action,
                        "from_episode": True,
                        "episode_similarity": similarity,
                        "episode_confidence": episode.confidence,
                        "episode_reuse_count": episode.reuse_count,
                    }
                )

            return suggested_actions

        return None

    async def cleanup_old_episodes(self):
        """Remove episodes older than retention period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            initial_count = len(self.episode_cache)
            self.episode_cache = [
                ep for ep in self.episode_cache if ep.timestamp > cutoff_date
            ]
            removed_count = initial_count - len(self.episode_cache)

            if removed_count > 0:
                logger.info(
                    f"Cleaned up {removed_count} old episodes "
                    f"(older than {self.retention_days} days)"
                )

        except Exception as e:
            logger.error(f"Error cleaning up episodes: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get episodic memory statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.episode_cache:
            return {
                "total_episodes": 0,
                "avg_confidence": 0.0,
                "avg_iterations": 0.0,
                "avg_elapsed_time": 0.0,
                "total_reuses": 0,
                "most_reused_query": None,
            }

        total_reuses = sum(ep.reuse_count for ep in self.episode_cache)
        most_reused = max(self.episode_cache, key=lambda ep: ep.reuse_count)

        return {
            "total_episodes": len(self.episode_cache),
            "avg_confidence": np.mean([ep.confidence for ep in self.episode_cache]),
            "avg_iterations": np.mean(
                [ep.total_iterations for ep in self.episode_cache]
            ),
            "avg_elapsed_time": np.mean([ep.elapsed_time for ep in self.episode_cache]),
            "total_reuses": total_reuses,
            "most_reused_query": (
                most_reused.query if most_reused.reuse_count > 0 else None
            ),
            "most_reused_count": most_reused.reuse_count,
        }
