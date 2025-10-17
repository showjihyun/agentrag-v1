"""
Simple script to create all database tables.
Run from the project root directory.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import Base, engine
from backend.db.models.user import User
from backend.db.models.conversation import Session, Message, MessageSource
from backend.db.models.document import Document, BatchUpload
from backend.db.models.feedback import AnswerFeedback
from backend.db.models.usage import UsageLog


def create_all_tables():
    """Create all tables in the database."""
    print("Creating all database tables...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")

        # List created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    create_all_tables()
