#!/usr/bin/env python
"""Clean up and consolidate Alembic migration files."""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def cleanup_migrations():
    """Archive old migration files and keep only essential ones."""
    
    print("=" * 80)
    print("ALEMBIC MIGRATION CLEANUP")
    print("=" * 80)
    
    versions_dir = Path(__file__).parent.parent / 'alembic' / 'versions'
    archive_dir = versions_dir / 'archive'
    archive_dir.mkdir(exist_ok=True)
    
    # Essential migrations to keep (in order)
    essential_migrations = [
        '9ce227b568e8_initial_schema.py',
        '20260115220929_add_context_and_mcp_to_agents.py',
        '20260120_create_missing_tables.py',
        '20260120_create_plugin_marketplace_tables.py',
    ]
    
    # Get all migration files
    all_files = list(versions_dir.glob('*.py'))
    all_files = [f for f in all_files if f.name != '__init__.py']
    
    print(f"\n✓ Found {len(all_files)} migration files")
    print(f"✓ Essential migrations: {len(essential_migrations)}")
    
    # Separate essential and non-essential
    essential_files = []
    archive_files = []
    
    for file in all_files:
        if file.name in essential_migrations:
            essential_files.append(file)
        else:
            archive_files.append(file)
    
    print(f"\n📦 Files to archive: {len(archive_files)}")
    
    if not archive_files:
        print("✅ No files to archive!")
        return True
    
    # Ask for confirmation
    print("\nFiles to be archived:")
    for file in sorted(archive_files):
        print(f"  • {file.name}")
    
    response = input("\nProceed with archiving? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Cancelled")
        return False
    
    # Archive files
    archived_count = 0
    for file in archive_files:
        try:
            dest = archive_dir / file.name
            file.rename(dest)
            archived_count += 1
            print(f"  ✓ Archived: {file.name}")
        except Exception as e:
            print(f"  ✗ Failed to archive {file.name}: {e}")
    
    print(f"\n✅ Archived {archived_count} files")
    print(f"✓ Remaining migrations: {len(essential_files)}")
    
    # Create README in archive
    readme_path = archive_dir / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"# Archived Migrations\n\n")
        f.write(f"**Archived on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"These migration files have been archived as they are no longer needed.\n")
        f.write(f"The database schema has been consolidated into essential migrations.\n\n")
        f.write(f"## Archived Files ({len(archive_files)})\n\n")
        for file in sorted(archive_files):
            f.write(f"- {file.name}\n")
    
    print(f"\n✓ Created archive README: {readme_path}")
    
    # List remaining migrations
    print("\n" + "=" * 80)
    print("REMAINING MIGRATIONS")
    print("=" * 80)
    
    remaining = sorted(versions_dir.glob('*.py'))
    remaining = [f for f in remaining if f.name != '__init__.py']
    
    for i, file in enumerate(remaining, 1):
        print(f"{i}. {file.name}")
    
    return True


if __name__ == "__main__":
    success = cleanup_migrations()
    sys.exit(0 if success else 1)
