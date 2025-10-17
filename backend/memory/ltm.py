"""
Long-Term Memory (LTM) implementation using Milvus.

This module provides persistent storage for successful interactions and learned patterns.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class Interaction:
    """Represents a stored interaction in long-term memory."""

    def __init__(
        self,
        id: str,
        query: str,
        response: str,
        session_id: str,
        timestamp: datetime,
        success_score: float,
        source_count: int,
        action_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.query = query
        self.response = response
        self.session_id = session_id
        self.timestamp = timestamp
        self.success_score = success_score
        self.source_count = source_count
        self.action_count = action_count
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "query": self.query,
            "response": self.response,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "success_score": self.success_score,
            "source_count": self.source_count,
            "action_count": self.action_count,
            "metadata": self.metadata,
        }


class LongTermMemory:
    """
    Long-Term Memory manager using Milvus for persistent storage.

    Features:
    - Store successful query-response interactions
    - Retrieve similar past interactions using vector search
    - Store and retrieve learned patterns
    - Separate Milvus collection for LTM data
    """

    def __init__(
        self, milvus_manager: MilvusManager, embedding_service: EmbeddingService
    ):
        """
        Initialize LongTermMemory.

        Args:
            milvus_manager: MilvusManager instance for LTM collection
            embedding_service: EmbeddingService for query embeddings

        Raises:
            ValueError: If parameters are invalid
        """
        if not milvus_manager:
            raise ValueError("milvus_manager cannot be None")
        if not embedding_service:
            raise ValueError("embedding_service cannot be None")

        self.milvus = milvus_manager
        self.embedding = embedding_service

        logger.info(
            f"LongTermMemory initialized with collection: {milvus_manager.collection_name}"
        )

    async def store_interaction(
        self,
        query: str,
        response: str,
        session_id: str,
        success_score: float = 1.0,
        source_count: int = 0,
        action_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a successful query-response interaction.

        Args:
            query: Original user query
            response: Generated response
            session_id: Session identifier
            success_score: Quality/success score (0-1, default: 1.0)
            source_count: Number of sources used
            action_count: Number of agent actions taken
            metadata: Optional additional metadata

        Returns:
            str: ID of the stored interaction

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If storage fails
        """
        if not query:
            raise ValueError("query cannot be empty")
        if not response:
            raise ValueError("response cannot be empty")
        if not session_id:
            raise ValueError("session_id cannot be empty")
        if not 0 <= success_score <= 1:
            raise ValueError("success_score must be between 0 and 1")

        try:
            # Generate unique ID
            interaction_id = f"ltm_{uuid.uuid4().hex[:16]}"

            # Generate query embedding (now async)
            query_embedding = await self.embedding.embed_text(query)

            # Prepare metadata for storage
            timestamp = int(datetime.now().timestamp())

            # Prepare data for LTM collection (different schema than documents)
            # LTM schema uses 'query_embedding' field instead of 'embedding'
            from pymilvus import Collection

            collection = self.milvus.get_collection()

            # Prepare data in column format matching LTM schema
            data = [
                [interaction_id],  # id
                [query],  # query
                [query_embedding],  # query_embedding
                [response],  # response
                [session_id],  # session_id
                [timestamp],  # timestamp
                [success_score],  # success_score
                [source_count],  # source_count
                [action_count],  # action_count
            ]

            # Insert directly into collection
            insert_result = collection.insert(data)
            collection.flush()

            logger.info(
                f"Stored interaction {interaction_id} for session {session_id}, "
                f"success_score: {success_score}, inserted: {insert_result.insert_count}"
            )

            logger.info(
                f"Stored interaction {interaction_id} for session {session_id}, "
                f"success_score: {success_score}"
            )

            return interaction_id

        except Exception as e:
            error_msg = f"Failed to store interaction: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def retrieve_similar_interactions(
        self, query: str, top_k: int = 5, min_success_score: float = 0.7
    ) -> List[Interaction]:
        """
        Retrieve similar past interactions using vector similarity search.

        Args:
            query: Query to find similar interactions for
            top_k: Number of similar interactions to retrieve
            min_success_score: Minimum success score filter (0-1)

        Returns:
            List of similar Interaction objects, sorted by similarity

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If retrieval fails
        """
        if not query:
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if not 0 <= min_success_score <= 1:
            raise ValueError("min_success_score must be between 0 and 1")

        try:
            # Generate query embedding (now async)
            query_embedding = await self.embedding.embed_text(query)

            # Build filter expression for minimum success score
            filters = f"success_score >= {min_success_score}"

            # Search for similar interactions using LTM collection
            # Note: LTM uses 'query_embedding' field, not 'embedding'
            from pymilvus import Collection
            from backend.models.milvus_schema import get_search_params

            collection = self.milvus.get_collection()
            await self.milvus._ensure_collection_loaded()

            # Get search parameters
            collection_size = collection.num_entities

            # Extract metric type from existing index
            index_info = collection.indexes[0] if collection.indexes else None
            if index_info:
                index_type = index_info.params.get("index_type", "HNSW")
                metric_type = index_info.params.get("metric_type", "COSINE")
            else:
                index_type = "HNSW"
                metric_type = "COSINE"

            search_params = get_search_params(index_type, collection_size, metric_type)

            # Perform search on query_embedding field
            search_results_raw = collection.search(
                data=[query_embedding],
                anns_field="query_embedding",  # LTM uses this field
                param=search_params,
                limit=top_k,
                expr=filters,
                output_fields=[
                    "id",
                    "query",
                    "response",
                    "session_id",
                    "timestamp",
                    "success_score",
                    "source_count",
                    "action_count",
                ],
            )

            # Parse results
            search_results = []
            for hits in search_results_raw:
                for hit in hits:
                    # Create a result object
                    result = type(
                        "obj",
                        (object,),
                        {
                            "id": hit.entity.get("id"),
                            "text": hit.entity.get("query"),  # query field
                            "response": hit.entity.get("response"),
                            "session_id": hit.entity.get("session_id"),
                            "timestamp": hit.entity.get("timestamp"),
                            "success_score": hit.entity.get("success_score"),
                            "source_count": hit.entity.get("source_count"),
                            "action_count": hit.entity.get("action_count"),
                            "score": hit.score,
                        },
                    )()
                    search_results.append(result)

            # Convert to Interaction objects
            interactions = []
            for result in search_results:
                interaction = Interaction(
                    id=result.id,
                    query=result.text,  # In LTM, 'text' field contains the query
                    response=getattr(result, "response", ""),
                    session_id=getattr(result, "session_id", ""),
                    timestamp=datetime.fromtimestamp(getattr(result, "timestamp", 0)),
                    success_score=getattr(result, "success_score", 0.0),
                    source_count=getattr(result, "source_count", 0),
                    action_count=getattr(result, "action_count", 0),
                    metadata={"similarity_score": result.score},
                )
                interactions.append(interaction)

            # Log results with safe access
            if interactions:
                top_similarity = interactions[0].metadata.get("similarity_score", 0.0)
                logger.info(
                    f"Retrieved {len(interactions)} similar interactions for query, "
                    f"top similarity: {top_similarity:.3f}"
                )
            else:
                logger.info("Retrieved 0 similar interactions for query")

            return interactions

        except Exception as e:
            error_msg = f"Failed to retrieve similar interactions: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def store_learned_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        description: str,
        success_score: float = 1.0,
    ) -> str:
        """
        Store a learned pattern for future use.

        Patterns can be query strategies, common workflows, or other
        learned behaviors that improve system performance.

        Args:
            pattern_type: Type of pattern (e.g., "query_strategy", "workflow")
            pattern_data: Pattern data as dictionary
            description: Human-readable description of the pattern
            success_score: Effectiveness score (0-1)

        Returns:
            str: ID of the stored pattern

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If storage fails
        """
        if not pattern_type:
            raise ValueError("pattern_type cannot be empty")
        if not pattern_data:
            raise ValueError("pattern_data cannot be empty")
        if not description:
            raise ValueError("description cannot be empty")
        if not 0 <= success_score <= 1:
            raise ValueError("success_score must be between 0 and 1")

        try:
            # Generate unique ID
            pattern_id = f"pattern_{pattern_type}_{uuid.uuid4().hex[:12]}"

            # Generate embedding from description (now async)
            description_embedding = await self.embedding.embed_text(description)

            # Prepare metadata
            timestamp = int(datetime.now().timestamp())

            # Store pattern as a special type of interaction
            # Query field contains the description, response contains pattern data
            from pymilvus import Collection

            collection = self.milvus.get_collection()

            # Prepare data in column format matching LTM schema
            data = [
                [pattern_id],  # id
                [description],  # query
                [description_embedding],  # query_embedding
                [str(pattern_data)],  # response (serialized pattern data)
                [f"pattern_{pattern_type}"],  # session_id
                [timestamp],  # timestamp
                [success_score],  # success_score
                [0],  # source_count
                [0],  # action_count
            ]

            # Insert directly into collection
            insert_result = collection.insert(data)
            collection.flush()

            logger.info(
                f"Stored learned pattern {pattern_id} of type '{pattern_type}', "
                f"success_score: {success_score}"
            )

            return pattern_id

        except Exception as e:
            error_msg = f"Failed to store learned pattern: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def retrieve_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_success_score: float = 0.8,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve learned patterns.

        Args:
            pattern_type: Filter by pattern type (None = all patterns)
            min_success_score: Minimum success score filter
            limit: Maximum number of patterns to retrieve

        Returns:
            List of pattern dictionaries

        Raises:
            RuntimeError: If retrieval fails
        """
        try:
            # Build filter expression
            filters = f"success_score >= {min_success_score}"
            if pattern_type:
                filters += f' and session_id == "pattern_{pattern_type}"'

            # For pattern retrieval, we can use a generic query embedding
            # or retrieve based on filters only
            # Using a neutral query embedding
            neutral_query = "learned pattern"
            query_embedding = await self.embedding.embed_text(neutral_query)

            # Search with filters using LTM collection
            from pymilvus import Collection
            from backend.models.milvus_schema import get_search_params

            collection = self.milvus.get_collection()
            await self.milvus._ensure_collection_loaded()

            # Get search parameters
            collection_size = collection.num_entities

            # Extract metric type from existing index
            index_info = collection.indexes[0] if collection.indexes else None
            if index_info:
                index_type = index_info.params.get("index_type", "HNSW")
                metric_type = index_info.params.get("metric_type", "COSINE")
            else:
                index_type = "HNSW"
                metric_type = "COSINE"

            search_params = get_search_params(index_type, collection_size, metric_type)

            # Perform search on query_embedding field
            search_results_raw = collection.search(
                data=[query_embedding],
                anns_field="query_embedding",  # LTM uses this field
                param=search_params,
                limit=limit,
                expr=filters,
                output_fields=[
                    "id",
                    "query",
                    "response",
                    "session_id",
                    "timestamp",
                    "success_score",
                ],
            )

            # Parse results
            search_results = []
            for hits in search_results_raw:
                for hit in hits:
                    result = type(
                        "obj",
                        (object,),
                        {
                            "id": hit.entity.get("id"),
                            "text": hit.entity.get("query"),
                            "response": hit.entity.get("response"),
                            "session_id": hit.entity.get("session_id"),
                            "timestamp": hit.entity.get("timestamp"),
                            "success_score": hit.entity.get("success_score"),
                            "score": hit.score,
                        },
                    )()
                    search_results.append(result)

            # Parse patterns
            patterns = []
            for result in search_results:
                # Extract pattern type from session_id
                session_id = getattr(result, "session_id", "")
                extracted_type = (
                    session_id.replace("pattern_", "")
                    if session_id.startswith("pattern_")
                    else "unknown"
                )

                pattern = {
                    "id": result.id,
                    "type": extracted_type,
                    "description": result.text,
                    "data": getattr(result, "response", ""),
                    "success_score": getattr(result, "success_score", 0.0),
                    "timestamp": datetime.fromtimestamp(
                        getattr(result, "timestamp", 0)
                    ).isoformat(),
                }
                patterns.append(pattern)

            logger.info(
                f"Retrieved {len(patterns)} patterns"
                f"{' of type ' + pattern_type if pattern_type else ''}"
            )

            return patterns

        except Exception as e:
            error_msg = f"Failed to retrieve patterns: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about long-term memory.

        Returns:
            Dictionary with LTM statistics
        """
        try:
            stats = self.milvus.get_collection_stats()

            return {
                "collection_name": self.milvus.collection_name,
                "total_interactions": stats.get("num_entities", 0),
                "embedding_dimension": self.embedding.dimension,
                "status": "healthy",
            }

        except Exception as e:
            logger.error(f"Failed to get LTM stats: {str(e)}")
            return {
                "collection_name": self.milvus.collection_name,
                "status": "error",
                "error": str(e),
            }

    def __repr__(self) -> str:
        return (
            f"LongTermMemory(collection={self.milvus.collection_name}, "
            f"embedding_dim={self.embedding.dimension})"
        )
