"""
Automatic Database Maintenance

Provides automated maintenance tasks for PostgreSQL and Milvus.
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
from backend.db.database import engine
from backend.services.milvus import MilvusManager
from backend.config import settings

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class AutoMaintenance:
    """
    Automated maintenance for databases.

    Tasks:
    - PostgreSQL VACUUM
    - PostgreSQL ANALYZE
    - PostgreSQL REINDEX
    - Milvus Compaction
    - Statistics collection
    """

    def __init__(self):
        self.stats = {
            "start_time": datetime.now(),
            "tasks_completed": [],
            "tasks_failed": [],
        }

    def vacuum_all_tables(self, analyze: bool = True) -> Dict[str, Any]:
        """
        Run VACUUM on all tables.

        Args:
            analyze: Also run ANALYZE to update statistics

        Returns:
            Dictionary with vacuum results
        """
        logger.info("Starting VACUUM operation...")

        try:
            with engine.connect() as conn:
                # Get all user tables
                result = conn.execute(
                    text(
                        """
                    SELECT schemaname, tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """
                    )
                )

                tables = result.fetchall()
                logger.info(f"Found {len(tables)} tables to vacuum")

                vacuumed_tables = []
                for schema, table in tables:
                    try:
                        command = (
                            f"VACUUM {'ANALYZE' if analyze else ''} {schema}.{table}"
                        )
                        logger.info(f"Running: {command}")

                        conn.execute(text(command))
                        conn.commit()

                        vacuumed_tables.append(table)
                        logger.info(f"✅ Vacuumed: {table}")

                    except Exception as e:
                        logger.error(f"❌ Failed to vacuum {table}: {e}")
                        self.stats["tasks_failed"].append(f"vacuum_{table}")

                result = {
                    "success": True,
                    "tables_vacuumed": len(vacuumed_tables),
                    "tables": vacuumed_tables,
                }

                self.stats["tasks_completed"].append("vacuum")
                logger.info(f"VACUUM completed: {len(vacuumed_tables)} tables")

                return result

        except Exception as e:
            logger.error(f"VACUUM operation failed: {e}")
            self.stats["tasks_failed"].append("vacuum")
            return {"success": False, "error": str(e)}

    def reindex_all(self, concurrent: bool = True) -> Dict[str, Any]:
        """
        Rebuild all indexes.

        Args:
            concurrent: Use REINDEX CONCURRENTLY (no table locks)

        Returns:
            Dictionary with reindex results
        """
        logger.info("Starting REINDEX operation...")

        try:
            with engine.connect() as conn:
                # Get all indexes
                result = conn.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    AND indexname NOT LIKE 'pg_%'
                    ORDER BY tablename, indexname
                """
                    )
                )

                indexes = result.fetchall()
                logger.info(f"Found {len(indexes)} indexes to rebuild")

                reindexed = []
                for schema, table, index in indexes:
                    try:
                        command = f"REINDEX {'CONCURRENTLY' if concurrent else ''} INDEX {schema}.{index}"
                        logger.info(f"Running: {command}")

                        conn.execute(text(command))
                        conn.commit()

                        reindexed.append(index)
                        logger.info(f"✅ Reindexed: {index}")

                    except Exception as e:
                        logger.error(f"❌ Failed to reindex {index}: {e}")
                        self.stats["tasks_failed"].append(f"reindex_{index}")

                result = {
                    "success": True,
                    "indexes_rebuilt": len(reindexed),
                    "indexes": reindexed,
                }

                self.stats["tasks_completed"].append("reindex")
                logger.info(f"REINDEX completed: {len(reindexed)} indexes")

                return result

        except Exception as e:
            logger.error(f"REINDEX operation failed: {e}")
            self.stats["tasks_failed"].append("reindex")
            return {"success": False, "error": str(e)}

    def compact_milvus_collection(self) -> Dict[str, Any]:
        """
        Compact Milvus collection.

        Returns:
            Dictionary with compaction results
        """
        logger.info("Starting Milvus compaction...")

        try:
            manager = MilvusManager(
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                collection_name=settings.MILVUS_COLLECTION_NAME,
            )

            manager.connect()

            try:
                collection = manager.get_collection()

                # Get size before compaction
                size_before = collection.num_entities

                logger.info(f"Compacting collection: {collection.name}")
                collection.compact()

                # Wait for compaction to complete
                logger.info("Waiting for compaction to complete...")
                collection.wait_for_compaction_completed()

                # Get size after compaction
                size_after = collection.num_entities

                result = {
                    "success": True,
                    "collection": collection.name,
                    "entities_before": size_before,
                    "entities_after": size_after,
                }

                self.stats["tasks_completed"].append("compact")
                logger.info(f"Compaction completed: {collection.name}")

                return result

            finally:
                manager.disconnect()

        except Exception as e:
            logger.error(f"Milvus compaction failed: {e}")
            self.stats["tasks_failed"].append("compact")
            return {"success": False, "error": str(e)}

    def update_statistics(self) -> Dict[str, Any]:
        """
        Update database statistics.

        Returns:
            Dictionary with statistics update results
        """
        logger.info("Updating database statistics...")

        try:
            with engine.connect() as conn:
                # Run ANALYZE on all tables
                conn.execute(text("ANALYZE"))
                conn.commit()

                result = {
                    "success": True,
                    "message": "Statistics updated for all tables",
                }

                self.stats["tasks_completed"].append("analyze")
                logger.info("Statistics update completed")

                return result

        except Exception as e:
            logger.error(f"Statistics update failed: {e}")
            self.stats["tasks_failed"].append("analyze")
            return {"success": False, "error": str(e)}

    def cleanup_old_data(self, days: int = 90) -> Dict[str, Any]:
        """
        Cleanup old data (placeholder).

        Args:
            days: Number of days to keep

        Returns:
            Dictionary with cleanup results
        """
        logger.info(f"Cleaning up data older than {days} days...")

        # Placeholder for cleanup logic
        # Actual implementation would delete:
        # - Old sessions
        # - Old messages
        # - Old logs
        # - Old temporary data

        result = {"success": True, "message": "Cleanup not implemented yet"}

        logger.info("Cleanup completed")
        return result

    def get_summary(self) -> Dict[str, Any]:
        """
        Get maintenance summary.

        Returns:
            Dictionary with maintenance summary
        """
        end_time = datetime.now()
        duration = (end_time - self.stats["start_time"]).total_seconds()

        return {
            "start_time": self.stats["start_time"].isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "tasks_completed": self.stats["tasks_completed"],
            "tasks_failed": self.stats["tasks_failed"],
            "success_rate": (
                len(self.stats["tasks_completed"])
                / (len(self.stats["tasks_completed"]) + len(self.stats["tasks_failed"]))
                * 100
                if (
                    len(self.stats["tasks_completed"]) + len(self.stats["tasks_failed"])
                )
                > 0
                else 0
            ),
        }


