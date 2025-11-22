"""
Add Python Code Tool directly using psycopg2.
"""

import psycopg2
from datetime import datetime
import json

def add_python_code_tool():
    """Add Python Code Tool to database using direct SQL."""
    
    # Database connection
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="agenticrag",
        user="postgres",
        password="postgres"
    )
    
    try:
        cursor = conn.cursor()
        
        # Tool configuration
        config_schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                    "required": True
                },
                "timeout": {
                    "type": "number",
                    "description": "Execution timeout in seconds",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300
                },
                "allowed_imports": {
                    "type": "array",
                    "description": "List of allowed Python modules",
                    "items": {"type": "string"},
                    "default": ["math", "json", "datetime", "re"]
                }
            }
        }
        
        # Insert or update tool
        cursor.execute("""
            INSERT INTO tools (
                id,
                name,
                description,
                category,
                input_schema,
                output_schema,
                implementation_type,
                implementation_ref,
                requires_auth,
                is_builtin,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                input_schema = EXCLUDED.input_schema,
                updated_at = EXCLUDED.updated_at
        """, (
            'python_code',
            'Python Code Executor',
            'Execute Python code in a secure sandbox environment. Supports data processing, calculations, and automation tasks.',
            'code',
            json.dumps(config_schema),
            json.dumps({"type": "object", "properties": {"result": {"type": "string"}, "output": {"type": "string"}}}),
            'custom',
            'backend.services.tools.code.python_executor.PythonCodeExecutor',
            False,
            True,
            datetime.now(),
            datetime.now()
        ))
        
        conn.commit()
        print("✅ Python Code Tool added successfully!")
        
        # Verify
        cursor.execute("SELECT id, name, category FROM tools WHERE id = 'python_code'")
        result = cursor.fetchone()
        if result:
            print(f"   ID: {result[0]}")
            print(f"   Name: {result[1]}")
            print(f"   Category: {result[2]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_python_code_tool()
