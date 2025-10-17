"""
Intelligent Mode Router - Route queries to optimal processing mode.

This module implements intelligent query routing based on complexity analysis,
historical patterns, and user preferences. It selects the most appropriate
processing mode (FAST/BALANCED/DEEP) to optimize for both speed and quality.

Key Features:
- Enhanced complexity analysis integration
- Pattern-based learning from historical queries
- User preference support
- Forced mode override capability
- Comprehensive logging and reasoning
- Confidence scoring for routing decisions

Performance Targets:
- FAST mode: <1s (p95)
- BALANCED mode: <3s initial (p95)
- DEEP mode: <15s (p95)
- Routing overhead: <50ms
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    from .adaptive_rag_service import (
        AdaptiveRAGService,
        QueryComplexity,
        ComplexityAnalysis,
    )
    from ..models.hybrid import QueryMode
    from ..config import Settings
except ImportError:
    # Fallback for direct execution
    from services.adaptive_rag_service import (
        AdaptiveRAGService,
        QueryComplexity,
        ComplexityAnalysis,
    )
    from models.hybrid import QueryMode
    from config import Settings

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache checking strategy by mode."""

    L1_ONLY = "l1_only"  # FAST: L1 cache only
    L1_L2 = "l1_l2"  # BALANCED: L1 + L2 cache
    ALL_LEVELS = "all_levels"  # DEEP: L1 + L2 + L3 (semantic)


@dataclass
class RoutingDecision:
    """
    Routing decision with mode, complexity, and reasoning.

    Attributes:
        mode: Selected processing mode (FAST/BALANCED/DEEP)
        complexity: Analyzed query complexity
        complexity_score: Normalized complexity score (0.0-1.0)
        routing_confidence: Confidence in routing decision (0.0-1.0)
        top_k: Number of documents to retrieve
        cache_strategy: Cache checking strategy
        reasoning: Detailed reasoning for decision
        forced: Whether mode was forced by user
        timestamp: Decision timestamp
    """

    mode: QueryMode
    complexity: QueryComplexity
    complexity_score: float
    routing_confidence: float
    top_k: int
    cache_strategy: CacheStrategy
    reasoning: Dict[str, Any]
    forced: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