def main():
    """Main entry point for maintenance script."""
    import argparse

    parser = argparse.ArgumentParser(description="Database Maintenance")
    parser.add_argument(
        "task",
        choices=["vacuum", "reindex", "compact", "analyze", "all"],
        help="Maintenance task to run",
    )
    parser.add_argument(
        "--no-analyze", action="store_true", help="Skip ANALYZE when running VACUUM"
    )
    parser.add_argument(
        "--no-concurrent",
        action="store_true",
        help="Skip CONCURRENTLY when running REINDEX",
    )

    args = parser.parse_args()

    maintenance = AutoMaintenance()

    logger.info("=" * 60)
    logger.info("DATABASE MAINTENANCE")
    logger.info("=" * 60)

    try:
        if args.task == "vacuum" or args.task == "all":
            maintenance.vacuum_all_tables(analyze=not args.no_analyze)

        if args.task == "reindex" or args.task == "all":
            maintenance.reindex_all(concurrent=not args.no_concurrent)

        if args.task == "compact" or args.task == "all":
            maintenance.compact_milvus_collection()

        if args.task == "analyze":
            maintenance.update_statistics()

        # Print summary
        summary = maintenance.get_summary()

        logger.info("=" * 60)
        logger.info("MAINTENANCE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Duration: {summary['duration_seconds']:.2f}s")
        logger.info(f"Tasks completed: {len(summary['tasks_completed'])}")
        logger.info(f"Tasks failed: {len(summary['tasks_failed'])}")
        logger.info(f"Success rate: {summary['success_rate']:.1f}%")

        if summary["tasks_failed"]:
            logger.warning(f"Failed tasks: {', '.join(summary['tasks_failed'])}")
            return 1
        else:
            logger.info("✅ All tasks completed successfully!")
            return 0

    except Exception as e:
        logger.error(f"Maintenance failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
