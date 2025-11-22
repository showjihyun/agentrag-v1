-- Add Python Code Tool to the database
INSERT INTO tools (
    id,
    name,
    description,
    category,
    icon,
    config_schema,
    requires_auth,
    is_active,
    created_at,
    updated_at
) VALUES (
    'python_code',
    'Python Code Executor',
    'Execute Python code in a secure sandbox environment. Supports data processing, calculations, and automation tasks.',
    'code',
    '🐍',
    '{
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute",
                "required": true
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
    }'::jsonb,
    false,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    config_schema = EXCLUDED.config_schema,
    updated_at = NOW();
