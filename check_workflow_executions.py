"""Check workflow executions in database."""
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text
from backend.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Check if workflow_executions table exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'workflow_executions'
        )
    """))
    exists = result.scalar()
    
    if not exists:
        print("❌ workflow_executions table does not exist!")
        sys.exit(1)
    
    print("✅ workflow_executions table exists")
    
    # Count workflow executions
    result = conn.execute(text("SELECT COUNT(*) FROM workflow_executions"))
    count = result.scalar()
    print(f"📊 Total workflow executions: {count}")
    
    if count > 0:
        # Show recent executions
        result = conn.execute(text("""
            SELECT id, workflow_id, status, started_at 
            FROM workflow_executions 
            ORDER BY started_at DESC 
            LIMIT 5
        """))
        print("\n📋 Recent workflow executions:")
        for row in result:
            print(f"  - {row[0]}: workflow={row[1]}, status={row[2]}, started={row[3]}")
    else:
        print("\n⚠️  No workflow executions found!")
        print("Possible reasons:")
        print("1. Workflow was not executed successfully")
        print("2. Execution record was not saved to DB")
        print("3. Commit did not happen")
    
    # Count agent executions for comparison
    result = conn.execute(text("SELECT COUNT(*) FROM agent_executions"))
    agent_count = result.scalar()
    print(f"\n📊 Total agent executions: {agent_count}")
