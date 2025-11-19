"""
Seed basic tools into the database.
Run this script to populate the tools table with essential tools.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now import after path is set
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from db.models import Tool
from config import settings

def seed_tools():
    """Seed essential tools into database."""
    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db: Session = SessionLocal()
    
    try:
        # Check if tools already exist
        existing_count = db.query(Tool).count()
        print(f"📊 Current tools in database: {existing_count}")
        
        # Essential tools to seed
        essential_tools = [
            {
                "id": "http_request",
                "name": "HTTP Request",
                "description": "Make HTTP requests to any API endpoint",
                "category": "api",
                "icon": "globe",
                "is_active": True,
            },
            {
                "id": "calculator",
                "name": "Calculator",
                "description": "Perform mathematical calculations",
                "category": "utility",
                "icon": "calculator",
                "is_active": True,
            },
            {
                "id": "vector_search",
                "name": "Vector Search",
                "description": "Search in vector database",
                "category": "data",
                "icon": "search",
                "is_active": True,
            },
            {
                "id": "web_search",
                "name": "Web Search",
                "description": "Search the web using DuckDuckGo",
                "category": "search",
                "icon": "globe",
                "is_active": True,
            },
            {
                "id": "python_executor",
                "name": "Python Executor",
                "description": "Execute Python code",
                "category": "code",
                "icon": "code",
                "is_active": True,
            },
            {
                "id": "slack",
                "name": "Slack",
                "description": "Send messages to Slack",
                "category": "communication",
                "icon": "message-square",
                "is_active": True,
            },
            {
                "id": "gmail",
                "name": "Gmail",
                "description": "Send and manage emails",
                "category": "communication",
                "icon": "mail",
                "is_active": True,
            },
            {
                "id": "discord",
                "name": "Discord",
                "description": "Send messages to Discord",
                "category": "communication",
                "icon": "message-square",
                "is_active": True,
            },
        ]
        
        added_count = 0
        updated_count = 0
        
        for tool_data in essential_tools:
            # Check if tool exists
            existing_tool = db.query(Tool).filter(Tool.id == tool_data["id"]).first()
            
            if existing_tool:
                # Update existing tool
                for key, value in tool_data.items():
                    if key != "id":
                        setattr(existing_tool, key, value)
                existing_tool.updated_at = datetime.utcnow()
                updated_count += 1
                print(f"✏️  Updated: {tool_data['id']}")
            else:
                # Create new tool
                new_tool = Tool(
                    id=tool_data["id"],
                    name=tool_data["name"],
                    description=tool_data["description"],
                    category=tool_data["category"],
                    icon=tool_data["icon"],
                    is_active=tool_data["is_active"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(new_tool)
                added_count += 1
                print(f"➕ Added: {tool_data['id']}")
        
        db.commit()
        
        print(f"\n✅ Seeding complete!")
        print(f"   Added: {added_count} tools")
        print(f"   Updated: {updated_count} tools")
        print(f"   Total: {db.query(Tool).count()} tools in database")
        
    except Exception as e:
        print(f"❌ Error seeding tools: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding essential tools into database...")
    seed_tools()
