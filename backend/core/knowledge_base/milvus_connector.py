"""
Milvus Connector for Knowledge Base Integration.

Provides connection management and search operations for the existing Milvus
document collection, reusing the established infrastructure.
"""

import logging
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, utility
from backend.config import settings
from backend.models.milvus_schema import (
    get_document_collection_schema,
    get_index_params,
    get_search_params,
)

logger = logging.getLogger(__name__)


class MilvusConnector:
    """
    Connector for Milvus vector database operations.
    
    Reuses existing Milvus infrastructure and provides workflow-compatible
    search interface for the Knowledge Base block.
    """

    def __init__(self):
        """Initialize Milvus connector."""
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self._collection: Optional[Collection] = None
        self._connected = False

    def connect(self) -> bool:
        """
        Connect to Milvus server.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            RuntimeError: If connection fails
        """
        try:
            # Check if already connected
            if self._connected:
                logger.debug("Already connected to Milvus")
                return True

            # Connect to Milvus
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
            )
            
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            self._connected = True
            
            # Verify collection exists
            if not utility.has_collection(self.collection_name):
                raise RuntimeError(
                    f"Collection '{self.collection_name}' does not exist. "
                    f"Please create the collection first."
                )
            
            # Load collection
            self._collection = Collection(self.collection_name)
            self._collection.load()
            
            logger.info(f"Loaded collection '{self.collection_name}'")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to connect to Milvus: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def disconnect(self) -> None:
        """Disconnect from Milvus server."""
        try:
            if self._collection:
                self._collection.release()
                self._collection = None
            
            connections.disconnect(alias="default")
            self._connected = False
            
            logger.info("Disconnected from Milvus")
            
        except Exception as e:
            logger.warning(f"Error during Milvus disconnect: {str(e)}")

    def get_collection(self) -> Collection:
        """
        Get the Milvus collection instance.
        
        Returns:
            Collection: Milvus collection
            
        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or not self._collection:
            raise RuntimeError("Not connected to Milvus. Call connect() first.")
        
        return self._collection

    def verify_schema(self) -> Dict[str, Any]:
        """
        Verify collection schema compatibility.
        
        Returns:
            dict: Schema information
            
        Raises:
            RuntimeError: If schema is incompatible
        """
        try:
            collection = self.get_collection()
            
            # Get schema
            schema = collection.schema
            
            # Verify required fields exist
            required_fields = [
                "id",
                "document_id",
                "text",
                "embedding",
                "chunk_index",
                "document_name",
                "file_type",
                "upload_date",
                "author",
                "creation_date",
                "language",
                "keywords",
            ]
            
            field_names = [field.name for field in schema.fields]
            
            missing_fields = [
                field for field in required_fields if field not in field_names
            ]
            
            if missing_fields:
                raise RuntimeError(
                    f"Collection schema is missing required fields: {missing_fields}"
                )
            
            # Get collection stats
            stats = {
                "collection_name": self.collection_name,
                "num_entities": collection.num_entities,
                "fields": field_names,
                "schema_compatible": True,
            }
            
            logger.info(
                f"Schema verified: {stats['num_entities']} entities, "
                f"{len(field_names)} fields"
            )
            
            return stats
            
        except Exception as e:
            error_msg = f"Schema verification failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        output_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"author": "John Doe"})
            output_fields: Fields to include in results
            
        Returns:
            List of search results with metadata
            
        Raises:
            RuntimeError: If search fails
        """
        try:
            collection = self.get_collection()
            
            # Default output fields
            if output_fields is None:
                output_fields = [
                    "text",
                    "document_name",
                    "document_id",
                    "chunk_index",
                    "author",
                    "keywords",
                    "file_type",
                    "language",
                ]
            
            # Build filter expression
            filter_expr = self._build_filter_expression(filters) if filters else None
            
            # Get search parameters
            search_params = get_search_params(
                index_type="HNSW",
                collection_size=collection.num_entities,
                metric_type="COSINE",
            )
            
            # Perform search
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params["params"],
                limit=top_k,
                expr=filter_expr,
                output_fields=output_fields,
            )
            
            # Format results
            formatted_results = []
            for hit in results[0]:
                result = {
                    "id": hit.id,
                    "score": float(hit.score),
                    "distance": float(hit.distance),
                }
                
                # Add output fields
                for field in output_fields:
                    result[field] = hit.entity.get(field)
                
                formatted_results.append(result)
            
            logger.info(
                f"Search completed: {len(formatted_results)} results "
                f"(top_k={top_k}, filters={bool(filters)})"
            )
            
            return formatted_results
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _build_filter_expression(self, filters: Dict[str, Any]) -> str:
        """
        Build Milvus filter expression from dictionary.
        
        Args:
            filters: Filter dictionary
            
        Returns:
            str: Milvus filter expression
        """
        if not filters:
            return ""
        
        expressions = []
        
        for key, value in filters.items():
            if isinstance(value, str):
                # String comparison
                expressions.append(f'{key} == "{value}"')
            elif isinstance(value, (int, float)):
                # Numeric comparison
                expressions.append(f"{key} == {value}")
            elif isinstance(value, list):
                # IN operator
                if all(isinstance(v, str) for v in value):
                    values_str = ", ".join(f'"{v}"' for v in value)
                    expressions.append(f"{key} in [{values_str}]")
                else:
                    values_str = ", ".join(str(v) for v in value)
                    expressions.append(f"{key} in [{values_str}]")
            elif isinstance(value, dict):
                # Range queries
                if "$gte" in value:
                    expressions.append(f"{key} >= {value['$gte']}")
                if "$lte" in value:
                    expressions.append(f"{key} <= {value['$lte']}")
                if "$gt" in value:
                    expressions.append(f"{key} > {value['$gt']}")
                if "$lt" in value:
                    expressions.append(f"{key} < {value['$lt']}")
        
        return " && ".join(expressions) if expressions else ""

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            dict: Collection statistics
        """
        try:
            collection = self.get_collection()
            
            stats = {
                "collection_name": self.collection_name,
                "num_entities": collection.num_entities,
                "num_partitions": len(collection.partitions),
                "loaded": True,
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {
                "collection_name": self.collection_name,
                "error": str(e),
            }


# Global connector instance
_connector: Optional[MilvusConnector] = None


def get_milvus_connector() -> MilvusConnector:
    """
    Get or create global Milvus connector instance.
    
    Returns:
        MilvusConnector: Global connector instance
    """
    global _connector
    
    if _connector is None:
        _connector = MilvusConnector()
    
    return _connector
