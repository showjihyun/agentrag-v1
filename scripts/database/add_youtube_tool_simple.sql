-- Add youtube_search tool to database

-- Check if tool exists
SELECT COUNT(*) as tool_exists FROM tools WHERE id = 'youtube_search';

-- Insert youtube_search tool if not exists
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
)
SELECT 
    'youtube_search',
    'YouTube Search',
    'Search YouTube videos using YouTube Data API. Returns video titles, descriptions, and URLs.',
    'search',
    '{"type": "object", "properties": {"query": {"type": "string", "description": "Search query for YouTube videos", "required": true}, "max_results": {"type": "integer", "description": "Maximum number of results to return (default: 5)", "required": false}}, "required": ["query"]}'::json,
    '{"type": "object", "properties": {"videos": {"type": "array", "description": "List of video results"}}}'::json,
    'registry',
    'ToolRegistry.youtube_search',
    true,
    true,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM tools WHERE id = 'youtube_search'
);

-- Verify
SELECT id, name, category, is_builtin FROM tools WHERE id = 'youtube_search';

-- Show all tools
SELECT id, name, category FROM tools ORDER BY category, name;
