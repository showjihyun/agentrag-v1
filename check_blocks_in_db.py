"""Check blocks in database."""

import psycopg2
from datetime import datetime

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
    print("Blocks Database Check")
    print("=" * 60)
    
    # Count total blocks
    cur.execute("SELECT COUNT(*) FROM blocks")
    total_count = cur.fetchone()[0]
    print(f"\n📊 Total blocks in database: {total_count}")
    
    if total_count == 0:
        print("\n❌ No blocks found in database!")
    else:
        # Get all blocks
        cur.execute("""
            SELECT id, user_id, name, block_type, is_public, created_at 
            FROM blocks 
            ORDER BY created_at DESC
        """)
        blocks = cur.fetchall()
        
        print(f"\n📋 All blocks ({len(blocks)} total):")
        print("-" * 60)
        for block in blocks:
            block_id, user_id, name, block_type, is_public, created_at = block
            public_str = "🌐 Public" if is_public else "🔒 Private"
            print(f"\n  ID: {block_id}")
            print(f"  Name: {name}")
            print(f"  Type: {block_type}")
            print(f"  User ID: {user_id}")
            print(f"  {public_str}")
            print(f"  Created: {created_at}")
        
        # Check for specific user's blocks
        print("\n" + "=" * 60)
        print("Blocks by User")
        print("=" * 60)
        
        cur.execute("""
            SELECT user_id, COUNT(*) as block_count
            FROM blocks
            GROUP BY user_id
            ORDER BY block_count DESC
        """)
        user_blocks = cur.fetchall()
        
        for user_id, count in user_blocks:
            print(f"\n  User {user_id}: {count} blocks")
    
    # Check recent blocks (last 10)
    print("\n" + "=" * 60)
    print("Recent Blocks (Last 10)")
    print("=" * 60)
    
    cur.execute("""
        SELECT id, name, block_type, created_at 
        FROM blocks 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    recent = cur.fetchall()
    
    if recent:
        for block_id, name, block_type, created_at in recent:
            print(f"\n  {name} ({block_type})")
            print(f"    ID: {block_id}")
            print(f"    Created: {created_at}")
    else:
        print("\n  No blocks found")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
