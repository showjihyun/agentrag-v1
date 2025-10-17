"""
Response Coordinator for merging speculative and agentic results.

This coordinator handles intelligent merging of responses from both paths,
deduplication of sources, streaming coordination, and response versioning.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator, Set
from datetime import datetime
from difflib import SequenceMatcher

from backend.models.hybrid import (
    ResponseChunk,
    ResponseType,
    PathSource,
    SpeculativeResponse,
    HybridQueryResponse,
)
from backend.models.query import SearchResult

logger = logging.getLogger(__name__)


class ResponseVersion:
    """
    Tracks different versions of a response for comparison.

    Used to preserve original speculative response and track changes
    as the agentic path refines the answer.
    """

    def __init__(
        self,
        version_id: str,
        content: str,
        path_source: PathSource,
        confidence_score: float,
        sources: List[SearchResult],
        timestamp: datetime,
    ):
        """
        Initialize a response version.

        Args:
            version_id: Unique identifier for this version
            content: Response text content
            path_source: Which path generated this version
            confidence_score: Confidence score for this version
            sources: Source documents used
            timestamp: When this version was created
        """
        self.version_id = version_id
        self.content = content
        self.path_source = path_source
        self.confidence_score = confidence_score
        self.sources = sources
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary format."""
        return {
            "version_id": self.version_id,
            "content": self.content,
            "path_source": self.path_source.value,
            "confidence_score": self.confidence_score,
            "sources": [s.model_dump() for s in self.sources],
            "timestamp": self.timestamp.isoformat(),
        }


