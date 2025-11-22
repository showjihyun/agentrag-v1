"""
Add Python Code Tool to the database.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from backend.db.models.agent_builder import Tool
from backend.config import settings
from datetime import datetime
import uuid

def add_python_code_tool():
    """Add Python Code Tool to database."""
    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db: Session = SessionLocal()
    
    try:
        # Check if tool already exists
        existing = db.query(Tool).filter(Tool.id == 'python_code').first()
        
        if existing:
            print("✅ Python Code Tool already exists, updating...")
            tool = existing
        else:
            print("➕ Adding Python Code Tool...")
            tool = Tool(id='python_code')
        
        # Update tool properties
        tool.name = 'Python Code'
        tool.description = 'Execute Python code in a secure sandbox environment (n8n style)'
        tool.category = 'code'
        tool.icon = '🐍'
        tool.bg_color = '#3776AB'
        tool.is_active = True
        tool.config = {
            'params': {
                'code': {
                    'type': 'code',
                    'description': 'Python code to execute',
                    'required': True,
                    'placeholder': '# Access input data\nresult = input["value"] * 2',
                    'language': 'python',
                },
                'mode': {
                    'type': 'select',
                    'description': 'Execution mode',
                    'enum': ['simple', 'advanced'],
                    'default': 'simple',
                    'helpText': 'Simple: expressions, Advanced: full scripts',
                },
                'timeout': {
                    'type': 'number',
                    'description': 'Execution timeout (seconds)',
                    'default': 30,
                    'min': 1,
                    'max': 300,
                },
            },
            'outputs': {
                'result': {
                    'type': 'any',
                    'description': 'Execution result',
                },
                'stdout': {
                    'type': 'string',
                    'description': 'Standard output',
                },
                'stderr': {
                    'type': 'string',
                    'description': 'Standard error',
                },
            },
            'examples': [
                {
                    'name': 'Simple Calculation',
                    'description': 'Calculate sum of numbers',
                    'config': {
                        'code': "result = sum(input['numbers'])",
                        'mode': 'simple',
                    }
                },
                {
                    'name': 'Data Filtering',
                    'description': 'Filter and transform data',
                    'config': {
                        'code': "items = input['items']\nactive_items = [x for x in items if x['status'] == 'active']\nresult = {'total': len(active_items), 'items': active_items}",
                        'mode': 'advanced',
                    }
                },
                {
                    'name': 'JSON Processing',
                    'description': 'Parse and transform JSON data',
                    'config': {
                        'code': "import json\ndata = json.loads(input['json_string'])\nresult = {'parsed': data, 'keys': list(data.keys())}",
                        'mode': 'advanced',
                    }
                },
            ],
        }
        tool.docs_link = 'https://docs.python.org/3/'
        tool.updated_at = datetime.utcnow()
        
        if not existing:
            tool.created_at = datetime.utcnow()
            db.add(tool)
        
        db.commit()
        
        print("✅ Python Code Tool added successfully!")
        print(f"   ID: {tool.id}")
        print(f"   Name: {tool.name}")
        print(f"   Category: {tool.category}")
        
    except Exception as e:
        print(f"❌ Error adding Python Code Tool: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_python_code_tool()
