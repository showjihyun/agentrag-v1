"""Milvus collection schemas for documents and long-term memory."""

from pymilvus import CollectionSchema, FieldSchema, DataType


def get_document_collection_schema(embedding_dim: int = 384) -> CollectionSchema:
    """
    Get the schema for the document chunks collection.

    Args:
        embedding_dim: Dimension of the embedding vectors (default: 384 for all-MiniLM-L6-v2)

    Returns:
        CollectionSchema for document storage
    """
    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            max_length=100,
            description="Unique chunk identifier",
        ),
        FieldSchema(
            name="document_id",
            dtype=DataType.VARCHAR,
            max_length=100,
            description="Parent document identifier",
        ),
        FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=65535,
            description="Text content of the chunk",
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=embedding_dim,
            description="Vector embedding of the text",
        ),
        FieldSchema(
            name="chunk_index",
            dtype=DataType.INT64,
            description="Position of chunk in document",
        ),
        FieldSchema(
            name="document_name",
            dtype=DataType.VARCHAR,
            max_length=500,
            description="Original document filename",
        ),
        FieldSchema(
            name="file_type",
            dtype=DataType.VARCHAR,
            max_length=50,
            description="Document file type",
        ),
        FieldSchema(
            name="upload_date",
            dtype=DataType.INT64,
            description="Upload timestamp (Unix epoch)",
        ),
        # Rich metadata fields
        FieldSchema(
            name="author",
            dtype=DataType.VARCHAR,
            max_length=200,
            description="Document author",
        ),
        FieldSchema(
            name="creation_date",
            dtype=DataType.INT64,
            description="Document creation timestamp (Unix epoch)",
        ),
        FieldSchema(
            name="language",
            dtype=DataType.VARCHAR,
            max_length=10,
            description="Document language (ISO 639-1 code)",
        ),
        FieldSchema(
            name="keywords",
            dtype=DataType.VARCHAR,
            max_length=1000,
            description="Document keywords (comma-separated)",
        ),
    ]

    schema = CollectionSchema(
        fields=fields,
        description="Document chunks with embeddings for RAG retrieval",
        enable_dynamic_field=True,  # Allow additional metadata fields
    )

    return schema


def get_ltm_collection_schema(embedding_dim: int = 384) -> CollectionSchema:
    """
    Get the schema for the long-term memory collection.

    Stores successful query-response interactions and learned patterns
    for future retrieval and learning.

    Args:
        embedding_dim: Dimension of the embedding vectors

    Returns:
        CollectionSchema for long-term memory storage
    """
    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            max_length=100,
            description="Unique interaction identifier",
        ),
        FieldSchema(
            name="query",
            dtype=DataType.VARCHAR,
            max_length=10000,
            description="Original user query",
        ),
        FieldSchema(
            name="query_embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=embedding_dim,
            description="Vector embedding of the query",
        ),
        FieldSchema(
            name="response",
            dtype=DataType.VARCHAR,
            max_length=65535,
            description="Generated response",
        ),
        FieldSchema(
            name="session_id",
            dtype=DataType.VARCHAR,
            max_length=100,
            description="Session identifier",
        ),
        FieldSchema(
            name="timestamp",
            dtype=DataType.INT64,
            description="Interaction timestamp (Unix epoch)",
        ),
        FieldSchema(
            name="success_score",
            dtype=DataType.FLOAT,
            description="Success/quality score (0-1)",
        ),
        FieldSchema(
            name="source_count",
            dtype=DataType.INT64,
            description="Number of sources used",
        ),
        FieldSchema(
            name="action_count",
            dtype=DataType.INT64,
            description="Number of agent actions taken",
        ),
    ]

    schema = CollectionSchema(
        fields=fields,
        description="Long-term memory for storing successful interactions and patterns",
        enable_dynamic_field=True,  # Allow additional metadata
    )

    return schema


def get_index_params(collection_size: int = 0, metric_type: str = "COSINE") -> dict:
    """
    Get optimized index parameters based on collection size.

    Args:
        collection_size: Number of vectors in collection
        metric_type: Distance metric type (COSINE, L2, or IP)

    Returns:
        Dictionary with index configuration

    Note:
        - COSINE: Best for normalized vectors, angle-based similarity (RAG standard)
        - L2: Euclidean distance, considers magnitude and direction
        - IP: Inner product, equivalent to COSINE for normalized vectors
    """
    # Validate metric type
    valid_metrics = ["COSINE", "L2", "IP"]
    if metric_type not in valid_metrics:
        raise ValueError(
            f"Invalid metric_type: {metric_type}. Must be one of {valid_metrics}"
        )

    # For small collections (< 100K), use HNSW for best performance
    if collection_size < 100000:
        return {
            "metric_type": metric_type,
            "index_type": "HNSW",
            "params": {
                "M": 16,  # Number of connections per layer
                "efConstruction": 200,  # Size of dynamic candidate list
            },
        }
    # For medium collections (100K - 1M), use IVF_PQ for memory efficiency
    elif collection_size < 1000000:
        return {
            "metric_type": metric_type,
            "index_type": "IVF_PQ",
            "params": {
                "nlist": 1024,  # Number of clusters
                "m": 8,  # Number of sub-quantizers
                "nbits": 8,  # Bits per sub-quantizer
            },
        }
    # For large collections (> 1M), use IVF_SQ8 for balance
    else:
        return {
            "metric_type": metric_type,
            "index_type": "IVF_SQ8",
            "params": {"nlist": 2048},
        }


def get_search_params(
    index_type: str = "HNSW", collection_size: int = 0, metric_type: str = "COSINE"
) -> dict:
    """
    Get optimized search parameters based on index type.

    Args:
        index_type: Type of index being used
        collection_size: Number of vectors in collection
        metric_type: Distance metric type (must match index metric_type)

    Returns:
        Dictionary with search configuration

    Note:
        The metric_type MUST match the metric_type used when creating the index.
        Mismatch will cause search errors.
    """
    # Validate metric type
    valid_metrics = ["COSINE", "L2", "IP"]
    if metric_type not in valid_metrics:
        raise ValueError(
            f"Invalid metric_type: {metric_type}. Must be one of {valid_metrics}"
        )

    if index_type == "HNSW":
        # Adjust ef based on collection size
        ef = 64 if collection_size < 100000 else 128
        return {
            "metric_type": metric_type,
            "params": {"ef": ef},
        }  # Size of dynamic candidate list for search
    elif index_type.startswith("IVF"):
        # Adjust nprobe based on collection size
        nprobe = 32 if collection_size < 1000000 else 64
        return {
            "metric_type": metric_type,
            "params": {"nprobe": nprobe},
        }  # Number of clusters to search
    else:
        return {"metric_type": metric_type, "params": {}}
