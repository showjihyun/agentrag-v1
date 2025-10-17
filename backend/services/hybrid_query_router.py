"""
Hybrid Query Router for coordinating speculative and agentic paths.

This router manages query processing across different modes (FAST, BALANCED, DEEP),
coordinates parallel execution, and handles resource sharing between paths.
"""

import logging
import uuid
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any, List
from datetime import datetime

from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.response_coordinator import ResponseCoordinator
from backend.agents.aggregator import AggregatorAgent
from backend.models.hybrid import (
    QueryMode,
    ResponseChunk,
    ResponseType,
    PathSource,
    SpeculativeResponse,
    HybridQueryResponse,
)
from backend.models.agent import AgentStep

logger = logging.getLogger(__name__)


class HybridQueryRouter:
    """
    Routes queries to speculative, agentic, or both paths based on mode.

    Features:
    - FAST mode: Speculative path only for quick responses
    - DEEP mode: Agentic path only for comprehensive analysis
    - BALANCED mode: Parallel execution with progressive refinement
    - Resource sharing between paths to avoid redundant work
    - Timeout handling and graceful degradation

    Requirements: 1.1, 1.4, 4.1, 4.2, 4.3, 6.2, 6.3, 6.4, 6.5
    """

    def __init__(
        self,
        speculative_processor: SpeculativeProcessor,
        agentic_processor: AggregatorAgent,
        response_coordinator: ResponseCoordinator,
        default_speculative_timeout: float = 5.0,  # Increased from 2.0 for Korean LLM processing
        default_agentic_timeout: float = 30.0,  # Increased from 15.0 for complex queries
    ):
        """
        Initialize HybridQueryRouter.

        Args:
            speculative_processor: Processor for fast speculative responses
            agentic_processor: Aggregator agent for deep reasoning
            response_coordinator: Coordinator for merging results
            default_speculative_timeout: Default timeout for speculative path (seconds)
            default_agentic_timeout: Default timeout for agentic path (seconds)
        """
        self.speculative = speculative_processor
        self.agentic = agentic_processor
        self.coordinator = response_coordinator
        self.default_speculative_timeout = default_speculative_timeout
        self.default_agentic_timeout = default_agentic_timeout

        logger.info(
            f"HybridQueryRouter initialized with "
            f"speculative_timeout={default_speculative_timeout}s, "
            f"agentic_timeout={default_agentic_timeout}s"
        )

    async def process_query(
        self,
        query: str,
        mode: QueryMode,
        session_id: Optional[str] = None,
        top_k: int = 10,
        enable_cache: bool = True,
        speculative_timeout: Optional[float] = None,
        agentic_timeout: Optional[float] = None,
    ) -> AsyncGenerator[ResponseChunk, None]:
        """
        Process query based on selected mode.

        Args:
            query: User query text
            mode: Query processing mode (FAST, BALANCED, DEEP)
            session_id: Session identifier for context
            top_k: Number of documents to retrieve
            enable_cache: Whether to use speculative caching
            speculative_timeout: Timeout for speculative path (uses default if None)
            agentic_timeout: Timeout for agentic path (uses default if None)

        Yields:
            ResponseChunk: Streaming response chunks

        Requirements: 1.1, 6.2, 6.3, 6.4, 6.5
        """
        # Generate query ID
        query_id = f"query_{uuid.uuid4().hex[:12]}"

        # Use default timeouts if not specified
        spec_timeout = speculative_timeout or self.default_speculative_timeout
        agent_timeout = agentic_timeout or self.default_agentic_timeout

        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        logger.info(
            f"Processing query {query_id} in {mode.value.upper()} mode "
            f"(session={session_id})"
        )

        try:
            # Route based on mode
            if mode == QueryMode.FAST:
                # Speculative only
                async for chunk in self._process_fast_mode(
                    query_id=query_id,
                    query=query,
                    session_id=session_id,
                    top_k=top_k,
                    enable_cache=enable_cache,
                    timeout=spec_timeout,
                ):
                    yield chunk

            elif mode == QueryMode.DEEP:
                # Agentic only
                async for chunk in self._process_deep_mode(
                    query_id=query_id,
                    query=query,
                    session_id=session_id,
                    top_k=top_k,
                    timeout=agent_timeout,
                ):
                    yield chunk

            elif mode == QueryMode.BALANCED:
                # Both paths in parallel
                async for chunk in self._process_balanced_mode(
                    query_id=query_id,
                    query=query,
                    session_id=session_id,
                    top_k=top_k,
                    enable_cache=enable_cache,
                    speculative_timeout=spec_timeout,
                    agentic_timeout=agent_timeout,
                ):
                    yield chunk

            else:
                raise ValueError(f"Unknown query mode: {mode}")

        except Exception as e:
            logger.error(f"Error processing query {query_id}: {e}")

            # Yield error chunk
            yield ResponseChunk(
                chunk_id=f"{query_id}_error",
                type=ResponseType.FINAL,
                content=f"An error occurred while processing your query: {str(e)}",
                path_source=PathSource.HYBRID,
                confidence_score=0.0,
                sources=[],
                reasoning_steps=[],
                timestamp=datetime.now(),
                metadata={"error": str(e), "mode": mode.value},
            )

    async def _process_fast_mode(
        self,
        query_id: str,
        query: str,
        session_id: str,
        top_k: int,
        enable_cache: bool,
        timeout: float,
    ) -> AsyncGenerator[ResponseChunk, None]:
        """
        Process query in FAST mode (speculative only).

        Args:
            query_id: Query identifier
            query: Query text
            session_id: Session identifier
            top_k: Number of results
            enable_cache: Whether to use cache
            timeout: Timeout in seconds

        Yields:
            ResponseChunk: Response chunks

        Requirements: 6.2
        """
        logger.info(f"Processing query {query_id} in FAST mode")

        try:
            # Run speculative processor with timeout
            spec_task = self.speculative.process(
                query=query, top_k=top_k, enable_cache=enable_cache
            )

            speculative_response = await asyncio.wait_for(spec_task, timeout=timeout)

            # Create and yield final chunk
            chunk = ResponseChunk(
                chunk_id=f"{query_id}_final",
                type=ResponseType.FINAL,
                content=speculative_response.response,
                path_source=PathSource.SPECULATIVE,
                confidence_score=speculative_response.confidence_score,
                sources=speculative_response.sources,
                reasoning_steps=[],
                timestamp=datetime.now(),
                metadata={
                    "mode": "fast",
                    "cache_hit": speculative_response.cache_hit,
                    "processing_time": speculative_response.processing_time,
                    **speculative_response.metadata,
                },
            )

            yield chunk

            logger.info(
                f"FAST mode completed for query {query_id} "
                f"(time={speculative_response.processing_time:.2f}s, "
                f"confidence={speculative_response.confidence_score:.2f})"
            )

        except asyncio.TimeoutError:
            # Log timeout event for monitoring (Requirement 8.4)
            logger.warning(
                f"FAST mode timed out for query {query_id} after {timeout}s - "
                f"no results available"
            )

            # Return clear error message (Requirement 8.5)
            yield ResponseChunk(
                chunk_id=f"{query_id}_timeout",
                type=ResponseType.FINAL,
                content=(
                    "The query took longer than expected to process. "
                    "Please try again or try a different query mode."
                ),
                path_source=PathSource.SPECULATIVE,
                confidence_score=0.0,
                sources=[],
                reasoning_steps=[],
                timestamp=datetime.now(),
                metadata={
                    "error": "timeout",
                    "timeout_seconds": timeout,
                    "mode": "fast",
                },
            )

        except Exception as e:
            logger.error(f"Error in FAST mode for query {query_id}: {e}")

            yield ResponseChunk(
                chunk_id=f"{query_id}_error",
                type=ResponseType.FINAL,
                content="An error occurred while processing your query.",
                path_source=PathSource.SPECULATIVE,
                confidence_score=0.0,
                sources=[],
                reasoning_steps=[],
                timestamp=datetime.now(),
                metadata={"error": str(e)},
            )

    async def _process_deep_mode(
        self, query_id: str, query: str, session_id: str, top_k: int, timeout: float
    ) -> AsyncGenerator[ResponseChunk, None]:
        """
        Process query in DEEP mode (agentic only).

        Args:
            query_id: Query identifier
            query: Query text
            session_id: Session identifier
            top_k: Number of results
            timeout: Timeout in seconds

        Yields:
            ResponseChunk: Response chunks

        Requirements: 6.4
        """
        logger.info(f"Processing query {query_id} in DEEP mode")

        try:
            # Run agentic processor with timeout
            agentic_generator = self.agentic.process_query(
                query=query, session_id=session_id, top_k=top_k
            )

            # Collect reasoning steps and final response
            reasoning_steps = []
            final_response = None
            sources = []

            # Stream reasoning steps with timeout
            async def stream_with_timeout():
                async for step in agentic_generator:
                    reasoning_steps.append(step.model_dump())

                    # Yield intermediate chunks for reasoning steps
                    yield ResponseChunk(
                        chunk_id=f"{query_id}_step_{len(reasoning_steps)}",
                        type=ResponseType.REFINEMENT,
                        content=step.content,
                        path_source=PathSource.AGENTIC,
                        confidence_score=None,
                        sources=[],
                        reasoning_steps=[step.model_dump()],
                        timestamp=datetime.now(),
                        metadata={
                            "mode": "deep",
                            "step_type": step.type,
                            "step_id": step.step_id,
                        },
                    )

                    # Extract final response and sources
                    if step.type == "response":
                        nonlocal final_response, sources
                        final_response = step.content
                        sources = step.metadata.get("sources", [])

            # Process with timeout
            try:
                # Wrap the generator iteration with timeout
                start_time = asyncio.get_event_loop().time()
                async for chunk in stream_with_timeout():
                    # Check if we've exceeded timeout
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        raise asyncio.TimeoutError()
                    yield chunk
            except asyncio.TimeoutError:
                # Log timeout event for monitoring (Requirement 8.4)
                logger.warning(
                    f"DEEP mode timed out for query {query_id} after {timeout}s - "
                    f"returning partial results (steps={len(reasoning_steps)})"
                )
                # Return partial results (Requirement 8.5)
                final_response = (
                    "The analysis is taking longer than expected. "
                    "Partial results are shown below."
                )

            # Yield final chunk
            is_timeout = "Partial results" in (final_response or "")
            yield ResponseChunk(
                chunk_id=f"{query_id}_final",
                type=ResponseType.FINAL,
                content=final_response or "Unable to generate response.",
                path_source=PathSource.AGENTIC,
                confidence_score=(
                    0.85
                    if final_response and not is_timeout
                    else 0.5 if is_timeout else 0.0
                ),
                sources=sources,
                reasoning_steps=reasoning_steps,
                timestamp=datetime.now(),
                metadata={
                    "mode": "deep",
                    "reasoning_step_count": len(reasoning_steps),
                    "timeout": is_timeout,
                    "partial_results": is_timeout,
                },
            )

            logger.info(
                f"DEEP mode completed for query {query_id} "
                f"(steps={len(reasoning_steps)})"
            )

        except Exception as e:
            logger.error(f"Error in DEEP mode for query {query_id}: {e}")

            yield ResponseChunk(
                chunk_id=f"{query_id}_error",
                type=ResponseType.FINAL,
                content="An error occurred during deep analysis.",
                path_source=PathSource.AGENTIC,
                confidence_score=0.0,
                sources=[],
                reasoning_steps=[],
                timestamp=datetime.now(),
                metadata={"error": str(e)},
            )

    async def _process_balanced_mode(
        self,
        query_id: str,
        query: str,
        session_id: str,
        top_k: int,
        enable_cache: bool,
        speculative_timeout: float,
        agentic_timeout: float,
    ) -> AsyncGenerator[ResponseChunk, None]:
        """
        Process query in BALANCED mode (parallel execution).

        Runs both speculative and agentic paths in parallel, streaming
        preliminary results first, then refinements. Implements graceful
        degradation if either path fails.

        Args:
            query_id: Query identifier
            query: Query text
            session_id: Session identifier
            top_k: Number of results
            enable_cache: Whether to use cache
            speculative_timeout: Timeout for speculative path
            agentic_timeout: Timeout for agentic path

        Yields:
            ResponseChunk: Response chunks

        Requirements: 1.4, 1.5, 4.1, 4.2, 4.3, 6.3, 8.1, 8.2, 8.3
        """
        logger.info(f"Processing query {query_id} in BALANCED mode")

        # Start both paths concurrently with error handling
        spec_task = asyncio.create_task(
            self._collect_speculative_response(
                query=query,
                top_k=top_k,
                enable_cache=enable_cache,
                timeout=speculative_timeout,
            )
        )

        agentic_task = asyncio.create_task(
            self._collect_agentic_response(
                query=query,
                session_id=session_id,
                top_k=top_k,
                timeout=agentic_timeout,
                shared_results=None,  # Will be populated after speculative completes
            )
        )

        # Use coordinator to stream progressive results with fallback handling
        try:
            async for chunk in self._coordinate_balanced_streaming(
                query_id=query_id, spec_task=spec_task, agentic_task=agentic_task
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Error in balanced mode coordination: {e}")

            # Attempt graceful degradation - try to get results from either path
            spec_result = None
            agentic_result = None

            try:
                if not spec_task.done():
                    spec_task.cancel()
                elif not spec_task.cancelled():
                    spec_result = spec_task.result()
            except Exception as spec_error:
                logger.error(f"Failed to retrieve speculative result: {spec_error}")

            try:
                if not agentic_task.done():
                    agentic_task.cancel()
                elif not agentic_task.cancelled():
                    agentic_result = agentic_task.result()
            except Exception as agent_error:
                logger.error(f"Failed to retrieve agentic result: {agent_error}")

            # Yield whatever we can salvage
            if spec_result or agentic_result:
                content = (
                    spec_result.response
                    if spec_result
                    else agentic_result.get("response", "Partial results available.")
                )
                confidence = (
                    spec_result.confidence_score
                    if spec_result
                    else agentic_result.get("confidence", 0.5)
                )
                sources = (
                    spec_result.sources
                    if spec_result
                    else agentic_result.get("sources", [])
                )

                yield ResponseChunk(
                    chunk_id=f"{query_id}_fallback",
                    type=ResponseType.FINAL,
                    content=content,
                    path_source=(
                        PathSource.SPECULATIVE if spec_result else PathSource.AGENTIC
                    ),
                    confidence_score=confidence,
                    sources=sources,
                    reasoning_steps=[],
                    timestamp=datetime.now(),
                    metadata={
                        "error": "coordination_failed",
                        "fallback": True,
                        "original_error": str(e),
                    },
                )
            else:
                # Complete failure - yield error message
                yield ResponseChunk(
                    chunk_id=f"{query_id}_error",
                    type=ResponseType.FINAL,
                    content="Unable to process query. Please try again.",
                    path_source=PathSource.HYBRID,
                    confidence_score=0.0,
                    sources=[],
                    reasoning_steps=[],
                    timestamp=datetime.now(),
                    metadata={"error": str(e), "both_paths_failed": True},
                )

    async def _collect_speculative_response(
        self, query: str, top_k: int, enable_cache: bool, timeout: float
    ) -> Optional[SpeculativeResponse]:
        """
        Collect speculative response with timeout and error handling.

        Implements graceful degradation:
        - Returns None on timeout (logged for monitoring)
        - Returns None on any error (logged with details)
        - Allows fallback to agentic-only mode

        Args:
            query: Query text
            top_k: Number of results
            enable_cache: Whether to use cache
            timeout: Timeout in seconds

        Returns:
            SpeculativeResponse or None if failed/timeout

        Requirements: 4.2, 8.1, 8.4
        """
        try:
            spec_task = self.speculative.process(
                query=query, top_k=top_k, enable_cache=enable_cache
            )

            response = await asyncio.wait_for(spec_task, timeout=timeout)

            logger.info(
                f"Speculative path completed "
                f"(time={response.processing_time:.2f}s, "
                f"confidence={response.confidence_score:.2f})"
            )

            return response

        except asyncio.TimeoutError:
            logger.warning(
                f"Speculative path timed out after {timeout}s - "
                f"falling back to agentic-only mode"
            )
            # Log timeout event for monitoring (Requirement 8.4)
            return None

        except asyncio.CancelledError:
            logger.info("Speculative path cancelled")
            return None

        except Exception as e:
            # Log error without exposing internal details (Requirement 8.6)
            logger.error(
                f"Speculative path failed with {type(e).__name__}: {str(e)[:100]}",
                exc_info=True,
            )
            # Graceful degradation - return None to allow agentic path to continue
            return None

    async def _collect_agentic_response(
        self,
        query: str,
        session_id: str,
        top_k: int,
        timeout: float,
        shared_results: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Collect agentic response with timeout and error handling.

        Implements graceful degradation:
        - Returns partial results on timeout if available
        - Returns None on complete failure
        - Logs errors for monitoring without exposing internals

        Args:
            query: Query text
            session_id: Session identifier
            top_k: Number of results
            timeout: Timeout in seconds
            shared_results: Shared results from speculative path (for resource sharing)

        Returns:
            Dictionary with agentic response data or None if failed/timeout

        Requirements: 4.2, 4.3, 8.2, 8.4, 8.5
        """
        reasoning_steps = []
        final_response = None
        sources = []

        try:
            agentic_generator = self.agentic.process_query(
                query=query, session_id=session_id, top_k=top_k
            )

            # Collect all steps
            async def collect_steps():
                async for step in agentic_generator:
                    reasoning_steps.append(step.model_dump())

                    if step.type == "response":
                        nonlocal final_response, sources
                        final_response = step.content
                        sources = step.metadata.get("sources", [])

            # Run with timeout
            await asyncio.wait_for(collect_steps(), timeout=timeout)

            logger.info(f"Agentic path completed " f"(steps={len(reasoning_steps)})")

            return {
                "response": final_response,
                "confidence": 0.85,
                "sources": sources,
                "reasoning_steps": reasoning_steps,
                "is_final": True,
            }

        except asyncio.TimeoutError:
            # Return partial results if we have any (Requirement 8.4, 8.5)
            logger.warning(
                f"Agentic path timed out after {timeout}s - "
                f"returning partial results (steps={len(reasoning_steps)})"
            )

            if reasoning_steps or final_response:
                # We have partial results - return them
                return {
                    "response": final_response
                    or "Analysis in progress (partial results)...",
                    "confidence": 0.5,  # Lower confidence for partial results
                    "sources": sources,
                    "reasoning_steps": reasoning_steps,
                    "is_final": False,
                    "timeout": True,
                }
            else:
                # No partial results available
                return None

        except asyncio.CancelledError:
            logger.info("Agentic path cancelled")
            return None

        except Exception as e:
            # Log error without exposing internal details (Requirement 8.6)
            logger.error(
                f"Agentic path failed with {type(e).__name__}: {str(e)[:100]}",
                exc_info=True,
            )
            # Graceful degradation - return None to allow speculative-only mode
            return None

    async def _coordinate_balanced_streaming(
        self, query_id: str, spec_task: asyncio.Task, agentic_task: asyncio.Task
    ) -> AsyncGenerator[ResponseChunk, None]:
        """
        Coordinate streaming from both paths in balanced mode.

        Workflow:
        1. Wait for speculative to complete (should be fast)
        2. Stream preliminary response
        3. Wait for agentic to complete
        4. Stream refinements and final merged response

        Args:
            query_id: Query identifier
            spec_task: Task for speculative processing
            agentic_task: Task for agentic processing

        Yields:
            ResponseChunk: Progressive response chunks

        Requirements: 1.4, 4.1, 4.2, 4.3
        """
        speculative_response = None
        agentic_response = None

        try:
            # Wait for speculative to complete first (should be quick)
            try:
                speculative_response = await spec_task

                if speculative_response:
                    # Yield preliminary chunk
                    yield ResponseChunk(
                        chunk_id=f"{query_id}_preliminary",
                        type=ResponseType.PRELIMINARY,
                        content=speculative_response.response,
                        path_source=PathSource.SPECULATIVE,
                        confidence_score=speculative_response.confidence_score,
                        sources=speculative_response.sources,
                        reasoning_steps=[],
                        timestamp=datetime.now(),
                        metadata={
                            "mode": "balanced",
                            "cache_hit": speculative_response.cache_hit,
                            "processing_time": speculative_response.processing_time,
                            **speculative_response.metadata,
                        },
                    )

                    logger.info(
                        f"Streamed preliminary response for query {query_id} "
                        f"(confidence={speculative_response.confidence_score:.2f})"
                    )

            except Exception as e:
                logger.error(f"Speculative path failed in balanced mode: {e}")

            # Wait for agentic to complete
            try:
                agentic_response = await agentic_task

                if agentic_response:
                    # Yield refinement chunks for reasoning steps
                    for i, step in enumerate(
                        agentic_response.get("reasoning_steps", []), 1
                    ):
                        yield ResponseChunk(
                            chunk_id=f"{query_id}_refinement_{i}",
                            type=ResponseType.REFINEMENT,
                            content=step.get("content", ""),
                            path_source=PathSource.AGENTIC,
                            confidence_score=None,
                            sources=[],
                            reasoning_steps=[step],
                            timestamp=datetime.now(),
                            metadata={
                                "mode": "balanced",
                                "step_type": step.get("type"),
                                "step_id": step.get("step_id"),
                            },
                        )

            except Exception as e:
                logger.error(f"Agentic path failed in balanced mode: {e}")

            # Use coordinator to create final merged response
            if speculative_response or agentic_response:
                # Merge responses
                spec_text = (
                    speculative_response.response if speculative_response else None
                )
                spec_conf = (
                    speculative_response.confidence_score
                    if speculative_response
                    else 0.0
                )
                spec_sources = (
                    speculative_response.sources if speculative_response else []
                )

                agent_text = (
                    agentic_response.get("response") if agentic_response else None
                )
                agent_conf = (
                    agentic_response.get("confidence", 0.85)
                    if agentic_response
                    else 0.0
                )
                agent_sources = (
                    agentic_response.get("sources", []) if agentic_response else []
                )

                # Get reasoning steps to check if we found documents
                reasoning_steps = (
                    agentic_response.get("reasoning_steps", [])
                    if agentic_response
                    else []
                )
                found_documents = any(
                    step.get("type") == "observation"
                    and "Found" in step.get("content", "")
                    for step in reasoning_steps
                )

                # If agentic response is just a placeholder/timeout message,
                # try to use speculative response or provide better error message (Requirement 8.5)
                if agent_text and (
                    "Analysis in progress" in agent_text
                    or "Partial results" in agent_text
                ):
                    if (
                        spec_text and spec_conf >= 0.4
                    ):  # Speculative has reasonable confidence
                        logger.info(
                            f"Agentic path timed out but speculative has good result "
                            f"(confidence={spec_conf:.2f}), using speculative as final"
                        )
                        agent_text = (
                            None  # Ignore placeholder, let merge logic use speculative
                        )
                        agent_conf = 0.0
                    elif not spec_text and found_documents:
                        # Agentic found documents but LLM synthesis timed out
                        # Provide a basic response indicating documents were found
                        logger.warning(
                            "LLM synthesis timed out but documents were found - "
                            "providing fallback response"
                        )
                        agent_text = (
                            "I found relevant documents for your query, but the detailed "
                            "analysis is taking longer than expected. "
                            "Please try using 'fast' mode for quicker results, or wait a moment "
                            "and try again."
                        )
                        agent_conf = 0.3
                    elif not spec_text:
                        # Both paths failed or timed out completely
                        logger.warning(
                            "Both speculative and agentic paths failed to produce results"
                        )
                        agent_text = (
                            "I'm having trouble processing your query at the moment. "
                            "This could be due to:\n"
                            "1. The LLM service is slow or unavailable\n"
                            "2. The query is taking longer than expected\n\n"
                            "Please try again, or try using 'fast' mode for quicker results."
                        )
                        agent_conf = 0.1

                # Use coordinator's merge logic
                final_content, final_confidence = self.coordinator._merge_responses(
                    speculative_response=spec_text,
                    agentic_response=agent_text,
                    speculative_confidence=spec_conf,
                    agentic_confidence=agent_conf,
                )

                merged_sources = self.coordinator._merge_sources(
                    spec_sources, agent_sources
                )

                # Convert sources to SearchResult models if they're dicts
                from backend.models.query import SearchResult

                final_sources = []
                for source in merged_sources:
                    if isinstance(source, dict):
                        # Ensure all required fields are present
                        final_sources.append(
                            SearchResult(
                                chunk_id=source.get("chunk_id", ""),
                                document_id=source.get("document_id", ""),
                                document_name=source.get("document_name", ""),
                                text=source.get("text", ""),
                                score=source.get("score", 0.0),
                                metadata=source.get("metadata", {}),
                            )
                        )
                    else:
                        final_sources.append(source)

                # Determine path used
                if speculative_response and agentic_response:
                    path_used = PathSource.HYBRID
                elif agentic_response:
                    path_used = PathSource.AGENTIC
                else:
                    path_used = PathSource.SPECULATIVE

                # Yield final chunk
                yield ResponseChunk(
                    chunk_id=f"{query_id}_final",
                    type=ResponseType.FINAL,
                    content=final_content,
                    path_source=path_used,
                    confidence_score=final_confidence,
                    sources=final_sources,
                    reasoning_steps=(
                        agentic_response.get("reasoning_steps", [])
                        if agentic_response
                        else []
                    ),
                    timestamp=datetime.now(),
                    metadata={
                        "mode": "balanced",
                        "speculative_completed": speculative_response is not None,
                        "agentic_completed": agentic_response is not None,
                        "source_count": len(final_sources),
                    },
                )

                logger.info(
                    f"BALANCED mode completed for query {query_id} "
                    f"(path={path_used.value}, confidence={final_confidence:.2f})"
                )

            else:
                # Both paths failed - provide clear error message (Requirement 8.3, 8.6)
                logger.error(
                    f"Both paths failed for query {query_id} - "
                    f"speculative={speculative_response is not None}, "
                    f"agentic={agentic_response is not None}"
                )

                yield ResponseChunk(
                    chunk_id=f"{query_id}_error",
                    type=ResponseType.FINAL,
                    content=(
                        "Unable to process your query at this time. "
                        "Please try again or rephrase your question."
                    ),
                    path_source=PathSource.HYBRID,
                    confidence_score=0.0,
                    sources=[],
                    reasoning_steps=[],
                    timestamp=datetime.now(),
                    metadata={
                        "error": "both_paths_failed",
                        "speculative_attempted": True,
                        "agentic_attempted": True,
                    },
                )

        except Exception as e:
            # Log error without exposing internal details (Requirement 8.6)
            logger.error(
                f"Error in balanced mode coordination for query {query_id}: "
                f"{type(e).__name__}: {str(e)[:100]}",
                exc_info=True,
            )

            yield ResponseChunk(
                chunk_id=f"{query_id}_error",
                type=ResponseType.FINAL,
                content=(
                    "An unexpected error occurred while processing your query. "
                    "Please try again."
                ),
                path_source=PathSource.HYBRID,
                confidence_score=0.0,
                sources=[],
                reasoning_steps=[],
                timestamp=datetime.now(),
                metadata={
                    "error": "coordination_error",
                    "error_type": type(e).__name__,
                },
            )

    def create_complete_response(
        self,
        query_id: str,
        query: str,
        mode: QueryMode,
        speculative_response: Optional[SpeculativeResponse],
        agentic_response: Optional[Dict[str, Any]],
        session_id: Optional[str] = None,
    ) -> HybridQueryResponse:
        """
        Create a complete hybrid query response (non-streaming).

        Args:
            query_id: Query identifier
            query: Original query text
            mode: Query mode used
            speculative_response: Response from speculative path
            agentic_response: Response from agentic path
            session_id: Session identifier

        Returns:
            Complete HybridQueryResponse

        Requirements: 1.6, 4.4
        """
        return self.coordinator.create_hybrid_response(
            query_id=query_id,
            query=query,
            mode=mode.value,
            speculative_response=speculative_response,
            agentic_response=agentic_response,
            session_id=session_id,
        )
