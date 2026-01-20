#!/usr/bin/env python
"""Comprehensive database schema validation."""

import os
import sys
from pathlib import Path
import dotenv

# Load environment variables
dotenv.load_dotenv('.env')

from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import sessionmaker

# Get DATABASE_URL from environment
# Docker: postgres service is at localhost:5433, database name is agenticrag
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/agenticrag')

def validate_schema():
    """Validate database schema against model definitions."""
    
    print("=" * 80)
    print("DATABASE SCHEMA VALIDATION")
    print("=" * 80)
    
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Get all tables
        all_tables = inspector.get_table_names()
        print(f"\n✓ Total tables in database: {len(all_tables)}")
        
        # Define expected tables based on models
        expected_tables = {
            # Core tables
            'users': ['id', 'email', 'username', 'password_hash', 'created_at', 'updated_at'],
            'conversations': ['id', 'user_id', 'title', 'created_at', 'updated_at'],
            'documents': ['id', 'user_id', 'filename', 'created_at', 'updated_at'],
            'feedback': ['id', 'conversation_id', 'user_id', 'rating', 'created_at'],
            
            # Agent Builder tables
            'agents': ['id', 'user_id', 'name', 'agent_type', 'llm_provider', 'llm_model', 
                      'configuration', 'context_items', 'mcp_servers', 'created_at', 'updated_at'],
            'agent_versions': ['id', 'agent_id', 'version_number', 'created_at'],
            'agent_tools': ['id', 'agent_id', 'tool_id', 'created_at'],
            'agent_templates': ['id', 'name', 'description', 'created_at'],
            'agent_knowledgebases': ['id', 'agent_id', 'knowledge_base_id'],
            'agent_executions': ['id', 'agent_id', 'user_id', 'status', 'created_at'],
            'agent_memories': ['id', 'agent_id', 'memory_type', 'content', 'created_at'],
            
            # Organization & Multi-tenancy
            'organizations': ['id', 'name', 'created_at', 'updated_at'],
            'teams': ['id', 'organization_id', 'name', 'created_at'],
            
            # Plugin System
            'plugin_registry': ['id', 'name', 'version', 'manifest', 'created_at'],
            'plugin_configurations': ['id', 'plugin_id', 'settings', 'created_at'],
            'plugin_metrics': ['id', 'plugin_id', 'metric_name', 'recorded_at'],
            'plugin_dependencies': ['id', 'plugin_id', 'dependency_name'],
            'plugin_audit_logs': ['id', 'plugin_id', 'action', 'timestamp'],
            'plugin_security_scans': ['id', 'plugin_id', 'scan_type', 'scan_result'],
            
            # Marketplace
            'marketplace_purchases': ['id', 'user_id', 'agent_id', 'created_at'],
            'marketplace_reviews': ['id', 'user_id', 'agent_id', 'rating', 'created_at'],
            'marketplace_revenue': ['id', 'agent_id', 'amount', 'created_at'],
            
            # Credit System
            'credits': ['id', 'user_id', 'amount', 'created_at'],
            
            # Rate Limiting
            'rate_limit_configs': ['id', 'user_id', 'limit_type', 'created_at'],
            
            # Bookmarks
            'bookmarks': ['id', 'user_id', 'conversation_id', 'created_at'],
            
            # Notifications
            'notifications': ['id', 'user_id', 'message', 'created_at'],
            
            # Conversation Shares
            'conversation_shares': ['id', 'conversation_id', 'shared_with_user_id', 'created_at'],
            
            # API Keys
            'api_keys': ['id', 'user_id', 'key_hash', 'created_at'],
            
            # Event Store
            'event_store': ['id', 'event_type', 'data', 'created_at'],
            
            # Flows
            'agentflows': ['id', 'user_id', 'name', 'created_at'],
            'agentflow_agents': ['id', 'agentflow_id', 'agent_id'],
            'agentflow_edges': ['id', 'agentflow_id', 'source_id', 'target_id'],
            
            # Knowledge Graph
            'knowledge_graphs': ['id', 'user_id', 'name', 'created_at'],
            
            # Tool Execution
            'tool_executions': ['id', 'agent_id', 'tool_name', 'status', 'created_at'],
            
            # Query Logs
            'query_logs': ['id', 'user_id', 'query', 'created_at'],
            
            # User Settings
            'user_settings': ['id', 'user_id', 'settings', 'created_at'],
        }
        
        print("\n" + "=" * 80)
        print("TABLE VALIDATION")
        print("=" * 80)
        
        missing_tables = []
        existing_tables = []
        
        for table_name, expected_cols in expected_tables.items():
            if table_name in all_tables:
                existing_tables.append(table_name)
                print(f"✅ {table_name}")
                
                # Check columns
                columns = inspector.get_columns(table_name)
                col_names = {col['name'] for col in columns}
                
                missing_cols = set(expected_cols) - col_names
                if missing_cols:
                    print(f"   ⚠️  Missing columns: {missing_cols}")
                else:
                    print(f"   ✓ All expected columns present ({len(col_names)} total)")
            else:
                missing_tables.append(table_name)
                print(f"❌ {table_name} - MISSING")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Expected tables: {len(expected_tables)}")
        print(f"Existing tables: {len(existing_tables)}")
        print(f"Missing tables: {len(missing_tables)}")
        
        if missing_tables:
            print(f"\n⚠️  Missing tables ({len(missing_tables)}):")
            for table in missing_tables:
                print(f"   • {table}")
        else:
            print("\n✅ All expected tables exist!")
        
        # Check for unexpected tables
        print("\n" + "=" * 80)
        print("UNEXPECTED TABLES (in DB but not in expected list)")
        print("=" * 80)
        
        expected_table_names = set(expected_tables.keys())
        unexpected = set(all_tables) - expected_table_names
        
        if unexpected:
            print(f"Found {len(unexpected)} unexpected tables:")
            for table in sorted(unexpected):
                if not table.startswith('alembic'):  # Ignore alembic tables
                    print(f"   • {table}")
        else:
            print("No unexpected tables found")
        
        # Check critical columns in key tables
        print("\n" + "=" * 80)
        print("CRITICAL COLUMNS CHECK")
        print("=" * 80)
        
        critical_checks = {
            'agents': {
                'context_items': 'JSONB',
                'mcp_servers': 'JSONB',
                'configuration': 'JSONB',
            },
            'users': {
                'email': 'VARCHAR',
                'username': 'VARCHAR',
            },
            'conversations': {
                'user_id': 'UUID',
                'title': 'VARCHAR',
            },
        }
        
        for table_name, cols_to_check in critical_checks.items():
            if table_name in all_tables:
                print(f"\n{table_name}:")
                columns = inspector.get_columns(table_name)
                col_dict = {col['name']: str(col['type']) for col in columns}
                
                for col_name, expected_type in cols_to_check.items():
                    if col_name in col_dict:
                        actual_type = col_dict[col_name]
                        if expected_type.lower() in actual_type.lower():
                            print(f"  ✅ {col_name}: {actual_type}")
                        else:
                            print(f"  ⚠️  {col_name}: {actual_type} (expected {expected_type})")
                    else:
                        print(f"  ❌ {col_name}: MISSING")
        
        # Check indexes
        print("\n" + "=" * 80)
        print("INDEX CHECK")
        print("=" * 80)
        
        critical_indexes = {
            'agents': ['ix_agents_user_type', 'ix_agents_user_created'],
            'users': ['ix_users_email'],
            'conversations': ['ix_conversations_user_id'],
        }
        
        for table_name, expected_indexes in critical_indexes.items():
            if table_name in all_tables:
                print(f"\n{table_name}:")
                indexes = inspector.get_indexes(table_name)
                index_names = {idx['name'] for idx in indexes}
                
                for idx_name in expected_indexes:
                    if idx_name in index_names:
                        print(f"  ✅ {idx_name}")
                    else:
                        print(f"  ⚠️  {idx_name} - NOT FOUND")
        
        # Check foreign keys
        print("\n" + "=" * 80)
        print("FOREIGN KEY CHECK")
        print("=" * 80)
        
        critical_fks = {
            'agents': 'user_id',
            'conversations': 'user_id',
            'documents': 'user_id',
            'feedback': 'user_id',
        }
        
        for table_name, fk_col in critical_fks.items():
            if table_name in all_tables:
                print(f"\n{table_name}:")
                fks = inspector.get_foreign_keys(table_name)
                fk_cols = {fk['constrained_columns'][0] for fk in fks if fk['constrained_columns']}
                
                if fk_col in fk_cols:
                    print(f"  ✅ {fk_col} has foreign key")
                else:
                    print(f"  ⚠️  {fk_col} - NO FOREIGN KEY")
        
        print("\n" + "=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    validate_schema()
