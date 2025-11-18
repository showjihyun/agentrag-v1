"""Check if executions are being saved to database"""

import sys
sys.path.insert(0, 'backend')

from backend.db.database import SessionLocal
from backend.db.models.agent_builder import AgentExecution
from sqlalchemy import inspect

def check_executions():
    db = SessionLocal()
    try:
        # Check if table exists
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        print(f"📊 Available tables: {len(tables)}")
        
        if 'agent_executions' in tables:
            print("✅ agent_executions table exists")
            
            # Get columns
            columns = inspector.get_columns('agent_executions')
            print(f"\n📋 Columns in agent_executions:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # Count records
            count = db.query(AgentExecution).count()
            print(f"\n📈 Total executions in DB: {count}")
            
            if count > 0:
                # Get latest 5
                latest = db.query(AgentExecution).order_by(
                    AgentExecution.started_at.desc()
                ).limit(5).all()
                
                print(f"\n🔍 Latest {len(latest)} executions:")
                for ex in latest:
                    print(f"  - ID: {ex.id}")
                    print(f"    Agent: {ex.agent_id}")
                    print(f"    User: {ex.user_id}")
                    print(f"    Status: {ex.status}")
                    print(f"    Started: {ex.started_at}")
                    print()
            else:
                print("\n⚠️  No executions found in database!")
                print("   This means executions are not being saved.")
        else:
            print("❌ agent_executions table does NOT exist!")
            print("   You need to run database migrations.")
            print("\n   Run: cd backend && alembic upgrade head")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_executions()
