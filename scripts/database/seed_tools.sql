-- Seed essential tools into the database
-- Run with: psql -h localhost -p 5433 -U postgres -d agentic_rag -f seed_tools.sql

INSERT INTO tools (id, name, description, category, icon, is_active, created_at, updated_at)
VALUES 
    ('http_request', 'HTTP Request', 'Make HTTP requests to any API endpoint', 'api', 'globe', true, NOW(), NOW()),
    ('calculator', 'Calculator', 'Perform mathematical calculations', 'utility', 'calculator', true, NOW(), NOW()),
    ('vector_search', 'Vector Search', 'Search in vector database', 'data', 'search', true, NOW(), NOW()),
    ('web_search', 'Web Search', 'Search the web using DuckDuckGo', 'search', 'globe', true, NOW(), NOW()),
    ('python_executor', 'Python Executor', 'Execute Python code', 'code', 'code', true, NOW(), NOW()),
    ('slack', 'Slack', 'Send messages to Slack', 'communication', 'message-square', true, NOW(), NOW()),
    ('gmail', 'Gmail', 'Send and manage emails', 'communication', 'mail', true, NOW(), NOW()),
    ('discord', 'Discord', 'Send messages to Discord', 'communication', 'message-square', true, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    icon = EXCLUDED.icon,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

SELECT COUNT(*) as total_tools FROM tools;