class ResponseCoordinator:
    """
    Coordinates and merges responses from speculative and agentic paths.

    Features:
    - Intelligent deduplication of sources
    - Progressive response merging
    - Response versioning and comparison
    - Change detection between versions
    - Streaming coordination for real-time updates

    Requirements: 1.6, 3.2, 3.3, 3.5, 3.6, 4.4, 10.9
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize ResponseCoordinator.

        Args:
            similarity_threshold: Threshold for considering sources as duplicates (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.response_versions: Dict[str, List[ResponseVersion]] = {}

        logger.info(
            f"ResponseCoordinator initialized with "
            f"similarity_threshold={similarity_threshold}"
        )

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Handle None or empty texts
        if not text1 or not text2:
            return 0.0 if text1 != text2 else 1.0

        return SequenceMatcher(None, text1, text2).ratio()

    def _deduplicate_sources(self, sources: List[SearchResult]) -> List[SearchResult]:
        """
        Deduplicate sources based on document ID and text similarity.

        Strategy:
        1. Remove exact duplicates by chunk_id
        2. Remove near-duplicates by text similarity
        3. Keep highest scoring version of similar sources

        Args:
            sources: List of search results to deduplicate

        Returns:
            Deduplicated list of search results

        Requirements: 1.6, 4.4
        """
        if not sources:
            return []

        # Track seen chunk IDs
        seen_ids: Set[str] = set()

        # Track deduplicated sources
        deduplicated: List[SearchResult] = []

        # Sort by score (highest first) to keep best versions
        # Handle both dict and object types
        def get_score(x):
            if isinstance(x, dict):
                return x.get("score", 0.0)
            return getattr(x, "score", 0.0)

        sorted_sources = sorted(sources, key=get_score, reverse=True)

        for source in sorted_sources:
            # Get chunk_id (handle both dict and object)
            chunk_id = (
                source.get("chunk_id")
                if isinstance(source, dict)
                else getattr(source, "chunk_id", None)
            )

            # Skip if we've seen this exact chunk
            if chunk_id in seen_ids:
                continue

            # Get text (handle both dict and object, and None values)
            source_text = (
                source.get("text")
                if isinstance(source, dict)
                else getattr(source, "text", "")
            )
            source_text = source_text or ""  # Convert None to empty string

            # Check for text similarity with existing sources
            is_duplicate = False
            for existing in deduplicated:
                existing_text = (
                    existing.get("text")
                    if isinstance(existing, dict)
                    else getattr(existing, "text", "")
                )
                existing_text = existing_text or ""  # Convert None to empty string
                similarity = self._calculate_text_similarity(source_text, existing_text)

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    logger.debug(
                        f"Skipping duplicate source (similarity={similarity:.2f}): "
                        f"{chunk_id}"
                    )
                    break

            if not is_duplicate:
                deduplicated.append(source)
                seen_ids.add(chunk_id)

        logger.info(
            f"Deduplicated sources: {len(sources)} -> {len(deduplicated)} "
            f"(removed {len(sources) - len(deduplicated)} duplicates)"
        )

        return deduplicated

    def _merge_sources(
        self,
        speculative_sources: List[SearchResult],
        agentic_sources: List[SearchResult],
    ) -> List[SearchResult]:
        """
        Merge sources from both paths with deduplication.

        Args:
            speculative_sources: Sources from speculative path
            agentic_sources: Sources from agentic path

        Returns:
            Merged and deduplicated list of sources

        Requirements: 1.6, 4.4
        """
        # Combine all sources
        all_sources = speculative_sources + agentic_sources

        # Deduplicate
        merged = self._deduplicate_sources(all_sources)

        logger.info(
            f"Merged sources: spec={len(speculative_sources)}, "
            f"agentic={len(agentic_sources)}, final={len(merged)}"
        )

        return merged

    def _merge_responses(
        self,
        speculative_response: Optional[str],
        agentic_response: Optional[str],
        speculative_confidence: float,
        agentic_confidence: float,
    ) -> tuple[str, float]:
        """
        Intelligently merge response text from both paths.

        Strategy:
        - If only one path has a response, use that
        - If agentic confidence is significantly higher, use agentic
        - If both are similar confidence, prefer agentic (more thorough)
        - If agentic contradicts speculative, use agentic with note

        Args:
            speculative_response: Response from speculative path
            agentic_response: Response from agentic path
            speculative_confidence: Confidence of speculative response
            agentic_confidence: Confidence of agentic response

        Returns:
            Tuple of (merged response text, final confidence score)

        Requirements: 3.2, 3.3, 4.4
        """
        # If only one path has a response
        if not speculative_response and agentic_response:
            return agentic_response, agentic_confidence

        if speculative_response and not agentic_response:
            return speculative_response, speculative_confidence

        if not speculative_response and not agentic_response:
            # Provide more helpful error message
            return (
                "Unable to generate a response. This may be because:\n"
                "1. No documents have been uploaded to the system\n"
                "2. No relevant documents were found for your query\n"
                "3. The system is experiencing technical difficulties\n\n"
                "Please try uploading documents or rephrasing your query."
            ), 0.0

        # Both paths have responses - check similarity
        similarity = self._calculate_text_similarity(
            speculative_response, agentic_response
        )

        # If responses are very similar, use agentic (more thorough)
        if similarity >= 0.8:
            logger.info(
                f"Responses are similar (similarity={similarity:.2f}), "
                f"using agentic response"
            )
            return agentic_response, agentic_confidence

        # If agentic confidence is significantly higher
        if agentic_confidence > speculative_confidence + 0.15:
            logger.info(
                f"Agentic confidence significantly higher "
                f"({agentic_confidence:.2f} vs {speculative_confidence:.2f}), "
                f"using agentic response"
            )
            return agentic_response, agentic_confidence

        # Responses differ - use agentic as it's more thorough
        logger.info(
            f"Responses differ (similarity={similarity:.2f}), "
            f"using refined agentic response"
        )
        return agentic_response, agentic_confidence

    def store_version(
        self,
        query_id: str,
        content: str,
        path_source: PathSource,
        confidence_score: float,
        sources: List[SearchResult],
    ) -> str:
        """
        Store a response version for later comparison.

        Args:
            query_id: Unique query identifier
            content: Response content
            path_source: Which path generated this
            confidence_score: Confidence score
            sources: Source documents

        Returns:
            Version ID

        Requirements: 3.5, 3.6, 10.9
        """
        version_id = f"v_{uuid.uuid4().hex[:8]}"

        version = ResponseVersion(
            version_id=version_id,
            content=content,
            path_source=path_source,
            confidence_score=confidence_score,
            sources=sources,
            timestamp=datetime.now(),
        )

        if query_id not in self.response_versions:
            self.response_versions[query_id] = []

        self.response_versions[query_id].append(version)

        logger.debug(
            f"Stored version {version_id} for query {query_id} "
            f"(path={path_source.value})"
        )

        return version_id

    def get_versions(self, query_id: str) -> List[ResponseVersion]:
        """
        Get all versions for a query.

        Args:
            query_id: Query identifier

        Returns:
            List of response versions

        Requirements: 3.5, 10.9
        """
        return self.response_versions.get(query_id, [])

    def detect_changes(
        self, query_id: str, version1_id: str, version2_id: str
    ) -> Dict[str, Any]:
        """
        Detect changes between two response versions.

        Args:
            query_id: Query identifier
            version1_id: First version ID
            version2_id: Second version ID

        Returns:
            Dictionary with change information

        Requirements: 3.5, 3.6, 10.9
        """
        versions = self.get_versions(query_id)

        v1 = next((v for v in versions if v.version_id == version1_id), None)
        v2 = next((v for v in versions if v.version_id == version2_id), None)

        if not v1 or not v2:
            return {"error": "Version not found"}

        # Calculate text similarity
        similarity = self._calculate_text_similarity(v1.content, v2.content)

        # Detect confidence change
        confidence_delta = v2.confidence_score - v1.confidence_score

        # Detect source changes
        v1_source_ids = {s.chunk_id for s in v1.sources}
        v2_source_ids = {s.chunk_id for s in v2.sources}

        added_sources = v2_source_ids - v1_source_ids
        removed_sources = v1_source_ids - v2_source_ids

        changes = {
            "similarity": similarity,
            "content_changed": similarity < 0.95,
            "confidence_delta": confidence_delta,
            "confidence_improved": confidence_delta > 0.05,
            "sources_added": len(added_sources),
            "sources_removed": len(removed_sources),
            "version1": v1.to_dict(),
            "version2": v2.to_dict(),
        }

        logger.info(
            f"Change detection for query {query_id}: "
            f"similarity={similarity:.2f}, "
            f"confidence_delta={confidence_delta:+.2f}, "
            f"sources_added={len(added_sources)}, "
            f"sources_removed={len(removed_sources)}"
        )

        return changes

    async def coordinate_streaming(
        self,
        query_id: str,
        speculative_response: Optional[SpeculativeResponse],
        agentic_generator: Optional[AsyncGenerator[Dict[str, Any], None]],
    ) -> AsyncGenerator[ResponseChunk, None]:
        """
        Coordinate streaming from both paths for progressive updates.

        Workflow:
        1. Stream preliminary response from speculative path (if available)
        2. Stream refinements from agentic path as they arrive
        3. Stream final merged response

        Args:
            query_id: Unique query identifier
            speculative_response: Response from speculative path (if available)
            agentic_generator: Async generator yielding agentic updates

        Yields:
            ResponseChunk: Progressive response chunks

        Requirements: 1.6, 3.2, 3.3, 4.4
        """
        chunk_counter = 0
        speculative_version_id = None
        agentic_content = None
        agentic_confidence = 0.0
        agentic_sources = []

        try:
            # Step 1: Stream preliminary speculative response
            if speculative_response:
                chunk_counter += 1
                chunk_id = f"{query_id}_chunk_{chunk_counter:03d}"

                # Store speculative version
                speculative_version_id = self.store_version(
                    query_id=query_id,
                    content=speculative_response.response,
                    path_source=PathSource.SPECULATIVE,
                    confidence_score=speculative_response.confidence_score,
                    sources=speculative_response.sources,
                )

                # Create preliminary chunk
                preliminary_chunk = ResponseChunk(
                    chunk_id=chunk_id,
                    type=ResponseType.PRELIMINARY,
                    content=speculative_response.response,
                    path_source=PathSource.SPECULATIVE,
                    confidence_score=speculative_response.confidence_score,
                    sources=speculative_response.sources,
                    reasoning_steps=[],
                    timestamp=datetime.now(),
                    metadata={
                        "version_id": speculative_version_id,
                        "cache_hit": speculative_response.cache_hit,
                        "processing_time": speculative_response.processing_time,
                        **speculative_response.metadata,
                    },
                )

                logger.info(
                    f"Streaming preliminary response for query {query_id} "
                    f"(confidence={speculative_response.confidence_score:.2f})"
                )

                yield preliminary_chunk

            # Step 2: Stream agentic refinements
            if agentic_generator:
                async for agentic_update in agentic_generator:
                    chunk_counter += 1
                    chunk_id = f"{query_id}_chunk_{chunk_counter:03d}"

                    # Extract agentic response data
                    agentic_content = agentic_update.get("response", "")
                    agentic_confidence = agentic_update.get("confidence", 0.8)
                    agentic_sources = agentic_update.get("sources", [])
                    reasoning_steps = agentic_update.get("reasoning_steps", [])

                    # Create refinement chunk
                    refinement_chunk = ResponseChunk(
                        chunk_id=chunk_id,
                        type=ResponseType.REFINEMENT,
                        content=agentic_content,
                        path_source=PathSource.AGENTIC,
                        confidence_score=agentic_confidence,
                        sources=agentic_sources,
                        reasoning_steps=reasoning_steps,
                        timestamp=datetime.now(),
                        metadata={
                            "is_final": agentic_update.get("is_final", False),
                            "step": agentic_update.get("step", ""),
                            "progress": agentic_update.get("progress", 0),
                        },
                    )

                    logger.debug(
                        f"Streaming refinement for query {query_id} "
                        f"(step={agentic_update.get('step', 'unknown')})"
                    )

                    yield refinement_chunk

            # Step 3: Stream final merged response
            if speculative_response or agentic_content:
                chunk_counter += 1
                chunk_id = f"{query_id}_chunk_{chunk_counter:03d}"

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

                final_content, final_confidence = self._merge_responses(
                    speculative_response=spec_text,
                    agentic_response=agentic_content,
                    speculative_confidence=spec_conf,
                    agentic_confidence=agentic_confidence,
                )

                # Merge and deduplicate sources
                final_sources = self._merge_sources(spec_sources, agentic_sources)

                # Determine path used
                if speculative_response and agentic_content:
                    path_used = PathSource.HYBRID
                elif agentic_content:
                    path_used = PathSource.AGENTIC
                else:
                    path_used = PathSource.SPECULATIVE

                # Store final version
                final_version_id = self.store_version(
                    query_id=query_id,
                    content=final_content,
                    path_source=path_used,
                    confidence_score=final_confidence,
                    sources=final_sources,
                )

                # Detect changes if we have both versions
                changes = None
                if speculative_version_id and agentic_content:
                    changes = self.detect_changes(
                        query_id=query_id,
                        version1_id=speculative_version_id,
                        version2_id=final_version_id,
                    )

                # Create final chunk
                final_chunk = ResponseChunk(
                    chunk_id=chunk_id,
                    type=ResponseType.FINAL,
                    content=final_content,
                    path_source=path_used,
                    confidence_score=final_confidence,
                    sources=final_sources,
                    reasoning_steps=[],
                    timestamp=datetime.now(),
                    metadata={
                        "version_id": final_version_id,
                        "speculative_version_id": speculative_version_id,
                        "changes": changes,
                        "total_chunks": chunk_counter,
                    },
                )

                logger.info(
                    f"Streaming final response for query {query_id} "
                    f"(path={path_used.value}, confidence={final_confidence:.2f}, "
                    f"sources={len(final_sources)})"
                )

                yield final_chunk

        except Exception as e:
            logger.error(f"Error in streaming coordination: {e}")

            # Yield error chunk
            chunk_counter += 1
            error_chunk = ResponseChunk(
                chunk_id=f"{query_id}_chunk_{chunk_counter:03d}",
                type=ResponseType.FINAL,
                content="An error occurred while processing your query.",
                path_source=PathSource.HYBRID,
                confidence_score=0.0,
                sources=[],
                reasoning_steps=[],
                timestamp=datetime.now(),
                metadata={"error": str(e)},
            )

            yield error_chunk

    def create_hybrid_response(
        self,
        query_id: str,
        query: str,
        mode: str,
        speculative_response: Optional[SpeculativeResponse],
        agentic_response: Optional[Dict[str, Any]],
        session_id: Optional[str] = None,
    ) -> HybridQueryResponse:
        """
        Create a complete hybrid query response from both paths.

        Args:
            query_id: Unique query identifier
            query: Original query text
            mode: Query mode used
            speculative_response: Response from speculative path
            agentic_response: Response from agentic path
            session_id: Session identifier

        Returns:
            Complete HybridQueryResponse

        Requirements: 1.6, 3.2, 4.4
        """
        # Extract data from responses
        spec_text = speculative_response.response if speculative_response else None
        spec_conf = (
            speculative_response.confidence_score if speculative_response else 0.0
        )
        spec_sources = speculative_response.sources if speculative_response else []
        spec_time = (
            speculative_response.processing_time if speculative_response else None
        )
        cache_hit = speculative_response.cache_hit if speculative_response else False

        agent_text = agentic_response.get("response") if agentic_response else None
        agent_conf = (
            agentic_response.get("confidence", 0.8) if agentic_response else 0.0
        )
        agent_sources = agentic_response.get("sources", []) if agentic_response else []
        agent_time = (
            agentic_response.get("processing_time") if agentic_response else None
        )
        reasoning_steps = (
            agentic_response.get("reasoning_steps", []) if agentic_response else []
        )

        # Merge responses
        final_content, final_confidence = self._merge_responses(
            speculative_response=spec_text,
            agentic_response=agent_text,
            speculative_confidence=spec_conf,
            agentic_confidence=agent_conf,
        )

        # Merge sources
        final_sources = self._merge_sources(spec_sources, agent_sources)

        # Determine path used
        if speculative_response and agentic_response:
            path_used = PathSource.HYBRID
        elif agentic_response:
            path_used = PathSource.AGENTIC
        elif speculative_response:
            path_used = PathSource.SPECULATIVE
        else:
            path_used = PathSource.HYBRID

        # Calculate total time
        times = [t for t in [spec_time, agent_time] if t is not None]
        total_time = max(times) if times else 0.0

        # Create response
        response = HybridQueryResponse(
            query_id=query_id,
            query=query,
            mode=mode,
            response=final_content,
            confidence_score=final_confidence,
            sources=final_sources,
            reasoning_steps=reasoning_steps,
            session_id=session_id,
            path_used=path_used,
            speculative_time=spec_time,
            agentic_time=agent_time,
            total_time=total_time,
            cache_hit=cache_hit,
            metadata={
                "source_count": len(final_sources),
                "reasoning_step_count": len(reasoning_steps),
            },
        )

        logger.info(
            f"Created hybrid response for query {query_id}: "
            f"path={path_used.value}, confidence={final_confidence:.2f}, "
            f"total_time={total_time:.2f}s"
        )

        return response
