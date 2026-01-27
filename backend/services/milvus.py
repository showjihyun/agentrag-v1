"""
Milvus Vector Database Manager for document storage and retrieval.

This service provides connection management, collection operations, and vector search
capabilities with retry logic and comprehensive error handling.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pymilvus import connections, Collection, utility, CollectionSchema, MilvusException
from backend.models.milvus_schema import (
    get_document_collection_schema,
    get_ltm_collection_schema,
    get_index_params,
    get_search_params,
)

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a single search result from Milvus."""

    def __init__(
        self,
        id: str,
        document_id: str,
        text: str,
        score: float,
        document_name: str,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.document_id = document_id
        self.text = text
        self.score = score
        self.document_name = document_name
        self.chunk_index = chunk_index
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "score": self.score,
            "document_name": self.document_name,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"SearchResult(id={self.id}, score={self.score:.4f}, doc={self.document_name})"


class MilvusManager:
    """
    Manager for Milvus vector database operations.

    Features:
    - Connection management with retry logic
    - Collection creation and schema management
    - Batch embedding insertion
    - Vector similarity search with filtering
    - Document deletion and cleanup
    - Health checks and connection validation
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = "documents",
        embedding_dim: int = 384,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        """
        Initialize MilvusManager.

        Args:
            host: Milvus server host
            port: Milvus server port
            collection_name: Name of the collection to use
            embedding_dim: Dimension of embedding vectors
            max_retries: Maximum number of connection retry attempts
            retry_delay: Delay between retry attempts in seconds

        Raises:
            ValueError: If parameters are invalid
        """
        if not host:
            raise ValueError("host cannot be empty")
        if port <= 0:
            raise ValueError("port must be positive")
        if not collection_name:
            raise ValueError("collection_name cannot be empty")
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")

        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._connection_alias = f"milvus_{collection_name}"
        self._collection: Optional[Collection] = None
        self._connected = False
        self._collection_loaded = False  # Track if collection is loaded in memory
        self._load_lock = None  # Will be initialized as asyncio.Lock when needed

        logger.info(
            f"MilvusManager initialized for {host}:{port}, "
            f"collection: {collection_name}, dim: {embedding_dim}"
        )

    def connect(self) -> None:
        """
        Establish connection to Milvus with retry logic.

        Raises:
            RuntimeError: If connection fails after all retries
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Connecting to Milvus at {self.host}:{self.port} "
                    f"(attempt {attempt}/{self.max_retries})"
                )

                connections.connect(
                    alias=self._connection_alias, host=self.host, port=self.port
                )

                self._connected = True
                logger.info(
                    f"Successfully connected to Milvus: {self._connection_alias}"
                )
                return

            except MilvusException as e:
                logger.warning(f"Connection attempt {attempt} failed: {str(e)}")

                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    error_msg = f"Failed to connect to Milvus after {self.max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg) from e

    def disconnect(self) -> None:
        """Disconnect from Milvus."""
        try:
            if self._connected:
                connections.disconnect(alias=self._connection_alias)
                self._connected = False
                logger.debug(f"Disconnected from Milvus: {self._connection_alias}")
        except Exception as e:
            logger.warning(f"Error during disconnect: {str(e)}")

    def is_connected(self) -> bool:
        """
        Check if connected to Milvus.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Milvus connection.

        Returns:
            Dictionary with health status information
        """
        try:
            if not self._connected:
                return {
                    "status": "disconnected",
                    "connected": False,
                    "error": "Not connected to Milvus",
                }

            # Check if we can list collections
            collections = utility.list_collections(using=self._connection_alias)

            # Check if our collection exists
            collection_exists = self.collection_name in collections

            health_info = {
                "status": "healthy",
                "connected": True,
                "host": self.host,
                "port": self.port,
                "collection_name": self.collection_name,
                "collection_exists": collection_exists,
                "total_collections": len(collections),
            }

            # If collection exists, get stats
            if collection_exists and self._collection:
                try:
                    self._collection.load()
                    health_info["num_entities"] = self._collection.num_entities
                except Exception as e:
                    logger.warning(f"Could not get collection stats: {str(e)}")

            logger.debug(f"Health check passed: {health_info}")
            return health_info

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "unhealthy",
                "connected": self._connected,
                "error": error_msg,
            }

    def create_collection(
        self, schema: Optional[CollectionSchema] = None, drop_existing: bool = False
    ) -> Collection:
        """
        Create a Milvus collection with the specified schema.

        Args:
            schema: Collection schema (uses default document schema if None)
            drop_existing: Whether to drop existing collection with same name

        Returns:
            Collection: The created or existing collection

        Raises:
            RuntimeError: If collection creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Milvus. Call connect() first.")

        try:
            # Check if collection already exists
            has_collection = utility.has_collection(
                self.collection_name, using=self._connection_alias
            )

            if has_collection:
                if drop_existing:
                    logger.warning(
                        f"Dropping existing collection: {self.collection_name}"
                    )
                    utility.drop_collection(
                        self.collection_name, using=self._connection_alias
                    )
                else:
                    logger.info(f"Collection already exists: {self.collection_name}")
                    self._collection = Collection(
                        name=self.collection_name, using=self._connection_alias
                    )
                    return self._collection

            # Use provided schema or default document schema
            if schema is None:
                schema = get_document_collection_schema(self.embedding_dim)

            # Create collection
            logger.info(f"Creating collection: {self.collection_name}")
            self._collection = Collection(
                name=self.collection_name, schema=schema, using=self._connection_alias
            )

            # Create index on embedding field
            # Get collection size for optimal index selection
            collection_size = 0  # New collection
            index_params = get_index_params(collection_size)
            logger.info(f"Creating index with params: {index_params}")
            self._collection.create_index(
                field_name="embedding", index_params=index_params
            )

            logger.info(f"Collection created successfully: {self.collection_name}")
            return self._collection

        except MilvusException as e:
            error_msg = (
                f"Failed to create collection '{self.collection_name}': {str(e)}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def get_collection(self) -> Collection:
        """
        Get the current collection instance with connection validation.

        Returns:
            Collection: The collection instance

        Raises:
            RuntimeError: If collection not initialized
        """
        # Ensure connection is established
        if not self._connected:
            logger.info(
                "Milvus not connected in get_collection, establishing connection..."
            )
            self.connect()

        # Validate connection is still alive
        try:
            # Quick connection check
            utility.list_collections(using=self._connection_alias)
        except Exception as e:
            logger.warning(f"Connection validation failed: {e}, reconnecting...")
            self._connected = False
            self._collection = None
            self._collection_loaded = False
            self.connect()

        if self._collection is None:
            # Try to load existing collection
            try:
                if utility.has_collection(
                    self.collection_name, using=self._connection_alias
                ):
                    self._collection = Collection(
                        name=self.collection_name, using=self._connection_alias
                    )
                    logger.info(f"Loaded existing collection: {self.collection_name}")
                else:
                    # Collection doesn't exist, create it
                    logger.info(
                        f"Collection '{self.collection_name}' not found, creating..."
                    )
                    self.create_collection()
            except Exception as e:
                logger.error(f"Error checking/loading collection: {e}")
                # Try to reconnect and create collection
                self._connected = False
                self._collection = None
                self._collection_loaded = False
                self.connect()
                self.create_collection()

        return self._collection

    async def _ensure_collection_loaded(self) -> None:
        """
        Ensure collection is loaded into memory once (thread-safe).

        This significantly improves search performance by avoiding
        repeated load operations on every search.

        Uses asyncio.Lock to prevent race conditions when multiple
        concurrent requests try to load the collection simultaneously.
        """
        # Initialize lock on first use (lazy initialization)
        if self._load_lock is None:
            import asyncio

            self._load_lock = asyncio.Lock()

        async with self._load_lock:
            # Double-check pattern: check again inside lock
            if not self._collection_loaded:
                try:
                    collection = self.get_collection()
                    collection.load()
                    self._collection_loaded = True
                    # Use INFO for first load (important event)
                    logger.info(
                        f"Collection '{self.collection_name}' loaded into memory"
                    )
                except Exception as e:
                    logger.error(f"Failed to load collection: {e}")
                    raise

    async def insert_embeddings(
        self, embeddings: List[List[float]], metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Insert embeddings with metadata into the collection.

        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries (one per embedding)
                     Must include: id, document_id, text, chunk_index,
                     document_name, file_type, upload_date

        Returns:
            List[str]: List of inserted IDs

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If insertion fails
        """
        if not embeddings:
            raise ValueError("embeddings cannot be empty")
        if not metadata:
            raise ValueError("metadata cannot be empty")
        if len(embeddings) != len(metadata):
            raise ValueError(
                f"embeddings and metadata length mismatch: "
                f"{len(embeddings)} vs {len(metadata)}"
            )

        # Validate embedding dimensions
        for i, emb in enumerate(embeddings):
            if len(emb) != self.embedding_dim:
                raise ValueError(
                    f"Embedding {i} has dimension {len(emb)}, "
                    f"expected {self.embedding_dim}"
                )

        try:
            # Ensure connection is established
            if not self._connected:
                logger.debug("Milvus not connected, establishing connection...")
                self.connect()

            # Ensure collection is loaded
            await self._ensure_collection_loaded()

            collection = self.get_collection()

            # Prepare data for insertion
            # Extract fields from metadata
            ids = []
            document_ids = []
            knowledgebase_ids = []
            texts = []
            chunk_indices = []
            document_names = []
            file_types = []
            upload_dates = []
            authors = []
            creation_dates = []
            languages = []
            keywords_list = []

            required_fields = [
                "id",
                "document_id",
                "text",
                "chunk_index",
                "document_name",
                "file_type",
                "upload_date",
            ]

            for i, meta in enumerate(metadata):
                # Validate required fields
                missing_fields = [f for f in required_fields if f not in meta]
                if missing_fields:
                    raise ValueError(
                        f"Metadata {i} missing required fields: {missing_fields}"
                    )

                ids.append(meta["id"])
                document_ids.append(meta["document_id"])
                knowledgebase_ids.append(meta.get("knowledgebase_id", ""))
                texts.append(meta["text"])
                chunk_indices.append(meta["chunk_index"])
                document_names.append(meta["document_name"])
                file_types.append(meta["file_type"])

                # Convert upload_date to Unix timestamp if it's a string
                upload_date = meta["upload_date"]
                if isinstance(upload_date, str):
                    from datetime import datetime

                    upload_date = int(
                        datetime.fromisoformat(
                            upload_date.replace("Z", "+00:00")
                        ).timestamp()
                    )
                upload_dates.append(upload_date)

                # Optional metadata fields with defaults
                authors.append(meta.get("author", ""))

                # Convert creation_date to Unix timestamp if present
                creation_date = meta.get("creation_date", 0)
                if isinstance(creation_date, str):
                    from datetime import datetime

                    try:
                        creation_date = int(
                            datetime.fromisoformat(
                                creation_date.replace("Z", "+00:00")
                            ).timestamp()
                        )
                    except:
                        creation_date = 0
                creation_dates.append(creation_date)

                languages.append(meta.get("language", ""))
                keywords_list.append(meta.get("keywords", ""))

            # Prepare data in column format (must match schema field order)
            data = [
                ids,
                document_ids,
                knowledgebase_ids,
                texts,
                embeddings,
                chunk_indices,
                document_names,
                file_types,
                upload_dates,
                authors,
                creation_dates,
                languages,
                keywords_list,
            ]

            logger.info(
                f"Inserting {len(embeddings)} embeddings into {self.collection_name}"
            )

            # Insert data
            insert_result = collection.insert(data)

            # Flush to ensure data is persisted
            collection.flush()

            logger.info(
                f"Successfully inserted {insert_result.insert_count} entities, "
                f"IDs: {insert_result.primary_keys[:5]}..."
            )

            return insert_result.primary_keys

        except MilvusException as e:
            error_msg = f"Failed to insert embeddings: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during insertion: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Perform similarity search in the collection.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Optional filter expression (e.g., "document_id == 'doc123'")
            output_fields: Fields to include in results (default: all)

        Returns:
            List[SearchResult]: Search results sorted by similarity

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If search fails
        """
        if not query_embedding:
            raise ValueError("query_embedding cannot be empty")
        if len(query_embedding) != self.embedding_dim:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} "
                f"does not match expected {self.embedding_dim}"
            )
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        try:
            # Ensure connection is established
            if not self._connected:
                logger.debug("Milvus not connected, establishing connection...")
                self.connect()

            collection = self.get_collection()

            # Ensure collection is loaded (only once, thread-safe)
            await self._ensure_collection_loaded()

            # Default output fields
            if output_fields is None:
                output_fields = [
                    "id",
                    "document_id",
                    "knowledgebase_id",
                    "text",
                    "document_name",
                    "chunk_index",
                    "file_type",
                    "upload_date",
                ]

            # Get collection size and index info for optimal search params
            collection_size = collection.num_entities
            index_info = collection.indexes[0] if collection.indexes else None

            # Extract index type and metric type from existing index
            if index_info:
                index_type = index_info.params.get("index_type", "HNSW")
                # IMPORTANT: Use the same metric_type as the index
                metric_type = index_info.params.get("metric_type", "COSINE")
                logger.debug(
                    f"Using existing index: type={index_type}, metric={metric_type}"
                )
            else:
                # Fallback to defaults if no index exists
                index_type = "HNSW"
                metric_type = "COSINE"
                logger.warning(
                    f"No index found, using defaults: type={index_type}, metric={metric_type}"
                )

            # Search parameters (must match index metric_type)
            search_params = get_search_params(index_type, collection_size, metric_type)

            filter_str = f" with filters: {filters}" if filters else ""
            logger.info(
                f"Searching for top {top_k} results (index: {index_type}, size: {collection_size})"
                f"{filter_str}"
            )

            # Perform search
            search_results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filters,
                output_fields=output_fields,
            )

            # Parse results
            results = []
            for hits in search_results:
                for hit in hits:
                    result = SearchResult(
                        id=hit.entity.get("id"),
                        document_id=hit.entity.get("document_id"),
                        text=hit.entity.get("text"),
                        score=hit.score,
                        document_name=hit.entity.get("document_name"),
                        chunk_index=hit.entity.get("chunk_index"),
                        metadata={
                            "filename": hit.entity.get("document_name"),
                            "document_name": hit.entity.get("document_name"),
                            "chunk_index": hit.entity.get("chunk_index"),
                            "file_type": hit.entity.get("file_type"),
                            "upload_date": hit.entity.get("upload_date"),
                            "page_number": hit.entity.get("page_number"),
                            "line_number": hit.entity.get("line_number"),
                        },
                    )
                    results.append(result)

            # Use DEBUG for search results count (too frequent for INFO)
            logger.debug(f"Search returned {len(results)} results")

            return results

        except MilvusException as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during search: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all chunks belonging to a specific document.

        Args:
            document_id: ID of the document to delete

        Returns:
            int: Number of entities deleted

        Raises:
            ValueError: If document_id is invalid
            RuntimeError: If deletion fails
        """
        if not document_id:
            raise ValueError("document_id cannot be empty")

        try:
            collection = self.get_collection()

            # Build filter expression
            expr = f'document_id == "{document_id}"'

            logger.info(f"Deleting all chunks for document: {document_id}")

            # Query to get IDs first (for counting)
            query_results = collection.query(expr=expr, output_fields=["id"])

            num_to_delete = len(query_results)

            if num_to_delete == 0:
                logger.warning(f"No chunks found for document_id: {document_id}")
                return 0

            # Delete by expression
            collection.delete(expr)

            # Flush to ensure deletion is persisted
            collection.flush()

            logger.info(f"Deleted {num_to_delete} chunks for document: {document_id}")

            return num_to_delete

        except MilvusException as e:
            error_msg = f"Failed to delete document '{document_id}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during deletion: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = self.get_collection()
            collection.load()

            stats = {
                "name": self.collection_name,
                "num_entities": collection.num_entities,
                "schema": {
                    "description": collection.schema.description,
                    "fields": [
                        {
                            "name": field.name,
                            "type": str(field.dtype),
                            "is_primary": field.is_primary,
                        }
                        for field in collection.schema.fields
                    ],
                },
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"name": self.collection_name, "error": str(e)}

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False

    def __repr__(self) -> str:
        return (
            f"MilvusManager(host={self.host}, port={self.port}, "
            f"collection={self.collection_name}, connected={self._connected})"
        )
