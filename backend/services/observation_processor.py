"""
Observation Processing Service for ReAct Pattern.

Processes and scores observations for relevance to improve
ReAct reasoning quality and efficiency.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set
from collections import Counter
import numpy as np

logger = logging.getLogger(__name__)


class ObservationProcessor:
    """
    Process and score observations for relevance.

    Features:
    - Semantic similarity scoring
    - Keyword overlap analysis
    - Information novelty detection
    - Observation filtering
    """

    def __init__(self, embedding_service):
        """
        Initialize observation processor.

        Args:
            embedding_service: Service for generating embeddings
        """
        self.embedding_service = embedding_service
        self.min_relevance_threshold = 0.6

        # Statistics tracking
        self.stats = {
            "total_observations": 0,
            "filtered_observations": 0,
            "total_relevance_score": 0.0,
            "filter_rate": 0.0,
            "avg_relevance": 0.0,
            "processing_count": 0,
        }

        logger.info("ObservationProcessor initialized")

    async def score_observation_relevance(
        self, query: str, observation: str, context: Dict[str, Any]
    ) -> float:
        """
        Score observation relevance to query (0.0-1.0).

        Args:
            query: Original user query
            observation: Observation text to score
            context: Current context including previous observations

        Returns:
            Relevance score between 0.0 and 1.0
        """
        try:
            # 1. Semantic similarity
            semantic_score = await self._calculate_semantic_similarity(
                query, observation
            )

            # 2. Keyword overlap
            keyword_score = self._calculate_keyword_overlap(query, observation)

            # 3. Information novelty
            novelty_score = self._calculate_novelty(observation, context)

            # Weighted combination
            relevance = 0.5 * semantic_score + 0.3 * keyword_score + 0.2 * novelty_score

            logger.debug(
                f"Observation relevance: {relevance:.3f} "
                f"(semantic={semantic_score:.3f}, "
                f"keyword={keyword_score:.3f}, "
                f"novelty={novelty_score:.3f})"
            )

            return float(relevance)

        except Exception as e:
            logger.error(f"Error scoring observation relevance: {e}")
            return 0.5  # Default to medium relevance on error

    async def _calculate_semantic_similarity(
        self, query: str, observation: str
    ) -> float:
        """
        Calculate semantic similarity using embeddings.

        Args:
            query: Query text
            observation: Observation text

        Returns:
            Similarity score (0.0-1.0)
        """
        try:
            # Generate embeddings
            query_emb = await self.embedding_service.embed(query)
            obs_emb = await self.embedding_service.embed(observation)

            # Calculate cosine similarity
            similarity = np.dot(query_emb, obs_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(obs_emb)
            )

            # Normalize to 0-1 range (cosine similarity is -1 to 1)
            normalized = (similarity + 1) / 2

            return float(normalized)

        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.5

    def _calculate_keyword_overlap(self, query: str, observation: str) -> float:
        """
        Calculate keyword overlap between query and observation.

        Args:
            query: Query text
            observation: Observation text

        Returns:
            Overlap score (0.0-1.0)
        """
        try:
            # Extract keywords
            query_keywords = self._extract_keywords(query)
            obs_keywords = self._extract_keywords(observation)

            if not query_keywords:
                return 0.5

            # Calculate overlap
            overlap = len(query_keywords & obs_keywords)
            overlap_score = overlap / len(query_keywords)

            return float(overlap_score)

        except Exception as e:
            logger.error(f"Error calculating keyword overlap: {e}")
            return 0.5

    def _extract_keywords(self, text: str) -> Set[str]:
        """
        Extract keywords from text.

        Args:
            text: Input text

        Returns:
            Set of keywords
        """
        # Convert to lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)

        # Split into words
        words = text.split()

        # Remove common stop words (simple list)
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
        }

        # Filter stop words and short words
        keywords = {word for word in words if word not in stop_words and len(word) > 2}

        return keywords

    def _calculate_novelty(self, observation: str, context: Dict[str, Any]) -> float:
        """
        Calculate information novelty compared to existing context.

        Args:
            observation: New observation
            context: Existing context

        Returns:
            Novelty score (0.0-1.0)
        """
        try:
            # Get previous observations
            previous_obs = context.get("retrieved_docs", [])

            if not previous_obs:
                return 1.0  # First observation is always novel

            # Extract keywords from new observation
            new_keywords = self._extract_keywords(observation)

            # Extract keywords from previous observations
            prev_keywords = set()
            for doc in previous_obs:
                content = doc.get("content", "") or doc.get("text", "")
                prev_keywords.update(self._extract_keywords(content))

            if not new_keywords:
                return 0.0

            # Calculate novelty as ratio of new keywords
            novel_keywords = new_keywords - prev_keywords
            novelty = len(novel_keywords) / len(new_keywords)

            return float(novelty)

        except Exception as e:
            logger.error(f"Error calculating novelty: {e}")
            return 0.5

    async def filter_observations(
        self,
        query: str,
        observations: List[Dict[str, Any]],
        context: Dict[str, Any],
        min_relevance: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter observations by relevance threshold.

        Args:
            query: Original query
            observations: List of observations to filter
            context: Current context
            min_relevance: Minimum relevance threshold (default: 0.6)

        Returns:
            Filtered list of observations with relevance scores
        """
        if min_relevance is None:
            min_relevance = self.min_relevance_threshold

        filtered = []

        for obs in observations:
            # Get observation content
            content = obs.get("content", "") or obs.get("text", "") or str(obs)

            # Score relevance
            relevance = await self.score_observation_relevance(query, content, context)

            # Add relevance score to observation
            obs_with_score = obs.copy() if isinstance(obs, dict) else {"content": obs}
            obs_with_score["relevance_score"] = relevance

            # Filter by threshold
            if relevance >= min_relevance:
                filtered.append(obs_with_score)

        # Sort by relevance (highest first)
        filtered.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Update statistics
        self.stats["total_observations"] += len(observations)
        self.stats["filtered_observations"] += len(filtered)
        self.stats["processing_count"] += 1

        if filtered:
            avg_relevance = sum(o["relevance_score"] for o in filtered) / len(filtered)
            self.stats["total_relevance_score"] += avg_relevance * len(filtered)
            self.stats["avg_relevance"] = self.stats["total_relevance_score"] / max(
                self.stats["filtered_observations"], 1
            )

        if self.stats["total_observations"] > 0:
            self.stats["filter_rate"] = 1 - (
                self.stats["filtered_observations"] / self.stats["total_observations"]
            )

        logger.info(
            f"Filtered observations: {len(filtered)}/{len(observations)} "
            f"(threshold={min_relevance:.2f})"
        )

        return filtered

    async def summarize_observation(
        self, observation: str, max_length: int = 200
    ) -> str:
        """
        Summarize long observation to reduce context length.

        Args:
            observation: Observation text
            max_length: Maximum length in characters

        Returns:
            Summarized observation
        """
        if len(observation) <= max_length:
            return observation

        # Simple truncation with ellipsis
        # TODO: Could use LLM for better summarization
        summarized = observation[: max_length - 3] + "..."

        logger.debug(
            f"Summarized observation: {len(observation)} → {len(summarized)} chars"
        )

        return summarized

    async def process_observations(
        self,
        query: str,
        observations: List[Dict[str, Any]],
        context: Dict[str, Any],
        filter_threshold: float = 0.6,
        summarize: bool = True,
        max_summary_length: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Process observations: score, filter, and optionally summarize.

        Args:
            query: Original query
            observations: Raw observations
            context: Current context
            filter_threshold: Minimum relevance threshold
            summarize: Whether to summarize long observations
            max_summary_length: Maximum length for summaries

        Returns:
            Processed observations
        """
        # Filter by relevance
        filtered = await self.filter_observations(
            query, observations, context, filter_threshold
        )

        # Summarize if requested
        if summarize:
            for obs in filtered:
                content = obs.get("content", "") or obs.get("text", "")
                if len(content) > max_summary_length:
                    obs["original_content"] = content
                    obs["content"] = await self.summarize_observation(
                        content, max_summary_length
                    )

        return filtered

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get observation processing statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_observations": self.stats["total_observations"],
            "filtered_observations": self.stats["filtered_observations"],
            "filter_rate": round(self.stats["filter_rate"], 3),
            "avg_relevance": round(self.stats["avg_relevance"], 3),
            "processing_count": self.stats["processing_count"],
            "avg_observations_per_query": (
                round(
                    self.stats["total_observations"]
                    / max(self.stats["processing_count"], 1),
                    1,
                )
            ),
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            "total_observations": 0,
            "filtered_observations": 0,
            "total_relevance_score": 0.0,
            "filter_rate": 0.0,
            "avg_relevance": 0.0,
            "processing_count": 0,
        }
        logger.info("Statistics reset")
