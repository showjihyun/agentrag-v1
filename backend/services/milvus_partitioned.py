"""
Partitioned Milvus Manager

Implements partitioning strategies for improved search performance.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from backend.services.milvus_adaptive import AdaptiveMilvusManager, SearchResult

logger = logging.getLogger(__name__)


class PartitionedMilvusManager(AdaptiveMilvusManager):
    """
    Milvus manager with partitioning support.

    Partition Strategies:
    1. User-based: user_{user_id}
    2. Date-based: date_{YYYY_MM}
    3. Language-based: lang_{ko|en|...}
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._partition_cache = {}

    def create_user_partition(self, user_id: str) -> str:
        """
        Create partition for specific user.

        Args:
            user_id: User identifier

        Returns:
            Partition name
        """
        partition_name = f"user_{user_id}"

        try:
            collection = self.get_collection()

            if not collection.has_partition(partition_name):
                collection.create_partition(partition_name)
                logger.info(f"Created user partition: {partition_name}")
            else:
                logger.debug(f"User partition already exists: {partition_name}")

            return partition_name

        except Exception as e:
            logger.error(f"Failed to create user partition: {e}")
            raise

    def create_date_partition(self, year: int, month: int) -> str:
        """
        Create partition for specific year-month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            Partition name
        """
        partition_name = f"date_{year}_{month:02d}"

        try:
            collection = self.get_collection()

            if not collection.has_partition(partition_name):
                collection.create_partition(partition_name)
                logger.info(f"Created date partition: {partition_name}")
            else:
                logger.debug(f"Date partition already exists: {partition_name}")

            return partition_name

        except Exception as e:
            logger.error(f"Failed to create date partition: {e}")
            raise

    def create_language_partition(self, language: str) -> str:
        """
        Create partition for specific language.

        Args:
            language: Language code (e.g., 'ko', 'en')

        Returns:
            Partition name
        """
        partition_name = f"lang_{language}"

        try:
            collection = self.get_collection()

            if not collection.has_partition(partition_name):
                collection.create_partition(partition_name)
                logger.info(f"Created language partition: {partition_name}")
            else:
                logger.debug(f"Language partition already exists: {partition_name}")

            return partition_name

        except Exception as e:
            logger.error(f"Failed to create language partition: {e}")
            raise

    async def search_in_partition(
        self,
        query_embedding: List[float],
        partition_name: str,
        top_k: int = 5,
        filters: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Search within specific partition.

        Args:
            query_embedding: Query vector
            partition_name: Partition to search in
            top_k: Number of results
            filters: Optional filter expression
            output_fields: Fields to include

        Returns:
            List of search results
        """
        try:
            collection = self.get_collection()
            await self._ensure_collection_loaded()

            # Get search parameters
            collection_size = collection.num_entities
            index_info = collection.indexes[0] if collection.indexes else None
            index_type = (
                index_info.params.get("index_type", "HNSW") if index_info else "HNSW"
            )

            from models.milvus_schema_korean import get_adaptive_search_params

            search_params = get_adaptive_search_params(
                index_type=index_type,
                collection_size=collection_size,
                query_complexity=0.5,  # Default balanced
            )

            # Default output fields
            if output_fields is None:
                output_fields = [
                    "id",
                    "document_id",
                    "text",
                    "document_name",
                    "chunk_index",
                    "file_type",
                    "upload_date",
                ]

            logger.info(f"Searching in partition: {partition_name}, top_k={top_k}")

            # Search in specific partition
            search_results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filters,
                output_fields=output_fields,
                partition_names=[partition_name],  # Partition-specific search
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
                            "file_type": hit.entity.get("file_type"),
                            "upload_date": hit.entity.get("upload_date"),
                            "partition": partition_name,
                        },
                    )
                    results.append(result)

            logger.debug(
                f"Partition search returned {len(results)} results "
                f"from {partition_name}"
            )

            return results

        except Exception as e:
            logger.error(f"Partition search failed: {e}")
            raise

    async def search_in_date_range(
        self,
        query_embedding: List[float],
        start_date: str,
        end_date: str,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """
        Search within date range using date partitions.

        Args:
            query_embedding: Query vector
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            top_k: Number of results

        Returns:
            List of search results
        """
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Get partition names for date range
        partitions = []
        current = start
        while current <= end:
            partition_name = f"date_{current.year}_{current.month:02d}"
            partitions.append(partition_name)

            # Move to next month
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)

        logger.info(
            f"Searching in date range: {start_date} to {end_date}, "
            f"partitions: {partitions}"
        )

        # Search across multiple partitions
        all_results = []
        for partition in partitions:
            try:
                results = await self.search_in_partition(
                    query_embedding=query_embedding,
                    partition_name=partition,
                    top_k=top_k,
                )
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Failed to search partition {partition}: {e}")

        # Sort by score and return top_k
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]

    def list_partitions(self) -> List[str]:
        """
        List all partitions in collection.

        Returns:
            List of partition names
        """
        try:
            collection = self.get_collection()
            partitions = [p.name for p in collection.partitions]
            logger.debug(f"Found {len(partitions)} partitions")
            return partitions

        except Exception as e:
            logger.error(f"Failed to list partitions: {e}")
            return []

    def get_partition_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all partitions.

        Returns:
            Dictionary with partition statistics
        """
        try:
            collection = self.get_collection()
            collection.load()

            partitions = collection.partitions
            stats = {"total_partitions": len(partitions), "partitions": []}

            total_entities = 0
            for partition in partitions:
                partition_info = {
                    "name": partition.name,
                    "num_entities": partition.num_entities,
                }
                stats["partitions"].append(partition_info)
                total_entities += partition.num_entities

            stats["total_entities"] = total_entities
            stats["avg_partition_size"] = (
                total_entities // len(partitions) if len(partitions) > 0 else 0
            )

            # Count by type
            user_partitions = [p for p in partitions if p.name.startswith("user_")]
            date_partitions = [p for p in partitions if p.name.startswith("date_")]
            lang_partitions = [p for p in partitions if p.name.startswith("lang_")]

            stats["partition_types"] = {
                "user": len(user_partitions),
                "date": len(date_partitions),
                "language": len(lang_partitions),
                "other": len(partitions)
                - len(user_partitions)
                - len(date_partitions)
                - len(lang_partitions),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get partition stats: {e}")
            return {"error": str(e)}

    def cleanup_old_partitions(self, months: int = 6) -> int:
        """
        Delete date partitions older than specified months.

        Args:
            months: Number of months to keep

        Returns:
            Number of partitions deleted
        """
        try:
            collection = self.get_collection()
            cutoff_date = datetime.now() - timedelta(days=months * 30)

            deleted_count = 0
            for partition in collection.partitions:
                if partition.name.startswith("date_"):
                    # Parse date from partition name
                    try:
                        parts = partition.name.split("_")
                        year = int(parts[1])
                        month = int(parts[2])
                        partition_date = datetime(year, month, 1)

                        if partition_date < cutoff_date:
                            logger.info(f"Deleting old partition: {partition.name}")
                            collection.drop_partition(partition.name)
                            deleted_count += 1
                    except (IndexError, ValueError) as e:
                        logger.warning(
                            f"Failed to parse partition date: {partition.name}"
                        )

            logger.info(f"Deleted {deleted_count} old partitions")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old partitions: {e}")
            return 0

    def migrate_to_partitions(
        self, strategy: str = "user", batch_size: int = 1000
    ) -> Dict[str, int]:
        """
        Migrate existing data to partitions.

        Args:
            strategy: Partitioning strategy ('user', 'date', 'language')
            batch_size: Number of entities to process per batch

        Returns:
            Dictionary with migration statistics
        """
        logger.info(f"Starting partition migration: strategy={strategy}")

        # This is a placeholder for the migration logic
        # Actual implementation would:
        # 1. Query all entities from default partition
        # 2. Group by partition key (user_id, date, language)
        # 3. Create partitions as needed
        # 4. Insert entities into appropriate partitions
        # 5. Delete from default partition

        stats = {
            "total_entities": 0,
            "partitions_created": 0,
            "entities_migrated": 0,
            "errors": 0,
        }

        logger.warning("Partition migration not fully implemented yet")
        return stats
