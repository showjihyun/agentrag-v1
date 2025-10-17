# Adaptive RAG: Dynamic Strategy Selection
import logging
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class RAGStrategy(Enum):
    """Available RAG strategies"""

    DIRECT = "direct"  # Simple vector search + generation
    HYBRID = "hybrid"  # Vector + BM25 search
    SELF_REFLECTIVE = "self_reflective"  # Self-RAG with reflection
    CORRECTIVE = "corrective"  # Corrective RAG with fallbacks
    MULTI_HOP = "multi_hop"  # Multi-hop reasoning


@dataclass
class StrategySelection:
    """Selected strategy with reasoning"""

    strategy: RAGStrategy
    confidence: float
    reasoning: str
    parameters: Dict[str, Any]


@dataclass
class AdaptiveRAGResult:
    """Result from Adaptive RAG"""

    response: str
    strategy_used: RAGStrategy
    selection_reasoning: str
    execution_time_ms: float
    confidence: float
    sources: List[Dict[str, str]]


class AdaptiveRAG:
    """
    Adaptive RAG with dynamic strategy selection.

    Automatically selects the best RAG strategy based on:
    1. Query complexity
    2. Query type (factual, analytical, etc.)
    3. Available resources
    4. Performance requirements
    5. Historical performance data
    """

    def __init__(self, llm_manager, query_analyzer, performance_tracker=None):
        """
        Initialize Adaptive RAG.

        Args:
            llm_manager: LLM manager for generation
            query_analyzer: Query analyzer service
            performance_tracker: Optional performance tracking service
        """
        self.llm_manager = llm_manager
        self.query_analyzer = query_analyzer
        self.performance_tracker = performance_tracker

        # Strategy performance history
        self.strategy_performance: Dict[RAGStrategy, List[float]] = {
            strategy: [] for strategy in RAGStrategy
        }

    def analyze_query_complexity(self, query: str) -> QueryComplexity:
        """
        Analyze query complexity.

        Args:
            query: User query

        Returns:
            QueryComplexity level
        """
        analysis = self.query_analyzer.analyze(query)

        if analysis.complexity_score < 0.35:
            return QueryComplexity.SIMPLE
        elif analysis.complexity_score < 0.70:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.COMPLEX

    async def select_strategy(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> StrategySelection:
        """
        Select optimal RAG strategy for query.

        Args:
            query: User query
            context: Optional context (user preferences, constraints, etc.)

        Returns:
            StrategySelection with chosen strategy and parameters
        """
        # Analyze query
        analysis = self.query_analyzer.analyze(query)
        complexity = self.analyze_query_complexity(query)

        logger.info(
            f"Query analysis: complexity={complexity.value}, "
            f"type={analysis.query_type}, "
            f"requires_reasoning={analysis.requires_reasoning}"
        )

        # Default parameters
        parameters = {"top_k": 10, "temperature": 0.7, "max_tokens": 500}

        # Strategy selection logic
        if complexity == QueryComplexity.SIMPLE:
            # Simple queries: Direct retrieval
            if analysis.query_type == "factual":
                strategy = RAGStrategy.DIRECT
                reasoning = "Simple factual query - direct retrieval sufficient"
                parameters["top_k"] = 5
            else:
                strategy = RAGStrategy.HYBRID
                reasoning = "Simple query - hybrid search for better coverage"
                parameters["top_k"] = 7

        elif complexity == QueryComplexity.MODERATE:
            # Moderate queries: Hybrid or Self-Reflective
            if analysis.requires_reasoning:
                strategy = RAGStrategy.SELF_REFLECTIVE
                reasoning = (
                    "Moderate complexity with reasoning - self-reflection needed"
                )
                parameters["top_k"] = 10
                parameters["max_iterations"] = 2
            else:
                strategy = RAGStrategy.HYBRID
                reasoning = "Moderate complexity - hybrid search recommended"
                parameters["top_k"] = 10

        else:  # COMPLEX
            # Complex queries: Self-Reflective or Corrective
            if analysis.requires_multiple_sources:
                strategy = RAGStrategy.CORRECTIVE
                reasoning = "Complex query needing multiple sources - corrective RAG"
                parameters["top_k"] = 15
                parameters["enable_web_search"] = True
            elif analysis.query_type == "multi-step":
                strategy = RAGStrategy.MULTI_HOP
                reasoning = "Multi-step query - multi-hop reasoning required"
                parameters["top_k"] = 12
                parameters["max_hops"] = 3
            else:
                strategy = RAGStrategy.SELF_REFLECTIVE
                reasoning = "Complex query - self-reflective approach"
                parameters["top_k"] = 12
                parameters["max_iterations"] = 3

        # Consider historical performance
        if self.performance_tracker:
            avg_performance = self._get_average_performance(strategy)
            if avg_performance < 0.6:
                # Strategy has been performing poorly, try alternative
                logger.warning(
                    f"Strategy {strategy.value} has low performance "
                    f"({avg_performance:.2f}), considering alternative"
                )
                # Fallback to hybrid for safety
                strategy = RAGStrategy.HYBRID
                reasoning += " (adjusted based on performance history)"

        # Apply context constraints if provided
        if context:
            if context.get("fast_mode"):
                # User wants fast response
                if strategy in [RAGStrategy.SELF_REFLECTIVE, RAGStrategy.CORRECTIVE]:
                    strategy = RAGStrategy.HYBRID
                    reasoning += " (optimized for speed)"
                    parameters["top_k"] = min(parameters["top_k"], 7)

            if context.get("high_accuracy"):
                # User wants high accuracy
                if strategy == RAGStrategy.DIRECT:
                    strategy = RAGStrategy.SELF_REFLECTIVE
                    reasoning += " (optimized for accuracy)"
                    parameters["max_iterations"] = 3

        confidence = 0.8  # Base confidence

        return StrategySelection(
            strategy=strategy,
            confidence=confidence,
            reasoning=reasoning,
            parameters=parameters,
        )

    async def execute_strategy(
        self,
        strategy: RAGStrategy,
        query: str,
        parameters: Dict[str, Any],
        retrieve_fn: Callable,
        generate_fn: Callable,
    ) -> Tuple[str, List[Dict[str, str]], float]:
        """
        Execute selected RAG strategy.

        Args:
            strategy: Selected RAG strategy
            query: User query
            parameters: Strategy parameters
            retrieve_fn: Document retrieval function
            generate_fn: Response generation function

        Returns:
            Tuple of (response, sources, confidence)
        """
        import time

        start_time = time.time()

        try:
            if strategy == RAGStrategy.DIRECT:
                # Direct retrieval + generation
                documents = await retrieve_fn(query, parameters.get("top_k", 5))
                response = await generate_fn(query, documents)
                confidence = 0.7

            elif strategy == RAGStrategy.HYBRID:
                # Hybrid search (implemented separately)
                documents = await retrieve_fn(query, parameters.get("top_k", 10))
                response = await generate_fn(query, documents)
                confidence = 0.75

            elif strategy == RAGStrategy.SELF_REFLECTIVE:
                # Self-RAG with reflection
                from backend.services.self_rag import get_self_rag

                self_rag = get_self_rag(self.llm_manager)
                result = await self_rag.generate_with_reflection(
                    query=query,
                    retrieve_fn=retrieve_fn,
                    generate_fn=generate_fn,
                    initial_top_k=parameters.get("top_k", 10),
                )

                response = result.response
                documents = []  # Documents are handled internally
                confidence = result.final_confidence

            elif strategy == RAGStrategy.CORRECTIVE:
                # Corrective RAG with fallbacks
                from backend.services.corrective_rag import get_corrective_rag

                corrective_rag = get_corrective_rag(self.llm_manager)
                result = await corrective_rag.generate_with_correction(
                    query=query,
                    retrieve_fn=retrieve_fn,
                    generate_fn=generate_fn,
                    top_k=parameters.get("top_k", 15),
                )

                response = result.response
                documents = result.sources
                confidence = result.final_confidence

            else:  # MULTI_HOP
                # Multi-hop reasoning (simplified)
                documents = await retrieve_fn(query, parameters.get("top_k", 12))
                response = await generate_fn(query, documents)
                confidence = 0.72

            execution_time = (time.time() - start_time) * 1000

            # Track performance
            self._record_performance(strategy, confidence)

            logger.info(
                f"Strategy {strategy.value} executed in {execution_time:.2f}ms, "
                f"confidence: {confidence:.2f}"
            )

            return response, documents, confidence

        except Exception as e:
            logger.error(f"Error executing strategy {strategy.value}: {e}")
            # Fallback to direct strategy
            documents = await retrieve_fn(query, 5)
            response = await generate_fn(query, documents)
            return response, documents, 0.5

    async def generate(
        self,
        query: str,
        retrieve_fn: Callable,
        generate_fn: Callable,
        context: Optional[Dict[str, Any]] = None,
    ) -> AdaptiveRAGResult:
        """
        Generate response with adaptive strategy selection.

        Args:
            query: User query
            retrieve_fn: Document retrieval function
            generate_fn: Response generation function
            context: Optional context for strategy selection

        Returns:
            AdaptiveRAGResult with response and metadata
        """
        import time

        start_time = time.time()

        # Select strategy
        selection = await self.select_strategy(query, context)

        logger.info(
            f"Selected strategy: {selection.strategy.value} "
            f"(confidence: {selection.confidence:.2f})"
        )
        logger.info(f"Reasoning: {selection.reasoning}")

        # Execute strategy
        response, sources, confidence = await self.execute_strategy(
            strategy=selection.strategy,
            query=query,
            parameters=selection.parameters,
            retrieve_fn=retrieve_fn,
            generate_fn=generate_fn,
        )

        execution_time = (time.time() - start_time) * 1000

        return AdaptiveRAGResult(
            response=response,
            strategy_used=selection.strategy,
            selection_reasoning=selection.reasoning,
            execution_time_ms=execution_time,
            confidence=confidence,
            sources=sources,
        )

    def _get_average_performance(self, strategy: RAGStrategy) -> float:
        """Get average performance for strategy"""
        performances = self.strategy_performance.get(strategy, [])
        if not performances:
            return 0.7  # Default
        return sum(performances) / len(performances)

    def _record_performance(self, strategy: RAGStrategy, confidence: float):
        """Record strategy performance"""
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = []

        self.strategy_performance[strategy].append(confidence)

        # Keep only recent performances (last 100)
        if len(self.strategy_performance[strategy]) > 100:
            self.strategy_performance[strategy] = self.strategy_performance[strategy][
                -100:
            ]


# Global Adaptive RAG instance
_adaptive_rag: Optional[AdaptiveRAG] = None


def get_adaptive_rag(llm_manager, query_analyzer) -> AdaptiveRAG:
    """Get global Adaptive RAG instance"""
    global _adaptive_rag
    if _adaptive_rag is None:
        _adaptive_rag = AdaptiveRAG(llm_manager, query_analyzer)
    return _adaptive_rag
