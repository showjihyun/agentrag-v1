"""
Query Pattern Learning System

Learns from query patterns and historical performance to improve routing decisions.
Stores patterns in Milvus LTM for persistent learning.
"""

import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from backend.memory.manager import MemoryManager
from backend.services.confidence_service import ConfidenceService
from backend.models.hybrid import QueryMode
from backend.services.adaptive_rag_service import QueryComplexity

logger = logging.getLogger(__name__)


@dataclass
class PatternEntry:
    """Represents a stored query pattern."""

    id: str
    query_hash: str
    query_embedding: List[float]
    complexity: QueryComplexity
    mode_used: QueryMode
    processing_time: float
    confidence_score: float
    user_feedback: Optional[float]
    timestamp: datetime
    metadata: Dict[str, Any]
    similarity_score: float = 0.0  # Similarity to current query

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "query_hash": self.query_hash,
            "complexity": (
                self.complexity.value
                if isinstance(self.complexity, QueryComplexity)
                else self.complexity
            ),
            "mode_used": (
                self.mode_used.value
                if isinstance(self.mode_used, QueryMode)
                else self.mode_used
            ),
            "processing_time": self.processing_time,
            "confidence_score": self.confidence_score,
            "user_feedback": self.user_feedback,
            "timestamp": (
                self.timestamp.isoformat()
                if isinstance(self.timestamp, datetime)
                else self.timestamp
            ),
            "metadata": self.metadata,
            "similarity_score": self.similarity_score,
        }


@dataclass
class PatternRecommendation:
    """Recommendation based on similar query patterns."""

    recommended_mode: QueryMode
    confidence: float
    similar_queries: int
    avg_processing_time: float
    avg_confidence_score: float
    success_rate: float
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommended_mode": (
                self.recommended_mode.value
                if isinstance(self.recommended_mode, QueryMode)
                else self.recommended_mode
            ),
            "confidence": self.confidence,
            "similar_queries": self.similar_queries,
            "avg_processing_time": self.avg_processing_time,
            "avg_confidence_score": self.avg_confidence_score,
            "success_rate": self.success_rate,
            "reasoning": self.reasoning,
        }


@dataclass
class PatternAnalysis:
    """Analysis of query patterns for threshold tuning."""

    total_patterns: int
    mode_distribution: Dict[str, float]
    avg_latency_by_mode: Dict[str, float]
    avg_confidence_by_mode: Dict[str, float]
    success_rate_by_mode: Dict[str, float]
    misclassified_patterns: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_patterns": self.total_patterns,
            "mode_distribution": self.mode_distribution,
            "avg_latency_by_mode": self.avg_latency_by_mode,
            "avg_confidence_by_mode": self.avg_confidence_by_mode,
            "success_rate_by_mode": self.success_rate_by_mode,
            "misclassified_patterns": self.misclassified_patterns,
        }


