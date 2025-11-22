"""
Add AI Agent Tool to Database

n8n-style AI Agent with Memory Management
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from config import settings
import json

def add_ai_agent_tool():
    """Add AI Agent tool to database."""
    
    engine = create_engine(settings.DATABASE_URL)
    
    tool_data = {
        'id': 'ai_agent',
        'name': 'AI Agent',
        'description': 'Advanced AI Agent with Memory Management (n8n style). Supports multiple LLM providers and Short/Mid/Long Term Memory.',
        'category': 'ai',
        'implementation_type': 'builtin',
        'implementation_ref': 'backend.services.tools.ai.ai_agent_executor.AIAgentExecutor',
        'requires_auth': True,
        'is_builtin': True,
        'input_schema': json.dumps({
            'provider': {
                'type': 'select',
                'description': 'LLM Provider',
                'required': True,
                'enum': ['openai', 'anthropic', 'ollama', 'azure_openai'],
                'default': 'openai'
            },
            'model': {
                'type': 'select',
                'description': 'Model',
                'required': True,
                'enum': [
                    'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo',
                    'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022',
                    'llama3.1:8b', 'llama3.1:70b'
                ],
                'default': 'gpt-4'
            },
            'system_prompt': {
                'type': 'textarea',
                'description': 'System Prompt',
                'required': False
            },
            'user_message': {
                'type': 'textarea',
                'description': 'User Message',
                'required': True
            },
            'enable_memory': {
                'type': 'boolean',
                'description': 'Enable Memory',
                'required': False,
                'default': True
            },
            'memory_type': {
                'type': 'select',
                'description': 'Memory Type',
                'required': False,
                'enum': ['short_term', 'mid_term', 'long_term', 'all'],
                'default': 'short_term'
            },
            'temperature': {
                'type': 'number',
                'description': 'Temperature',
                'required': False,
                'default': 0.7,
                'min': 0,
                'max': 2
            },
            'max_tokens': {
                'type': 'number',
                'description': 'Max Tokens',
                'required': False,
                'default': 1000,
                'min': 1,
                'max': 4096
            }
        }),
        'output_schema': json.dumps({
            'content': {
                'type': 'string',
                'description': 'AI response content'
            },
            'metadata': {
                'type': 'object',
                'description': 'Usage stats and metadata'
            }
        })
    }
    
    with engine.connect() as conn:
        # Check if tool already exists
        result = conn.execute(
            text("SELECT id FROM tools WHERE id = :id"),
            {"id": tool_data['id']}
        )
        
        if result.fetchone():
            print(f"[OK] Tool '{tool_data['name']}' already exists")
            
            # Update existing tool
            conn.execute(
                text("""
                    UPDATE tools 
                    SET name = :name,
                        description = :description,
                        category = :category,
                        implementation_type = :implementation_type,
                        implementation_ref = :implementation_ref,
                        requires_auth = :requires_auth,
                        is_builtin = :is_builtin,
                        input_schema = :input_schema,
                        output_schema = :output_schema,
                        updated_at = NOW()
                    WHERE id = :id
                """),
                tool_data
            )
            conn.commit()
            print(f"[OK] Updated tool '{tool_data['name']}'")
        else:
            # Insert new tool
            conn.execute(
                text("""
                    INSERT INTO tools (id, name, description, category, implementation_type, implementation_ref, requires_auth, is_builtin, input_schema, output_schema, created_at, updated_at)
                    VALUES (:id, :name, :description, :category, :implementation_type, :implementation_ref, :requires_auth, :is_builtin, :input_schema, :output_schema, NOW(), NOW())
                """),
                tool_data
            )
            conn.commit()
            print(f"[OK] Added new tool '{tool_data['name']}'")
    
    print("\n" + "="*60)
    print("AI Agent Tool Configuration")
    print("="*60)
    print(f"ID: {tool_data['id']}")
    print(f"Name: {tool_data['name']}")
    print(f"Category: {tool_data['category']}")
    print(f"Features:")
    print("  - Multiple LLM providers (OpenAI, Anthropic, Ollama)")
    print("  - Short Term Memory (current session)")
    print("  - Mid Term Memory (session context)")
    print("  - Long Term Memory (persistent knowledge)")
    print("  - Advanced generation parameters")
    print("  - JSON extraction")
    print("  - Context management")
    print("="*60)

if __name__ == "__main__":
    try:
        add_ai_agent_tool()
        print("\n[SUCCESS] AI Agent Tool added successfully!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
