"""Add youtube_search tool to database."""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models.agent_builder import Tool
from datetime import datetime

def check_and_add_youtube_tool():
    """Check if youtube_search tool exists and add if missing."""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("YouTube Search Tool - Database Check")
        print("=" * 60)
        
        # Check all tools in database
        all_tools = db.query(Tool).all()
        print(f"\n📊 Current tools in database: {len(all_tools)}")
        
        if all_tools:
            print("\n📋 Available tools:")
            for tool in all_tools:
                print(f"  - {tool.id}: {tool.name}")
        
        # Check if youtube_search exists
        youtube_tool = db.query(Tool).filter(Tool.id == "youtube_search").first()
        
        if youtube_tool:
            print(f"\n✅ youtube_search tool already exists!")
            print(f"   Name: {youtube_tool.name}")
            print(f"   Description: {youtube_tool.description}")
            print(f"   Category: {youtube_tool.category}")
            return
        
        print(f"\n❌ youtube_search tool NOT FOUND in database")
        print(f"\n➕ Creating youtube_search tool...")
        
        # Create youtube_search tool
        new_tool = Tool(
            id="youtube_search",
            name="YouTube Search",
            description="Search YouTube videos using YouTube Data API. Returns video titles, descriptions, and URLs.",
            category="search",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for YouTube videos",
                        "required": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "required": False
                    }
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "videos": {
                        "type": "array",
                        "description": "List of video results"
                    }
                }
            },
            implementation_type="registry",
            implementation_ref="ToolRegistry.youtube_search",
            requires_auth=True,
            is_builtin=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_tool)
        db.commit()
        
        print(f"✅ Successfully created youtube_search tool!")
        
        # Verify
        verify_tool = db.query(Tool).filter(Tool.id == "youtube_search").first()
        if verify_tool:
            print(f"\n✅ Verification successful!")
            print(f"   ID: {verify_tool.id}")
            print(f"   Name: {verify_tool.name}")
            print(f"   Category: {verify_tool.category}")
        
        # Show updated tool count
        updated_count = db.query(Tool).count()
        print(f"\n📊 Total tools in database: {updated_count}")
        
        print("\n" + "=" * 60)
        print("✅ Done! You can now use youtube_search tool in agents.")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_and_add_youtube_tool()
