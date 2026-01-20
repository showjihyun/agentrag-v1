#!/usr/bin/env python
"""Export current database schema to SQL file."""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment variables
dotenv.load_dotenv('.env')

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/agenticrag')


def export_schema():
    """Export database schema to SQL file."""
    
    print("=" * 80)
    print("DATABASE SCHEMA EXPORT")
    print("=" * 80)
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Create output directory
        output_dir = Path(__file__).parent.parent / 'schemas'
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'schema_{timestamp}.sql'
        
        print(f"\n✓ Exporting schema to: {output_file}")
        
        with engine.connect() as conn:
            # Get schema using pg_dump-like approach
            result = conn.execute(text("""
                SELECT 
                    'CREATE TABLE ' || table_name || ' (' || 
                    string_agg(
                        column_name || ' ' || data_type || 
                        CASE WHEN character_maximum_length IS NOT NULL 
                            THEN '(' || character_maximum_length || ')' 
                            ELSE '' 
                        END ||
                        CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END,
                        ', '
                    ) || ');' as create_statement
                FROM information_schema.columns
                WHERE table_schema = 'public'
                GROUP BY table_name
                ORDER BY table_name;
            """))
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"-- Database Schema Export\n")
                f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: agenticrag\n")
                f.write(f"-- Total Tables: {result.rowcount}\n")
                f.write("\n")
                f.write("-- ============================================\n")
                f.write("-- DROP EXISTING TABLES (if needed)\n")
                f.write("-- ============================================\n\n")
                
                # Get all tables
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                
                # Write DROP statements
                for table in reversed(tables):
                    f.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")
                
                f.write("\n")
                f.write("-- ============================================\n")
                f.write("-- CREATE TABLES\n")
                f.write("-- ============================================\n\n")
                
                # Write CREATE statements for each table
                for table in tables:
                    f.write(f"\n-- Table: {table}\n")
                    f.write(f"-- ============================================\n")
                    
                    # Get columns
                    columns = inspector.get_columns(table)
                    col_defs = []
                    
                    for col in columns:
                        col_def = f"    {col['name']} {col['type']}"
                        if not col['nullable']:
                            col_def += " NOT NULL"
                        if col.get('default'):
                            col_def += f" DEFAULT {col['default']}"
                        col_defs.append(col_def)
                    
                    # Get primary key
                    pk = inspector.get_pk_constraint(table)
                    if pk and pk['constrained_columns']:
                        pk_cols = ', '.join(pk['constrained_columns'])
                        col_defs.append(f"    PRIMARY KEY ({pk_cols})")
                    
                    # Get foreign keys
                    fks = inspector.get_foreign_keys(table)
                    for fk in fks:
                        fk_cols = ', '.join(fk['constrained_columns'])
                        ref_table = fk['referred_table']
                        ref_cols = ', '.join(fk['referred_columns'])
                        on_delete = fk.get('ondelete', 'NO ACTION')
                        col_defs.append(
                            f"    FOREIGN KEY ({fk_cols}) REFERENCES {ref_table}({ref_cols}) ON DELETE {on_delete}"
                        )
                    
                    # Get unique constraints
                    uniques = inspector.get_unique_constraints(table)
                    for uq in uniques:
                        uq_cols = ', '.join(uq['column_names'])
                        uq_name = uq.get('name', f'uq_{table}')
                        col_defs.append(f"    CONSTRAINT {uq_name} UNIQUE ({uq_cols})")
                    
                    # Write CREATE TABLE
                    f.write(f"CREATE TABLE {table} (\n")
                    f.write(',\n'.join(col_defs))
                    f.write("\n);\n")
                    
                    # Get indexes
                    indexes = inspector.get_indexes(table)
                    for idx in indexes:
                        if not idx.get('unique'):  # Skip unique indexes (already in constraints)
                            idx_cols = ', '.join(idx['column_names'])
                            idx_name = idx['name']
                            f.write(f"CREATE INDEX {idx_name} ON {table}({idx_cols});\n")
                    
                    f.write("\n")
                
                f.write("\n")
                f.write("-- ============================================\n")
                f.write("-- SCHEMA EXPORT COMPLETE\n")
                f.write("-- ============================================\n")
        
        print(f"✅ Schema exported successfully!")
        print(f"   File: {output_file}")
        print(f"   Size: {output_file.stat().st_size} bytes")
        
        # Also create a latest.sql symlink/copy
        latest_file = output_dir / 'schema_latest.sql'
        import shutil
        shutil.copy(output_file, latest_file)
        print(f"   Latest: {latest_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = export_schema()
    sys.exit(0 if success else 1)
