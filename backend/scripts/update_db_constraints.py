#!/usr/bin/env python3
"""
Update database constraints for workflow nodes and edges
Run this script to fix the CHECK constraint violation error
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings

def update_constraints():
    """Update database constraints"""
    
    print("=" * 80)
    print("DATABASE CONSTRAINT UPDATE")
    print("=" * 80)
    print()
    
    # Create engine
    print(f"📡 Connecting to database...")
    print(f"   Host: {settings.POSTGRES_HOST}")
    print(f"   Port: {settings.POSTGRES_PORT}")
    print(f"   Database: {settings.POSTGRES_DB}")
    print()
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("✅ Connected successfully!")
            print()
            
            # Start transaction
            trans = conn.begin()
            
            try:
                # 1. Drop old node_type constraint
                print("🔧 Dropping old node_type constraint...")
                conn.execute(text("""
                    ALTER TABLE workflow_nodes 
                    DROP CONSTRAINT IF EXISTS check_node_type_valid
                """))
                print("   ✅ Old constraint dropped")
                print()
                
                # 2. Add new node_type constraint
                print("🔧 Adding new node_type constraint (27 types)...")
                conn.execute(text("""
                    ALTER TABLE workflow_nodes 
                    ADD CONSTRAINT check_node_type_valid 
                    CHECK (node_type IN (
                        'start', 'end', 'agent', 'block', 'condition', 'switch',
                        'loop', 'parallel', 'delay', 'merge', 'http_request', 'code',
                        'slack', 'discord', 'email', 'google_drive', 's3', 'database',
                        'memory', 'human_approval', 'consensus', 'manager_agent',
                        'webhook_trigger', 'schedule_trigger', 'webhook_response',
                        'trigger', 'try_catch', 'control'
                    ))
                """))
                print("   ✅ New constraint added")
                print()
                
                # 3. Drop old edge_type constraint (if exists)
                print("🔧 Updating edge_type constraint...")
                try:
                    conn.execute(text("""
                        ALTER TABLE workflow_edges 
                        DROP CONSTRAINT IF EXISTS check_edge_type_valid
                    """))
                    
                    conn.execute(text("""
                        ALTER TABLE workflow_edges 
                        ADD CONSTRAINT check_edge_type_valid 
                        CHECK (edge_type IN ('normal', 'conditional', 'true', 'false', 'custom'))
                    """))
                    print("   ✅ Edge constraint updated")
                except Exception as e:
                    print(f"   ⚠️  Edge constraint update skipped: {str(e)}")
                print()
                
                # Commit transaction
                trans.commit()
                print("=" * 80)
                print("✅ ALL CONSTRAINTS UPDATED SUCCESSFULLY!")
                print("=" * 80)
                print()
                
                # Verify
                print("🔍 Verifying constraints...")
                result = conn.execute(text("""
                    SELECT conname, pg_get_constraintdef(oid) 
                    FROM pg_constraint 
                    WHERE conrelid = 'workflow_nodes'::regclass 
                    AND conname = 'check_node_type_valid'
                """))
                
                for row in result:
                    print(f"   Constraint: {row[0]}")
                    constraint_def = row[1]
                    if 'start' in constraint_def and 'end' in constraint_def:
                        print("   ✅ Constraint includes 'start' and 'end' types")
                    else:
                        print("   ⚠️  Constraint might not be correct")
                print()
                
                print("=" * 80)
                print("🎉 DATABASE UPDATE COMPLETE!")
                print("=" * 80)
                print()
                print("Next steps:")
                print("1. Restart your backend server")
                print("2. Try creating a workflow again")
                print("3. It should work now! ✨")
                print()
                
                return True
                
            except Exception as e:
                trans.rollback()
                print()
                print("=" * 80)
                print("❌ ERROR DURING UPDATE")
                print("=" * 80)
                print(f"Error: {str(e)}")
                print()
                print("Possible solutions:")
                print("1. Check if PostgreSQL is running")
                print("2. Check database credentials in .env")
                print("3. Try running SQL manually (see WORKFLOW_DATABASE_MIGRATION.md)")
                print()
                return False
                
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ CONNECTION ERROR")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        print("Possible solutions:")
        print("1. Check if PostgreSQL is running:")
        print("   docker ps  # or")
        print("   pg_isready -h localhost -p 5433")
        print()
        print("2. Check database credentials in backend/.env:")
        print("   POSTGRES_HOST=localhost")
        print("   POSTGRES_PORT=5433")
        print("   POSTGRES_USER=postgres")
        print("   POSTGRES_PASSWORD=your_password")
        print("   POSTGRES_DB=agenticrag")
        print()
        return False


if __name__ == "__main__":
    success = update_constraints()
    sys.exit(0 if success else 1)
