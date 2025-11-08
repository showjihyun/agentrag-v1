"""Add youtube_search tool directly using SQL."""

import psycopg2
from datetime import datetime
import json

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="agenticrag",
    user="postgres",
    password="postgres"
)

try:
    cur = conn.cursor()
    
    print("=" * 60)
    print("YouTube Search Tool - Direct Database Insert")
    print("=" * 60)
    
    # Check current tools
    cur.execute("SELECT COUNT(*) FROM tools")
    tool_count = cur.fetchone()[0]
    print(f"\n📊 Current tools in database: {tool_count}")
    
    # Check if youtube_search exists
    cur.execute("SELECT id, name FROM tools WHERE id = 'youtube_search'")
    existing = cur.fetchone()
    
    if existing:
        print(f"\n✅ youtube_search already exists: {existing[1]}")
    else:
        print(f"\n❌ youtube_search NOT FOUND")
        print(f"➕ Creating youtube_search tool...")
        
        # Insert youtube_search tool
        input_schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for YouTube videos",
                    "required": True
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "required": False
                }
            },
            "required": ["query"]
        }
        
        output_schema = {
            "type": "object",
            "properties": {
                "videos": {
                    "type": "array",
                    "description": "List of video results"
                }
            }
        }
        
        cur.execute("""
            INSERT INTO tools (
                id, name, description, category,
                input_schema, output_schema,
                implementation_type, implementation_ref,
                requires_auth, is_builtin,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            'youtube_search',
            'YouTube Search',
            'Search YouTube videos using YouTube Data API',
            'search',
            json.dumps(input_schema),
            json.dumps(output_schema),
            'builtin',  # Changed from 'registry' to 'builtin'
            'ToolRegistry.youtube_search',
            True,
            True,
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        conn.commit()
        print(f"✅ Successfully created youtube_search tool!")
    
    # Verify
    cur.execute("SELECT id, name, category FROM tools WHERE id = 'youtube_search'")
    result = cur.fetchone()
    if result:
        print(f"\n✅ Verification successful!")
        print(f"   ID: {result[0]}")
        print(f"   Name: {result[1]}")
        print(f"   Category: {result[2]}")
    
    # Show all tools
    cur.execute("SELECT id, name, category FROM tools ORDER BY category, name")
    all_tools = cur.fetchall()
    print(f"\n📋 All tools in database ({len(all_tools)} total):")
    for tool in all_tools:
        print(f"  - {tool[0]}: {tool[1]} ({tool[2]})")
    
    print("\n" + "=" * 60)
    print("✅ Done! You can now use youtube_search in agents.")
    print("=" * 60)
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