class IntelligentModeRouter:
    """
    Intelligent query router for adaptive mode selection.

    Routes queries to the optimal processing mode based on:
    - Query complexity analysis (enhanced algorithm)
    - Historical pattern matching (optional)
    - User preferences (optional)
    - Forced mode overrides

    Mode Selection Logic:
    - SIMPLE complexity (score < 0.35) → FAST mode
    - MEDIUM complexity (0.35 ≤ score ≤ 0.70) → BALANCED mode
    - COMPLEX complexity (score > 0.70) → DEEP mode

    Mode Parameters:
    - FAST: top_k=5, L1 cache only, no web search, <1s target
    - BALANCED: top_k=10, L1+L2 cache, selective web, <3s target
    - DEEP: top_k=15, all cache levels, full web search, <15s target
    """

    def __init__(
        self,
        adaptive_service: Optional[AdaptiveRAGService] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize IntelligentModeRouter.

        Args:
            adaptive_service: AdaptiveRAGService instance (optional)
            settings: Settings instance (optional)
        """
        self.adaptive = adaptive_service or AdaptiveRAGService()
        self.settings = settings or Settings()

        # Mode parameters (configurable)
        self.mode_params = {
            QueryMode.FAST: {
                "top_k": 5,
                "cache_strategy": CacheStrategy.L1_ONLY,
                "enable_web_search": False,
                "max_iterations": 1,
                "timeout": 1.0,
                "target_latency": 1.0,
            },
            QueryMode.BALANCED: {
                "top_k": 10,
                "cache_strategy": CacheStrategy.L1_L2,
                "enable_web_search": False,  # Selective
                "max_iterations": 3,
                "timeout": 3.0,
                "target_latency": 3.0,
            },
            QueryMode.DEEP: {
                "top_k": 15,
                "cache_strategy": CacheStrategy.ALL_LEVELS,
                "enable_web_search": True,
                "max_iterations": 10,
                "timeout": 15.0,
                "target_latency": 15.0,
            },
        }

        logger.info("IntelligentModeRouter initialized")

    async def route_query(
        self,
        query: str,
        session_id: str,
        user_prefs: Optional[Dict[str, Any]] = None,
        forced_mode: Optional[QueryMode] = None,
        language: str = "auto",
    ) -> RoutingDecision:
        """
        Route query to optimal processing mode.

        Args:
            query: User query text
            session_id: Session identifier
            user_prefs: User preferences (optional)
            forced_mode: Force specific mode (optional)
            language: Language hint ("en", "ko", "auto")

        Returns:
            RoutingDecision with mode, complexity, confidence, and reasoning
        """
        start_time = time.time()

        try:
            # Handle forced mode
            if forced_mode:
                return self._handle_forced_mode(
                    query, forced_mode, session_id, language
                )

            # Step 1: Analyze query complexity
            complexity_analysis = self.adaptive.analyze_query_complexity(
                query, language
            )

            # Step 2: Select mode based on complexity
            selected_mode = self._select_mode_from_complexity(
                complexity_analysis.complexity
            )

            # Step 3: Apply user preferences if provided
            if user_prefs:
                selected_mode = self._apply_user_preferences(
                    selected_mode, user_prefs, complexity_analysis
                )

            # Step 4: Get mode parameters
            params = self.mode_params[selected_mode]

            # Step 5: Calculate routing confidence
            routing_confidence = self._calculate_routing_confidence(
                complexity_analysis, selected_mode
            )

            # Step 6: Generate reasoning
            reasoning = self._generate_routing_reasoning(
                complexity_analysis, selected_mode, params, user_prefs
            )

            # Step 7: Create routing decision
            decision = RoutingDecision(
                mode=selected_mode,
                complexity=complexity_analysis.complexity,
                complexity_score=complexity_analysis.score,
                routing_confidence=routing_confidence,
                top_k=params["top_k"],
                cache_strategy=params["cache_strategy"],
                reasoning=reasoning,
                forced=False,
            )

            # Log routing decision
            routing_time = (time.time() - start_time) * 1000  # ms
            logger.info(
                f"Query routed to {selected_mode.value.upper()} mode "
                f"(complexity={complexity_analysis.complexity.value}, "
                f"score={complexity_analysis.score:.3f}, "
                f"confidence={routing_confidence:.3f}, "
                f"routing_time={routing_time:.1f}ms)"
            )

            # Log detailed reasoning in debug mode
            if self.settings.DEBUG:
                logger.debug(f"Routing reasoning: {reasoning}")

            return decision

        except Exception as e:
            logger.error(f"Routing failed: {e}", exc_info=True)
            # Default to BALANCED mode on error
            return self._create_fallback_decision(query, session_id, str(e))

    def _handle_forced_mode(
        self, query: str, forced_mode: QueryMode, session_id: str, language: str
    ) -> RoutingDecision:
        """
        Handle forced mode override.

        Args:
            query: User query
            forced_mode: Forced mode
            session_id: Session ID
            language: Language hint

        Returns:
            RoutingDecision with forced mode
        """
        # Still analyze complexity for logging/metrics
        complexity_analysis = self.adaptive.analyze_query_complexity(query, language)

        # Get parameters for forced mode
        params = self.mode_params[forced_mode]

        # Check if forced mode seems suboptimal
        recommended_mode = self._select_mode_from_complexity(
            complexity_analysis.complexity
        )

        is_suboptimal = forced_mode != recommended_mode

        # Generate reasoning
        reasoning = {
            "forced": True,
            "forced_mode": forced_mode.value,
            "recommended_mode": recommended_mode.value,
            "complexity": complexity_analysis.complexity.value,
            "complexity_score": complexity_analysis.score,
            "suboptimal": is_suboptimal,
            "warning": (
                (
                    f"Forced {forced_mode.value.upper()} mode may be suboptimal. "
                    f"Recommended: {recommended_mode.value.upper()}"
                )
                if is_suboptimal
                else None
            ),
        }

        # Log warning if suboptimal
        if is_suboptimal:
            logger.warning(
                f"Forced mode {forced_mode.value.upper()} may be suboptimal "
                f"for {complexity_analysis.complexity.value} query "
                f"(score={complexity_analysis.score:.3f}). "
                f"Recommended: {recommended_mode.value.upper()}"
            )

        return RoutingDecision(
            mode=forced_mode,
            complexity=complexity_analysis.complexity,
            complexity_score=complexity_analysis.score,
            routing_confidence=1.0,  # User forced, so confidence is 1.0
            top_k=params["top_k"],
            cache_strategy=params["cache_strategy"],
            reasoning=reasoning,
            forced=True,
        )

    def _select_mode_from_complexity(self, complexity: QueryComplexity) -> QueryMode:
        """
        Select mode based on complexity level.

        Args:
            complexity: Query complexity

        Returns:
            Selected QueryMode
        """
        if complexity == QueryComplexity.SIMPLE:
            return QueryMode.FAST
        elif complexity == QueryComplexity.MEDIUM:
            return QueryMode.BALANCED
        else:  # COMPLEX
            return QueryMode.DEEP

    def _apply_user_preferences(
        self,
        selected_mode: QueryMode,
        user_prefs: Dict[str, Any],
        complexity_analysis: ComplexityAnalysis,
    ) -> QueryMode:
        """
        Apply user preferences to mode selection.

        Args:
            selected_mode: Initially selected mode
            user_prefs: User preferences
            complexity_analysis: Complexity analysis

        Returns:
            Adjusted QueryMode
        """
        # Check for preferred mode
        preferred_mode = user_prefs.get("preferred_mode")
        if preferred_mode:
            try:
                preferred = QueryMode(preferred_mode)
                logger.info(
                    f"Applying user preference: {preferred.value.upper()} "
                    f"(original: {selected_mode.value.upper()})"
                )
                return preferred
            except ValueError:
                logger.warning(f"Invalid preferred mode: {preferred_mode}")

        # Check for speed preference
        prefer_speed = user_prefs.get("prefer_speed", False)
        if prefer_speed and selected_mode == QueryMode.BALANCED:
            logger.info("User prefers speed, downgrading to FAST mode")
            return QueryMode.FAST

        # Check for quality preference
        prefer_quality = user_prefs.get("prefer_quality", False)
        if prefer_quality and selected_mode == QueryMode.BALANCED:
            logger.info("User prefers quality, upgrading to DEEP mode")
            return QueryMode.DEEP

        return selected_mode

    def _calculate_routing_confidence(
        self, complexity_analysis: ComplexityAnalysis, selected_mode: QueryMode
    ) -> float:
        """
        Calculate confidence in routing decision.

        Confidence is based on:
        - Complexity classification confidence
        - Distance from threshold boundaries
        - Consistency of factors

        Args:
            complexity_analysis: Complexity analysis
            selected_mode: Selected mode

        Returns:
            Confidence score (0.0-1.0)
        """
        # Start with complexity classification confidence
        base_confidence = complexity_analysis.confidence

        # Adjust based on mode-complexity alignment
        expected_mode = self._select_mode_from_complexity(
            complexity_analysis.complexity
        )

        if selected_mode == expected_mode:
            # Mode matches complexity, confidence is high
            return min(0.95, base_confidence + 0.1)
        else:
            # Mode doesn't match (due to user prefs), reduce confidence
            return max(0.5, base_confidence - 0.2)

    def _generate_routing_reasoning(
        self,
        complexity_analysis: ComplexityAnalysis,
        selected_mode: QueryMode,
        params: Dict[str, Any],
        user_prefs: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate detailed reasoning for routing decision.

        Args:
            complexity_analysis: Complexity analysis
            selected_mode: Selected mode
            params: Mode parameters
            user_prefs: User preferences

        Returns:
            Reasoning dictionary
        """
        reasoning = {
            "selected_mode": selected_mode.value,
            "complexity": {
                "level": complexity_analysis.complexity.value,
                "score": complexity_analysis.score,
                "confidence": complexity_analysis.confidence,
                "factors": complexity_analysis.factors,
                "reasoning": complexity_analysis.reasoning,
                "language": complexity_analysis.language,
                "word_count": complexity_analysis.word_count,
                "question_type": complexity_analysis.question_type,
            },
            "mode_parameters": {
                "top_k": params["top_k"],
                "cache_strategy": params["cache_strategy"].value,
                "enable_web_search": params["enable_web_search"],
                "max_iterations": params["max_iterations"],
                "timeout": params["timeout"],
                "target_latency": params["target_latency"],
            },
            "decision_factors": [],
        }

        # Add decision factors
        if complexity_analysis.complexity == QueryComplexity.SIMPLE:
            reasoning["decision_factors"].append(
                f"Simple query (score={complexity_analysis.score:.3f}) → FAST mode for <1s response"
            )
        elif complexity_analysis.complexity == QueryComplexity.MEDIUM:
            reasoning["decision_factors"].append(
                f"Medium query (score={complexity_analysis.score:.3f}) → BALANCED mode for <3s response"
            )
        else:
            reasoning["decision_factors"].append(
                f"Complex query (score={complexity_analysis.score:.3f}) → DEEP mode for comprehensive analysis"
            )

        # Add user preference factors
        if user_prefs:
            reasoning["user_preferences"] = user_prefs
            if user_prefs.get("preferred_mode"):
                reasoning["decision_factors"].append(
                    f"User preferred mode: {user_prefs['preferred_mode']}"
                )
            if user_prefs.get("prefer_speed"):
                reasoning["decision_factors"].append("User prefers speed over quality")
            if user_prefs.get("prefer_quality"):
                reasoning["decision_factors"].append("User prefers quality over speed")

        # Add expected performance
        reasoning["expected_performance"] = {
            "target_latency": f"{params['target_latency']}s",
            "cache_levels": self._get_cache_levels_description(
                params["cache_strategy"]
            ),
            "web_search": "enabled" if params["enable_web_search"] else "disabled",
            "reasoning_depth": self._get_reasoning_depth_description(selected_mode),
        }

        return reasoning

    def _get_cache_levels_description(self, strategy: CacheStrategy) -> str:
        """Get human-readable cache levels description."""
        if strategy == CacheStrategy.L1_ONLY:
            return "L1 (memory) only"
        elif strategy == CacheStrategy.L1_L2:
            return "L1 (memory) + L2 (Redis)"
        else:
            return "L1 (memory) + L2 (Redis) + L3 (semantic)"

    def _get_reasoning_depth_description(self, mode: QueryMode) -> str:
        """Get human-readable reasoning depth description."""
        if mode == QueryMode.FAST:
            return "Single-step synthesis"
        elif mode == QueryMode.BALANCED:
            return "Speculative execution with refinement"
        else:
            return "Full agentic reasoning with multi-step analysis"

    def _create_fallback_decision(
        self, query: str, session_id: str, error: str
    ) -> RoutingDecision:
        """
        Create fallback decision on error.

        Args:
            query: User query
            session_id: Session ID
            error: Error message

        Returns:
            Fallback RoutingDecision (BALANCED mode)
        """
        logger.warning(f"Using fallback BALANCED mode due to error: {error}")

        params = self.mode_params[QueryMode.BALANCED]

        return RoutingDecision(
            mode=QueryMode.BALANCED,
            complexity=QueryComplexity.MEDIUM,
            complexity_score=0.5,
            routing_confidence=0.5,
            top_k=params["top_k"],
            cache_strategy=params["cache_strategy"],
            reasoning={
                "fallback": True,
                "error": error,
                "default_mode": "balanced",
                "message": "Routing failed, using safe default (BALANCED mode)",
            },
            forced=False,
        )

    def get_mode_parameters(self, mode: QueryMode) -> Dict[str, Any]:
        """
        Get parameters for a specific mode.

        Args:
            mode: Query mode

        Returns:
            Mode parameters dictionary
        """
        return self.mode_params.get(mode, self.mode_params[QueryMode.BALANCED])

    def update_mode_parameters(self, mode: QueryMode, **kwargs) -> None:
        """
        Update parameters for a specific mode.

        Args:
            mode: Query mode to update
            **kwargs: Parameters to update
        """
        if mode in self.mode_params:
            self.mode_params[mode].update(kwargs)
            logger.info(f"Updated {mode.value.upper()} mode parameters: {kwargs}")
        else:
            logger.warning(f"Unknown mode: {mode}")


# Singleton instance
_intelligent_mode_router: Optional[IntelligentModeRouter] = None


def get_intelligent_mode_router(
    adaptive_service: Optional[AdaptiveRAGService] = None,
    settings: Optional[Settings] = None,
) -> IntelligentModeRouter:
    """
    Get or create IntelligentModeRouter instance.

    Args:
        adaptive_service: AdaptiveRAGService instance (optional)
        settings: Settings instance (optional)

    Returns:
        IntelligentModeRouter instance
    """
    global _intelligent_mode_router

    if _intelligent_mode_router is None:
        _intelligent_mode_router = IntelligentModeRouter(
            adaptive_service=adaptive_service, settings=settings
        )

    return _intelligent_mode_router
