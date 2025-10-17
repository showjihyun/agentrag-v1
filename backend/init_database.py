"""Initialize database - create all tables."""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database."""
    try:
        logger.info("Importing database modules...")
        from db.database import Base, engine, init_db
        from db.models import (
            User,
            Session,
            Message,
            MessageSource,
            Document,
            BatchUpload,
            Feedback,
            UsageLog,
        )

        logger.info("Creating all tables...")
        init_db()

        logger.info("✅ Database initialized successfully!")
        logger.info(
            f"Tables created: {', '.join([t.name for t in Base.metadata.sorted_tables])}"
        )

        return 0

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