class QueryPatternLearner:
    """
    Learn from query patterns and improve routing decisions over time.

    Features:
    - Store query execution data in Milvus LTM
    - Find similar historical queries using semantic search
    - Calculate recommendation confidence based on historical performance
    - Analyze patterns for threshold tuning
    """

    # Pattern storage configuration
    PATTERN_TYPE = "query_routing"
    MIN_SAMPLES_FOR_RECOMMENDATION = 3
    SIMILARITY_THRESHOLD = 0.80

    # Success criteria
    MIN_CONFIDENCE_FOR_SUCCESS = 0.70
    MAX_PROCESSING_TIME_FAST = 1.5
    MAX_PROCESSING_TIME_BALANCED = 4.0
    MAX_PROCESSING_TIME_DEEP = 20.0

    def __init__(
        self,
        memory_manager: MemoryManager,
        confidence_service: ConfidenceService,
        min_samples: int = 3,
        similarity_threshold: float = 0.80,
    ):
        """
        Initialize QueryPatternLearner.

        Args:
            memory_manager: MemoryManager for LTM storage
            confidence_service: ConfidenceService for feedback integration
            min_samples: Minimum samples needed for recommendation
            similarity_threshold: Minimum similarity for pattern matching

        Raises:
            ValueError: If parameters are invalid
        """
        if not memory_manager:
            raise ValueError("memory_manager cannot be None")
        if not confidence_service:
            raise ValueError("confidence_service cannot be None")
        if min_samples < 1:
            raise ValueError("min_samples must be at least 1")
        if not 0 <= similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")

        self.memory = memory_manager
        self.confidence = confidence_service
        self.min_samples = min_samples
        self.similarity_threshold = similarity_threshold

        # In-memory cache for recent patterns
        self.pattern_cache: Dict[str, PatternEntry] = {}
        self.cache_size = 1000

        logger.info(
            f"QueryPatternLearner initialized with min_samples={min_samples}, "
            f"similarity_threshold={similarity_threshold}"
        )

    def _hash_query(self, query: str) -> str:
        """
        Generate privacy-preserving hash of query.

        Args:
            query: Query text

        Returns:
            SHA256 hash of query
        """
        return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]

    async def record_query(
        self,
        query: str,
        complexity: QueryComplexity,
        mode_used: QueryMode,
        processing_time: float,
        confidence_score: float,
        user_feedback: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record query execution for learning.

        Args:
            query: Original query text
            complexity: Detected complexity level
            mode_used: Mode that was used
            processing_time: Actual processing time in seconds
            confidence_score: Confidence score of response
            user_feedback: Optional user feedback (0-1 scale)
            metadata: Optional additional metadata

        Returns:
            str: ID of stored pattern

        Raises:
            ValueError: If parameters are invalid
        """
        if not query:
            raise ValueError("query cannot be empty")
        if processing_time < 0:
            raise ValueError("processing_time must be non-negative")
        if not 0 <= confidence_score <= 1:
            raise ValueError("confidence_score must be between 0 and 1")
        if user_feedback is not None and not 0 <= user_feedback <= 1:
            raise ValueError("user_feedback must be between 0 and 1")

        try:
            # Generate pattern ID
            pattern_id = f"pattern_{uuid.uuid4().hex[:12]}"
            query_hash = self._hash_query(query)

            # Prepare pattern data
            pattern_data = {
                "query_hash": query_hash,
                "complexity": (
                    complexity.value
                    if isinstance(complexity, QueryComplexity)
                    else complexity
                ),
                "mode_used": (
                    mode_used.value if isinstance(mode_used, QueryMode) else mode_used
                ),
                "processing_time": processing_time,
                "confidence_score": confidence_score,
                "user_feedback": user_feedback,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
            }

            # Calculate success score
            success_score = self._calculate_success_score(
                mode_used=mode_used,
                processing_time=processing_time,
                confidence_score=confidence_score,
                user_feedback=user_feedback,
            )

            # Store in LTM using pattern storage
            description = (
                f"Query pattern: complexity={complexity.value}, mode={mode_used.value}"
            )

            stored_id = await self.memory.store_pattern(
                pattern_type=self.PATTERN_TYPE,
                pattern_data=pattern_data,
                description=description,
                success_score=success_score,
            )

            # Update in-memory cache
            if stored_id:
                pattern_entry = PatternEntry(
                    id=stored_id,
                    query_hash=query_hash,
                    query_embedding=[],  # Will be populated on retrieval
                    complexity=complexity,
                    mode_used=mode_used,
                    processing_time=processing_time,
                    confidence_score=confidence_score,
                    user_feedback=user_feedback,
                    timestamp=datetime.now(),
                    metadata=metadata or {},
                )

                self._update_cache(stored_id, pattern_entry)

                logger.info(
                    f"Recorded query pattern {stored_id}: "
                    f"complexity={complexity.value}, mode={mode_used.value}, "
                    f"time={processing_time:.2f}s, confidence={confidence_score:.2f}, "
                    f"success={success_score:.2f}"
                )

            return stored_id or pattern_id

        except Exception as e:
            logger.error(f"Failed to record query pattern: {e}")
            # Don't raise - pattern recording failure shouldn't break the flow
            return f"error_{uuid.uuid4().hex[:8]}"

    def _calculate_success_score(
        self,
        mode_used: QueryMode,
        processing_time: float,
        confidence_score: float,
        user_feedback: Optional[float],
    ) -> float:
        """
        Calculate success score for a query execution.

        Args:
            mode_used: Mode that was used
            processing_time: Actual processing time
            confidence_score: Confidence score
            user_feedback: Optional user feedback

        Returns:
            float: Success score (0-1)
        """
        # Start with confidence score
        score = confidence_score * 0.5

        # Add latency component (meeting target = good)
        latency_targets = {
            QueryMode.FAST: self.MAX_PROCESSING_TIME_FAST,
            QueryMode.BALANCED: self.MAX_PROCESSING_TIME_BALANCED,
            QueryMode.DEEP: self.MAX_PROCESSING_TIME_DEEP,
        }

        target = latency_targets.get(mode_used, 10.0)
        if processing_time <= target:
            score += 0.3
        elif processing_time <= target * 1.5:
            score += 0.15

        # Add user feedback if available (highest weight)
        if user_feedback is not None:
            score = score * 0.5 + user_feedback * 0.5
        else:
            score += 0.2  # Default bonus if no negative feedback

        return max(0.0, min(1.0, score))

    def _update_cache(self, pattern_id: str, pattern: PatternEntry):
        """Update in-memory pattern cache."""
        self.pattern_cache[pattern_id] = pattern

        # Evict oldest if cache is full
        if len(self.pattern_cache) > self.cache_size:
            oldest_id = min(
                self.pattern_cache.keys(), key=lambda k: self.pattern_cache[k].timestamp
            )
            del self.pattern_cache[oldest_id]

    async def get_pattern_recommendation(
        self, query: str, current_complexity: Optional[QueryComplexity] = None
    ) -> Optional[PatternRecommendation]:
        """
        Get mode recommendation based on similar historical patterns.

        Args:
            query: Current query text
            current_complexity: Optional current complexity assessment

        Returns:
            PatternRecommendation if sufficient data exists, None otherwise
        """
        if not query:
            return None

        try:
            # Find similar patterns
            similar_patterns = await self._find_similar_patterns(query=query, top_k=10)

            if len(similar_patterns) < self.min_samples:
                logger.debug(
                    f"Insufficient patterns for recommendation: "
                    f"{len(similar_patterns)} < {self.min_samples}"
                )
                return None

            # Analyze patterns by mode
            mode_performance = self._analyze_mode_performance(similar_patterns)

            if not mode_performance:
                return None

            # Select best mode
            best_mode = max(
                mode_performance.keys(),
                key=lambda m: self._calculate_mode_score(mode_performance[m]),
            )

            best_perf = mode_performance[best_mode]

            # Calculate recommendation confidence
            confidence = self._calculate_recommendation_confidence(
                similar_patterns=similar_patterns,
                best_performance=best_perf,
                all_performance=mode_performance,
            )

            # Generate reasoning
            reasoning = self._generate_reasoning(
                best_mode=best_mode,
                performance=best_perf,
                similar_count=len(similar_patterns),
                current_complexity=current_complexity,
            )

            recommendation = PatternRecommendation(
                recommended_mode=best_mode,
                confidence=confidence,
                similar_queries=len(similar_patterns),
                avg_processing_time=best_perf["avg_time"],
                avg_confidence_score=best_perf["avg_confidence"],
                success_rate=best_perf["success_rate"],
                reasoning=reasoning,
            )

            logger.info(
                f"Pattern recommendation: mode={best_mode.value}, "
                f"confidence={confidence:.2f}, similar={len(similar_patterns)}"
            )

            return recommendation

        except Exception as e:
            logger.error(f"Failed to get pattern recommendation: {e}")
            return None

    async def _find_similar_patterns(
        self, query: str, top_k: int = 10
    ) -> List[PatternEntry]:
        """
        Find similar query patterns using semantic search.

        Args:
            query: Query text
            top_k: Number of similar patterns to retrieve

        Returns:
            List of similar PatternEntry objects
        """
        try:
            # Get patterns from LTM
            patterns = await self.memory.get_relevant_patterns(
                pattern_type=self.PATTERN_TYPE, limit=top_k
            )

            # Convert to PatternEntry objects
            pattern_entries = []
            for pattern in patterns:
                try:
                    # Parse pattern data
                    data = pattern.get("data", "{}")
                    if isinstance(data, str):
                        import json

                        data = json.loads(data) if data.startswith("{") else {}

                    # Extract fields
                    complexity_str = data.get("complexity", "MEDIUM")
                    mode_str = data.get("mode_used", "BALANCED")

                    # Convert to enums
                    complexity = (
                        QueryComplexity(complexity_str)
                        if complexity_str in [c.value for c in QueryComplexity]
                        else QueryComplexity.MEDIUM
                    )
                    mode = (
                        QueryMode(mode_str)
                        if mode_str in [m.value for m in QueryMode]
                        else QueryMode.BALANCED
                    )

                    # Parse timestamp
                    timestamp_str = data.get("timestamp", datetime.now().isoformat())
                    timestamp = (
                        datetime.fromisoformat(timestamp_str)
                        if isinstance(timestamp_str, str)
                        else datetime.now()
                    )

                    entry = PatternEntry(
                        id=pattern.get("id", ""),
                        query_hash=data.get("query_hash", ""),
                        query_embedding=[],
                        complexity=complexity,
                        mode_used=mode,
                        processing_time=float(data.get("processing_time", 0.0)),
                        confidence_score=float(data.get("confidence_score", 0.0)),
                        user_feedback=data.get("user_feedback"),
                        timestamp=timestamp,
                        metadata=data.get("metadata", {}),
                        similarity_score=pattern.get("success_score", 0.0),
                    )

                    # Filter by similarity threshold
                    if entry.similarity_score >= self.similarity_threshold:
                        pattern_entries.append(entry)

                except Exception as e:
                    logger.warning(f"Failed to parse pattern: {e}")
                    continue

            logger.debug(f"Found {len(pattern_entries)} similar patterns")
            return pattern_entries

        except Exception as e:
            logger.error(f"Failed to find similar patterns: {e}")
            return []

    def _analyze_mode_performance(
        self, patterns: List[PatternEntry]
    ) -> Dict[QueryMode, Dict[str, Any]]:
        """
        Analyze performance by mode.

        Args:
            patterns: List of pattern entries

        Returns:
            Dict mapping mode to performance metrics
        """
        mode_data: Dict[QueryMode, List[PatternEntry]] = {
            QueryMode.FAST: [],
            QueryMode.BALANCED: [],
            QueryMode.DEEP: [],
        }

        # Group by mode
        for pattern in patterns:
            if pattern.mode_used in mode_data:
                mode_data[pattern.mode_used].append(pattern)

        # Calculate metrics for each mode
        performance = {}
        for mode, mode_patterns in mode_data.items():
            if not mode_patterns:
                continue

            # Calculate averages
            avg_time = sum(p.processing_time for p in mode_patterns) / len(
                mode_patterns
            )
            avg_confidence = sum(p.confidence_score for p in mode_patterns) / len(
                mode_patterns
            )

            # Calculate success rate
            successful = sum(
                1
                for p in mode_patterns
                if p.confidence_score >= self.MIN_CONFIDENCE_FOR_SUCCESS
                and (p.user_feedback is None or p.user_feedback >= 0.6)
            )
            success_rate = successful / len(mode_patterns)

            performance[mode] = {
                "count": len(mode_patterns),
                "avg_time": avg_time,
                "avg_confidence": avg_confidence,
                "success_rate": success_rate,
                "patterns": mode_patterns,
            }

        return performance

    def _calculate_mode_score(self, performance: Dict[str, Any]) -> float:
        """
        Calculate overall score for a mode's performance.

        Args:
            performance: Performance metrics dict

        Returns:
            float: Overall score
        """
        # Weighted scoring
        score = (
            performance["success_rate"] * 0.5
            + performance["avg_confidence"] * 0.3
            + min(1.0, 1.0 / (performance["avg_time"] / 5.0)) * 0.2
        )

        return score

    def _calculate_recommendation_confidence(
        self,
        similar_patterns: List[PatternEntry],
        best_performance: Dict[str, Any],
        all_performance: Dict[QueryMode, Dict[str, Any]],
    ) -> float:
        """
        Calculate confidence in the recommendation.

        Args:
            similar_patterns: All similar patterns found
            best_performance: Performance of recommended mode
            all_performance: Performance of all modes

        Returns:
            float: Confidence score (0-1)
        """
        # Base confidence from sample size
        sample_confidence = min(1.0, len(similar_patterns) / 10.0)

        # Confidence from success rate
        success_confidence = best_performance["success_rate"]

        # Confidence from mode dominance
        best_count = best_performance["count"]
        total_count = sum(p["count"] for p in all_performance.values())
        dominance = best_count / total_count if total_count > 0 else 0.0

        # Confidence from similarity scores
        avg_similarity = sum(p.similarity_score for p in similar_patterns) / len(
            similar_patterns
        )

        # Weighted combination
        confidence = (
            sample_confidence * 0.25
            + success_confidence * 0.35
            + dominance * 0.20
            + avg_similarity * 0.20
        )

        return max(0.0, min(1.0, confidence))

    def _generate_reasoning(
        self,
        best_mode: QueryMode,
        performance: Dict[str, Any],
        similar_count: int,
        current_complexity: Optional[QueryComplexity],
    ) -> str:
        """Generate human-readable reasoning for recommendation."""
        reasoning_parts = [
            f"Based on {similar_count} similar queries",
            f"{best_mode.value} mode achieved {performance['success_rate']:.1%} success rate",
            f"with average processing time of {performance['avg_time']:.2f}s",
        ]

        if current_complexity:
            reasoning_parts.append(f"(current complexity: {current_complexity.value})")

        return ", ".join(reasoning_parts)

    async def analyze_patterns(self, time_window_hours: int = 24) -> PatternAnalysis:
        """
        Analyze patterns for threshold tuning.

        Args:
            time_window_hours: Time window for analysis

        Returns:
            PatternAnalysis with insights
        """
        try:
            # Get all recent patterns
            patterns = await self.memory.get_relevant_patterns(
                pattern_type=self.PATTERN_TYPE, limit=1000
            )

            if not patterns:
                return PatternAnalysis(
                    total_patterns=0,
                    mode_distribution={},
                    avg_latency_by_mode={},
                    avg_confidence_by_mode={},
                    success_rate_by_mode={},
                    misclassified_patterns=[],
                )

            # Convert to PatternEntry objects
            pattern_entries = []
            for pattern in patterns:
                try:
                    data = pattern.get("data", "{}")
                    if isinstance(data, str):
                        import json

                        data = json.loads(data) if data.startswith("{") else {}

                    complexity_str = data.get("complexity", "MEDIUM")
                    mode_str = data.get("mode_used", "BALANCED")

                    complexity = (
                        QueryComplexity(complexity_str)
                        if complexity_str in [c.value for c in QueryComplexity]
                        else QueryComplexity.MEDIUM
                    )
                    mode = (
                        QueryMode(mode_str)
                        if mode_str in [m.value for m in QueryMode]
                        else QueryMode.BALANCED
                    )

                    timestamp_str = data.get("timestamp", datetime.now().isoformat())
                    timestamp = (
                        datetime.fromisoformat(timestamp_str)
                        if isinstance(timestamp_str, str)
                        else datetime.now()
                    )

                    entry = PatternEntry(
                        id=pattern.get("id", ""),
                        query_hash=data.get("query_hash", ""),
                        query_embedding=[],
                        complexity=complexity,
                        mode_used=mode,
                        processing_time=float(data.get("processing_time", 0.0)),
                        confidence_score=float(data.get("confidence_score", 0.0)),
                        user_feedback=data.get("user_feedback"),
                        timestamp=timestamp,
                        metadata=data.get("metadata", {}),
                    )

                    pattern_entries.append(entry)

                except Exception as e:
                    logger.warning(f"Failed to parse pattern for analysis: {e}")
                    continue

            # Analyze by mode
            mode_performance = self._analyze_mode_performance(pattern_entries)

            # Calculate distributions
            total = len(pattern_entries)
            mode_distribution = {
                mode.value: perf["count"] / total
                for mode, perf in mode_performance.items()
            }

            avg_latency_by_mode = {
                mode.value: perf["avg_time"] for mode, perf in mode_performance.items()
            }

            avg_confidence_by_mode = {
                mode.value: perf["avg_confidence"]
                for mode, perf in mode_performance.items()
            }

            success_rate_by_mode = {
                mode.value: perf["success_rate"]
                for mode, perf in mode_performance.items()
            }

            # Identify misclassified patterns
            misclassified = self._identify_misclassified(pattern_entries)

            analysis = PatternAnalysis(
                total_patterns=total,
                mode_distribution=mode_distribution,
                avg_latency_by_mode=avg_latency_by_mode,
                avg_confidence_by_mode=avg_confidence_by_mode,
                success_rate_by_mode=success_rate_by_mode,
                misclassified_patterns=misclassified,
            )

            logger.info(
                f"Pattern analysis complete: {total} patterns, "
                f"distribution={mode_distribution}"
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze patterns: {e}")
            return PatternAnalysis(
                total_patterns=0,
                mode_distribution={},
                avg_latency_by_mode={},
                avg_confidence_by_mode={},
                success_rate_by_mode={},
                misclassified_patterns=[],
            )

    def _identify_misclassified(
        self, patterns: List[PatternEntry]
    ) -> List[Dict[str, Any]]:
        """
        Identify potentially misclassified patterns.

        A pattern is considered misclassified if:
        - FAST mode took too long or had low confidence
        - DEEP mode was too fast (could have used BALANCED)
        - Low user feedback despite high confidence
        """
        misclassified = []

        for pattern in patterns:
            issues = []

            # Check FAST mode issues
            if pattern.mode_used == QueryMode.FAST:
                if pattern.processing_time > self.MAX_PROCESSING_TIME_FAST:
                    issues.append(
                        f"Exceeded FAST timeout: {pattern.processing_time:.2f}s"
                    )
                if pattern.confidence_score < 0.6:
                    issues.append(f"Low confidence: {pattern.confidence_score:.2f}")

            # Check DEEP mode efficiency
            elif pattern.mode_used == QueryMode.DEEP:
                if pattern.processing_time < 3.0 and pattern.confidence_score > 0.8:
                    issues.append("Could have used BALANCED mode")

            # Check user feedback mismatch
            if pattern.user_feedback is not None:
                if pattern.confidence_score > 0.8 and pattern.user_feedback < 0.5:
                    issues.append("High confidence but low user feedback")
                elif pattern.confidence_score < 0.5 and pattern.user_feedback > 0.8:
                    issues.append("Low confidence but high user feedback")

            if issues:
                misclassified.append(
                    {
                        "id": pattern.id,
                        "complexity": pattern.complexity.value,
                        "mode_used": pattern.mode_used.value,
                        "processing_time": pattern.processing_time,
                        "confidence_score": pattern.confidence_score,
                        "user_feedback": pattern.user_feedback,
                        "issues": issues,
                    }
                )

        return misclassified[:20]  # Return top 20

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about pattern learning."""
        return {
            "cache_size": len(self.pattern_cache),
            "cache_capacity": self.cache_size,
            "min_samples": self.min_samples,
            "similarity_threshold": self.similarity_threshold,
            "pattern_type": self.PATTERN_TYPE,
        }

    def __repr__(self) -> str:
        return (
            f"QueryPatternLearner(min_samples={self.min_samples}, "
            f"similarity_threshold={self.similarity_threshold})"
        )


# Singleton instance
_pattern_learner: Optional[QueryPatternLearner] = None


def get_pattern_learner(
    memory_manager: MemoryManager, confidence_service: ConfidenceService
) -> QueryPatternLearner:
    """Get or create singleton pattern learner."""
    global _pattern_learner
    if _pattern_learner is None:
        _pattern_learner = QueryPatternLearner(
            memory_manager=memory_manager, confidence_service=confidence_service
        )
    return _pattern_learner
