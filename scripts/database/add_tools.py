import psycopg2
from datetime import datetime

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="agenticrag",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

# Essential tools
tools = [
    ('http_request', 'HTTP Request', 'Make HTTP requests to any API endpoint', 'api', 'globe'),
    ('calculator', 'Calculator', 'Perform mathematical calculations', 'utility', 'calculator'),
    ('vector_search', 'Vector Search', 'Search in vector database', 'data', 'search'),
    ('web_search', 'Web Search', 'Search the web using DuckDuckGo', 'search', 'globe'),
    ('python_executor', 'Python Executor', 'Execute Python code', 'code', 'code'),
    ('slack', 'Slack', 'Send messages to Slack', 'communication', 'message-square'),
    ('gmail', 'Gmail', 'Send and manage emails', 'communication', 'mail'),
    ('discord', 'Discord', 'Send messages to Discord', 'communication', 'message-square'),
]

for tool_id, name, description, category, icon in tools:
    cur.execute("""
        INSERT INTO tools (id, name, description, category, input_schema, implementation_type, is_builtin, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, 'builtin', true, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            category = EXCLUDED.category,
            updated_at = NOW()
    """, (tool_id, name, description, category, '{}'))
    print(f"✅ Added/Updated: {tool_id}")

conn.commit()

# Count total tools
cur.execute("SELECT COUNT(*) FROM tools")
count = cur.fetchone()[0]
print(f"\n📊 Total tools in database: {count}")

cur.close()
conn.close()
print("✅ Done!")
